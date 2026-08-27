#!/usr/bin/env python3
"""nl2sql 하네스 채점기 — 생성한 SQL을 실제로 실행해 기준 결과와 대조한다.

  python3 harness/build/run_nl2sql.py --set holdout --harness annotated

전제: PostgreSQL 에 데이터셋이 적재되어 있고 Ollama 가 떠 있다.
  docker run -d --name cx-pg -e POSTGRES_PASSWORD=cx -e POSTGRES_DB=companyx \
    -p 55432:5432 pgvector/pgvector:pg16
  docker exec cx-pg psql -U postgres -d companyx -f /tmp/01-schema.sql
"""
import argparse, csv, io, json, os, re, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A    = os.path.join(ROOT, "harness", "assets")
MODEL = json.load(open(os.path.join(A, "model.json"), encoding="utf-8"))["llm"]

BARE      = open(os.path.join(ROOT, "companyx-dataset-v1.0", "sql", "01-schema.sql"), encoding="utf-8").read()
ANNOTATED = open(os.path.join(A, "schema-annotated.sql"), encoding="utf-8").read()


def adopted_template():
    """채택안 프롬프트는 assets/prompts/nl2sql.md 의 첫 코드블록이 실물이다.

    여기에 다시 적지 않는다 — 두 벌이 되면 갈라진다 (docs/design.md D13).
    """
    md = open(os.path.join(A, "prompts", "nl2sql.md"), encoding="utf-8").read()
    m = re.search(r"```\n(.*?)```", md, re.S)
    if not m:
        sys.exit("prompts/nl2sql.md 에서 프롬프트 코드블록을 찾지 못했다")
    return m.group(1)


ADOPTED = adopted_template()

# ── 단위 힌트 대조군 (#39) ────────────────────────────────────────────────
# C0 은 현행 그대로(annotated 별칭)다. C1·C2 는 build_assets.py 의 UNIT_HINT
# 한 줄만 바꾼 대조군이고, 각각 C0 에서 **한 가지만** 다르다 — 섞으면 이겨도
# 왜 이겼는지 못 가른다.
#   C1  예시를 표기 계열로 교체 — 아라비아 표기 계열을 더한다
#   C2  실측 범위만 추가 — column-ranges.json 에서 읽는다 (검출기와 같은 파일)
HINT_C0 = "단위: 만원 (1억원=10000, 5천만원=5000, 100만원=100)"
HINT_C1 = "단위: 만원 (1억원=10000, 5천만원=5000, 3000만원=3000, 500만원=500)"
MONEY_LINES = 5           # 스키마의 금액 컬럼 줄 수 — 어긋나면 스키마가 표류한 것이다


def unit_schema(variant):
    if variant == "C1":
        n = ANNOTATED.count(HINT_C0)
        if n != MONEY_LINES:
            sys.exit(f"UNIT_HINT 가 {n}줄이다 — schema-annotated.sql 표류")
        return ANNOTATED.replace(HINT_C0, HINT_C1)
    ranges = json.load(open(os.path.join(A, "column-ranges.json"), encoding="utf-8"))
    out, tbl, hits = [], None, 0
    for line in ANNOTATED.splitlines():
        m = re.match(r"CREATE TABLE (\w+)", line)
        if m:
            tbl = m.group(1)
        if HINT_C0 in line:
            col = re.match(r"\s+(\w+)", line).group(1)
            lo, hi = ranges[f"{tbl}.{col}"]
            line = line.replace(
                HINT_C0, f"단위: 만원 (실측 {lo}~{hi}, 1억원=10000, 5천만원=5000, 100만원=100)")
            hits += 1
        out.append(line)
    if hits != MONEY_LINES:
        sys.exit(f"UNIT_HINT 가 {hits}줄이다 — schema-annotated.sql 표류")
    return "\n".join(out)


def build_prompt(harness, question):
    """`annotated` 만이 채택안이다. 나머지는 **대조군**이고 자산이 아니다 —
    "값·단위를 안 주면 / 별도 블록으로 주면 / 단위 힌트를 바꾸면 어떻게 되는가"를
    재려고 여기에만 둔다."""
    if harness in ("annotated", "C0"):
        return ADOPTED.replace("{{SCHEMA}}", ANNOTATED).replace("{{QUESTION}}", question)
    if harness in ("C1", "C2"):
        return ADOPTED.replace("{{SCHEMA}}", unit_schema(harness)).replace("{{QUESTION}}", question)

    rules = ("\n[출력 규칙]\n- SELECT 문 하나만 출력한다.\n"
             "- 설명·주석·코드펜스를 붙이지 않는다.\n- 세미콜론으로 끝낸다.\n"
             "- PostgreSQL 문법만 쓴다. 날짜에서 연도를 뽑을 때는 EXTRACT(YEAR FROM 컬럼)을 쓴다.\n")
    if harness == "bare":                      # 대조군 ① — DDL만, 출력 규칙도 없다
        return (f"너는 SQL 생성기다. 아래 스키마에 대해 PostgreSQL SELECT 문 하나를 만든다.\n\n"
                f"[스키마]\n{BARE}\n\n[질문]\n{question}\n\nSQL만 출력해라.\n")
    vals = json.load(open(os.path.join(A, "column-values.json"), encoding="utf-8"))
    vb = "\n".join(f"- {k}: {', '.join(v)}" for k, v in sorted(vals.items()))
    ub = ("- salary / price_monthly / amount / budget: 단위 만원 "
          "(1억원=10000, 5천만원=5000, 100만원=100)")
    return (                                   # 대조군 ② — 같은 정보를 별도 블록으로
        f"너는 SQL 생성기다. 아래 스키마에 대해 PostgreSQL SELECT 문 하나를 만든다.\n\n"
        f"[스키마]\n{BARE}\n\n[컬럼에 실제로 들어있는 값]\n{vb}\n"
        f"\n[컬럼 의미와 단위]\n{ub}\n\n[질문]\n{question}\n" + rules)


def generate(prompt):
    body = {"model": MODEL["name"], "prompt": prompt, "stream": False,
            "options": MODEL["options"]}
    if not MODEL.get("think", False):
        body["think"] = False                   # 켜면 빈 응답이 나온다. assets/model.json 주석 참조
    req = urllib.request.Request("http://localhost:11434/api/generate",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=900).read())["response"]


def extract_sql(text):
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    m = re.search(r"(SELECT\b.*?)(?:;|$)", text, re.S | re.I)
    return (m.group(1).strip() if m else text.strip())


def psql(sql, container="cx-pg"):
    p = subprocess.run(["docker", "exec", "-i", container, "psql", "-U", "postgres",
                        "-d", "companyx", "-v", "ON_ERROR_STOP=1", "--csv", "-c", sql],
                       capture_output=True, text=True, timeout=30)
    if p.returncode != 0:
        err = p.stderr.strip().splitlines()
        return None, (err[0][:80] if err else "error")
    rows = list(csv.reader(io.StringIO(p.stdout)))
    return rows[1:] if rows else [], None


def normalize(rows):
    def cell(v):
        try:    return round(float(v), 3)
        except ValueError: return v
    return None if rows is None else sorted(tuple(cell(v) for v in r) for r in rows)


def zero_result(got, ref):
    """빈손 — 접지 실패의 격자 서명 (#39). 목록형은 0행, 집계형은 값 0/NULL 한 행.

    집계형에서는 접지가 틀려도 행이 온다 (`COUNT(*)` → `0` 한 행) — 0행만 세면
    격자 절반이 이 지표에서 빠진다."""
    if got == []:
        return ref != []
    if len(got) == 1 and len(got[0]) == 1 and got[0][0] in ("", "0"):
        return normalize(got) != normalize(ref)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="holdout",
                    choices=["dev", "holdout", "unit-dev", "unit-holdout"])
    ap.add_argument("--harness", default="annotated",
                    choices=["bare", "blocks", "annotated", "C0", "C1", "C2"])
    ap.add_argument("--container", default="cx-pg")
    ap.add_argument("--dump", default=None,
                    help="생성 SQL 전량 기록 (JSONL). 기본 logs/nl2sql-<set>-<harness>.jsonl")
    args = ap.parse_args()

    tests = json.load(open(os.path.join(ROOT, "harness", "tests",
                                        f"nl2sql-{args.set}.json"), encoding="utf-8"))
    ok = err = empty = 0
    misses, records, t0 = [], [], time.time()
    for t in tests:
        sql = extract_sql(generate(build_prompt(args.harness, t["q"])))
        rec = {"id": t["id"], "cat": t["cat"], "q": t["q"], "ref": t["ref"], "sql": sql}
        if "axes" in t:
            rec["axes"], rec["value"] = t["axes"], t["value"]
        records.append(rec)
        if not re.match(r"^\s*SELECT\b", sql, re.I):        # D4 SELECT-only
            err += 1; rec["verdict"] = "not_select"
            misses.append((t["id"], t["cat"], "NOT_SELECT", sql[:60])); continue
        got, e = psql(sql, args.container)
        if e:
            err += 1; rec["verdict"] = "exec_error"; rec["error"] = e
            misses.append((t["id"], t["cat"], "EXEC_ERROR", e[:60])); continue
        ref, _ = psql(t["ref"], args.container)
        rec["got_rows"], rec["ref_rows"] = len(got), len(ref)
        if normalize(got) == normalize(ref):
            ok += 1; rec["verdict"] = "match"
        elif zero_result(got, ref):
            empty += 1; rec["verdict"] = "zero_result"
            misses.append((t["id"], t["cat"], "빈손", sql[:70]))
        else:
            rec["verdict"] = "mismatch"
            misses.append((t["id"], t["cat"], f"{len(got)}행/{len(ref)}행", sql[:70]))

    dump = args.dump or os.path.join(ROOT, "logs", f"nl2sql-{args.set}-{args.harness}.jsonl")
    os.makedirs(os.path.dirname(dump), exist_ok=True)
    with open(dump, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    mismatch = len(misses) - err - empty
    print(f"{args.harness} · {args.set}: 정답 {ok}/{len(tests)} "
          f"({ok/len(tests):.0%}) · 빈손 {empty} · 불일치 {mismatch} · 실행오류 {err} "
          f"· {round(time.time()-t0)}s")
    for m in misses:
        print(f"  {m[0]:8} {m[1]:3} {m[2]:12} {m[3]}")
    print(f"  → SQL 전량 기록: {os.path.relpath(dump, ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
