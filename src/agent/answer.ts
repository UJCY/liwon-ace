/**
 * 질문 하나를 최종 답변으로 바꾼다 — 에이전트의 본체.
 *
 * **얇다.** `ask` 를 한 번 부르고, 실패면 LLM 을 태우지 않고, 아니면 결과를 펴서
 * 자산 프롬프트에 넣는다. 판별·실행·병합은 서버가 한다 (D1 게이트웨이형).
 * 프롬프트는 `harness/assets/prompts/agent-answer.md` 에서 읽는다 — 코드에 두 번째
 * 사본을 두지 않는다 (D13).
 */
import { agentAnswerPrompt } from "../assets.js";
import { generate } from "../ollama.js";
import type { AgentClient } from "./client.js";
import { fitBudget, flatten } from "./context.js";
import { appendLog, type AgentLogRecord } from "./log.js";

/**
 * 실행 실패 시 내보내는 고정 문자열. **LLM 을 태우지 않는다** —
 * 읽을 구조화 응답이 없는 상태에서 생성을 돌리면 그것이 정확히 환각이다.
 */
export const SYSTEM_ERROR_ANSWER =
  "시스템 오류가 발생해 지금은 답변할 수 없습니다. 잠시 후 다시 시도해 주세요.";

export interface AgentAnswer {
  text: string;
  log: AgentLogRecord;
}

const firstLine = (s: string) => s.split("\n").map((l) => l.trim()).find((l) => l) ?? "";

/**
 * 동명이인 부록 줄 — 후보를 **코드가** 덧붙인다.
 *
 * 프롬프트에 규칙을 더하지 않는다 (D13 규약 2). 채점기는 앞 3줄만 읽으므로
 * 이 줄이 하네스 점수를 움직이지 않는다.
 */
function candidateLine(flat: Record<string, unknown>): string {
  const name = String(flat["name"] ?? "");
  const cands = (flat["candidates"] ?? []) as { type?: string; hint?: string }[];
  return `후보: ${cands.map((c) => `${name}(${c.type}: ${c.hint})`).join(" / ")}`;
}

export async function answerQuestion(
  client: AgentClient,
  question: string,
): Promise<AgentAnswer> {
  const seen = client.calls().length;
  const env = await client.askOnly(question);
  const calls = client.calls().slice(seen);

  const base = {
    ts: new Date().toISOString(),
    question,
    calls,
    is_error: env.isError,
  };

  // 가드 — 실행 실패(isError)와 봉투 부재(structuredContent 없음)를 하나로 덮는다.
  // 라우팅·임베딩 단계에서 죽으면 도구 래퍼(D14)가 닿지 못해 두 번째 모양이 나온다.
  if (env.isError || env.structured === undefined) {
    const record: AgentLogRecord = {
      ...base,
      guard: "is_error",
      error_text: env.text,
      envelope_status: env.status ?? null,
      routed_to: env.routed_to ?? null,
      matched_rule: env.matched_rule ?? null,
      flat_status: null,
      context_chars: null,
      truncations: [],
      answer_first_line: SYSTEM_ERROR_ANSWER,
    };
    appendLog(record);
    return { text: SYSTEM_ERROR_ANSWER, log: record };
  }

  const { flat, status } = flatten(env);
  const { json, before, truncations } = fitBudget(flat);

  const prompt = agentAnswerPrompt
    .replace("{{QUESTION}}", question)
    .replace("{{STRUCTURED_RESULT}}", json);
  const out = (await generate(prompt)).trim();

  const text = status === "ambiguous_entity" ? `${out}\n${candidateLine(flat)}` : out;

  const record: AgentLogRecord = {
    ...base,
    guard: null,
    error_text: null,
    envelope_status: env.status ?? null,
    routed_to: env.routed_to ?? null,
    matched_rule: env.matched_rule ?? null,
    flat_status: status,
    context_chars: before,
    truncations,
    answer_first_line: firstLine(out),
  };
  appendLog(record);
  return { text, log: record };
}
