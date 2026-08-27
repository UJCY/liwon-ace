#!/usr/bin/env python3
"""하네스 자산 생성기.

자산은 출처로 가른다. **섞어서 "생성물"이라고 부르면 안 된다.**

  파생(derived)  — 데이터셋에서 기계적으로 뽑는다. 사람 손이 닿지 않는다.
                   schema-annotated.sql · column-values.json · doc-topics.json ·
                   surface-gate.json
  저작(authored) — 사람이 쓴 것을 이 파일이 그대로 덤프한다.
                   tool-signatures.json · model.json
  혼합(mixed)    — 한 파일 안에서 **필드마다 출처가 다르다.** `_provenance` 를
                   필드별 객체로 쓴다 (docs/design.md D13).
                   pair-axes.json

**저작 자산에는 사람 판단이 들어 있다.** 특히 TOOL_SIGNATURES 는 라우터의
도구 선택 기제 전부이고, 작성자는 questions.json 30문항을 이미 읽은 사람이다 —
docs/design.md D12 가 옛 표층 사전을 기각할 때 든 논거("사람이 30문항을 읽은 뒤 썼다")가
여기에도 그대로 적용된다. 한계는 docs/harness-evaluation.md 6절에 기록돼 있다.

파생 자산의 입력은 companyx-dataset-v1.0/ 의 스키마와 데이터뿐이고,
questions.json 과 edge-set/ 은 어느 쪽 입력에도 들어가지 않는다 (docs/design.md D7).

  python3 harness/build/build_assets.py
"""
import json, re, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DS   = os.path.join(ROOT, "companyx-dataset-v1.0")
OUT  = os.path.join(ROOT, "harness", "assets")

# 금액·수량 컬럼의 단위. 데이터 값 범위로 확인했다 (salary 3736~9520 등 전부 만원 단위).
UNITS = {"salary": "만원", "price_monthly": "만원", "amount": "만원", "budget": "만원"}
UNIT_HINT = "단위: 만원 (1억원=10000, 5천만원=5000, 100만원=100)"
MAX_VALUES = 12          # 이 개수 이하인 컬럼만 값 목록을 붙인다


def read_ddl():
    ddl = open(os.path.join(DS, "sql", "01-schema.sql"), encoding="utf-8").read()
    for pat in (r"CREATE EXTENSION[^;]*;", r"CREATE INDEX[^;]*;",
                r"ALTER TABLE[^;]*;", r"SELECT setval[^;]*;", r"COMMENT ON[^;]*;"):
        ddl = re.sub(pat, "", ddl, flags=re.I)
    return re.sub(r"\n{3,}", "\n\n", ddl).strip()


def read_column_values():
    """INSERT 문에서 컬럼별 실제 값을 뽑는다."""
    sql = open(os.path.join(DS, "sql", "02-data.sql"), encoding="utf-8").read()
    vals = defaultdict(set)
    for m in re.finditer(r"INSERT INTO (\w+)\s*\(([^)]*)\)\s*VALUES(.*?);", sql, re.S | re.I):
        tbl  = m.group(1)
        cols = [c.strip() for c in m.group(2).split(",")]
        for row in re.finditer(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)", m.group(3)):
            cells = [c.strip().strip("'") for c in
                     re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", row.group(1))]
            if len(cells) != len(cols):
                continue
            for c, v in zip(cols, cells):
                if v and not v.isdigit() and len(v) <= 20:
                    vals[f"{tbl}.{c}"].add(v)
    return {k: sorted(v) for k, v in vals.items() if 1 < len(v) <= MAX_VALUES}


def tables_with_inserts():
    """02-data.sql 에 INSERT 가 있는 테이블 집합.

    column_values_ko 와 **같은 입력 기준**이다 — 참가자가 채우는
    `document_chunks` 는 INSERT 가 없어 자연히 빠진다.
    """
    sql = open(os.path.join(DS, "sql", "02-data.sql"), encoding="utf-8").read()
    return {t.lower() for t in re.findall(r"INSERT INTO (\w+)", sql, re.I)}


def gate_tables():
    """테이블 표층형 — 01-schema.sql 의 `-- N. 라벨` 주석에서 뽑는다.

    라벨은 스키마 작성자가 테이블마다 붙여 둔 한국어 이름이다. 괄호를 지우고
    `/` 로 나눈 뒤 조각의 **마지막 어절**(우핵)을 쓴다 — `기술 지원 티켓` 에서
    질문에 실제로 나오는 낱말은 `티켓` 이다.
    """
    sql   = open(os.path.join(DS, "sql", "01-schema.sql"), encoding="utf-8").read()
    known = tables_with_inserts()
    out   = {}
    for label, tbl in re.findall(r"--\s*\d+\.\s*([^\n]+)\nCREATE TABLE (\w+)", sql):
        if tbl.lower() not in known:
            continue
        out[tbl] = [p.strip().split()[-1]
                    for p in re.sub(r"\([^)]*\)", "", label).split("/") if p.strip()]
    return out


def annotate(ddl, values):
    """DDL 각 컬럼 줄 끝에 값 목록과 단위를 인라인 주석으로 붙인다.

    별도 블록이 아니라 인라인이어야 한다 — 정보량이 같아도 배치에 따라
    홀드아웃 정확도가 갈린다 (docs/harness-evaluation.md).
    """
    out, tbl = [], None
    for line in ddl.splitlines():
        m = re.match(r"CREATE TABLE (\w+)", line)
        if m:
            tbl = m.group(1)
        c = re.match(r"\s+(\w+)\s+\w", line)
        if c and tbl:
            col, note = c.group(1), []
            key = f"{tbl}.{col}"
            if key in values:
                note.append("값: " + " | ".join(values[key]))
            if col in UNITS:
                note.append(UNIT_HINT)
            if note:
                line = line.rstrip() + "   -- " + " · ".join(note)
        out.append(line)
    return "\n".join(out)


def surface_gate(values):
    """라우터 거절 게이트용 어휘. 테이블 표층형 + 컬럼의 한국어 값.

    도구 선택에는 쓰지 않는다 — 게이트는 '걸렸는가'만 본다.
    두 필드 다 데이터셋에서 파생된다 (이슈 #19).
    """
    korean = sorted({v for vs in values.values() for v in vs if re.search(r"[가-힣]", v)})
    return {"_provenance": {
                "tables": "derived — 01-schema.sql 의 '-- N. 라벨' 주석에서 우핵 규칙으로 "
                          "추출 (02-data.sql 에 INSERT 있는 8개)",
                "column_values_ko": "derived — 02-data.sql 의 저카디널리티 컬럼 값"},
            "tables": gate_tables(), "column_values_ko": korean}


# 저작 — TOOL_SIGNATURES 의 nl2sql 문장에 든 명사 그대로다. 새 낱말이 아니라
# **기존 저작 자산의 인용**이고, 그래서 그 문장의 저작 오염(작성자가 30문항을 읽은
# 뒤 썼다)이 짝 선택에도 그대로 이어진다 — harness-evaluation.md 6절.
#
# **인용이라는 말은 단언으로 지킨다** (`pair_axes` 의 assert). 손으로 옮겨 적은 목록이라,
# 시그니처 문장을 고치면서 이쪽을 안 고치면 "기존 자산에서만 왔다"는 근거가 조용히
# 무너진다 — 축 어휘가 자산에 없는 저작 낱말로 바뀌는데 아무도 못 본다.
NL2SQL_SIGNATURE_NOUNS = ["금액", "연봉", "예산", "기간", "상태", "건수", "합계", "개수", "평균"]


def pair_axes(gate):
    """병렬 짝의 **목록 변**을 가르는 두 축의 어휘 (이슈 #12 결정 3).

    서술 변(`vector_search`)은 고정 멤버라 규칙이 정하지 않는다. 규칙이 정하는 것은
    목록 변 한 자리(`nl2sql` vs `knowledge_graph`)뿐이고, 이 파일은 그 판정에 쓸
    어휘를 **기존 자산 3곳에서만** 모은다 — 이 이슈에서 낱말을 새로 저작하지 않는다.

      테이블 축  surface-gate.json 의 테이블 표층형(파생) + nl2sql 시그니처 명사(저작)
                 + 사건 어휘 이슈·장애·문제(저작, RELATION_WORDS 에서 이관)
      그래프 축  RELATION_WORDS 의 나머지 관계 표층형(저작)

    사건 어휘가 테이블 축인 근거는 스키마 구조 대조다 — `REPORTED_ISSUE` 엣지는
    고객사→제품 연결일 뿐 어떤 사건인지를 담지 않고, 사건 실물은
    `support_tickets.title` 에만 있다. `RELATION_WORDS` 의 항목 자체는 도구 내부의
    관계 순회용으로 그대로 남는다 (결정 2).

    양쪽 축에 걸리는 낱말(`프로젝트`)은 정의상 모호하므로 **기계적으로 둘 다에서**
    뺀다 — 배제 목록을 `_excluded` 에 남긴다.

    **부트스트랩 주의**: `tools` 는 커밋된 자산(entity-patterns.json·model.json·
    schema-annotated.sql·pair-axes.json)을 import 시점에 읽는다. 그래서 자산을
    통째로 비운 채로는 재생성할 수 없다.
    """
    import tools

    # 시그니처 명사는 **인용**이다 — 원문에서 이탈하면 여기서 멈춘다 (위 주석).
    missing = [w for w in NL2SQL_SIGNATURE_NOUNS if w not in TOOL_SIGNATURES["nl2sql"]]
    assert not missing, (
        f"NL2SQL_SIGNATURE_NOUNS 가 nl2sql 시그니처 문장에서 이탈했다: {missing}. "
        "짝 축 어휘는 기존 자산의 인용이어야 한다 (이슈 #12 결정 3) — "
        "낱말을 새로 저작하려면 결정 3 부터 다시 연다.")

    table = [w for ws in gate["tables"].values() for w in ws] \
            + NL2SQL_SIGNATURE_NOUNS + tools.RELATION_WORDS["REPORTED_ISSUE"]
    graph = [w for rel, ws in tools.RELATION_WORDS.items() if rel != "REPORTED_ISSUE"
             for w in ws]
    both = sorted(set(table) & set(graph))
    return {"_provenance": {
                "table": "derived+authored — surface-gate.json 의 테이블 표층형 + "
                         "tool-signatures.json 의 nl2sql 문장 명사 + "
                         "RELATION_WORDS 의 REPORTED_ISSUE (이슈 #12 결정 2·3)",
                "graph": "authored — tools.py RELATION_WORDS 의 REPORTED_ISSUE 제외 "
                         "나머지 관계 표층형 (서버 knowledge-graph.ts 와 공유)",
                "_excluded": "양쪽 축에 걸려 정의상 모호한 낱말 — 기계적으로 배제한다"},
            "table": [w for w in table if w not in both],
            "graph": [w for w in graph if w not in both],
            "_excluded": both}


def doc_topics():
    """제품 × 기술주제 격자 — 기술문서 제목 `[기술문서] {제품} {주제} …` 에서 뽑는다.

    `vector_search` 의 T4-form 판정(#13)이 쓴다: 질문이 주제어를 담는데 매칭된
    제품이 그 주제를 커버하지 않으면, 개체 청크가 있어도 `ok` 가 아니라 `partial` 이다.
    docs/dataset-analysis.md 3장의 격자(10/60, 주제 2개 이상 가진 제품 0개)가 근거다.
    """
    idx = json.load(open(os.path.join(DS, "documents", "index.json"), encoding="utf-8"))
    cov = defaultdict(set)
    for d in idx:
        if d["type"] == "technical_doc":
            _, product, topic = d["title"].split()[:3]
            cov[product].add(topic)
    return {"_provenance": "derived — documents/index.json 기술문서 제목에서 기계 추출 "
                           "(dataset-analysis.md 3장 제품 × 기술주제 격자)",
            "topics": sorted({t for ts in cov.values() for t in ts}),
            "coverage": {p: sorted(ts) for p, ts in cov.items()}}


# 저작 자산 — 사람이 썼다. design.md D11-1 의 (연산 × 피연산자 × 출력 형태)
# 표를 문장화한 것이고, 데이터셋에서 도출된 것이 아니다.
# 저작 — 데이터에 **없는** 이름을 알아보기 위한 상호 접미사.
# T5(개체 부재)는 정의상 데이터 밖이라 데이터에서 뽑을 수 없다.
# 라우터(개체 한정어 인식)와 knowledge_graph(미등록 언급 판정)가 **같은 목록을 쓴다** —
# 갈라지면 라우터가 거절한 질문이 도구에 닿지 못한다.
COMPANY_SUFFIX = ["테크", "물산", "전자", "산업", "그룹", "솔루션", "시스템", "코퍼", "홀딩스"]

TOOL_SIGNATURES = {
    "_provenance": "authored — design.md D11-1 표를 사람이 문장화. "
                   "작성자는 questions.json 30문항을 읽은 뒤였다 "
                   "(harness-evaluation.md 6절 한계). 소비자는 밑줄로 시작하는 키를 건너뛴다.",
    "vector_search":
        "문서에서 원인, 이유, 방법, 절차, 결정, 제안을 서술로 찾는다. "
        "장애보고서, 기술문서, 회의록, 제안서 본문.",
    "nl2sql":
        "정형 테이블에서 금액, 연봉, 예산, 기간, 상태, 건수 같은 속성값과 "
        "합계·개수·평균 집계를 구한다. 고객사, 직원, 계약, 프로젝트, 매출, "
        "지원티켓, 제품, 부서 테이블.",
    "knowledge_graph":
        "개체 사이의 관계를 따라간다. 누가 무엇을 사용하는지, 누가 어디에 소속인지, "
        "누가 담당·리드하는지, 누가 이슈를 보고했는지.",
}

# 저작 자산 — 사람이 썼다. 값의 근거는 실측이지만 구성은 판단이다.
MODEL = {
    "llm": {
        "name": "gemma4:e2b-it-qat",
        "options": {"temperature": 0, "num_predict": 400, "seed": 0},
        "think": False,
        "_note": "seed를 빼면 temperature 0 에서도 생성이 흔들린다 — 같은 질문의 SQL이 실행마다 달라지고(고유 SQL 2/5) 답변 라벨도 뒤집힌다. seed를 박으면 둘 다 1/5로 고정된다. "
                 "think를 켜면 숨은 추론 토큰이 num_predict를 소진해 빈 응답이 나온다. "
                 "정확도 이득은 작고 지연은 6배 이상이다.",
    },
    "embedding": {
        "name": "bge-m3", "dim": 1024,
        "_note": "nomic-embed-text는 라우팅 정확도가 절반이고 거절 임계가 성립하지 않는다. "
                 "document_chunks.embedding 을 vector(1024) 로 바꿔야 한다.",
    },
    "router": {"reject_threshold": 0.52, "_note": "0.48~0.57 구간에서 점수가 동일하다."},
}


def main():
    os.makedirs(OUT, exist_ok=True)
    ddl    = read_ddl()
    values = read_column_values()
    gate   = surface_gate(values)          # 게이트 어휘 · 짝 축 어휘의 공통 입력
    open(os.path.join(OUT, "schema-annotated.sql"), "w", encoding="utf-8").write(annotate(ddl, values) + "\n")
    for name, obj in (("column-values.json", values),
                      ("doc-topics.json", doc_topics()),
                      ("surface-gate.json", gate),
                      ("pair-axes.json", pair_axes(gate)),
                      ("tool-signatures.json", TOOL_SIGNATURES),
                      ("entity-patterns.json", {"_provenance": "authored — 데이터 밖의 이름을 잡는 목록",
                                                "company_suffix": COMPANY_SUFFIX,
                                                "id_prefixes": ["Client", "Product", "employee",
                                                                "project", "dept"]}),
                      ("model.json", MODEL)):
        json.dump(obj, open(os.path.join(OUT, name), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, sort_keys=True)
        print(f"  {name}")
    print(f"  schema-annotated.sql  (컬럼 값 {len(values)}개 컬럼, 단위 {len(UNITS)}개 컬럼)")


if __name__ == "__main__":
    main()
