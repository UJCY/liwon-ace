#!/usr/bin/env python3
"""하네스 자산 생성기.

자산은 두 종류다. **섞어서 "생성물"이라고 부르면 안 된다.**

  파생(derived)  — 데이터셋에서 기계적으로 뽑는다. 사람 손이 닿지 않는다.
                   schema-annotated.sql · column-values.json · doc-topics.json ·
                   surface-gate.json
  저작(authored) — 사람이 쓴 것을 이 파일이 그대로 덤프한다.
                   tool-signatures.json · model.json

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
    open(os.path.join(OUT, "schema-annotated.sql"), "w", encoding="utf-8").write(annotate(ddl, values) + "\n")
    for name, obj in (("column-values.json", values),
                      ("doc-topics.json", doc_topics()),
                      ("surface-gate.json", surface_gate(values)),
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
