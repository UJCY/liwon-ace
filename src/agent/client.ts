/**
 * MCP 클라이언트 — 에이전트가 서버에 닿는 유일한 통로.
 *
 * **부를 수 있는 도구가 `ask` 하나뿐인 것을 코드가 보장한다** (Q4 · D15).
 * `listTools` 를 부르지 않고 LLM 에 도구 목록도 선택권도 주지 않는다 — 시스템
 * 프롬프트 지시로 두면 소형 모델에서 샌다 (edge-cases.md Q4). 도구 4개가
 * `tools/list` 에 노출되는 것은 프로토콜 사실이고, 그것을 막는 것은 이 파일이다.
 *
 * 나간 호출은 전부 `calls()` 에 남는다 — 호출 축 검증의 원천이다
 * (`scripts/agent-check.mjs`).
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/** 에이전트가 부르는 도구 이름. **상수 하나** 이고 바깥에서 바꿀 수 없다. */
const ASK = "ask";

export interface CallRecord {
  /** 이 연결에서 몇 번째 호출인가. */
  seq: number;
  tool: string;
}

/** `ask` 봉투 (`src/gateway.ts`) + MCP 응답 계층의 두 신호. */
export interface AskEnvelope {
  status?: string;
  routed_to?: string[];
  matched_rule?: string;
  why?: unknown;
  results?: Record<string, unknown>;
  /** MCP 에러 2계층의 위 계층 — 태운 도구가 실행에 실패했는가. */
  isError: boolean;
  /** `structuredContent` 실물. **부재 자체가 실패 신호다** — 가드가 이것을 본다. */
  structured: unknown;
  /** content 텍스트. 구조화 응답이 없을 때 로그에 남길 유일한 단서다. */
  text: string;
}

export interface AgentClient {
  askOnly(question: string): Promise<AskEnvelope>;
  close(): Promise<void>;
  calls(): CallRecord[];
}

export async function connectAgent(): Promise<AgentClient> {
  // dist/agent/client.js 기준 상대 위치 — 같은 저장소의 서버를 그대로 띄운다.
  const serverPath = join(dirname(fileURLToPath(import.meta.url)), "..", "server.js");
  const client = new Client({ name: "companyx-agent", version: "0.1.0" });
  await client.connect(
    new StdioClientTransport({ command: process.execPath, args: [serverPath] }),
  );

  const calls: CallRecord[] = [];
  return {
    async askOnly(question: string): Promise<AskEnvelope> {
      // 호출 전에 적는다 — 던지고 죽은 호출도 나간 호출이다.
      calls.push({ seq: calls.length + 1, tool: ASK });
      const r = await client.callTool({ name: ASK, arguments: { question } });
      const envelope = (r.structuredContent ?? {}) as Partial<AskEnvelope>;
      const content = (r.content ?? []) as { type: string; text?: string }[];
      return {
        ...envelope,
        isError: r.isError === true,
        structured: r.structuredContent,
        text: content.map((c) => c.text ?? "").join("").slice(0, 200),
      };
    },
    calls: () => [...calls],
    close: () => client.close(),
  };
}
