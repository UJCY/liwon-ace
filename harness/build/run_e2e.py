#!/usr/bin/env python3
"""엔드투엔드 채점기 — 라우터가 고른 도구를 **실제로 태워** 응답 상태를 낸다.

  python3 harness/build/run_e2e.py

`run_router.py` 와 다른 점: 도구를 실행한다. 그래서 `partial` 과
`entity_not_found` 를 낼 수 있고, 실행 축의 포화가 풀린다.
(docs/harness-evaluation.md 4절 · docs/design.md D10)

전제: PostgreSQL 에 `load_pg.py` 로 적재돼 있고 Ollama 가 떠 있다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import router, tools

ROOT = router.ROOT
edge = json.load(open(os.path.join(ROOT, "edge-set", "edge-questions.json"), encoding="utf-8"))
docvecs = router.doc_vectors()


def answer(question):
    """라우팅 → 도구 실행 → 응답 상태. 병렬은 아직 없다 (D12 말미)."""
    qvec = router.embed(question)
    tools_chosen, state = router.route(question, qvec, docvecs)
    if not tools_chosen:
        return tools_chosen, state                       # out_of_scope — 도구를 안 부른다
    tool = tools_chosen[0]
    if tool == "knowledge_graph":
        r = tools.knowledge_graph(question)
    elif tool == "vector_search":
        r = tools.vector_search(question, qvec, router.THRESHOLD)
    else:
        return tools_chosen, "single"                    # nl2sql 은 run_nl2sql.py 가 잰다
    return tools_chosen, {"ok": "single", "no_result": "single"}.get(r["status"], r["status"])


routing = execution = 0
rows = []
for x in edge:
    got, state = answer(x["q"])
    r_ok = set(got) == set(x["expected"]["routing"])
    e_ok = state == x["expected"]["response"]
    routing += r_ok
    execution += e_ok
    if not (r_ok and e_ok):
        rows.append((x["id"], x["case"], "R" if not r_ok else " ", "E" if not e_ok else " ",
                     f"{x['expected']['response']} → {state}", x["q"][:26]))

n = len(edge)
reachable = {"single", "out_of_scope", "partial", "entity_not_found"}
ceiling = sum(1 for x in edge if x["expected"]["response"] in reachable)
print(f"엣지 {n}문항 (도구 실행 포함)")
print(f"  라우팅 축: {routing}/{n}")
print(f"  실행 축  : {execution}/{n}   (도달 가능 상한 {ceiling} — "
      f"parallel_merge {n - ceiling}문항은 아직 낼 수 없다)")
print("\n  실패 (R=라우팅 E=실행):")
for r in rows:
    print(f"    {r[0]:8} {r[1]:3} {r[2]}{r[3]}  {r[4]:34} {r[5]}")
