#!/usr/bin/env python3
"""단위 어형 격자 생성기 (#39).

`nl2sql` 의 단위 접지가 **어형**에 얼마나 흔들리는지 재는 세트를 만든다.
기존 96문항은 8개 템플릿의 슬롯 치환이라 이 축을 재지 못한다
(docs/harness-evaluation.md 1.2 정정 참조).

  파생 자산  column-ranges.json — 02-data.sql 의 금액 컬럼 실측 최소·최대.
             column-values.json 과 같은 출처·같은 규약이고, C2 주석과
             0행 접지 검출기(check_grounding.py)가 **같은 파일**을 읽는다.
  테스트     nl2sql-unit-{dev,holdout}.json — 본 격자 64 + 정답 0행 대조군 12.

격자 축은 4개로 확정이다 — 결과를 보고 늘리지 않는다 (#39 확정 제약).

  컬럼(4)     salary · price_monthly · amount(contracts) · budget
  표기(3)     한글형(자릿수 낱말: 8천만원·3백만원) · 아라비아형(8000만원) · 억형(1억 2천만원)
  술어(3)     넘는(>) · 이상인(>=) · 미만인(<)
  요구 형태(2) 개수(COUNT) · 목록(name, contracts 만 id)

규칙 셋 — 여기가 이 세트의 장치다.

  ① 본 격자의 기준 결과는 **반드시 1행 이상**이다. 그래야 "0행 = 접지 실패"가
     정의상 성립한다. 생성 시 기준 SQL 을 실제로 실행해 단언한다.
  ② 한글형↔아라비아형 셀은 **같은 기준값**을 다른 표기로 쓴다 — 표기 축의
     효과가 값 차이와 섞이지 않는다. 억형만 자기 크기(≥1억)를 가진다.
  ③ salary·price_monthly 는 최대가 1억 미만이라 억형×넘는/이상인 8셀이
     ①과 모순이다 — 버린다. mod 2 분할에서 dev·holdout 대칭(4/4)으로 빠진다.

대조군은 **접지가 맞는데 0행**인 셀이다 — 검출기의 거짓 양성(정답 0행을 접지
실패로 오인)을 재는 자리다. 최댓값 위 넘는/이상인, 또는 최솟값 아래 미만인.

분할은 (표기 + 술어 + 요구형태) mod 2 — 각 축 값은 양쪽에 고루 들어가고
축 조합은 겹치지 않는다. 대조군은 (컬럼 + 표기) mod 2.

  python3 harness/build/build_unit_grid.py            # 생성 + 단언 + 커밋용 출력
"""
import csv, io, json, os, re, subprocess, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DS   = os.path.join(ROOT, "companyx-dataset-v1.0")
ASSETS = os.path.join(ROOT, "harness", "assets")
TESTS  = os.path.join(ROOT, "harness", "tests")
CONTAINER = os.environ.get("CX_PG", "cx-pg")

# 금액 컬럼 — build_assets.py 의 UNITS 와 같은 목록에 테이블을 명시한 것.
# 동명 컬럼(contracts.amount / sales.amount)을 가르기 위해 table.column 으로 적는다.
MONEY_COLUMNS = ["employees.salary", "products.price_monthly",
                 "contracts.amount", "sales.amount", "projects.budget"]


def read_ranges():
    """INSERT 문에서 금액 컬럼의 실측 최소·최대를 뽑는다 (만원 단위).

    column-values.json 과 같은 파서 골격 — 출처는 02-data.sql 뿐이다.
    """
    sql = open(os.path.join(DS, "sql", "02-data.sql"), encoding="utf-8").read()
    vals = defaultdict(list)
    for m in re.finditer(r"INSERT INTO (\w+)\s*\(([^)]*)\)\s*VALUES(.*?);", sql, re.S | re.I):
        tbl  = m.group(1)
        cols = [c.strip() for c in m.group(2).split(",")]
        for row in re.finditer(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)", m.group(3)):
            cells = [c.strip().strip("'") for c in
                     re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", row.group(1))]
            if len(cells) != len(cols):
                continue
            for c, v in zip(cols, cells):
                if f"{tbl}.{c}" in MONEY_COLUMNS and re.fullmatch(r"\d+", v):
                    vals[f"{tbl}.{c}"].append(int(v))
    missing = [k for k in MONEY_COLUMNS if not vals[k]]
    if missing:
        sys.exit(f"금액 컬럼 값을 못 뽑았다: {missing}")
    return {k: [min(vals[k]), max(vals[k])] for k in MONEY_COLUMNS}


# ── 표기 렌더러 ──────────────────────────────────────────────────────────
DIGIT_KO = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9"}


def render_hangul(v):
    """한글 자릿수 낱말 표기 (만원 단위 값 → 문면). 억은 억형의 몫이라 금지."""
    assert v < 10000, f"한글형은 1억 미만만: {v}"
    thousands, hundreds = divmod(v, 1000)
    parts = []
    if thousands:
        parts.append(f"{DIGIT_KO[thousands]}천")
    if hundreds:
        assert hundreds % 100 == 0, f"백 단위 아래는 격자에 없다: {v}"
        parts.append(f"{DIGIT_KO[hundreds // 100]}백")
    return "".join(parts) + "만원"


def render_arabic(v):
    assert v < 10000, f"아라비아형은 1억 미만만: {v}"
    return f"{v}만원"


def render_eok(v):
    assert v >= 10000 and v % 1000 == 0, f"억형은 1억 이상 천만 단위만: {v}"
    eok, rest = divmod(v, 10000)
    return f"{eok}억원" if rest == 0 else f"{eok}억 {DIGIT_KO[rest // 1000]}천만원"


NOTATIONS = [("h", "한글형", render_hangul), ("a", "아라비아형", render_arabic),
             ("e", "억형", render_eok)]
PREDICATES = [("gt", "넘는", ">"), ("ge", "이상인", ">="), ("lt", "미만인", "<")]
FORMS = ["c", "l"]  # 개수 / 목록

# 컬럼별 문면 조각. 목록형의 SELECT 컬럼은 name, contracts 만 id (name 이 없다).
COLUMNS = [
    {"key": "employees.salary", "id": "sal", "table": "employees", "col": "salary",
     "noun": "직원", "attr": "연봉이", "counter": "명", "list_col": "name", "list_word": "명단"},
    {"key": "products.price_monthly", "id": "prc", "table": "products", "col": "price_monthly",
     "noun": "제품", "attr": "월 구독료가", "counter": "개", "list_col": "name", "list_word": "목록"},
    {"key": "contracts.amount", "id": "amt", "table": "contracts", "col": "amount",
     "noun": "계약", "attr": "계약 금액이", "counter": "건", "list_col": "id", "list_word": "목록"},
    {"key": "projects.budget", "id": "bdg", "table": "projects", "col": "budget",
     "noun": "프로젝트", "attr": "예산이", "counter": "개", "list_col": "name", "list_word": "목록"},
]

# 본 격자 기준값 (만원 단위). (컬럼 × 술어) 당 하나 — 한글형과 아라비아형이
# 같은 값을 나눠 쓴다 (규칙 ②). 억형은 별도 값이다 (≥1억).
# 실측 범위 안에서 ①(기준 ≥1행)이 성립하도록 골랐고, 생성 시 단언으로 확인한다.
MAIN_VALUES = {
    #                넘는     이상인   미만인    억형(넘는, 이상인, 미만인; None = ③으로 버림)
    "sal": {"gt": 5000, "ge": 8000, "lt": 4000, "e": {"gt": None, "ge": None, "lt": 10000}},
    "prc": {"gt": 300,  "ge": 200,  "lt": 100,  "e": {"gt": None, "ge": None, "lt": 10000}},
    "amt": {"gt": 5000, "ge": 3000, "lt": 1000, "e": {"gt": 10000, "ge": 10000, "lt": 10000}},
    "bdg": {"gt": 8000, "ge": 5000, "lt": 3000, "e": {"gt": 10000, "ge": 12000, "lt": 10000}},
}

# 대조군 — 접지가 맞는데 0행. (컬럼 × 표기) 당 하나.
# 한글형·아라비아형은 같은 값을 나눠 쓰고, 표현 제약 때문에 최솟값 아래 미만인이
# 대부분이다 (최댓값 위를 백·천 단위로 못 쓰는 컬럼이 있다 — #39 정정 코멘트).
CONTROL = {
    "sal": {"h": (3000, "lt"), "a": (3000, "lt"), "e": (10000, "gt")},
    "prc": {"h": (600, "gt"), "a": (600, "gt"), "e": (10000, "gt")},
    "amt": {"h": (400, "lt"), "a": (400, "lt"), "e": (15000, "gt")},
    "bdg": {"h": (800, "lt"), "a": (800, "lt"), "e": (20000, "gt")},
}


def _batchim(word):
    return (ord(word[-1]) - 0xAC00) % 28 != 0


def question(c, value_text, pred_word, form):
    if form == "c":
        topic = "은" if _batchim(c["noun"]) else "는"
        end = "이야" if _batchim(c["counter"]) else "야"
        return f"{c['attr']} {value_text} {pred_word} {c['noun']}{topic} 몇 {c['counter']}{end}?"
    return f"{c['attr']} {value_text} {pred_word} {c['noun']} {c['list_word']} 알려줘."


def ref_sql(c, op, v, form):
    sel = "COUNT(*)" if form == "c" else c["list_col"]
    return f"SELECT {sel} FROM {c['table']} WHERE {c['col']} {op} {v}"


def psql(sql):
    p = subprocess.run(["docker", "exec", "-i", CONTAINER, "psql", "-U", "postgres",
                        "-d", "companyx", "-v", "ON_ERROR_STOP=1", "--csv", "-c", sql],
                       capture_output=True, text=True, timeout=30)
    if p.returncode != 0:
        sys.exit(f"기준 SQL 실행 실패: {sql}\n{p.stderr.strip()[:200]}")
    rows = list(csv.reader(io.StringIO(p.stdout)))
    return rows[1:] if rows else []


def data_rows(c, op, v):
    """이 술어를 만족하는 **데이터 행 수** — 단언용. COUNT 기준도 이것으로 가른다."""
    return int(psql(f"SELECT COUNT(*) FROM {c['table']} WHERE {c['col']} {op} {v}")[0][0])


def build():
    items = []
    for c in COLUMNS:
        mv = MAIN_VALUES[c["id"]]
        # 본 격자
        for ni, (nid, _, render) in enumerate(NOTATIONS):
            for pi, (pid, pred_word, op) in enumerate(PREDICATES):
                v = mv["e"][pid] if nid == "e" else mv[pid]
                if v is None:
                    continue                      # 규칙 ③ — 성립 불가 셀
                for fi, form in enumerate(FORMS):
                    n = data_rows(c, op, v)
                    assert n >= 1, f"본 격자 기준이 0행이다: {c['id']} {nid} {op} {v}"
                    items.append({
                        "id": f"UG-{c['id']}-{nid}-{pid}-{form}", "cat": "UG",
                        "q": question(c, render(v), pred_word, form),
                        "ref": ref_sql(c, op, v, form),
                        "rows": 1 if form == "c" else n,
                        "axes": {"col": c["id"], "notation": nid, "pred": pid, "form": form},
                        "value": v,
                        "split": (ni + pi + fi) % 2,
                    })
        # 대조군 — 접지가 맞는데 0행
        for ni, (nid, _, render) in enumerate(NOTATIONS):
            v, pid = CONTROL[c["id"]][nid]
            pred_word, op = next((w, o) for p, w, o in PREDICATES if p == pid)
            ci = COLUMNS.index(c)
            form = FORMS[(ci + ni) % 2]           # 형태도 양쪽에 고루
            n = data_rows(c, op, v)
            assert n == 0, f"대조군 기준이 0행이 아니다: {c['id']} {nid} {op} {v} → {n}행"
            items.append({
                "id": f"UGC-{c['id']}-{nid}", "cat": "UGC",
                "q": question(c, render(v), pred_word, form),
                "ref": ref_sql(c, op, v, form),
                "rows": 1 if form == "c" else 0,  # COUNT 는 값 0 한 행이 온다
                "axes": {"col": c["id"], "notation": nid, "pred": pid, "form": form},
                "value": v,
                "split": (ci + ni) % 2,
            })
    return items


def main():
    ranges = read_ranges()
    for key, (lo, hi) in ranges.items():
        print(f"  {key}: {lo}~{hi}")

    items = build()
    dev      = [i for i in items if i["split"] == 0]
    holdout  = [i for i in items if i["split"] == 1]
    for i in items:
        del i["split"]

    # 축 조합이 두 세트에 겹치지 않는가 — 본 격자의 (표기, 술어, 형태) 조합 기준.
    combo = lambda s: {(i["axes"]["notation"], i["axes"]["pred"], i["axes"]["form"])
                       for i in s if i["cat"] == "UG"}
    overlap = combo(dev) & combo(holdout)
    assert not overlap, f"축 조합이 겹친다: {overlap}"

    os.makedirs(TESTS, exist_ok=True)
    json.dump({"_provenance": "derived — 02-data.sql 의 금액 컬럼 실측 최소·최대 (만원 단위). "
                              "C2 주석과 check_grounding.py 가 같은 파일을 읽는다 (#39)",
               **ranges},
              open(os.path.join(ASSETS, "column-ranges.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    for name, data in (("nl2sql-unit-dev.json", dev), ("nl2sql-unit-holdout.json", holdout)):
        json.dump(data, open(os.path.join(TESTS, name), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        ug  = sum(1 for i in data if i["cat"] == "UG")
        ugc = sum(1 for i in data if i["cat"] == "UGC")
        print(f"  {name}: 본 {ug} + 대조 {ugc} = {len(data)}")
    print(f"  column-ranges.json ({len(ranges)}개 컬럼)")




if __name__ == "__main__":
    main()
