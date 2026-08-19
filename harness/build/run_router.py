#!/usr/bin/env python3
"""라우터 판별 함수 채점기 — 자체 엣지 세트와 회귀 세트를 나란히 잰다.

  python3 harness/build/run_router.py

D12 의 판별 함수를 그대로 구현한다. 문서 청크 임베딩은 첫 실행에서 만들고
`harness/build/.cache/` 에 둔다 (gitignore). Ollama 가 떠 있어야 한다.

두 점수를 나란히 두는 것이 목적이다 — 회귀만 높고 엣지가 낮으면 그 규칙은
`questions.json` 30개에 맞춰진 것이다 (design.md D7 · 이슈 #7).
"""
import glob, json, math, os, re, sys, urllib.request

ROOT  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A     = os.path.join(ROOT, "harness", "assets")
CACHE = os.path.join(ROOT, "harness", "build", ".cache")
CFG   = json.load(open(os.path.join(A, "model.json"), encoding="utf-8"))
EMB, THRESHOLD = CFG["embedding"]["name"], CFG["router"]["reject_threshold"]
SIGNATURES = json.load(open(os.path.join(A, "tool-signatures.json"), encoding="utf-8"))
GATE       = json.load(open(os.path.join(A, "surface-gate.json"), encoding="utf-8"))

GATE_WORDS = ([w for ws in GATE["tables"].values() for w in ws] + GATE["column_values_ko"])

# route() 가 실제로 낼 수 있는 응답 상태. 병렬 승격(parallel_merge)과
# 부재 판정(partial · entity_not_found)은 아직 구현하지 않았다 (design.md D12 말미).
# 실행 축 점수를 이 집합으로 나눠 읽어야 한다 — 아래 ceiling 계산 참조.
EMITTABLE_STATES = {"single", "out_of_scope"}
ENTITY = re.compile(r"(Client|Product|employee|project|dept)[-_ ]?[A-Za-z0-9]+"
                    r"|[가-힣]{2,4}(?:물산|전자|산업|그룹)")


def embed(text):
    req = urllib.request.Request("http://localhost:11434/api/embed",
        data=json.dumps({"model": EMB, "input": text}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=600).read())["embeddings"][0]


def cosine(a, b):
    return (sum(x * y for x, y in zip(a, b))
            / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))))


def doc_vectors():
    """문서 40건을 고정 길이로 잘라 임베딩한다. 청킹 전략은 열어둔 항목이라 단순 기본값."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"docs-{EMB.replace(':','_')}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    chunks = []
    for p in sorted(glob.glob(os.path.join(ROOT, "companyx-dataset-v1.0", "documents", "*.md"))):
        txt = open(p, encoding="utf-8").read()
        for s in range(0, max(1, len(txt) - 100), 500):
            c = txt[s:s + 600].strip()
            if len(c) > 80:
                chunks.append(c)
    print(f"  문서 청크 {len(chunks)}개 임베딩 중… (최초 1회)", file=sys.stderr)
    vecs = [embed(c) for c in chunks]
    json.dump(vecs, open(path, "w"))
    return vecs


def route(question, qvec, docvecs):
    """D12 판별 함수. 파라미터는 임계 하나뿐이다."""
    if not any(w in question for w in GATE_WORDS):
        if max(cosine(qvec, d) for d in docvecs) >= THRESHOLD:
            return ["vector_search"], "single"          # 표층 충돌(R5) 해소
        if not ENTITY.search(question):
            return [], "out_of_scope"                   # 거절(R1)
    scores = {t: cosine(qvec, v) for t, v in SIGVEC.items()}
    return [max(scores, key=scores.get)], "single"


docvecs = doc_vectors()
SIGVEC  = {t: embed(v) for t, v in SIGNATURES.items() if not t.startswith("_")}

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
