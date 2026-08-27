/**
 * 벡터 검색 — 문서 청크 유사도. 빈손이면 인접 사실을 붙여 부분 응답으로 승격한다.
 *
 * **개체를 지목한 질문은 그 개체를 담은 청크로 좁혀서 찾는다** (하이브리드 검색).
 * 순수 유사도만 쓰면 개체명이 질문 벡터에 거의 기여하지 않아 정작 그 개체를 다루는
 * 청크가 상위에 안 든다 — `Client-A` 를 담은 청크 2개가 상위 5에 못 드는 것을 실측했다.
 */
import { query, toVector } from "../db.js";
import { docTopics, model } from "../assets.js";
import { findEntities, type NodeRef } from "./entities.js";
import { graphFacts, knowledgeGraph } from "./knowledge-graph.js";
import type { ToolResult } from "./types.js";

interface Chunk { doc_id: string; content: string; sim: string }

/**
 * 제품 × 기술주제 격자 검사 (#13, T4-form) — `harness/build/tools.py` 의 `_form_gap`.
 *
 * 질문이 기술주제 어휘를 담고 매칭 개체에 제품이 있는데 어느 제품도 그 주제를
 * 커버하지 않으면, 개체 청크가 있어도 요구 형태가 없는 것이다 — `ok` 가 아니라
 * `partial`. 유사도로는 못 가른다 — X5-02(0.520)가 X4-01(0.494)보다 높다 (실측).
 * 주제어가 여럿이면 하나라도 커버될 때 검사를 통과시킨다 (보수 방향).
 */
function formGap(question: string, matched: NodeRef[]): boolean {
  const requested = docTopics.topics.filter((t) => question.includes(t));
  const products = matched.filter((e) => e.type === "product");
  if (!requested.length || !products.length) return false;
  const covered = new Set(products.flatMap((p) => docTopics.coverage[p.name] ?? []));
  return !requested.some((t) => covered.has(t));
}

/**
 * 반환 행의 모양.
 *
 * **`sim` 을 반올림하지 않는다 — 재 보고 기각했다.** 17자리 부동소수가 답에 새는 것을
 * 관측해(`0.7183327628673172`) 3자리로 줄여 봤더니 `X5-02` 가 5/5 정답에서 5/5 오답으로
 * 뒤집혔다 (`0.5197…` → `아니오` · `0.520` → `예`, 같은 프롬프트 5회씩). 종단에서도
 * 응답 축 18/21 → 16/21 이다. 유출은 표시 폭이 아니라 선별에서 다룬다 (`curation.ts`).
 */
const chunkRow = (r: Chunk) => ({ doc: r.doc_id, content: r.content, sim: Number(r.sim) });

/**
 * 실행 실패를 **도구 안에서** 구조화로 바꾼다 (D14, edge-cases.md T6).
 *
 * 승격 경로에서 부르는 `knowledgeGraph` 도 같은 래퍼를 갖고, 그것이 `error` 를
 * 내면 `graphFacts` 가 빈 배열을 주므로 여기서 따로 볼 것이 없다.
 */
export async function vectorSearch(question: string, qvec: number[]): Promise<ToolResult> {
  try {
    return await vectorSearchInner(question, qvec);
  } catch (e) {
    return { status: "error", reason: (e as Error).message.slice(0, 120) };  // T6
  }
}

async function vectorSearchInner(question: string, qvec: number[]): Promise<ToolResult> {
  const v = toVector(qvec);
  const { matched } = await findEntities(question);

  if (matched.length) {
    const names = matched.map((e) => `%${e.name}%`);
    const rows = await query<Chunk>(
      `SELECT doc_id, content, (1 - (embedding <=> $1::vector))::text AS sim
         FROM document_chunks WHERE content ILIKE ANY($2)
         ORDER BY embedding <=> $1::vector LIMIT 5`,
      [v, names],
    );
    if (rows.length && !formGap(question, matched)) {
      return { status: "ok", data: rows.map(chunkRow) };
    }
    // 개체 청크 0건(T4) 또는 격자 빈칸(T4-form, #13) — 아래에서 인접 사실을 붙인다.
    // 격자 빈칸일 때 찾아 둔 청크는 싣지 않는다 — "API 인증" 질문 옆에 "API 키" 든
    // 설치 본문을 놓으면 Q1 환각의 정확한 지점이다 (D10).
  } else {
    const rows = await query<Chunk>(
      `SELECT doc_id, content, (1 - (embedding <=> $1::vector))::text AS sim
         FROM document_chunks ORDER BY embedding <=> $1::vector LIMIT 5`,
      [v],
    );
    const top = rows[0];
    if (top && Number(top.sim) >= model.router.reject_threshold) {
      return { status: "ok", data: rows.map(chunkRow) };
    }
    return { status: "no_result", asset: "documents" };   // T4 단독 — 인접 사실도 없다
  }

  // T4 → X5 승격: 개체는 다른 자산에 있으니 인접 사실을 분리해서 함께 준다
  const facts = graphFacts(await knowledgeGraph(question));
  return {
    status: "partial",
    requested_form: "narrative",
    unavailable: {
      asset: "documents",
      reason: facts.length ? "form_not_covered" : "no_document_for_entity",
    },
    adjacent_facts: { source: "graph", data: facts },
  };
}
