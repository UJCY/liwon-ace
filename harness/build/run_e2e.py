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

# ── 유저-결과 내역 — 자동층 (docs/design.md D17) ─────────────────────────────
# 실패 문항을 유저가 받은 결과로 가른다. 서열: 속는다 > 오류 표면화 >
# 정직한 거절/부분 > 중복·토큰 낭비. 어휘는 응답 상태 규약(D6·D10·D14)에서 온다.
# 이 채점기는 답변 LLM 을 안 태우므로 "오답 도구가 ok" 칸은 속는다/정직을
# 원리적으로 못 가른다 — 사람 판정으로 넘기고, 판정은 harness-evaluation.md 에 적는다.
HONEST = {"no_result", "partial", "entity_not_found", "ambiguous_entity", "out_of_scope"}
SEVERITY = ["속는다", "오류 표면화", "정직한 거절/부분", "중복·토큰 낭비"]


def user_outcome(exp_tools, exp_resp, got, results, state):
    """`(범주, 로그 서명)` 을 돌려준다. exp_resp 는 회귀 세트에서 None 이다."""
    raws = [results[t]["status"] for t in got if t in results] or [state]
    if "error" in raws:
        return "오류 표면화", "error"
    if all(r in HONEST for r in raws):
        return "정직한 거절/부분", raws[0]
    # 내용 있는 응답(ok)이 유저에게 나갔다. 기대 도구가 전부 포함돼 있으면
    # 맞는 답 + 잉여 도구다 — 로그만으로 중복이 확정된다 (#4 #10 의 무늬).
    if exp_resp in (None, "single", "parallel_merge") and set(exp_tools) <= set(got):
        return "중복·토큰 낭비", "초집합 병렬"
    # 부분 겹침 — 기대 도구 중 일부가 살아 있으면 맞는 내용이 나갔을 수 있다 (#5 무늬).
    if set(exp_tools) == set(got):
        sig = "위장 ok"
    elif set(exp_tools) & set(got):
        sig = "부분 겹침"
    else:
        sig = "오답 도구 ok"
    return "사람 판정 필요", sig


def print_outcomes(items):
    """0건 범주도 항상 찍는다 — D17 강제 한 줄("속는다를 늘리는 변경은 기각")의
    관측 대상이 속는다 줄이라, 생략하면 실행마다 감시 대상이 안 보인다."""
    manual = [x for x in items if x[1] == "사람 판정 필요"]
    auto = [x for x in items if x[1] != "사람 판정 필요"]
    print(f"  유저-결과 내역 — 실패 {len(items)}건 (자동 {len(auto)} · 사람 판정 {len(manual)})")
    for cat in SEVERITY:
        rows = [x for x in auto if x[1] == cat]
        tail = ("   " + " ".join(f"{i}({sig})" for i, _, sig in rows)) if rows else ""
        print(f"    {cat} {len(rows)}{tail}")
    tail = ("   " + " ".join(f"{i}({sig})" for i, _, sig in manual)) if manual else ""
    print(f"    ── 사람 판정 필요 {len(manual)}{tail}")


def normalize(status):
    """도구 응답 상태를 채점 어휘로 옮긴다 — src/composition.ts 의 normalize 와 같다.

    `error` 도 `single` 로 접는 것은 채점 축의 규약이다. 실행 실패 자체는
    서버 쪽에서 MCP 응답의 `isError` 로 올라간다 (docs/edge-cases.md 공통 규약).
    `ungrounded` 도 같이 접는다 — 어휘 출처는 D18 이다 (D17 허용 범위).
    """
    return "single" if status in ("ok", "no_result", "error", "ungrounded") else status


def run_tool(tool, question, qvec):
    if tool == "knowledge_graph":
        return tools.knowledge_graph(question)
    if tool == "vector_search":
        return tools.vector_search(question, qvec, router.THRESHOLD)
    return tools.nl2sql(question)


def answer(question, qvec=None):
    """판별 → 실행 → (필요하면) 병렬 확정. **덤프도 이 함수를 쓴다** —
    대조가 러너와 다른 경로를 보면 출하 경로의 이식 버그를 못 잡는다.

    `(고른 도구, 응답 상태, 도구 결과)` 셋을 돌려준다. **셋째가 있는 것은 대조가
    반환 형태까지 보게 하기 위해서다** — 종전에는 도구 결과를 버렸고, 그래서 반환
    필드를 한쪽 구현에만 더해도 대조가 그대로 통과했다 (#25). `src/composition.ts`
    의 `compose` 가 `results` 를 함께 돌려주는 것과 같은 모양이다.
    """
    qvec = router.embed(question) if qvec is None else qvec
    chosen, state = router.route(question, qvec, docvecs)
    if not chosen:
        return chosen, state, {}                          # 거절 — 도구를 안 부른다

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
            return sorted(alive), "parallel_merge", results
        # 한쪽만 살았다 → 병렬이 아니다. **라우터의 원래 선택으로 되돌아간다** —
        # 병렬 분기는 도구를 더하기만 하고, 라우터의 판정을 덮어쓰지 않는다.
        if chosen[0] in results:
            return chosen, normalize(results[chosen[0]]["status"]), results

    r = run_tool(chosen[0], question, qvec)
    return chosen, normalize(r["status"]), {chosen[0]: r}


def score_edge():
    edge = json.load(open(os.path.join(ROOT, "edge-set", "edge-questions.json"), encoding="utf-8"))
    routing = execution = 0
    rows = []
    outcomes = []
    for x in edge:
        got, state, res = answer(x["q"])
        r_ok = set(got) == set(x["expected"]["routing"])
        e_ok = state == x["expected"]["response"]
        routing += r_ok
        execution += e_ok
        if not (r_ok and e_ok):
            rows.append((x["id"], x["case"], "R" if not r_ok else " ", "E" if not e_ok else " ",
                         f"{x['expected']['response']} → {state}", x["q"][:26]))
            outcomes.append((x["id"], *user_outcome(x["expected"]["routing"],
                                                    x["expected"]["response"], got, res, state)))
    n = len(edge)
    print(f"엣지 {n}문항  ·  라우팅 축 {routing}/{n}  ·  실행 축 {execution}/{n}")
    for r in rows:
        print(f"    {r[0]:8} {r[1]:3} {r[2]}{r[3]}  {r[4]:34} {r[5]}")
    print_outcomes(outcomes)


def score_regression():
    base = json.load(open(os.path.join(ROOT, "companyx-dataset-v1.0", "questions.json"),
                          encoding="utf-8"))
    hit = 0
    rows = []
    outcomes = []
    for i, x in enumerate(base):
        got, state, res = answer(x["q"])
        if set(got) == {x["tool"]}:
            hit += 1
        else:
            rows.append((f"#{i}", f"기대[{x['tool']}] 실제{sorted(got)}", x["q"][:34]))
            outcomes.append((f"#{i}", *user_outcome([x["tool"]], None, got, res, state)))
    print(f"\n회귀 {len(base)}문항  ·  라우팅 축 {hit}/{len(base)}")
    for r in rows:
        print(f"    {r[0]:5} {r[1]:52} {r[2]}")
    print_outcomes(outcomes)


if __name__ == "__main__":
    if ARG in ("edge", "both"):
        score_edge()
    if ARG in ("regression", "both"):
        score_regression()
