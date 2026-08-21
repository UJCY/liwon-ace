#!/usr/bin/env python3
"""에이전트 최종 답변 규약 채점기.

  python3 harness/build/run_answer.py

도구가 돌려준 구조화 응답(partial · out_of_scope · entity_not_found)을 주고,
에이전트가 **인접 사실을 요구된 답인 것처럼 말하지 않는가**를 잰다
(docs/edge-cases.md Q1·Q3, docs/design.md D10 에이전트 규약).

프롬프트는 harness/assets/prompts/agent-answer.md 의 코드블록에서 **추출한다** —
여기에 다시 적지 않는다 (docs/design.md D13).

**LLM 판정자를 쓰지 않는다.** 채점은 두 축의 결정적 비교로 끝난다
(edge-set/README.md 2절) — 그것을 가능하게 하려고 프롬프트가 첫 줄에
열거형(`답변가능: 예|아니오`)을 강제한다.
"""
import json, os, re, sys, urllib.request

ROOT  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A     = os.path.join(ROOT, "harness", "assets")
MODEL = json.load(open(os.path.join(A, "model.json"), encoding="utf-8"))["llm"]
TESTS = json.load(open(os.path.join(ROOT, "harness", "tests",
                                    "answer-protocol.json"), encoding="utf-8"))


def template():
    """agent-answer.md 의 첫 코드블록이 프롬프트 실물이다."""
    md = open(os.path.join(A, "prompts", "agent-answer.md"), encoding="utf-8").read()
    m = re.search(r"```\n(.*?)```", md, re.S)
    if not m:
        sys.exit("agent-answer.md 에서 프롬프트 코드블록을 찾지 못했다")
    return m.group(1)


TEMPLATE = template()


def build_prompt(case):
    return (TEMPLATE
            .replace("{{QUESTION}}", case["q"])
            .replace("{{STRUCTURED_RESULT}}",
                     json.dumps(case["tool_result"], ensure_ascii=False, indent=1)))


def generate(prompt):
    body = {"model": MODEL["name"], "prompt": prompt, "stream": False,
            "options": MODEL["options"]}
    if not MODEL.get("think", False):
        body["think"] = False
    req = urllib.request.Request("http://localhost:11434/api/generate",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=900).read())["response"].strip()


def grade(case, out):
    """두 축. 형식 축이 깨지면 판정 축은 잴 수 없다 — 그래서 따로 센다."""
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    form = (len(lines) >= 3
            and lines[0].startswith("답변가능:")
            and lines[1].startswith("확인된 답:")
            and lines[2].startswith("인접 사실:"))
    verdict = None
    if form:
        verdict = re.sub(r"^답변가능:\s*", "", lines[0]).strip()
    ok = form and verdict == case["expected"]["answerable"]
    leaked = re.search(case["forbidden_regex"], out)     # 환각 문구가 새어 나왔는가
    return form, ok and not leaked, (leaked.group(0) if leaked else None), lines[:2]


form_hits = verdict_hits = 0
rows = []
for case in TESTS:
    out = generate(build_prompt(case))
    form, ok, leaked, head = grade(case, out)
    form_hits += form
    verdict_hits += ok
    rows.append((case["id"], "형식OK" if form else "형식X",
                 "통과" if ok else ("환각" if leaked else "판정X"),
                 leaked or " / ".join(head)[:64]))

n = len(TESTS)
print(f"답변 규약 {n}문항")
print(f"  형식 축 (열거형 3줄 준수): {form_hits}/{n}   ← 판정 축이 성립하는 전제")
print(f"  판정 축 (답변가능 라벨 일치 + 금지 문구 없음): {verdict_hits}/{n}")
for r in rows:
    print(f"  {r[0]:6} {r[1]:5} {r[2]:4} | {r[3]}")
