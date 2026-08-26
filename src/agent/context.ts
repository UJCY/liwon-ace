/**
 * 프롬프트에 넣을 컨텍스트를 만든다 — 봉투를 평평하게 펴고, 넘치면 행을 덜어낸다.
 *
 * **평탄화가 정확도를 바꾼다.** `ask` 봉투를 통째로 넣으면 모델이 `routed_to`·`why`
 * 같은 라우팅 메타데이터까지 답의 재료로 읽는다. 도구 결과 항목 하나로 펴서 주면
 * `harness/tests/answer-protocol.json` 이 채점하는 모양과 같아진다 (D15).
 *
 * **절사는 안전장치다 — 그리고 예산은 토큰 상한 아래여야 한다.** `num_ctx` 에서
 * `num_predict` 를 뺀 것이 프롬프트 예산이고, 실측하면 그것이 이 예산보다 **적은**
 * 글자수에서 찬다. **종전 6000자는 그 상한보다 커서 안전장치가 아니었다** — 그 구간에서는
 * 여기가 덜기 전에 Ollama 가 먼저 조용히 자르고 `truncations` 는 빈 채로 남는다.
 * 본문을 싣는 #25 가 실측 최대를 끌어올려 이 자리가 사정권에 들어왔다.
 * 행 상한은 여전히 두지 않는다: 상한을 두면 안 넘치는 질문에서도 행이 잘려 판정이 바뀐다.
 *
 * **수치는 여기 적지 않는다** — 원본은 `docs/harness-evaluation.md` 7.2·7.6 이고,
 * 사본을 두면 채점·측정이 바뀔 때 표류한다 (D15 ⑧, #28).
 */
import type { AskEnvelope } from "./client.js";

export interface FlatContext {
  flat: Record<string, unknown>;
  /** 평탄화 결과의 `status` — 환각 축 채점의 입력이다. */
  status: string;
}

export interface Truncation {
  path: string;
  droppedRows: number;
}

/**
 * 봉투를 도구 결과 모양으로 편다.
 *
 * **개수가 아니라 봉투 `status` 로 가른다.** 병렬 되돌리기 경로(`composition.ts`)는
 * `results` 가 2개인 채로 `single` 류 상태를 낼 수 있어서, 개수로 가르면 오판한다.
 */
export function flatten(env: AskEnvelope): FlatContext {
  const results = env.results ?? {};
  let flat: Record<string, unknown>;

  if (env.status === "out_of_scope") {
    flat = { status: "out_of_scope", reason: "no_candidate_tool", note: env.matched_rule };
  } else if (env.status === "parallel_merge") {
    flat = { status: "parallel_merge", results };
  } else {
    // 봉투의 single·partial·entity_not_found·ambiguous_entity 는 전부 여기다.
    // 항목 자체의 status 가 ok·no_result·partial… 로 드러난다.
    const chosen = env.routed_to?.[0];
    const item = chosen ? (results[chosen] as Record<string, unknown> | undefined) : undefined;
    flat = item ?? { status: env.status, results };
  }
  return { flat, status: String(flat["status"] ?? "") };
}

interface ArrayRef {
  path: string;
  arr: unknown[];
}

/** 트리 안의 배열을 경로와 함께 모은다. */
function collectArrays(node: unknown, path: string, out: ArrayRef[]): void {
  if (Array.isArray(node)) {
    out.push({ path, arr: node });
    for (const v of node) collectArrays(v, path, out);
    return;
  }
  if (node === null || typeof node !== "object") return;
  for (const [k, v] of Object.entries(node as Record<string, unknown>)) {
    collectArrays(v, path ? `${path}.${k}` : k, out);
  }
}

/**
 * 예산을 넘으면 **가장 긴 배열의 마지막 행부터** 하나씩 덜어낸다.
 *
 * 무엇을 얼마나 덜어냈는지 돌려준다 — 조용한 절사는 "다 넣었다"로 읽힌다 (Q2).
 * `indent = 1` 은 `harness/build/run_answer.py` 의 `json.dumps(..., indent=1)` 과 맞춘 것이다.
 */
export function fitBudget(
  flat: Record<string, unknown>,
  budget = 5000,
): { json: string; before: number; truncations: Truncation[] } {
  const work = structuredClone(flat);
  let json = JSON.stringify(work, null, 1);
  const before = json.length;
  const dropped = new Map<string, number>();

  while (json.length > budget) {
    const refs: ArrayRef[] = [];
    collectArrays(work, "", refs);
    const longest = refs
      .filter((r) => r.arr.length > 0)
      .sort((a, b) => b.arr.length - a.arr.length)[0];
    if (!longest) break;                       // 덜어낼 행이 없다
    longest.arr.pop();
    dropped.set(longest.path, (dropped.get(longest.path) ?? 0) + 1);
    json = JSON.stringify(work, null, 1);
  }

  return {
    json,
    before,
    truncations: [...dropped].map(([path, droppedRows]) => ({ path, droppedRows })),
  };
}
