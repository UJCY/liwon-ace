#!/usr/bin/env python3
"""하네스 자산 생성기.

자산은 두 종류다. **섞어서 "생성물"이라고 부르면 안 된다.**

  파생(derived)  — 데이터셋에서 기계적으로 뽑는다. 사람 손이 닿지 않는다.
                   schema-annotated.sql · column-values.json
  저작(authored) — 사람이 쓴 것을 이 파일이 그대로 덤프한다.
                   tool-signatures.json · model.json · surface-gate.json 의 tables

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
    """
    # tables 는 **저작**이다 — 테이블명의 한국어 표층형을 사람이 썼다.
    # column_values_ko 만 데이터에서 파생된다.
    tables = {
        "departments": ["부서", "부서장"], "employees": ["직원", "인력", "팀원", "사원"],
        "clients": ["고객", "고객사", "거래처"], "products": ["제품", "상품"],
        "contracts": ["계약", "계약서"], "projects": ["프로젝트", "과제"],
        "sales": ["매출", "판매", "영업"], "support_tickets": ["티켓", "문의", "지원요청"],
    }
    korean = sorted({v for vs in values.values() for v in vs if re.search(r"[가-힣]", v)})
    return {"_provenance": {"tables": "authored — 사람이 쓴 표층형",
                        "column_values_ko": "derived — 02-data.sql 의 저카디널리티 컬럼 값"},
            "tables": tables, "column_values_ko": korean}


# 저작 자산 — 사람이 썼다. design.md D11-1 의 (연산 × 피연산자 × 출력 형태)
# 표를 문장화한 것이고, 데이터셋에서 도출된 것이 아니다.
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
        "options": {"temperature": 0, "num_predict": 400},
        "think": False,
        "_note": "think를 켜면 숨은 추론 토큰이 num_predict를 소진해 빈 응답이 나온다. "
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
                      ("surface-gate.json", surface_gate(values)),
                      ("tool-signatures.json", TOOL_SIGNATURES),
                      ("model.json", MODEL)):
        json.dump(obj, open(os.path.join(OUT, name), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, sort_keys=True)
        print(f"  {name}")
    print(f"  schema-annotated.sql  (컬럼 값 {len(values)}개 컬럼, 단위 {len(UNITS)}개 컬럼)")


if __name__ == "__main__":
    main()
