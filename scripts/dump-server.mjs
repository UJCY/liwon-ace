/**
 * 서버 쪽 판정을 문항별로 덤프한다 — 하네스와 대조하기 위한 것이다.
 *
 *   node scripts/dump-server.mjs > /tmp/server.json
 *
 * MCP 를 거치지 않고 컴파일된 모듈을 직접 부른다. 프로토콜 왕복은
 * scripts/smoke.mjs 가 따로 확인하고, 여기서 보는 것은 **판정이 같은가** 다.
 */
import { readFileSync } from "node:fs";
import { pool } from "../dist/db.js";
import { compose } from "../dist/composition.js";

const j = (p) => JSON.parse(readFileSync(p, "utf8"));
const edge = j("edge-set/edge-questions.json");
const base = j("companyx-dataset-v1.0/questions.json");

/**
 * **출하 경로를 그대로 부른다.** `ask` 가 부르는 함수가 `compose` 이므로
 * 여기서도 그것을 부른다 — 대조용으로 판별·실행을 다시 짜면 그 사본이
 * 출하물과 갈라져도 대조가 통과해 버린다. 병렬 합성도 이 경로 안에 있다.
 */
async function decide(question) {
  const c = await compose(question);
  return {
    tools: c.tools, state: c.state,
    twoRequests: c.routing.twoRequests, ranked: c.routing.ranked,
  };
}

const out = { edge: {}, regression: {} };
for (const x of edge) out.edge[x.id] = await decide(x.q);
for (const [i, x] of base.entries()) out.regression[`#${i}`] = await decide(x.q);
await pool.end();
process.stdout.write(JSON.stringify(out, null, 1));
