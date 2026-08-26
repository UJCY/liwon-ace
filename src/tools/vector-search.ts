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
import { graphFacts, knowledgeGraph } from "./knowledge-graph.js";
import type { ToolResult } from "./types.js";

interface Chunk { doc_id: string; sim: string }

/**
 * 반환 행의 모양 — **유사도는 소수 3자리로 줄인다.**
 *
 * 17자리 부동소수를 컨텍스트에 넣을 이유가 없고, 실제로 모델이 그것을 답에 그대로
 * 옮겨 적는 것을 관측했다 (`0.7183327628673172`, `logs/agent-calls.jsonl`).
 * 문서가 인용하는 유사도 수치도 전부 3자리다. `harness/build/tools.py` 와 같은 폭이다.
 */
const shape = (r: Chunk) => ({ doc: r.doc_id, sim: Math.round(Number(r.sim) * 1000) / 1000 });

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
      `SELECT doc_id, (1 - (embedding <=> $1::vector))::text AS sim
         FROM document_chunks WHERE content ILIKE ANY($2)
         ORDER BY embedding <=> $1::vector LIMIT 5`,
      [v, names],
    );
    if (rows.length) {
      return { status: "ok", data: rows.map(shape) };
    }
    // 개체를 담은 청크가 0건 — T4. 아래에서 인접 사실을 붙인다.
  } else {
    const rows = await query<Chunk>(
      `SELECT doc_id, (1 - (embedding <=> $1::vector))::text AS sim
         FROM document_chunks ORDER BY embedding <=> $1::vector LIMIT 5`,
      [v],
    );
    const top = rows[0];
    // **임계 비교는 반올림 전 값으로 한다.** 반올림은 표시용이고 판정용이 아니다.
    if (top && Number(top.sim) >= model.router.reject_threshold) {
      return { status: "ok", data: rows.map(shape) };
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
