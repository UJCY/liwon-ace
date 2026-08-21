#!/usr/bin/env python3
"""측정용 PostgreSQL 적재 — 문서 청크·임베딩과 그래프.

  python3 harness/build/load_pg.py

이것은 **측정 환경 준비**다. 출하되는 MCP 서버의 적재 경로는 D8 대로 TypeScript로
따로 만든다 — 여기서 정하는 것은 스키마와 청킹 규칙이지 구현체가 아니다.

세 가지를 한다.
  ① document_chunks.embedding 을 vector(768) → vector(1024) 로 바꾼다.
     배포 스키마의 768은 nomic-embed-text 기준이고 우리는 bge-m3(1024)를 쓴다
     (docs/design.md D12 · 열어둔 항목 '임베딩 모델'). 이 테이블은 빈 상태로
     배포되므로 변경을 막는 문면이 없다.
  ② 문서 40건을 고정 길이로 잘라 임베딩해 적재한다. 청킹 전략은 아직 열어둔
     항목이라 단순 기본값(600자 · stride 500)을 쓴다.
  ③ nodes / edges 를 테이블로 적재한다. 그래프를 테이블 뷰로 둘지 별도 테이블로
     둘지는 열어둔 항목이라(D5 하위), 측정에는 별도 테이블을 쓴다.
"""
import glob, json, os, subprocess, sys, urllib.request

ROOT  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DS    = os.path.join(ROOT, "companyx-dataset-v1.0")
CFG   = json.load(open(os.path.join(ROOT, "harness", "assets", "model.json"), encoding="utf-8"))
EMB, DIM = CFG["embedding"]["name"], CFG["embedding"]["dim"]
CONTAINER = os.environ.get("CX_PG", "cx-pg")

CHUNK, STRIDE, MIN_LEN = 600, 500, 80


def psql(sql, quiet=False):
    # SQL 을 stdin 으로 넘긴다 — 임베딩 1024차원 × 40행이 인자 길이 한계를 넘는다
    p = subprocess.run(["docker", "exec", "-i", CONTAINER, "psql", "-U", "postgres",
                        "-d", "companyx", "-v", "ON_ERROR_STOP=1", "-q"],
                       input=sql, capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        sys.exit(f"psql 실패: {p.stderr.strip().splitlines()[:2]}")
    if not quiet and p.stdout.strip():
        print("   ", p.stdout.strip().splitlines()[-1])
    return p.stdout


def embed(text):
    req = urllib.request.Request("http://localhost:11434/api/embed",
        data=json.dumps({"model": EMB, "input": text}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=600).read())["embeddings"][0]


def chunks():
    """문서 40건 → 청크. run_router.py 와 같은 규칙을 쓴다."""
    out = []
    for p in sorted(glob.glob(os.path.join(DS, "documents", "*.md"))):
        txt = open(p, encoding="utf-8").read()
        doc_id = os.path.basename(p)[:-3]
        for i, s in enumerate(range(0, max(1, len(txt) - 100), STRIDE)):
            c = txt[s:s + CHUNK].strip()
            if len(c) > MIN_LEN:
                out.append((doc_id, i, c))
    return out


def load_documents():
    print(f"① embedding 컬럼을 vector({DIM}) 로 바꾼다")
    psql(f"ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector({DIM});")
    cs = chunks()
    print(f"② 청크 {len(cs)}개 임베딩·적재 (600자 · stride 500)")
    psql("TRUNCATE document_chunks;", quiet=True)
    rows = []
    for doc_id, idx, text in cs:
        v = "[" + ",".join(f"{x:.6f}" for x in embed(text)) + "]"
        rows.append((doc_id, idx, text.replace("'", "''"), v))
    values = ",".join(f"('{d}',{i},'{t}','{v}')" for d, i, t, v in rows)
    psql(f"INSERT INTO document_chunks (doc_id, chunk_index, content, embedding) VALUES {values};")
    psql("SELECT count(*) FROM document_chunks;")


def load_graph():
    print("③ nodes / edges 적재")
    nodes = json.load(open(os.path.join(DS, "graph", "nodes.json"), encoding="utf-8"))
    edges = json.load(open(os.path.join(DS, "graph", "edges.json"), encoding="utf-8"))
    psql("""DROP TABLE IF EXISTS edges; DROP TABLE IF EXISTS nodes;
            CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT NOT NULL,
                                name TEXT NOT NULL, properties JSONB DEFAULT '{}');
            CREATE TABLE edges (source TEXT NOT NULL REFERENCES nodes(id),
                                target TEXT NOT NULL REFERENCES nodes(id),
                                relation TEXT NOT NULL);
            CREATE INDEX idx_edges_source ON edges(source, relation);
            CREATE INDEX idx_edges_target ON edges(target, relation);
            CREATE INDEX idx_nodes_name ON nodes(name);""", quiet=True)
    q = lambda s: str(s).replace("'", "''")
    nv = ",".join("('{}','{}','{}','{}')".format(
        q(n["id"]), q(n["type"]), q(n["name"]),
        q(json.dumps(n.get("properties", {}), ensure_ascii=False))) for n in nodes)
    psql(f"INSERT INTO nodes (id, type, name, properties) VALUES {nv};")
    ev = ",".join("('{}','{}','{}')".format(q(e["source"]), q(e["target"]), q(e["relation"]))
                  for e in edges)
    psql(f"INSERT INTO edges (source, target, relation) VALUES {ev};")
    psql("SELECT count(*) || ' nodes, ' || (SELECT count(*) FROM edges) || ' edges' FROM nodes;")


if __name__ == "__main__":
    load_documents()
    load_graph()
    print("적재 완료")
