#!/usr/bin/env node
/**
 * Company-X MCP 서버.
 *
 * 등록 도구는 **4개** — `ask` + 도구 3종 (D2).
 *
 * `ask` 가 게이트웨이다 (A안, D1 확정 2026-08-21). 판별·실행·병합까지 하고
 * 결과와 **라우팅 판단**을 함께 돌려준다. 도구 3종도 등록해 두는 것은 개별
 * 검증·시연·심사 창구를 남기기 위해서다.
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
import { ask } from "./gateway.js";
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
  "ask",
  {
    description:
      "사내 데이터에 대한 자연어 질문에 답한다. 규칙 기반 라우터가 적합한 도구를 " +
      "골라 실행하고 결과를 돌려준다. 어느 도구를 왜 골랐는지도 함께 온다. " +
      "평소에는 이 도구 하나만 부르면 된다.",
    inputSchema: { question: z.string().describe("사용자 질문 한 문장") },
  },
  async ({ question }) => {
    const r = await ask(question);
    return {
      content: [{ type: "text" as const, text: JSON.stringify(r, null, 1) }],
      structuredContent: r as unknown as Record<string, unknown>,
    };
  },
);

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
