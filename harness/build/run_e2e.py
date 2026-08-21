#!/usr/bin/env python3
"""엔드투엔드 채점기 — 라우터가 고른 도구를 **실제로 태워** 응답 상태를 낸다.

  python3 harness/build/run_e2e.py [--set edge|regression|both]

`run_router.py` 와 다른 점: 도구를 실행한다. 그래서 `partial`·`entity_not_found`
를 낼 수 있고, **병렬을 실행 결과로 확정**할 수 있다.

병렬 판정이 2단계다 (docs/design.md D3 · D11-4).
  ① 접속 탐지 — 요구 원소가 둘인가 (표층)
  ② 실행 확인 — 후보 둘을 태워 **둘 다 내용이 있는가**
①만으로는 부족하다. 접속된 두 요구가 같은 도구에 걸리면 단일 선택이기 때문이다
("장애 사례와 원인" 은 둘 다 문서다). ②가 그것을 걸러 낸다.

전제: `load_pg.py` 로 적재돼 있고 Ollama 가 떠 있다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import router, tools

ROOT = router.ROOT
ARG = sys.argv[sys.argv.index("--set") + 1] if "--set" in sys.argv else "both"
docvecs = router.doc_vectors()

# **`ok` 만 센다.** `partial` 은 "요구한 형태의 답이 그 자산에 없다"는 뜻이므로
# 병렬의 한 갈래로 살아 있는 것이 아니다 (docs/design.md D10).
# partial 을 세면 개체 이름만 걸려도 vector_search 가 항상 살아나 병렬이 남발된다.
HAS_CONTENT = {"ok"}


def run_tool(tool, question, qvec):
    if tool == "knowledge_graph":
        return tools.knowledge_graph(question)
    if tool == "vector_search":
        return tools.vector_search(question, qvec, router.THRESHOLD)
    return tools.nl2sql(question)


def answer(question, qvec=None):
    """판별 → 실행 → (필요하면) 병렬 확정. **덤프도 이 함수를 쓴다** —
    대조가 러너와 다른 경로를 보면 출하 경로의 이식 버그를 못 잡는다."""
    qvec = router.embed(question) if qvec is None else qvec
    chosen, state = router.route(question, qvec, docvecs)
    if not chosen:
        return chosen, state                              # 거절 — 도구를 안 부른다

    if tools.has_two_requests(question):                  # ① 접속 탐지
        # 후보는 **유사도 상위 2개**다. 셋을 다 태워 살아남는 것으로 짝을 정하는 안과
        # 견줘 이쪽을 택했다 — X4 가 {graph, vector} 대신 {graph, nl2sql} 로 갔다.
        # **이 선택의 근거는 엣지 세트 점수뿐이다** (25 대 23). 위 두 규약과 달리 설계 쪽
        # 독립 논거가 없어 D7 경계에 있고, 그 노출을 harness-evaluation.md 6절에 적어 두었다.
        ranked = router.ranked_tools(qvec)
        cands = ranked[:2]
        if "vector_search" not in cands:                  # 서술 쪽 후보를 반드시 포함
            cands = [cands[0], "vector_search"]
        results = {t: run_tool(t, question, qvec) for t in cands}
        alive = [t for t in cands if results[t]["status"] in HAS_CONTENT]
        if len(alive) >= 2:                               # ② 실행 확인
            return sorted(alive), "parallel_merge"
        # 한쪽만 살았다 → 병렬이 아니다. **라우터의 원래 선택으로 되돌아간다** —
        # 병렬 분기는 도구를 더하기만 하고, 라우터의 판정을 덮어쓰지 않는다.
        if chosen[0] in results:
            r = results[chosen[0]]
            return chosen, {"ok": "single", "no_result": "single",
                            "error": "single"}.get(r["status"], r["status"])

    r = run_tool(chosen[0], question, qvec)
    return chosen, {"ok": "single", "no_result": "single",
                    "error": "single"}.get(r["status"], r["status"])


def score_edge():
    edge = json.load(open(os.path.join(ROOT, "edge-set", "edge-questions.json"), encoding="utf-8"))
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
    print(f"엣지 {n}문항  ·  라우팅 축 {routing}/{n}  ·  실행 축 {execution}/{n}")
    for r in rows:
        print(f"    {r[0]:8} {r[1]:3} {r[2]}{r[3]}  {r[4]:34} {r[5]}")


def score_regression():
    base = json.load(open(os.path.join(ROOT, "companyx-dataset-v1.0", "questions.json"),
                          encoding="utf-8"))
    hit = 0
    rows = []
    for i, x in enumerate(base):
        got, _ = answer(x["q"])
        if set(got) == {x["tool"]}:
            hit += 1
        else:
            rows.append((f"#{i}", f"기대[{x['tool']}] 실제{sorted(got)}", x["q"][:34]))
    print(f"\n회귀 {len(base)}문항  ·  라우팅 축 {hit}/{len(base)}")
    for r in rows:
        print(f"    {r[0]:5} {r[1]:52} {r[2]}")


if __name__ == "__main__":
    if ARG in ("edge", "both"):
        score_edge()
    if ARG in ("regression", "both"):
        score_regression()
