/**
 * 규칙 판별 함수 — 질문 하나를 받아 도구 배열과 응답 상태를 정한다 (D12).
 *
 * 파라미터는 임계 하나뿐이다. 0.48~0.57 구간에서 점수가 같다.
 *
 * **판별만 한다 — 도구를 태우지 않는다.** 그래서 여기서 낼 수 있는 상태는
 * `single` 과 `out_of_scope` 둘뿐이다. 실행·병합은 `composition.ts` 가 하고,
 * 그것을 MCP 로 내는 것이 `ask` 다 (D1 게이트웨이형 확정, 2026-08-21).
 */
import { cosine } from "./similarity.js";
import { embed } from "./ollama.js";
import { query, toVector } from "./db.js";
import { entityPattern, gateWords, model, toolSignatures } from "./assets.js";

export type ToolName = "vector_search" | "nl2sql" | "knowledge_graph";

export interface Routing {
  tools: ToolName[];
  /** 도구를 부르기 전에 확정되는 상태. 실제 응답 상태는 도구 실행이 정한다. */
  state: "single" | "out_of_scope";
  /** 요구 원소가 둘로 보이는가 — 병렬 후보 판단에 쓴다 (D11-4). */
  twoRequests: boolean;
  /** 유사도 내림차순. 병렬 짝을 고를 때 쓴다. */
  ranked: ToolName[];
}

let signatureVectors: Map<ToolName, number[]> | null = null;

async function signatures(): Promise<Map<ToolName, number[]>> {
  if (signatureVectors) return signatureVectors;
  const m = new Map<ToolName, number[]>();
  for (const [name, text] of Object.entries(toolSignatures)) {
    m.set(name as ToolName, await embed(text));
  }
  signatureVectors = m;
  return m;
}

/** 질문과 문서 청크의 최대 유사도. 거절과 문서 선호를 이 값 하나가 가른다. */
async function maxDocSimilarity(qvec: number[]): Promise<number> {
  const rows = await query<{ sim: string }>(
    `SELECT 1 - (embedding <=> $1::vector) AS sim
       FROM document_chunks ORDER BY embedding <=> $1::vector LIMIT 1`,
    [toVector(qvec)],
  );
  return rows[0] ? Number(rows[0].sim) : 0;
}

// 저작 — 한국어 접속 표층형. "요구 원소 2개"(D11-4)가 문장에서 드러나는 자리다.
// 이 신호만으로 병렬을 확정하지 않는다 — 접속된 두 요구가 같은 도구에 걸리면
// 단일 선택이다(X1·X2). 확정은 도구를 태워 본 뒤에 한다.
//
// **문항 문면을 그대로 옮긴 패턴은 두지 않는다 (D7).** `는지와`·`현황과` 는
// 채점 대상인 X4-02·X4-01 의 문면에서만 나왔고, `그리고`·`[고]\s+[그왜어]` 는
// 두 세트 어디에도 걸리지 않았다. 넷 다 일반형에 흡수되거나 사문이라
// 지워도 두 세트 점수가 움직이지 않는다.
const CONJUNCTION = [
  /[고]\s*,/, /[가-힣]과\s/, /[가-힣]와\s/, /\?\s*\S/, /[가-힣],\s*[가-힣]/,
];

export const hasTwoRequests = (q: string) => CONJUNCTION.some((re) => re.test(q));

export async function route(question: string, qvec?: number[]): Promise<Routing> {
  const v = qvec ?? (await embed(question));
  const twoRequests = hasTwoRequests(question);
  const sig = await signatures();
  const ranked = [...sig.entries()]
    .map(([t, sv]) => [t, cosine(v, sv)] as const)
    .sort((a, b) => b[1] - a[1])
    .map(([t]) => t);

  // maxDocSimilarity 는 DB 조회다 — 게이트 미히트 ∧ 개체 없음일 때만 돈다.
  if (!gateWords.some((w) => question.includes(w)) && !entityPattern.test(question)) {
    const sim = await maxDocSimilarity(v);
    if (sim >= model.router.reject_threshold) {
      // 거절 직전 구제(R5) — 스키마 어휘도 개체 한정어도 없지만 문서와 충분히 닮았다
      return { tools: ["vector_search"], state: "single", twoRequests, ranked };
    }
    // 무매칭(R1) — 도구를 호출하지 않는다 (D6)
    return { tools: [], state: "out_of_scope", twoRequests, ranked };
  }
  return { tools: [ranked[0]!], state: "single", twoRequests, ranked };
}
