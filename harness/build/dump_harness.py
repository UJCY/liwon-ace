#!/usr/bin/env python3
"""하네스 쪽 판정을 문항별로 덤프한다 — 서버와 대조하기 위한 것이다.

  python3 harness/build/dump_harness.py > /tmp/harness.json

**병렬 합성까지 덤프한다.** 예전에는 껐다 — 서버에 그 계층이 없었기 때문이다.
지금은 `src/composition.ts` 가 그 계층이고 `ask` 가 그것을 부르므로, 끄면
출하 경로의 절반이 대조 밖에 남는다. 양쪽 다 `run_e2e.answer` / `compose` 라는
**러너와 같은 함수**를 부른다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import router, tools, run_e2e

ROOT = router.ROOT


# **대조에 넣는 도구.** 임베딩과 고정 SQL 로만 결과가 정해져 실행 간 같다.
# `nl2sql` 은 생성 SQL 이 실행마다 흔들려 뺀다 — 넣으면 결정적 축이 결합 축으로
# 무너지고 "깨지면 이식 버그다" 라는 축의 뜻이 사라진다.
DETERMINISTIC = ("vector_search", "knowledge_graph")


def decide(question):
    qvec = router.embed(question)
    chosen, state, results, plog = run_e2e.answer(question, qvec)
    # 짝은 None 도 싣는다 — 분기가 안 탔다는 사실 자체가 대조 대상이다.
    return {"tools": chosen, "state": state,
            "twoRequests": tools.has_two_requests(question),
            "ranked": router.ranked_tools(qvec),
            "pair": plog["pair"] if plog else None,
            "pairSource": plog["source"] if plog else None,
            "payload": {t: r for t, r in results.items() if t in DETERMINISTIC}}


edge = json.load(open(os.path.join(ROOT, "edge-set", "edge-questions.json"), encoding="utf-8"))
base = json.load(open(os.path.join(ROOT, "companyx-dataset-v1.0", "questions.json"), encoding="utf-8"))
out = {"edge": {x["id"]: decide(x["q"]) for x in edge},
       "regression": {f"#{i}": decide(x["q"]) for i, x in enumerate(base)}}
print(json.dumps(out, ensure_ascii=False, indent=1))
