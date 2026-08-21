/**
 * NL2SQL — 도구 안에서 LLM 이 SQL 을 만들고 실행한다 (D4). SELECT 만 허용한다.
 *
 * 프롬프트는 자산에서 읽는다 (D13). 스키마는 **인라인 주석본**이다 —
 * 값 목록과 단위가 컬럼 옆에 붙어 있어야 한다. 같은 정보를 별도 블록으로 주면
 * 홀드아웃 정확도가 90% 에서 75% 로 떨어진다 (docs/harness-evaluation.md 1절).
 */
import { annotatedSchema, nl2sqlPrompt } from "../assets.js";
import { generate } from "../ollama.js";
import { query } from "../db.js";
import type { ToolResult } from "./types.js";

const SELECT_ONLY = /^\s*SELECT\b/i;

export function extractSql(raw: string): string {
  const fenced = /```(?:sql)?\s*([\s\S]*?)```/.exec(raw);
  const body = fenced?.[1] ?? raw;
  const m = /(SELECT\b[\s\S]*?)(?:;|$)/i.exec(body);
  return (m?.[1] ?? body).trim();
}

export async function nl2sql(question: string): Promise<ToolResult> {
  const prompt = nl2sqlPrompt
    .replace("{{SCHEMA}}", annotatedSchema)
    .replace("{{QUESTION}}", question);

  const raw = await generate(prompt);
  if (!raw.trim()) {
    // 빈 응답은 T1 이 아니다 — think 가 켜져 num_predict 를 추론이 소진한 것이다.
    return { status: "error", reason: "empty_generation_check_think_option" };
  }
  const sql = extractSql(raw);
  if (!SELECT_ONLY.test(sql)) {
    return { status: "error", reason: "not_select" };            // T2 — 무조건 차단
  }
  try {
    const rows = await query(sql);
    return rows.length
      ? { status: "ok", data: rows }
      : { status: "no_result", asset: "tables" };                // T3 — 실패가 아니다
  } catch (e) {
    return { status: "error", reason: (e as Error).message.slice(0, 120) };  // T1
  }
}
