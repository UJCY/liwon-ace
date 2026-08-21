#!/usr/bin/env python3
"""하네스 쪽 판정을 문항별로 덤프한다 — 서버와 대조하기 위한 것이다.

  python3 harness/build/dump_harness.py > /tmp/harness.json

병렬 합성을 **끈 상태**로 덤프한다. 서버에 그 계층이 아직 없어서
켜 두면 모든 접속 문항이 "다르다"로 나와 이식 버그가 묻힌다.
병렬 자체의 대조는 4번째 도구가 생긴 뒤에 한다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import router, tools

ROOT = router.ROOT
docvecs = router.doc_vectors()


def decide(question):
    qvec = router.embed(question)
    chosen, state = router.route(question, qvec, docvecs)
    if not chosen:
        return {"tools": [], "state": state,
                "twoRequests": tools.has_two_requests(question),
                "ranked": router.ranked_tools(qvec)}
    t = chosen[0]
    r = (tools.knowledge_graph(question) if t == "knowledge_graph"
         else tools.vector_search(question, qvec, router.THRESHOLD) if t == "vector_search"
         else tools.nl2sql(question))
    st = {"ok": "single", "no_result": "single", "error": "single"}.get(r["status"], r["status"])
    return {"tools": chosen, "state": st,
            "twoRequests": tools.has_two_requests(question),
            "ranked": router.ranked_tools(qvec)}


edge = json.load(open(os.path.join(ROOT, "edge-set", "edge-questions.json"), encoding="utf-8"))
base = json.load(open(os.path.join(ROOT, "companyx-dataset-v1.0", "questions.json"), encoding="utf-8"))
out = {"edge": {x["id"]: decide(x["q"]) for x in edge},
       "regression": {f"#{i}": decide(x["q"]) for i, x in enumerate(base)}}
print(json.dumps(out, ensure_ascii=False, indent=1))
