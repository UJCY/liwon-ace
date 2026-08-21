#!/usr/bin/env python3
"""라우터 판별 함수 채점기 — 자체 엣지 세트와 회귀 세트를 **라우팅 축**으로 잰다.

  python3 harness/build/run_router.py

판별 로직은 router.py 한 곳에 있다. 도구를 태우지 않으므로 실행 축은
`single`/`out_of_scope` 두 상태로 포화한다 — 실행 축을 재려면 run_e2e.py 를 쓴다.

두 점수를 나란히 두는 것이 목적이다 — 회귀만 높고 엣지가 낮으면 그 규칙은
`questions.json` 30개에 맞춰진 것이다 (design.md D7 · 이슈 #7).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import router
from router import ROOT, EMITTABLE_STATES, embed, route

docvecs = router.doc_vectors()

regression = json.load(open(os.path.join(ROOT, "companyx-dataset-v1.0", "questions.json"), encoding="utf-8"))
edge       = json.load(open(os.path.join(ROOT, "edge-set", "edge-questions.json"), encoding="utf-8"))

hit, misses = 0, []
for i, x in enumerate(regression):
    got, _ = route(x["q"], embed(x["q"]), docvecs)
    if set(got) == {x["tool"]}: hit += 1
    else: misses.append(("#%d" % i, "", f"기대[{x['tool']}] 실제{got}", x["q"][:34]))
print(f"회귀 {len(regression)}문항 · 라우팅 축: {hit}/{len(regression)}")
for m in misses: print(f"  {m[0]:6} {m[2]:44} {m[3]}")

routing = execution = 0
efail = []
for x in edge:
    got, state = route(x["q"], embed(x["q"]), docvecs)
    ok = set(got) == set(x["expected"]["routing"])
    routing += ok
    execution += state == x["expected"]["response"]
    if not ok:
        efail.append((x["id"], x["case"],
                      f"기대{sorted(x['expected']['routing'])} 실제{sorted(got)}", x["q"][:32]))
ceiling = sum(1 for x in edge if x["expected"]["response"] in EMITTABLE_STATES)
unreachable = {}
for x in edge:
    r = x["expected"]["response"]
    if r not in EMITTABLE_STATES:
        unreachable[r] = unreachable.get(r, 0) + 1

print(f"\n엣지 {len(edge)}문항 · 라우팅 축: {routing}/{len(edge)} · "
      f"실행 축: {execution}/{len(edge)}  (도달 가능 상한 {ceiling}"
      f"{' — 포화' if execution == ceiling else ''})")
if unreachable:
    print("  route() 가 낼 수 없는 상태: "
          + " · ".join(f"{k} {v}" for k, v in sorted(unreachable.items()))
          + f"  → 실행 축은 {ceiling}/{len(edge)} 를 넘을 수 없다")
for m in efail: print(f"  {m[0]:8} {m[1]:3} {m[2]:52} {m[3]}")
