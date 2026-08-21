#!/usr/bin/env node
/**
 * Company-X MCP 서버.
 *
 * 지금 등록하는 것은 **도구 3종**이다. 네 번째(라우터 도구 `ask` 또는 `route`)는
 * 라우터 배치가 정해진 뒤에 붙는다 — D1 이 *"공통부 구현 후 재평가"* 로 미뤄 두었고,
 * 도구 3종·판별 함수·응답 스키마가 그 공통부다. 배치가 정해지면 이 파일에
 * 도구 하나가 추가되고 나머지는 그대로다 (D2 — 최종 4개).
 *
 * transport 는 stdio 로 시작한다 (열어둔 항목). 심사 시연에서 원격 접근이
 * 필요해지면 Streamable HTTP 를 더한다.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { embed } from "./ollama.js";
import { pool } from "./db.js";
import { toolSignatures } from "./assets.js";
import { vectorSearch } from "./tools/vector-search.js";
import { nl2sql } from "./tools/nl2sql.js";
import { knowledgeGraph } from "./tools/knowledge-graph.js";
import type { ToolResult } from "./tools/types.js";

/**
 * 도구 결과를 MCP 응답으로 감싼다.
 *
 * **데이터 부재는 에러가 아니다.** `no_result`·`entity_not_found`·`partial` 은
 * `isError` 없는 정상 결과이고, 모델이 읽고 "모른다"고 답해야 하므로 데이터다.
 * 실행 실패(`error`)만 `isError: true` 다 (MCP 스펙 에러 2계층 · edge-cases.md).
 */
function wrap(result: ToolResult) {
  return {
    content: [{ type: "text" as const, text: JSON.stringify(result, null, 1) }],
    structuredContent: result as unknown as Record<string, unknown>,
    ...(result.status === "error" ? { isError: true } : {}),
  };
}

const server = new McpServer(
  { name: "companyx-mcp", version: "0.1.0" },
  { capabilities: { tools: {} } },
);

// 등록 순서를 고정한다 — tools/list 가 결정적이어야 클라이언트·프롬프트 캐시가 산다.
server.registerTool(
  "vector_search",
  {
    description: toolSignatures["vector_search"]!,
    inputSchema: { question: z.string().describe("사용자 질문 한 문장") },
  },
  async ({ question }) => wrap(await vectorSearch(question, await embed(question))),
);

server.registerTool(
  "nl2sql",
  {
    description: toolSignatures["nl2sql"]!,
    inputSchema: { question: z.string().describe("사용자 질문 한 문장") },
  },
  async ({ question }) => wrap(await nl2sql(question)),
);

server.registerTool(
  "knowledge_graph",
  {
    description: toolSignatures["knowledge_graph"]!,
    inputSchema: { question: z.string().describe("사용자 질문 한 문장") },
  },
  async ({ question }) => wrap(await knowledgeGraph(question)),
);

async function main() {
  await server.connect(new StdioServerTransport());
  process.on("SIGINT", () => void pool.end().then(() => process.exit(0)));
}

main().catch((e: unknown) => {
  console.error("서버 시작 실패:", e);
  process.exit(1);
});
