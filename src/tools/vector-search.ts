/**
 * 벡터 검색 — 문서 청크 유사도. 빈손이면 인접 사실을 붙여 부분 응답으로 승격한다.
 *
 * **개체를 지목한 질문은 그 개체를 담은 청크로 좁혀서 찾는다** (하이브리드 검색).
 * 순수 유사도만 쓰면 개체명이 질문 벡터에 거의 기여하지 않아 정작 그 개체를 다루는
 * 청크가 상위에 안 든다 — `Client-A` 를 담은 청크 2개가 상위 5에 못 드는 것을 실측했다.
 */
import { query, toVector } from "../db.js";
import { model } from "../assets.js";
import { findEntities } from "./entities.js";
import { knowledgeGraph } from "./knowledge-graph.js";
import type { ToolResult } from "./types.js";

interface Chunk { doc_id: string; sim: string }

export async function vectorSearch(question: string, qvec: number[]): Promise<ToolResult> {
  const v = toVector(qvec);
  const { matched } = await findEntities(question);

  if (matched.length) {
    const names = matched.map((e) => `%${e.name}%`);
    const rows = await query<Chunk>(
      `SELECT doc_id, (1 - (embedding <=> $1::vector))::text AS sim
         FROM document_chunks WHERE content ILIKE ANY($2)
         ORDER BY embedding <=> $1::vector LIMIT 5`,
      [v, names],
    );
    if (rows.length) {
      return { status: "ok", data: rows.map((r) => ({ doc: r.doc_id, sim: Number(r.sim) })) };
    }
    // 개체를 담은 청크가 0건 — T4. 아래에서 인접 사실을 붙인다.
  } else {
    const rows = await query<Chunk>(
      `SELECT doc_id, (1 - (embedding <=> $1::vector))::text AS sim
         FROM document_chunks ORDER BY embedding <=> $1::vector LIMIT 5`,
      [v],
    );
    const top = rows[0];
    if (top && Number(top.sim) >= model.router.reject_threshold) {
      return { status: "ok", data: rows.map((r) => ({ doc: r.doc_id, sim: Number(r.sim) })) };
    }
    return { status: "no_result", asset: "documents" };   // T4 단독 — 인접 사실도 없다
  }

  // T4 → X5 승격: 개체는 다른 자산에 있으니 인접 사실을 분리해서 함께 준다
  const adj = await knowledgeGraph(question);
  const facts = adj.status === "ok" || adj.status === "partial"
    ? (adj.status === "ok" ? adj.data : adj.adjacent_facts.data)
    : [];
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
