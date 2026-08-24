/**
 * `ask` 가 에이전트에게 줄 결과에서 무관 필드를 거르고 동명이인 힌트를 줄인다.
 *
 * **TACC 적용 실물이다** (D15) — 열어둔 항목 `TACC 적용 세부` 가 말한 "반환 컨텍스트
 * 선별" 지점이 여기 하나다. 절사가 아니라 **선별**이다: 소형 LLM 은 식별자·타임스탬프를
 * 답으로 뱉는다. 실측 — 무관 필드를 거르자 `OP-05` 가 `아니오` → `예` 로 돌아섰고
 * 동명이인 힌트를 축약하자 ambiguous 판정이 2/8 → 8/8 이 됐다.
 *
 * **도구 3종 직접 호출 경로(`src/server.ts` 의 `wrap`)에는 걸지 않는다.** 그 창구는
 * 심사·시연용이라 원본을 그대로 보여야 하고, 무엇보다 `harness/build/tools.py` 와
 * 갈라지면 안 된다 — 대조 59/59 의 전제다.
 */
import type { ToolName } from "./router.js";
import type { ToolResult } from "./tools/types.js";

/** 프롬프트에 들어가면 안 되는 키 — 식별자·타임스탬프류 (TACC 적용 실물, D15). */
const NOISE_KEY = /^id$|_id$|_at$|email|^is_|^created|^updated/;

/**
 * 배열 안의 객체에서만 무관 키를 지운다.
 *
 * `ToolResult` 최상위 구조 필드(`status`·`data`·`adjacent_facts`·`unavailable`·
 * `candidates`)는 정규식에 걸리지 않아 그대로 남고, 행 객체의 식별자만 빠진다.
 * `candidates[].id` 는 걸려서 빠진다 — 후보를 구별하는 단서는 `hint` 가 맡는다
 * (`types.ts` AmbiguousEntity 의 "후보와 구별 단서" 규약).
 */
function strip(value: unknown, inArrayItem: boolean): unknown {
  if (Array.isArray(value)) return value.map((v) => strip(v, true));
  if (value === null || typeof value !== "object") return value;
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
    if (inArrayItem && NOISE_KEY.test(k)) continue;
    out[k] = strip(v, false);
  }
  return out;
}

/**
 * 동명이인 후보의 구별 단서를 첫 항목만 남긴다.
 *
 * 힌트가 관계 이름 전량이면 후보 하나가 수십 자가 되고, 그러면 모델이 되묻지 않고
 * 그 안의 이름 하나를 답으로 고른다. 1개짜리(`"(관계 없음)"`)는 그대로 둔다.
 */
function shortenHints(r: ToolResult): ToolResult {
  if (r.status !== "ambiguous_entity") return r;
  return {
    ...r,
    candidates: r.candidates.map((c) => {
      const parts = c.hint.split(", ");
      return parts.length > 1 ? { ...c, hint: `${parts[0]!} 외` } : c;
    }),
  };
}

/** 순수 함수 — 입력을 변형하지 않고 새 객체를 만든다. */
export function curateResults(
  results: Partial<Record<ToolName, ToolResult>>,
): Partial<Record<ToolName, ToolResult>> {
  const out: Partial<Record<ToolName, ToolResult>> = {};
  for (const [tool, r] of Object.entries(results) as [ToolName, ToolResult | undefined][]) {
    if (!r) continue;
    out[tool] = strip(shortenHints(r), false) as ToolResult;
  }
  return out;
}
