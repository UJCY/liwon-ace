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

import check_grounding

CONTAINER = os.environ.get("CX_PG", "cx-pg")

# 저작 — 사람이 썼다. graph/schema.md 의 관계 7종에 한국어 표층형을 붙인 것이다.
# 어간은 불변 접두사까지만 줄이고(맡), ㄹ 말음 어간은 맞춤법 18항 ㄹ 탈락 짝으로
# 둔다(이끌·이끄·이끕). 잔여 한계와 근거는 src/tools/knowledge-graph.ts 와
# docs/references/korean-inflection-matching.md (#32). **서버와 같은 목록이어야 한다.**
RELATION_WORDS = {
    "LEADS":            ["이끌", "이끄", "이끕", "리드", "맡", "총괄"],
    "BELONGS_TO":       ["소속", "속한", "어느 팀", "어느 부서"],
    "MANAGES_ACCOUNT":  ["담당", "관리"],
    "USES":             ["사용", "쓰는", "쓰고", "도입"],
    "HAS_PROJECT":      ["프로젝트"],
    "REPORTED_ISSUE":   ["이슈", "장애", "문제"],
    "HEAD_IS":          ["팀장", "부서장", "책임자"],
}

# 최상급·타입 표층형 — src/tools/knowledge-graph.ts 와 같은 목록·같은 정의 순서다
# (마지막 타입 어휘의 동순위 처리까지 순서에 물린다).
SUPERLATIVE_WORDS = ["가장", "제일", "최다"]
TYPE_WORDS = {
    "employee":   ["직원", "사원"],
    "project":    ["프로젝트"],
    "client":     ["고객사", "고객"],
    "product":    ["제품"],
    "department": ["부서", "팀"],
}


def _asked_type(question):
    """질문의 **마지막** 타입 어휘가 가리키는 노드 타입 — 한국어는 묻는 명사가 문미에 온다."""
    best, pos = None, -1
    for t, ws in TYPE_WORDS.items():
        for w in ws:
            i = question.rfind(w)
            if i > pos:
                pos, best = i, t
    return best
# 미등록 개체를 알아보기 위한 상호 접미사. 데이터에 없는 이름을 잡아야 하므로
# 데이터에서 뽑을 수 없다 (T5 는 정의상 데이터 밖이다).
# **라우터와 같은 자산을 읽는다** — 목록이 갈라지면 라우터가 거절한 질문이 여기 닿지 못한다.
_EP = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "assets", "entity-patterns.json"), encoding="utf-8"))
COMPANY_SUFFIX = _EP["company_suffix"]
ID_PREFIXES = _EP["id_prefixes"]


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
    # 접두사 목록도 자산에서 읽고 대소문자를 무시한다 — src/tools/entities.ts 의
    # ID_RE 가 `gi` 플래그로 같은 목록을 쓴다. 하드코딩해 두면 `project-7`·
    # `employee-99`·`dept-3` 이 서버에서만 미등록 언급으로 잡혀 T5 가 갈린다.
    unmatched = []
    for pat, flags in ((r"(?:" + "|".join(ID_PREFIXES) + r")[- ]?[A-Za-z0-9]+", re.I),
                       (r"[가-힣]{2,5}(?:" + "|".join(COMPANY_SUFFIX) + ")", 0)):
        for m in re.finditer(pat, question, flags):
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
    """개체 식별 → 관계 순회. 빈손이면 인접 사실을 함께 돌려준다.

    실행 실패는 **도구 안에서** 구조화로 바꾼다 (D14, edge-cases.md T6) —
    `psql()` 이 RuntimeError 를 던지므로 이것으로 충분하다.
    src/tools/knowledge-graph.ts 의 래퍼와 같은 판정이어야 한다.
    """
    try:
        return _knowledge_graph(question)
    except RuntimeError as e:
        return {"status": "error", "reason": str(e)[:120]}            # T6


def _knowledge_graph(question):
    matched, unmatched = find_entities(question)
    if unmatched and not matched:
        # `searched` 는 자산 이름이다 (src/tools/types.ts Asset = documents|graph|tables).
        return {"status": "entity_not_found", "entity": unmatched[0],
                "searched": "graph"}                                 # T5
    if not matched:
        # 개체 **언급 자체가 없는** 질문이다 (집계·최상급 등). 부재가 아니라 무관이다.
        # 관계 전체를 세는 질의로 넘긴다 — 빈손이면 no_result 이지 entity_not_found 가 아니다.
        wanted = requested_relations(question)
        if not wanted:
            return {"status": "no_result", "asset": "graph"}
        rel = ",".join("'" + r + "'" for r in wanted)
        # 최상급 + 타입 어휘가 걸리면 관계 총계가 아니라 개체별 최다를 센다 (#32).
        # 물어본 타입이 있는 쪽 끝만 세고, 동률은 전부 싣는다 — 서버와 같은 판정.
        if any(w in question for w in SUPERLATIVE_WORDS):
            t = _asked_type(question)
            if t:
                top = psql(f"""WITH ends AS (
                                 SELECT e.relation, n.name FROM edges e
                                   JOIN nodes n ON n.id = e.source
                                  WHERE e.relation IN ({rel}) AND n.type = '{t}'
                                 UNION ALL
                                 SELECT e.relation, n.name FROM edges e
                                   JOIN nodes n ON n.id = e.target
                                  WHERE e.relation IN ({rel}) AND n.type = '{t}'),
                               counted AS (SELECT relation, name, count(*) AS n
                                             FROM ends GROUP BY relation, name)
                               SELECT relation, name, n::text
                                 FROM (SELECT relation, name, n,
                                              rank() OVER (PARTITION BY relation
                                                           ORDER BY n DESC) AS rk
                                         FROM counted) ranked
                                WHERE rk = 1 ORDER BY relation, name;""")
                if top:
                    return {"status": "ok",
                            "data": [{"relation": r, "name": nm, "count": c}
                                     for r, nm, c in top]}
                # 빈손이면 아래 총계로 떨어진다 — 타입 어휘 부재와 같은 폴백.
        hits = psql(f"""SELECT e.relation, count(*) FROM edges e
                        WHERE e.relation IN ({rel}) GROUP BY e.relation;""")
        # `count` 는 **문자열이다** — 서버의 `count(*)::text` 와 맞춘 것이고, 숫자로
        # 바꾸면 `X1-01` 이 5/5 오답이 된다. 소형 모델이 숫자 표현에 민감하다.
        # 빈손이면 `data` 가 아니라 `asset` 을 실은 NoResult 다 (types.ts) — 서버와 같다.
        # 지금 이 분기에 닿는 문항이 없어 **넓힌 대조도 이것을 못 잡는다** (4.6 이 적은 종류).
        if not hits:
            return {"status": "no_result", "asset": "graph"}
        return {"status": "ok", "data": [{"relation": r, "count": c} for r, c in hits]}
    # 같은 이름이 여럿을 가리키면 관계를 합쳐서 답하면 안 된다 — 어느 쪽인지 모른다.
    # src/tools/knowledge-graph.ts 와 같은 판정이어야 한다 (대조: scripts/dump-server.mjs).
    by_name = {}
    for e in matched:
        by_name.setdefault(e["name"], []).append(e)
    for name, group in by_name.items():
        if len(group) < 2:
            continue
        gid = ",".join("'" + _q(g["id"]) + "'" for g in group)
        hints = psql(f"""SELECT n.id, n.type,
                                coalesce(string_agg(DISTINCT m.name, ', '), '(관계 없음)')
                           FROM nodes n LEFT JOIN edges e ON e.source = n.id
                           LEFT JOIN nodes m ON m.id = e.target
                          WHERE n.id IN ({gid}) GROUP BY n.id, n.type;""")
        return {"status": "ambiguous_entity", "name": name,
                "candidates": [{"id": a, "type": b, "hint": c} for a, b, c in hints]}

    ids = ",".join("'" + _q(e["id"]) + "'" for e in matched)
    wanted = requested_relations(question)
    if wanted:
        rel = ",".join("'" + r + "'" for r in wanted)
        # 행마다 앵커(질문이 가리킨 매칭 개체)를 entity 로 싣는다 —
        # src/tools/knowledge-graph.ts 의 traverse 와 같은 모양이어야 한다 (#26).
        # ORDER BY 는 대조 요건이다 — 앵커 조인 후 순서가 실행 계획 종속이 되어
        # 두 구현이 같은 행을 다른 순서로 냈다. 정렬은 DB 에서 한다 (아래 세 질의 공통)
        hits = psql(f"""SELECT a.name, e.relation, n.name FROM edges e
                        JOIN nodes n ON n.id = e.target JOIN nodes a ON a.id = e.source
                        WHERE e.source IN ({ids}) AND e.relation IN ({rel})
                        UNION ALL
                        SELECT a.name, e.relation, n.name FROM edges e
                        JOIN nodes n ON n.id = e.source JOIN nodes a ON a.id = e.target
                        WHERE e.target IN ({ids}) AND e.relation IN ({rel})
                        ORDER BY 1, 2, 3;""")
        if hits:
            return {"status": "ok",
                    "data": [{"entity": a, "relation": r, "name": t} for a, r, t in hits]}
        # T7 — 개체는 있는데 요구한 관계가 없다. 다른 관계를 인접 사실로 돌려준다
        adj = psql(f"""SELECT a.name, e.relation, n.name FROM edges e
                       JOIN nodes n ON n.id = e.target JOIN nodes a ON a.id = e.source
                       WHERE e.source IN ({ids})
                       UNION ALL
                       SELECT a.name, e.relation, n.name FROM edges e
                       JOIN nodes n ON n.id = e.source JOIN nodes a ON a.id = e.target
                       WHERE e.target IN ({ids})
                       ORDER BY 1, 2, 3;""")
        return {"status": "partial", "requested_form": "entity_list",
                "unavailable": {"asset": "graph", "reason": "relation_absent",
                                "relation": wanted},
                "adjacent_facts": {"source": "graph",
                                   "data": [{"entity": a, "relation": r, "name": t}
                                            for a, r, t in adj]}}
    hits = psql(f"""SELECT a.name, e.relation, n.name FROM edges e
                    JOIN nodes n ON n.id = e.target JOIN nodes a ON a.id = e.source
                    WHERE e.source IN ({ids})
                    UNION ALL
                    SELECT a.name, e.relation, n.name FROM edges e
                    JOIN nodes n ON n.id = e.source JOIN nodes a ON a.id = e.target
                    WHERE e.target IN ({ids})
                       ORDER BY 1, 2, 3;""")
    if hits:
        return {"status": "ok",
                "data": [{"entity": a, "relation": r, "name": t} for a, r, t in hits]}
    # 관계가 하나도 없다. **partial 로 내지 않는다** — partial 은 `unavailable` 과
    # `adjacent_facts` 를 분리해 담아야 하는 타입인데(D10 · types.ts PartialResult)
    # 여기엔 붙일 인접 사실이 없다. src/tools/knowledge-graph.ts 와 같은 판정이다.
    return {"status": "no_result", "asset": "graph"}


def _chunk_row(row):
    """반환 행의 모양 — src/tools/vector-search.ts 의 `shape` 와 같아야 한다.

    **본문을 싣는다** (#25). 종전에는 `doc` 과 `sim` 만 돌려주어, 내용을 요구하는
    질문에서 요구된 답이 에이전트 컨텍스트에 물리적으로 존재할 수 없었다.
    **유사도를 반올림하지 않는다** — 서버가 그렇고, 줄여 봤더니 `X5-02` 가 뒤집혔다.
    """
    doc, content, sim = row
    return {"doc": doc, "content": content, "sim": float(sim)}


def graph_facts(r):
    """그래프 결과에서 **사실 목록만** 꺼낸다 — src/tools/knowledge-graph.ts 의 `graphFacts`.

    어느 상태가 사실을 어느 필드에 담는지는 이쪽이 안다. 호출자가 `ok` 는 `data`,
    `partial` 은 `adjacent_facts.data` 라고 분기하면 상태를 하나 더할 때마다
    호출자도 같이 고쳐야 한다.
    """
    if r["status"] == "ok":
        return r["data"]
    if r["status"] == "partial":
        return r["adjacent_facts"]["data"]
    return []


# 파생 — build_assets.py 가 index.json 기술문서 제목에서 뽑은 제품 × 기술주제 격자 (#13).
# **서버와 같은 자산을 읽는다** — src/assets.ts 의 docTopics.
_DT = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "assets", "doc-topics.json"), encoding="utf-8"))


def _form_gap(question, matched):
    """제품 × 기술주제 격자 검사 (#13, T4-form) — src/tools/vector-search.ts 의 `formGap`.

    질문이 기술주제 어휘를 담고 매칭 개체에 제품이 있는데 어느 제품도 그 주제를
    커버하지 않으면, 개체 청크가 있어도 요구 형태가 없는 것이다 — `ok` 가 아니라
    `partial`. 유사도로는 못 가른다 — X5-02(0.520)가 X4-01(0.494)보다 높다 (실측).
    주제어가 여럿이면 하나라도 커버될 때 검사를 통과시킨다 (보수 방향).
    """
    requested = [t for t in _DT["topics"] if t in question]
    products = [e for e in matched if e["type"] == "product"]
    if not requested or not products:
        return False
    covered = {t for p in products for t in _DT["coverage"].get(p["name"], [])}
    return not any(t in covered for t in requested)


def vector_search(question, qvec, threshold):
    """문서 청크 유사도 검색. 임계 미만이면 T4 — 인접 사실이 있으면 부분 응답.

    knowledge_graph 와 같은 T6 래퍼를 쓴다 (D14).
    """
    try:
        return _vector_search(question, qvec, threshold)
    except RuntimeError as e:
        return {"status": "error", "reason": str(e)[:120]}            # T6


def _vector_search(question, qvec, threshold):
    v = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
    matched, _ = find_entities(question)

    # **개체를 지목한 질문은 그 개체를 담은 청크로 좁혀서 찾는다** (하이브리드 검색).
    # 순수 유사도만 쓰면 개체명이 질문의 의미 벡터에 거의 기여하지 않아
    # 정작 그 개체를 다루는 청크가 상위에 안 든다 — Client-A 를 담은 청크 2개가
    # 상위 5에 못 드는 것을 실측했다. 좁혀서 0건이면 그것이 T4 다.
    if matched:
        # ILIKE — 대소문자를 구분하지 않는다. src/tools/vector-search.ts 와 맞춘 것이다.
        # 이 데이터셋의 개체명은 대소문자가 하나뿐이라 결과가 같지만, 두 구현이
        # 다른 연산자를 쓰면 언젠가 갈라진다 (대조: scripts/dump-server.mjs).
        names = " OR ".join("content ILIKE '%" + _q(e["name"]) + "%'" for e in matched)
        rows = psql(f"""SELECT doc_id, content, 1 - (embedding <=> '{v}') AS sim
                        FROM document_chunks WHERE {names}
                        ORDER BY embedding <=> '{v}' LIMIT 5;""")
        top = [(d, c, float(s)) for d, c, s in rows]
        if top and not _form_gap(question, matched):
            return {"status": "ok", "data": [_chunk_row(r) for r in top]}
        # 개체 청크 0건(T4) 또는 격자 빈칸(T4-form, #13) — 아래에서 인접 사실을 붙여
        # 부분 응답으로 승격한다. 격자 빈칸일 때 찾아 둔 청크는 싣지 않는다 —
        # "API 인증" 질문 옆에 "API 키" 든 설치 본문을 놓으면 Q1 환각의 정확한 지점이다 (D10).
    else:
        rows = psql(f"""SELECT doc_id, content, 1 - (embedding <=> '{v}') AS sim
                        FROM document_chunks ORDER BY embedding <=> '{v}' LIMIT 5;""")
        top = [(d, c, float(s)) for d, c, s in rows]
        if top and top[0][2] >= threshold:
            return {"status": "ok", "data": [_chunk_row(r) for r in top]}
                                                                      # T4 → X5 승격 후보
    if matched:
        # **그래프 질의를 여기서 다시 짜지 않는다.** 사본을 두면 그것이 출하물과 갈라져도
        # 대조가 통과한다 — 실제로 그랬다: 관계 필터와 양방향 순회가 빠져 `X5-01` 이
        # 서버와 다른 인접 사실을 냈다. `src/tools/vector-search.ts` 와 같이 도구를 부른다.
        adj = graph_facts(knowledge_graph(question))
        return {"status": "partial", "requested_form": "narrative",
                "unavailable": {"asset": "documents",
                                "reason": "no_document_for_entity" if not adj else "form_not_covered"},
                # `source` 는 자산 이름이다 — types.ts 의 Asset 에 knowledge_graph 는 없다.
                "adjacent_facts": {"source": "graph", "data": adj}}
    return {"status": "no_result", "asset": "documents"}              # T4 단독

# ── 요구 원소가 둘인가 (D11-4) ─────────────────────────────────────────────
# 저작 — 한국어 접속 표층형. "요구 원소 2개"는 문서가 정의한 개념이고(D11-4),
# 그것이 한국어 문장에서 드러나는 자리는 접속이다.
# **이 신호만으로는 병렬을 확정하지 않는다** — 접속된 두 요구가 같은 도구에 걸리면
# 단일 선택이다(X1·X2). 그래서 후보를 실제로 태워 둘 다 내용이 있을 때만 병렬로 굳힌다.
#
# **문항 문면을 그대로 옮긴 패턴은 두지 않는다 (D7).** `는지와`·`현황과` 는 채점
# 대상인 X4-02·X4-01 의 문면에서만 나왔고, `그리고`·`[고]\s+[그왜어]` 는 두 세트
# 어디에도 걸리지 않았다. 넷 다 일반형에 흡수되거나 사문이라 지워도 점수가 같다.
CONJUNCTION = [r"[고]\s*,", r"[가-힣]과\s", r"[가-힣]와\s",
               r"\?\s*\S", r"[가-힣],\s*[가-힣]"]


def has_two_requests(question):
    import re
    return any(re.search(p, question) for p in CONJUNCTION)


# ── nl2sql 실행부 ────────────────────────────────────────────────────────
_A = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
_MODEL = json.load(open(os.path.join(_A, "model.json"), encoding="utf-8"))["llm"]
_SCHEMA = open(os.path.join(_A, "schema-annotated.sql"), encoding="utf-8").read()


def _sql_prompt(question):
    import re
    md = open(os.path.join(_A, "prompts", "nl2sql.md"), encoding="utf-8").read()
    tpl = re.search(r"```\n(.*?)```", md, re.S).group(1)
    return tpl.replace("{{SCHEMA}}", _SCHEMA).replace("{{QUESTION}}", question)


# 접지 검출 (D18) — **정의는 check_grounding.py 한 곳에 있다.** 여기는 그것을 부르고
# 채택 정책(숫자 ×10 + 문자열 오배치)으로 거를 뿐이다. 서버 `src/tools/nl2sql.ts` 가
# 같은 판정을 이식해 갖고 있고, 두 구현은 같은 SQL 에 같은 결과를 내야 한다.
_RANGES = check_grounding.load_ranges()          # json 하나라 모듈 로드 시 읽어도 싸다
_TXT_COLS = None


def _txt_cols():
    """텍스트 컬럼 목록 — 첫 호출에서 한 번만 묻는다 (스키마는 실행 중 안 바뀐다)."""
    global _TXT_COLS
    if _TXT_COLS is None:
        _TXT_COLS = check_grounding.text_columns()
    return _TXT_COLS


def _empty_handed(rows):
    """빈손인가 — 0행, 또는 집계 0/NULL 한 행. 격자 `zero_result` 정의 그대로다.

    적발 22/22 · 오인 0 이 정확히 이 정의 위에서 검증됐으므로 **넓히지 않는다**.
    psql --csv 는 NULL 을 `""` 로, COUNT 를 `"0"` 으로 준다 (서버 쪽은 None / "0").
    """
    return not rows or (len(rows) == 1 and len(rows[0]) == 1 and rows[0][0] in ("", "0"))


def nl2sql(question):
    """SQL 생성 → 실행. 빈손이면 접지를 보고 T3 와 T9 를 가른다 (edge-cases.md T3·T9)."""
    import re, urllib.request
    body = {"model": _MODEL["name"], "prompt": _sql_prompt(question), "stream": False,
            "options": _MODEL["options"]}
    if not _MODEL.get("think", False):
        body["think"] = False
    req = urllib.request.Request("http://localhost:11434/api/generate",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    raw = json.loads(urllib.request.urlopen(req, timeout=900).read())["response"]
    m = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.S)
    if m:
        raw = m.group(1)
    m = re.search(r"(SELECT\b.*?)(?:;|$)", raw, re.S | re.I)
    sql = (m.group(1).strip() if m else raw.strip())
    if not re.match(r"^\s*SELECT\b", sql, re.I):
        return {"status": "error", "reason": "not_select"}          # T2
    try:
        rows = psql(sql)
    except RuntimeError as e:
        return {"status": "error", "reason": str(e)}                # T1
    # 빈손이면 리터럴이 데이터에 접지됐는지 본다 — 0행의 이중 의미를 가른다 (D18).
    # **채택 정책 필터**: 숫자 ×10 과 문자열 오배치만. `string`(어디에도 없음)은
    # "값이 진짜 없는 정직한 질문"과 못 갈라서 뺀다 — 서버 nl2sql.ts 와 같은 자리다.
    if _empty_handed(rows):
        hits = [h for h in check_grounding.detect(sql, _RANGES, _txt_cols())
                if h["kind"] != "string"]
        if hits:
            return {"status": "ungrounded", "sql": sql, "hits": hits}   # T9
    # 집계 0 한 행 + 미적발은 여기 안 걸리고 `ok` 로 남는다 — "0건"이 정답인 질문이다.
    if not rows:
        return {"status": "no_result", "asset": "tables", "sql": sql}   # T3
    # 계약 필드는 `data` 다 (src/tools/types.ts OkResult). `sql` 은 서버와 같은 자리의
    # 부가 필드다 — 어떤 SQL 이 그 답을 냈는지 러너 출력·로그에서 봐야 한다.
    return {"status": "ok", "data": rows, "sql": sql}
