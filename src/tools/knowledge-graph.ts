/**
 * 지식 그래프 — 개체 식별 → 관계 순회.
 *
 * **관계 어휘는 여기 산다. 라우터에 두지 않는다.** D12 는 *도구 선택*에 표층 관계
 * 어휘가 필요 없다고 정했지, 관계 *순회*에 필요 없다고 정한 것이 아니다.
 * 어느 관계를 따라갈지는 도구가 알아야 한다.
 */
import { query } from "../db.js";
import { findEntities } from "./entities.js";
import type { ToolResult } from "./types.js";

// 저작 — graph/schema.md 의 관계 7종에 한국어 표층형을 붙인 것이다.
const RELATION_WORDS: Record<string, string[]> = {
  LEADS: ["이끄", "리드", "맡고", "맡은", "총괄"],
  BELONGS_TO: ["소속", "속한", "어느 팀", "어느 부서"],
  MANAGES_ACCOUNT: ["담당", "관리하"],
  USES: ["사용", "쓰는", "쓰고", "도입"],
  HAS_PROJECT: ["프로젝트"],
  REPORTED_ISSUE: ["이슈", "장애", "문제"],
  HEAD_IS: ["팀장", "부서장", "책임자"],
};

const requestedRelations = (q: string) =>
  Object.entries(RELATION_WORDS).filter(([, ws]) => ws.some((w) => q.includes(w))).map(([r]) => r);

interface Edge { relation: string; name: string }

/** 엣지를 **양방향으로** 탄다 — 부서는 들어오는 BELONGS_TO 를 받는다. */
async function traverse(ids: string[], relations: string[] | null): Promise<Edge[]> {
  const relFilter = relations ? "AND e.relation = ANY($2)" : "";
  const params: unknown[] = relations ? [ids, relations] : [ids];
  return query<Edge>(
    `SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.target
       WHERE e.source = ANY($1) ${relFilter}
     UNION ALL
     SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.source
       WHERE e.target = ANY($1) ${relFilter}`,
    params,
  );
}

export async function knowledgeGraph(question: string): Promise<ToolResult> {
  const { matched, unmatched } = await findEntities(question);

  if (unmatched.length && !matched.length) {
    return { status: "entity_not_found", entity: unmatched[0]!, searched: "graph" }; // T5
  }
  const wanted = requestedRelations(question);

  if (!matched.length) {
    // 개체 **언급 자체가 없는** 질문이다 (집계·최상급). 부재가 아니라 무관이다.
    if (!wanted.length) return { status: "no_result", asset: "graph" };
    const counts = await query<{ relation: string; count: string }>(
      `SELECT relation, count(*)::text FROM edges WHERE relation = ANY($1) GROUP BY relation`,
      [wanted],
    );
    return counts.length
      ? { status: "ok", data: counts }
      : { status: "no_result", asset: "graph" };
  }

  // 같은 이름이 여럿을 가리키면 관계를 합쳐서 답하면 안 된다 — 어느 쪽인지 모른다.
  const byName = new Map<string, typeof matched>();
  for (const e of matched) byName.set(e.name, [...(byName.get(e.name) ?? []), e]);
  for (const [name, group] of byName) {
    if (group.length < 2) continue;
    const hints = await query<{ id: string; type: string; hint: string }>(
      `SELECT n.id, n.type, coalesce(string_agg(DISTINCT m.name, ', '), '(관계 없음)') AS hint
         FROM nodes n LEFT JOIN edges e ON e.source = n.id
         LEFT JOIN nodes m ON m.id = e.target
        WHERE n.id = ANY($1) GROUP BY n.id, n.type`,
      [group.map((g) => g.id)],
    );
    return { status: "ambiguous_entity", name, candidates: hints };
  }

  const ids = matched.map((e) => e.id);
  if (wanted.length) {
    const hits = await traverse(ids, wanted);
    if (hits.length) return { status: "ok", data: hits };
    // T7 — 개체는 있는데 요구한 관계가 없다. 다른 관계를 인접 사실로 붙여 승격한다.
    return {
      status: "partial",
      requested_form: "entity_list",
      unavailable: { asset: "graph", reason: "relation_absent", relation: wanted },
      adjacent_facts: { source: "graph", data: await traverse(ids, null) },
    };
  }
  const hits = await traverse(ids, null);
  return hits.length
    ? { status: "ok", data: hits }
    : { status: "no_result", asset: "graph" };
}
