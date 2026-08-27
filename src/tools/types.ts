/**
 * 도구 응답 타입 (docs/design.md D10, docs/edge-cases.md).
 *
 * **"데이터에 없음"과 "시스템 오류"는 다른 타입이다.** MCP 스펙의 에러 2계층과
 * 대응한다 — 실행 실패(T1·T6)는 `isError: true`, 데이터 부재(T3~T5·T7·T9)·거절(R1)·
 * 부분 응답(X5)은 `isError` 없는 정상 결과 + 구조화 필드다.
 */
export type Asset = "documents" | "graph" | "tables";

export interface OkResult {
  status: "ok";
  /** nl2sql 만 싣는 부가 필드 — 어떤 SQL 이 그 답을 냈는가 (D18). `error` 엔 안 붙인다. */
  sql?: string;
  data: unknown[];
}

/** T3·T4·T7 — 빈손. 인접 사실이 없어 부분 응답으로 승격하지 못한 상태. */
export interface NoResult {
  status: "no_result";
  asset: Asset;
  /** nl2sql 만 싣는 부가 필드 — `OkResult.sql` 과 같은 자리 (D18). */
  sql?: string;
}

/**
 * 접지 실패의 판정 근거 — 검출기(`harness/build/check_grounding.py`)의 hit 모양 그대로다.
 * **판정 근거를 담는다** (D16) — 직접 호출 창구(심사·시연)와 사람 판정이 이것을 읽는다.
 *
 * 채택 정책은 이 두 갈래뿐이다 (D18): 숫자 ×10 초과와 문자열 오배치.
 * 검출기가 함께 내는 `string`(어디에도 없음)은 호출부 필터에서 빠진다.
 */
export type GroundingHit =
  | { kind: "number"; column: string; literal: string; observed_range: [number, number] }
  | { kind: "string_misplaced"; column: string; literal: string; found_in: string[] };

/**
 * T9 — 실행은 됐고 **빈손**인데, 리터럴이 데이터에 접지되지 않았다 (D18).
 *
 * 0행이 두 가지를 뜻한다: "정말 없다"(T3)와 "질문의 값 조건이 데이터와 안 맞는다"(T9).
 * 후자를 "0건입니다"로 답하면 자신 있는 오답이 나간다. **`isError` 없는 정상 계층**이고
 * (실행이 실패한 것이 아니다), **X5 승격 금지**다 — 자료가 있으므로 X5 정의에 안 맞고
 * 인접 사실을 얹으면 모델이 그것을 답으로 쓴다 (Q1).
 */
export interface UngroundedResult {
  status: "ungrounded";
  sql: string;
  hits: GroundingHit[];
}

/** T5 — 개체 자체가 없다. 유사 이름을 추측하지 않는다. */
export interface EntityNotFound {
  status: "entity_not_found";
  entity: string | null;
  searched: Asset;
}

/**
 * X5 — 도구도 맞고 개체도 있는데 **요구한 형태의 자료만** 없다.
 * 없는 것과 있는 것을 **별도 필드로 분리**한다. 섞으면 모델이 인접 사실로부터
 * 요구된 답을 지어낸다 (Q1 이 발생하는 정확한 지점).
 */
export interface PartialResult {
  status: "partial";
  requested_form: "narrative" | "attribute" | "aggregate" | "entity" | "entity_list";
  unavailable: { asset: Asset; reason: string; relation?: string[] };
  adjacent_facts: { source: Asset; data: unknown[] };
}

/** T1·T2·T6 — 실행 실패. 데이터 부재와 구분한다. */
export interface ErrorResult {
  status: "error";
  reason: string;
}

/**
 * 개체 이름이 여럿을 가리킨다 — 답이 없는 것이 아니라 **어느 것인지 모르는** 것이다.
 * T5(개체 부재)와 다르고 X5(형태 부재)와도 다르다. 하나를 골라 답하면 조용히 틀린다.
 */
export interface AmbiguousEntity {
  status: "ambiguous_entity";
  name: string;
  candidates: { id: string; type: string; hint: string }[];
}

export type ToolResult =
  | OkResult | NoResult | EntityNotFound | PartialResult | ErrorResult | AmbiguousEntity
  | UngroundedResult;
