/**
 * 도구 응답 타입 (docs/design.md D10, docs/edge-cases.md).
 *
 * **"데이터에 없음"과 "시스템 오류"는 다른 타입이다.** MCP 스펙의 에러 2계층과
 * 대응한다 — 실행 실패(T1·T6)는 `isError: true`, 데이터 부재(T3~T5·T7)·거절(R1)·
 * 부분 응답(X5)은 `isError` 없는 정상 결과 + 구조화 필드다.
 */
export type Asset = "documents" | "graph" | "tables";

export interface OkResult {
  status: "ok";
  data: unknown[];
}

/** T3·T4·T7 — 빈손. 인접 사실이 없어 부분 응답으로 승격하지 못한 상태. */
export interface NoResult {
  status: "no_result";
  asset: Asset;
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
  | OkResult | NoResult | EntityNotFound | PartialResult | ErrorResult | AmbiguousEntity;
