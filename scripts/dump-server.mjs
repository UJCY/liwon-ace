/**
 * 서버 쪽 판정을 문항별로 덤프한다 — 하네스와 대조하기 위한 것이다.
 *
 *   node scripts/dump-server.mjs > /tmp/server.json
 *
 * MCP 를 거치지 않고 컴파일된 모듈을 직접 부른다. 프로토콜 왕복은
 * scripts/smoke.mjs 가 따로 확인하고, 여기서 보는 것은 **판정이 같은가** 다.
 */
import { readFileSync } from "node:fs";
import { route } from "../dist/router.js";
import { embed } from "../dist/ollama.js";
import { pool } from "../dist/db.js";
import { vectorSearch } from "../dist/tools/vector-search.js";
import { nl2sql } from "../dist/tools/nl2sql.js";
import { knowledgeGraph } from "../dist/tools/knowledge-graph.js";

const j = (p) => JSON.parse(readFileSync(p, "utf8"));
const edge = j("edge-set/edge-questions.json");
const base = j("companyx-dataset-v1.0/questions.json");

async function runTool(tool, question, qvec) {
  if (tool === "knowledge_graph") return knowledgeGraph(question);
  if (tool === "vector_search") return vectorSearch(question, qvec);
  return nl2sql(question);
}

/** 서버에는 병렬 합성 계층이 없다 — 4번째 도구가 붙을 자리다 (D1). */
async function decide(question) {
  const qvec = await embed(question);
  const r = await route(question, qvec);
  if (!r.tools.length) {
    return { tools: [], state: r.state, twoRequests: r.twoRequests, ranked: r.ranked };
  }
  const res = await runTool(r.tools[0], question, qvec);
  const state = ({ ok: "single", no_result: "single", error: "single" })[res.status] ?? res.status;
  return { tools: r.tools, state, twoRequests: r.twoRequests, ranked: r.ranked };
}

const out = { edge: {}, regression: {} };
for (const x of edge) out.edge[x.id] = await decide(x.q);
for (const [i, x] of base.entries()) out.regression[`#${i}`] = await decide(x.q);
await pool.end();
process.stdout.write(JSON.stringify(out, null, 1));
