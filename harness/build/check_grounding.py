#!/usr/bin/env python3
"""0행 접지 검출기 — 하네스판 (#39).

실행 **후, 결과가 빈손일 때만** 도는 리터럴 접지 검사다. SQL 파서를 쓰지 않는다.
채택은 #6 에서 확정됐다 (design.md D18) — **이 파일이 판정 정의의 원본이고**,
`harness/build/tools.py` 와 서버 `src/tools/nl2sql.ts` 가 같은 판정을 쓴다
(하네스는 import, 서버는 이식). 채택 근거는 이 파일이 격자 기록 위에서 낸 두 수치다:
**적발률** 22/22(빈손 실패를 잡는가) · **오인률** 0(정답 0행을 접지 실패로 오인하는가).

**채택 정책은 숫자 + `string_misplaced` 뿐이다.** 아래 문자열 갈래가 함께 내는
`string`(어디에도 없음)은 소비자 쪽 필터에서 빠진다 — "값이 진짜 없는 정직한
질문"(`region='평양'`)과 "리터럴을 잘못 씀"을 못 가르기 때문이다 (D18). 검출기는
세 갈래를 다 내고 정책은 부르는 쪽이 정한다 — 정의를 한 곳에 남기기 위해서다.

두 갈래다.

  숫자    금액 컬럼 곁의 리터럴이 실측 범위(column-ranges.json)를 **10배 이상**
          넘으면 접지 실패. 10의 출처는 dev 실측이다: 정당한 최댓값 위 질문은
          ×2 안이고("2억 넘는 프로젝트" 20000/14738), 관측된 최소 오류는 ×27
          이다 — 컬럼 오배치 복합 케이스(월 구독료를 contracts.amount 에 걸고
          ×1000)가 엉뚱한 컬럼의 넓은 범위로 나눠져 줄어든 값이다. 순수 단위
          오류는 ×1000~×10000 이다. 10은 2~27 틈에 서고, 홀드아웃이 검증한다.
          최댓값 배수만 본다 — 최솟값 아래(`3천만원 미만` → 0행)는 정당한 질문과
          모양이 같고, 아래 방향 단위 실수는 관측된 적이 없다.
  문자열  따옴표 리터럴을 DB 전 텍스트 컬럼에서 찾는다. 어디에도 없으면 미접지,
          **다른 컬럼에만 있으면 컬럼 오배치**다 (R4-02: 'Client-B' 를
          employees.name 에 물었다 — clients.name 에 있다).

평가는 오프라인이다 — run_nl2sql.py 가 기록한 SQL 전량(logs/*.jsonl) 위에서
돌므로 재생성 비용이 없다.

  python3 harness/build/check_grounding.py logs/nl2sql-unit-dev-C0.jsonl
"""
import csv, io, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A    = os.path.join(ROOT, "harness", "assets")
CONTAINER = os.environ.get("CX_PG", "cx-pg")

OVER_FACTOR = 10           # 위 docstring — dev 실측: 정당 ≤×2, 최소 오류 ×27


def load_ranges():
    """컬럼 이름(테이블 없이) → 실측 범위의 합집합.

    동명 컬럼(contracts.amount / sales.amount)은 합집합을 쓴다 — 별칭 해소 없이
    보수적으로 판정하기 위해서다. 단위 실수는 ×1000 이상이라 합집합으로도 갈린다.
    """
    ranges = json.load(open(os.path.join(A, "column-ranges.json"), encoding="utf-8"))
    merged = {}
    for key, val in ranges.items():
        if key.startswith("_"):
            continue
        (lo, hi), col = val, key.split(".")[1]
        m = merged.setdefault(col, [lo, hi])
        m[0], m[1] = min(m[0], lo), max(m[1], hi)
    return merged


def psql(sql):
    p = subprocess.run(["docker", "exec", "-i", CONTAINER, "psql", "-U", "postgres",
                        "-d", "companyx", "-v", "ON_ERROR_STOP=1", "--csv"],
                       input=sql, capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise RuntimeError((p.stderr.strip().splitlines() or ["error"])[0][:120])
    rows = list(csv.reader(io.StringIO(p.stdout)))
    return rows[1:] if rows else []


def text_columns():
    return [(t, c) for t, c in (r for r in psql(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND data_type IN "
        "('character varying','text','character') ORDER BY 1,2;"))]


def alias_map(sql):
    """FROM/JOIN 절의 별칭 → 테이블. 최소 해소다 — 파서를 만들지 않는다."""
    out = {}
    for m in re.finditer(r"\b(?:FROM|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(?!ON\b|WHERE\b|JOIN\b|LEFT\b|RIGHT\b|INNER\b|GROUP\b|ORDER\b)(\w+))?",
                         sql, re.I):
        tbl, alias = m.group(1), m.group(2)
        out[tbl] = tbl
        if alias:
            out[alias] = tbl
    return out


NUM_RE = re.compile(
    r"\b(?:(\w+)\.)?(salary|price_monthly|amount|budget)\b\s*(?:>=|<=|<>|!=|=|>|<)\s*(\d+(?:\.\d+)?)")
STR_RE = re.compile(r"(\w+(?:\.\w+)?)\s*(?:=|ILIKE|LIKE)\s*'([^']+)'", re.I)
SKIP_LITERAL = re.compile(r"^\d{4}-\d{2}(-\d{2})?$|^\d{4}-Q\d$|^\d+(\.\d+)?$")


def detect(sql, ranges, txt_cols=None):
    """접지 실패 목록. 비면 통과다. txt_cols 를 안 주면 문자열 갈래를 건너뛴다."""
    hits = []
    for _, col, lit in NUM_RE.findall(sql):
        lo, hi = ranges.get(col, (None, None))
        if hi is not None and float(lit) >= OVER_FACTOR * hi:
            hits.append({"kind": "number", "column": col, "literal": lit,
                         "observed_range": [lo, hi]})
    if txt_cols is None:
        return hits
    amap = alias_map(sql)
    for used, raw in STR_RE.findall(sql):
        lit = raw.strip("%")
        if not lit or SKIP_LITERAL.match(lit):
            continue
        op_like = "%" in raw
        found = []
        for t, c in txt_cols:
            cond = f"{c} LIKE '%{lit}%'" if op_like else f"{c} = '{lit}'"
            try:
                n = int(psql(f"SELECT COUNT(*) FROM {t} WHERE {cond};")[0][0])
            except RuntimeError:
                continue
            if n:
                found.append(f"{t}.{c}")
        parts = used.split(".")
        used_col = parts[-1]
        used_tbl = amap.get(parts[0]) if len(parts) == 2 else None
        if not found:
            hits.append({"kind": "string", "column": used, "literal": lit, "found_in": []})
        elif used_tbl and f"{used_tbl}.{used_col}" not in found:
            hits.append({"kind": "string_misplaced", "column": f"{used_tbl}.{used_col}",
                         "literal": lit, "found_in": found})
        elif not used_tbl and not any(f.endswith(f".{used_col}") for f in found):
            hits.append({"kind": "string_misplaced", "column": used_col,
                         "literal": lit, "found_in": found})
    return hits


# ── 격자 기록 위의 평가 ──────────────────────────────────────────────────

def grounded_by_value(rec):
    """생성 리터럴이 의도한 기준값(만원)과 같은가 — 검출기와 **독립**인 정답 기준.

    격자 문항에만 쓸 수 있다 (기준값을 아는 문항이라서). 검출기 평가가 검출기
    자신을 정답 기준으로 삼으면 순환이라, 이 별도 기준으로 가른다.
    """
    col = rec["axes"]["col"]
    target = {"sal": "salary", "prc": "price_monthly", "amt": "amount", "bdg": "budget"}[col]
    lits = [float(l) for _, c, l in NUM_RE.findall(rec["sql"]) if c == target]
    return bool(lits) and all(l == rec["value"] for l in lits)


def evaluate(path, ranges):
    recs = [json.loads(l) for l in open(path, encoding="utf-8")]
    unit = [r for r in recs if r.get("cat") in ("UG", "UGC")]
    if not unit:
        print(f"{os.path.basename(path)}: 격자 문항이 없다 — 건너뜀")
        return

    # 적발률 — 본 격자의 빈손 실패를 잡는가 (문자열 갈래는 격자에 없어 숫자만 돈다)
    zero = [r for r in unit if r["cat"] == "UG" and r["verdict"] == "zero_result"]
    caught = [r for r in zero if detect(r["sql"], ranges)]
    # 오인률 — 대조군에서, 접지가 실제로 맞는 SQL 을 실패로 모는가
    ctrl = [r for r in unit if r["cat"] == "UGC" and r["verdict"] not in ("exec_error", "not_select")]
    ctrl_ok = [r for r in ctrl if grounded_by_value(r)]
    false_pos = [r for r in ctrl_ok if detect(r["sql"], ranges)]

    name = os.path.basename(path)
    z = f"{len(caught)}/{len(zero)}" if zero else "—/0"
    print(f"{name}: 적발 {z} · 오인 {len(false_pos)}/{len(ctrl_ok)}"
          f" (대조군 자체 접지 실패 {len(ctrl) - len(ctrl_ok)}건 제외)")
    for r in zero:
        mark = "잡음" if r in caught else "놓침 ← 사람 판정"
        print(f"  {r['id']:16} {mark:14} {r['sql'][:80]}")
    for r in false_pos:
        print(f"  {r['id']:16} 오인!          {r['sql'][:80]}")
    for r in ctrl:
        if r not in ctrl_ok:
            print(f"  {r['id']:16} 대조군 접지실패 {r['sql'][:80]}")


def main():
    if len(sys.argv) < 2:
        sys.exit("사용법: check_grounding.py <logs/*.jsonl> [...]")
    ranges = load_ranges()
    for path in sys.argv[1:]:
        evaluate(path, ranges)


if __name__ == "__main__":
    main()
