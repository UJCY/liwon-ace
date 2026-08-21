/**
 * MCP 서버 연기 시험 — 실제로 뜨고, 도구를 노출하고, 응답하는가.
 *
 *   node scripts/smoke.mjs
 *
 * 정확도는 여기서 재지 않는다 (그건 harness/ 의 몫이다).
 * 여기서 보는 것은 **프로토콜이 오가는가** 하나다.
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const client = new Client({ name: "smoke", version: "0.0.1" });
await client.connect(new StdioClientTransport({ command: "node", args: ["dist/server.js"] }));

const { tools } = await client.listTools();
console.log(`tools/list — ${tools.length}개 (결정적 순서)`);
for (const t of tools) console.log(`  ${t.name}  ${t.description.slice(0, 46)}…`);

const cases = [
  ["knowledge_graph", "Client-A가 사용 중인 제품 목록은?", "ok 기대"],
  ["knowledge_graph", "Client-ZZ의 담당 매니저는 누구인가요?", "entity_not_found 기대 (T5)"],
  ["vector_search", "Client-P에서 발생한 장애의 원인이 뭐야?", "partial 기대 (T4→X5)"],
  ["nl2sql", "서울 지역 고객사는 몇 곳이야?", "ok 기대"],
];

console.log("\ntools/call");
let fail = 0;
for (const [name, question, expect] of cases) {
  const r = await client.callTool({ name, arguments: { question } });
  const status = r.structuredContent?.status ?? "(구조화 응답 없음)";
  const err = r.isError ? " isError" : "";
  const ok = status !== "(구조화 응답 없음)";
  if (!ok) fail++;
  console.log(`  ${name.padEnd(16)} ${String(status).padEnd(18)}${err}  ${expect}`);
}
await client.close();
console.log(fail ? `\n실패 ${fail}건` : "\n연기 시험 통과");
process.exit(fail ? 1 : 0);
