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

/**
 * 서버에 넘길 환경변수 — **우리 서버가 읽는 것만** 명시한다.
 *
 * SDK 기본 상속은 `HOME·LOGNAME·PATH·SHELL·TERM·USER` 뿐이라
 * (`stdio.js` 의 `DEFAULT_INHERITED_ENV_VARS`) 이걸 안 넘기면 `PG*`·`OLLAMA_HOST` 가
 * 전부 버려진다. 그러면 `npm start` 는 환경변수로 설정되는데 **`npm run agent` 만
 * 기본값에 고정되고**, 에이전트의 답변 생성(in-process)과 서버의 임베딩이 서로 다른
 * Ollama 로 갈릴 수도 있다.
 *
 * `process.env` 를 통째로 넘기지 않는 것은 자식 프로세스로 새는 면적 때문이다
 * (실측 51개 대 6개). SDK 는 기본값과 **합치므로** `PATH` 는 그대로 산다.
 *
 * 목록의 출처는 `src/db.ts` (PG 5종) 와 `src/ollama.ts` (`OLLAMA_HOST`) 다.
 * 거기에 환경변수를 더하면 여기도 더해야 한다.
 */
const PASS_ENV = ["PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE", "OLLAMA_HOST"];

const passEnv = (): Record<string, string> =>
  Object.fromEntries(
    PASS_ENV.flatMap((k) => {
      const v = process.env[k];
      return v === undefined ? [] : [[k, v] as [string, string]];
    }),
  );

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
    new StdioClientTransport({
      command: process.execPath,
      args: [serverPath],
      env: passEnv(),
    }),
  );

  const calls: CallRecord[] = [];
  return {
    async askOnly(question: string): Promise<AskEnvelope> {
      // 호출 전에 적는다 — 던지고 죽은 호출도 나간 호출이다.
      calls.push({ seq: calls.length + 1, tool: ASK });
      // 타임아웃 300초 — SDK 기본 60초는 기계가 다른 부하와 겹치면 `ask` 하나로도
      // 넘는다 (실측: 부하평균 20 에서 종단 실행 2회 연속 중단 사망). 판정 경로가
      // 아니라 중단 방지다 — 느린 답은 완주하고, 축은 내용으로만 채점된다.
      const r = await client.callTool(
        { name: ASK, arguments: { question } },
        undefined,
        { timeout: 300_000 },
      );
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
