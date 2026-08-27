"""라우터 판별 함수 — 두 러너가 공유한다 (docs/design.md D12).

`run_router.py` 는 라우팅 축만, `run_e2e.py` 는 도구까지 태워 두 축을 잰다.
판별 로직은 여기 한 벌만 둔다.
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
# 개체 한정어 인식. 목록은 자산에서 읽는다 — tools.py 의 미등록 언급 판정과 **같은 목록**이다.
# 갈라지면 라우터가 거절한 질문이 knowledge_graph 에 닿지 못해 T5 를 낼 수 없다.
_EP = json.load(open(os.path.join(A, "entity-patterns.json"), encoding="utf-8"))
ENTITY = re.compile(r"(" + "|".join(_EP["id_prefixes"]) + r")[-_ ]?[A-Za-z0-9]+"
                    r"|[가-힣]{2,5}(?:" + "|".join(_EP["company_suffix"]) + r")")

# route() 가 실제로 낼 수 있는 응답 상태. 도구를 태우지 않으면 이 둘뿐이다.
EMITTABLE_STATES = {"single", "out_of_scope"}

CHUNK, STRIDE, MIN_LEN = 600, 500, 80


def embed(text, attempts=3):
    """일시 오류에 재시도한다 — 측정 도중 Ollama 가 400 을 한 번 내면
    59문항 측정이 통째로 죽는다. 실제로 두 번 겪었다.
    이것은 T1 재시도 정책과 무관하다 — 생성 품질이 아니라 전송 실패다."""
    import time
    for i in range(attempts):
        try:
            req = urllib.request.Request("http://localhost:11434/api/embed",
                data=json.dumps({"model": EMB, "input": text}).encode(),
                headers={"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=600).read())["embeddings"][0]
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(2 * (i + 1))


def cosine(a, b):
    return (sum(x * y for x, y in zip(a, b))
            / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))))


def doc_vectors():
    """문서 청크 임베딩. load_pg.py 와 같은 청킹 규칙을 쓴다."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"docs-{EMB.replace(':','_')}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    chunks = []
    for p in sorted(glob.glob(os.path.join(ROOT, "companyx-dataset-v1.0", "documents", "*.md"))):
        txt = open(p, encoding="utf-8").read()
        for s in range(0, max(1, len(txt) - 100), STRIDE):
            c = txt[s:s + CHUNK].strip()
            if len(c) > MIN_LEN:
                chunks.append(c)
    print(f"  문서 청크 {len(chunks)}개 임베딩 중… (최초 1회)", file=sys.stderr)
    vecs = [embed(c) for c in chunks]
    json.dump(vecs, open(path, "w"))
    return vecs


SIGVEC = {t: embed(v) for t, v in SIGNATURES.items() if not t.startswith("_")}


def route(question, qvec, docvecs):
    """D12 판별 함수. 파라미터는 임계 하나뿐이다."""
    if (not any(w in question for w in GATE_WORDS)
            and not ENTITY.search(question)):
        if max(cosine(qvec, d) for d in docvecs) >= THRESHOLD:
            return ["vector_search"], "single"          # 거절 직전 구제(R5)
        return [], "out_of_scope"                       # 거절(R1)
    scores = {t: cosine(qvec, v) for t, v in SIGVEC.items()}
    return [max(scores, key=scores.get)], "single"


def ranked_tools(qvec):
    """시그니처 유사도 내림차순. 병렬 후보를 고를 때 쓴다."""
    scores = {t: cosine(qvec, v) for t, v in SIGVEC.items()}
    return sorted(scores, key=scores.get, reverse=True)
