/**
 * 호출 로그 — 1질문 1레코드 JSONL.
 *
 * **호출 축(Q4)과 절사 내역(Q2)의 원천이다.** 무엇을 부르고 무엇을 얼마나 잘라
 * 넣었는지가 여기 남지 않으면 두 축 다 사후에 확인할 수 없다.
 */
import { appendFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { CallRecord } from "./client.js";
import type { Truncation } from "./context.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const LOG_DIR = join(HERE, "..", "..", "logs");
const LOG_FILE = join(LOG_DIR, "agent-calls.jsonl");

export interface AgentLogRecord {
  ts: string;
  question: string;
  /** 이 질문에서 나간 MCP 호출 전부 — 호출 축의 원천 (Q4). */
  calls: CallRecord[];
  is_error: boolean;
  /** 가드가 발동했으면 `"is_error"` — 그 질문은 LLM 을 타지 않았다. */
  guard: "is_error" | null;
  /** 가드 발동 시 MCP 응답 본문 요약. 구조화 응답이 없을 때 유일한 단서다. */
  error_text: string | null;
  envelope_status: string | null;
  routed_to: string[] | null;
  /** `ask` 봉투의 라우팅 판단 — CLI 관측 줄이 읽는다. */
  matched_rule: string | null;
  /** 평탄화 결과의 status — 환각 축 입력. 봉투 status 와 다르다. */
  flat_status: string | null;
  /** 절사 **전** 직렬화 길이. */
  context_chars: number | null;
  truncations: Truncation[];
  answer_first_line: string;
}

export function appendLog(record: AgentLogRecord): void {
  mkdirSync(LOG_DIR, { recursive: true });
  appendFileSync(LOG_FILE, `${JSON.stringify(record)}\n`, "utf8");
}
