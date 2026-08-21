/**
 * 규칙 판별 함수 — 질문 하나를 받아 도구 배열과 응답 상태를 정한다 (D12).
 *
 * 파라미터는 임계 하나뿐이다. 0.48~0.57 구간에서 점수가 같다.
 *
 * **라우터 배치(A안/B안)와 무관하다** — 이 함수는 두 배치의 공통부다 (D1).
 * 누가 이것을 호출하고 결과로 무엇을 하는지는 배치가 정한다.
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
const CONJUNCTION = [
  /[고]\s*,/, /는지와/, /현황과/, /[가-힣]과\s/, /[가-힣]와\s/,
  /\?\s*\S/, /[가-힣],\s*[가-힣]/, /그리고/, /[고]\s+[그왜어]/,
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

  if (!gateWords.some((w) => question.includes(w))) {
    const sim = await maxDocSimilarity(v);
    if (sim >= model.router.reject_threshold) {
      // 표층 문자열 충돌(R5) — 스키마 값이 안 걸리고 문서와 충분히 닮았다
      return { tools: ["vector_search"], state: "single", twoRequests, ranked };
    }
    if (!entityPattern.test(question)) {
      // 무매칭(R1) — 도구를 호출하지 않는다 (D6)
      return { tools: [], state: "out_of_scope", twoRequests, ranked };
    }
  }
  return { tools: [ranked[0]!], state: "single", twoRequests, ranked };
}
