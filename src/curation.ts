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
import type { NoResult, OkResult, ToolResult, UngroundedResult } from "./tools/types.js";

/**
 * 선별을 거친 도구 결과 — `nl2sql` 의 `sql`·`hits` 가 빠진 모양이다 (hideNl2sqlEvidence).
 *
 * `ToolResult` 와 **다른 타입인 것이 요점이다.** 필드를 지우고도 원래 타입이라고 하면
 * 그 자리에서 타입이 거짓말을 한다 — `UngroundedResult` 는 `sql`·`hits` 를 필수로 갖는다.
 * 직접 호출 창구는 `ToolResult` 그대로이고 (D16), 줄어든 모양은 `ask` 경로에만 있다.
 */
export type CuratedResult =
  | Exclude<ToolResult, OkResult | NoResult | UngroundedResult>
  | Omit<OkResult, "sql">
  | Omit<NoResult, "sql">
  | Omit<UngroundedResult, "sql" | "hits">;

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

/**
 * `nl2sql` 의 부가 필드를 에이전트 경로에서만 뺀다 — **종단 유출을 재고 나서 넣었다** (D18).
 *
 * `sql` 과 `hits` 는 **판정 근거이지 답의 재료가 아니다.** D16("도구 반환은 판정 근거를
 * 담는다")은 도구 **반환**의 규약이라 직접 호출 창구(`server.ts` 의 `wrap`)에는 그대로
 * 남는다 — 선별은 `ask` 경로에만 걸리기 때문이다.
 *
 * 실측이 근거다 (7.10): 소형 모델이 이 둘을 답으로 옮겨 적었다. `OP-02` 는
 * `observed_range` 를 *"salary는 3736에서 9520 사이의 범위를 가집니다"* 로,
 * `X3-02` 는 생성 SQL 을 *"…키워드가 포함된 티켓 목록입니다"* 로 쓰고 **둘 다 `예`** 라고
 * 답해 환각 축이 0 → 2 로 깨졌다. 정확히 D16 이 경고한 인접-사실 미끼다.
 *
 * **`nl2sql` 결과에만 건다.** 두 필드를 갖는 도구가 지금은 이것뿐이라 전 도구에 걸어도
 * 오늘 동작은 같지만, 나중에 다른 도구가 정당한 `hits` 를 실으면 조용히 지워진다.
 *
 * **로그의 `sql` 은 여기서 지워도 남는다** — `gateway.ts` 가 선별 **앞**의 봉투에서
 * 뽑기 때문이고, "로그에 생성 SQL" AC 를 선별 정책과 무관하게 세우려고 그렇게 두었다.
 */
function hideNl2sqlEvidence(r: ToolResult): CuratedResult {
  // 상태로 좁히고 나머지만 취한다 — 캐스트로 타입을 덮지 않는다.
  if (r.status === "ungrounded") {
    const { sql, hits, ...rest } = r;
    return rest;
  }
  if (r.status === "ok" || r.status === "no_result") {
    const { sql, ...rest } = r;
    return rest;
  }
  return r;                                    // error — `sql` 을 안 싣는 자리다
}

/** 순수 함수 — 입력을 변형하지 않고 새 객체를 만든다. */
export function curateResults(
  results: Partial<Record<ToolName, ToolResult>>,
): Partial<Record<ToolName, CuratedResult>> {
  const out: Partial<Record<ToolName, CuratedResult>> = {};
  for (const [tool, r] of Object.entries(results) as [ToolName, ToolResult | undefined][]) {
    if (!r) continue;
    const curated = strip(shortenHints(r), false) as ToolResult;
    out[tool] = tool === "nl2sql" ? hideNl2sqlEvidence(curated) : curated;
  }
  return out;
}
