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
RULES = ("\n[출력 규칙]\n- SELECT 문 하나만 출력한다.\n"
         "- 설명·주석·코드펜스를 붙이지 않는다.\n- 세미콜론으로 끝낸다.\n"
         "- PostgreSQL 문법만 쓴다. 날짜에서 연도를 뽑을 때는 EXTRACT(YEAR FROM 컬럼)을 쓴다.\n")


def build_prompt(harness, question):
    if harness == "bare":                      # 대조군 — DDL만
        return (f"너는 SQL 생성기다. 아래 스키마에 대해 PostgreSQL SELECT 문 하나를 만든다.\n\n"
                f"[스키마]\n{BARE}\n\n[질문]\n{question}\n\nSQL만 출력해라.\n")
    if harness == "blocks":                    # 값·단위를 별도 블록으로
        vals = json.load(open(os.path.join(A, "column-values.json"), encoding="utf-8"))
        vb = "\n".join(f"- {k}: {', '.join(v)}" for k, v in sorted(vals.items()))
        ub = ("- salary / price_monthly / amount / budget: 단위 만원 "
              "(1억원=10000, 5천만원=5000, 100만원=100)")
        return (f"너는 SQL 생성기다. 아래 스키마에 대해 PostgreSQL SELECT 문 하나를 만든다.\n\n"
                f"[스키마]\n{BARE}\n\n[컬럼에 실제로 들어있는 값]\n{vb}\n"
                f"\n[컬럼 의미와 단위]\n{ub}\n\n[질문]\n{question}\n" + RULES)
    return (                                    # annotated — 채택안
        "너는 SQL 생성기다. 아래 스키마에 대해 PostgreSQL SELECT 문 하나를 만든다.\n"
        "주석(--)에 그 컬럼에 실제로 들어있는 값과 단위가 적혀 있다. 반드시 그 값을 그대로 써라.\n\n"
        f"[스키마]\n{ANNOTATED}\n\n[질문]\n{question}\n" + RULES)


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="holdout", choices=["dev", "holdout"])
    ap.add_argument("--harness", default="annotated", choices=["bare", "blocks", "annotated"])
    ap.add_argument("--container", default="cx-pg")
    args = ap.parse_args()

    tests = json.load(open(os.path.join(ROOT, "harness", "tests",
                                        f"nl2sql-{args.set}.json"), encoding="utf-8"))
    ok = err = 0
    misses, t0 = [], time.time()
    for t in tests:
        sql = extract_sql(generate(build_prompt(args.harness, t["q"])))
        if not re.match(r"^\s*SELECT\b", sql, re.I):        # D4 SELECT-only
            err += 1; misses.append((t["id"], t["cat"], "NOT_SELECT", sql[:60])); continue
        got, e = psql(sql, args.container)
        if e:
            err += 1; misses.append((t["id"], t["cat"], "EXEC_ERROR", e[:60])); continue
        ref, _ = psql(t["ref"], args.container)
        if normalize(got) == normalize(ref):
            ok += 1
        else:
            misses.append((t["id"], t["cat"], f"{len(got)}행/{len(ref)}행", sql[:70]))

    print(f"{args.harness} · {args.set}: 정답 {ok}/{len(tests)} "
          f"({ok/len(tests):.0%}) · 실행오류 {err} · {round(time.time()-t0)}s")
    for m in misses:
        print(f"  {m[0]:8} {m[1]:3} {m[2]:12} {m[3]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
