"""도구 2종의 실행부 — `vector_search` 와 `knowledge_graph`.

**이것이 실행 축을 여는 열쇠다.** `partial`(빈손인데 인접 사실은 있음)과
`entity_not_found`(개체 자체가 없음)는 라우터가 낼 수 없다 — 도구를 태워
결과를 봐야 안다 (docs/edge-cases.md T3·T4·T5·T7, docs/design.md D10).

**관계 어휘는 여기 산다. 라우터에 두지 않는다.**
D12 는 *도구 선택*에 표층 관계 어휘가 필요 없다고 정했지, 관계 *순회*에
필요 없다고 정한 것이 아니다. `knowledge_graph` 는 어느 관계를 따라갈지
알아야 하므로 그 어휘를 자기 안에 갖는다.
"""
import csv, io, json, os, subprocess

CONTAINER = os.environ.get("CX_PG", "cx-pg")

# 저작 — 사람이 썼다. graph/schema.md 의 관계 7종에 한국어 표층형을 붙인 것이다.
RELATION_WORDS = {
    "LEADS":            ["이끄", "리드", "맡고", "맡은", "총괄"],
    "BELONGS_TO":       ["소속", "속한", "어느 팀", "어느 부서"],
    "MANAGES_ACCOUNT":  ["담당", "관리하"],
    "USES":             ["사용", "쓰는", "쓰고", "도입"],
    "HAS_PROJECT":      ["프로젝트"],
    "REPORTED_ISSUE":   ["이슈", "장애", "문제"],
    "HEAD_IS":          ["팀장", "부서장", "책임자"],
}
# 미등록 개체를 알아보기 위한 상호 접미사. 데이터에 없는 이름을 잡아야 하므로
# 데이터에서 뽑을 수 없다 (T5 는 정의상 데이터 밖이다).
# **라우터와 같은 자산을 읽는다** — 목록이 갈라지면 라우터가 거절한 질문이 여기 닿지 못한다.
_EP = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "assets", "entity-patterns.json"), encoding="utf-8"))
COMPANY_SUFFIX = _EP["company_suffix"]


def psql(sql):
    p = subprocess.run(["docker", "exec", "-i", CONTAINER, "psql", "-U", "postgres",
                        "-d", "companyx", "-v", "ON_ERROR_STOP=1", "--csv"],
                       input=sql, capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise RuntimeError((p.stderr.strip().splitlines() or ["error"])[0][:90])
    rows = list(csv.reader(io.StringIO(p.stdout)))
    return rows[1:] if rows else []


def _q(s):
    return s.replace("'", "''")


def find_entities(question):
    """질문에 등장하는 개체명을 찾는다. 등록된 것과 등록되지 않은 언급을 나눈다."""
    rows = psql("SELECT id, type, name FROM nodes;")
    import re
    names = {n for _, _, n in rows if n}
    matched = [{"id": i, "type": t, "name": n} for i, t, n in rows if n and n in question]

    # 등록되지 않은 언급: 합성 패턴 초과형 · 한국어 상호형
    unmatched = []
    for pat in (r"(?:Client|Product|Employee)[- ]?[A-Za-z0-9]+",
                r"[가-힣]{2,5}(?:" + "|".join(COMPANY_SUFFIX) + ")"):
        for m in re.finditer(pat, question):
            mention = m.group(0)
            if mention not in names:
                unmatched.append(mention)

    # 미등록 언급이 등록 이름을 **포함**하면 그 등록 이름은 우연한 부분문자열이다.
    # 예: "Client-ZZ" 안의 "Client-Z" — 개체 부재(T5)를 부분 매칭이 가리면 안 된다.
    if unmatched:
        matched = [e for e in matched
                   if not any(e["name"] in u and e["name"] != u for u in unmatched)]
    return matched, sorted(set(unmatched))


def requested_relations(question):
    return [r for r, ws in RELATION_WORDS.items() if any(w in question for w in ws)]


def knowledge_graph(question):
    """개체 식별 → 관계 순회. 빈손이면 인접 사실을 함께 돌려준다."""
    matched, unmatched = find_entities(question)
    if unmatched and not matched:
        return {"status": "entity_not_found", "entity": unmatched[0],
                "searched": "knowledge_graph"}                       # T5
    if not matched:
        # 개체 **언급 자체가 없는** 질문이다 (집계·최상급 등). 부재가 아니라 무관이다.
        # 관계 전체를 세는 질의로 넘긴다 — 빈손이면 no_result 이지 entity_not_found 가 아니다.
        wanted = requested_relations(question)
        if not wanted:
            return {"status": "no_result", "asset": "graph"}
        rel = ",".join("'" + r + "'" for r in wanted)
        hits = psql(f"""SELECT e.relation, count(*) FROM edges e
                        WHERE e.relation IN ({rel}) GROUP BY e.relation;""")
        return {"status": "ok" if hits else "no_result",
                "data": [{"relation": r, "count": int(c)} for r, c in hits]}
    ids = ",".join("'" + _q(e["id"]) + "'" for e in matched)
    wanted = requested_relations(question)
    if wanted:
        rel = ",".join("'" + r + "'" for r in wanted)
        hits = psql(f"""SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.target
                        WHERE e.source IN ({ids}) AND e.relation IN ({rel})
                        UNION ALL
                        SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.source
                        WHERE e.target IN ({ids}) AND e.relation IN ({rel});""")
        if hits:
            return {"status": "ok", "data": [{"relation": r, "target": t} for r, t in hits]}
        # T7 — 개체는 있는데 요구한 관계가 없다. 다른 관계를 인접 사실로 돌려준다
        adj = psql(f"""SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.target
                       WHERE e.source IN ({ids})
                       UNION ALL
                       SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.source
                       WHERE e.target IN ({ids});""")
        return {"status": "partial", "requested_form": "entity_list",
                "unavailable": {"asset": "graph", "reason": "relation_absent",
                                "relation": wanted},
                "adjacent_facts": {"source": "graph",
                                   "data": [{"relation": r, "target": t} for r, t in adj]}}
    hits = psql(f"""SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.target
                    WHERE e.source IN ({ids})
                    UNION ALL
                    SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.source
                    WHERE e.target IN ({ids});""")
    return {"status": "ok" if hits else "partial",
            "data": [{"relation": r, "target": t} for r, t in hits]}


def vector_search(question, qvec, threshold):
    """문서 청크 유사도 검색. 임계 미만이면 T4 — 인접 사실이 있으면 부분 응답."""
    v = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
    matched, _ = find_entities(question)

    # **개체를 지목한 질문은 그 개체를 담은 청크로 좁혀서 찾는다** (하이브리드 검색).
    # 순수 유사도만 쓰면 개체명이 질문의 의미 벡터에 거의 기여하지 않아
    # 정작 그 개체를 다루는 청크가 상위에 안 든다 — Client-A 를 담은 청크 2개가
    # 상위 5에 못 드는 것을 실측했다. 좁혀서 0건이면 그것이 T4 다.
    if matched:
        names = " OR ".join("content LIKE '%" + _q(e["name"]) + "%'" for e in matched)
        rows = psql(f"""SELECT doc_id, 1 - (embedding <=> '{v}') AS sim
                        FROM document_chunks WHERE {names}
                        ORDER BY embedding <=> '{v}' LIMIT 5;""")
        top = [(d, float(s)) for d, s in rows]
        if top:
            return {"status": "ok", "data": [{"doc": d, "sim": round(s, 3)} for d, s in top]}
        # 개체를 담은 청크가 0건 — T4. 아래에서 인접 사실을 붙여 부분 응답으로 승격한다.
    else:
        rows = psql(f"""SELECT doc_id, 1 - (embedding <=> '{v}') AS sim
                        FROM document_chunks ORDER BY embedding <=> '{v}' LIMIT 5;""")
        top = [(d, float(s)) for d, s in rows]
        if top and top[0][1] >= threshold:
            return {"status": "ok", "data": [{"doc": d, "sim": round(s, 3)} for d, s in top]}
                                                                      # T4 → X5 승격 후보
    if matched:
        ids = ",".join("'" + _q(e["id"]) + "'" for e in matched)
        adj = psql(f"""SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.target
                       WHERE e.source IN ({ids}) LIMIT 10;""")
        return {"status": "partial", "requested_form": "narrative",
                "unavailable": {"asset": "documents",
                                "reason": "no_document_for_entity" if not adj else "form_not_covered"},
                "adjacent_facts": {"source": "knowledge_graph",
                                   "data": [{"relation": r, "target": t} for r, t in adj]}}
    return {"status": "no_result", "asset": "documents"}              # T4 단독
