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
// 동사 어간은 **불변 접두사**까지만 줄인다 (맡고·맡은 → 맡). ㄹ 말음 어간은 한글
// 맞춤법 제18항의 ㄹ 탈락으로 표층 접두사가 갈리므로 짝으로 둔다 (이끌·이끄·이끕) —
// 짝 추가는 휴리스틱이 아니라 닫힌 규칙의 전개다. 접두사를 더 줄이면 오발하는
// 어간(쓰 — "글쓰기"류)은 활용형 열거를 유지하고, 부분문자열이 원리상 못 잡는
// 잔여 부류(ㅡ 탈락 "써", 하다 활용 "속해" 등)는 알려진 한계로 둔다 — 근거와
// 한계 목록은 docs/references/korean-inflection-matching.md (#32).
const RELATION_WORDS: Record<string, string[]> = {
  LEADS: ["이끌", "이끄", "이끕", "리드", "맡", "총괄"],
  BELONGS_TO: ["소속", "속한", "어느 팀", "어느 부서"],
  MANAGES_ACCOUNT: ["담당", "관리"],
  USES: ["사용", "쓰는", "쓰고", "도입"],
  HAS_PROJECT: ["프로젝트"],
  REPORTED_ISSUE: ["이슈", "장애", "문제"],
  HEAD_IS: ["팀장", "부서장", "책임자"],
};

const requestedRelations = (q: string) =>
  Object.entries(RELATION_WORDS).filter(([, ws]) => ws.some((w) => q.includes(w))).map(([r]) => r);

// 최상급 표층형 — 문항이 아니라 언어의 최상급 표현에서 뽑았다 (D7).
const SUPERLATIVE_WORDS = ["가장", "제일", "최다"];

// 노드 타입 5종(graph/schema.md)의 표층형 — 표층 신호를 스키마 어휘에서 뽑는
// D9-a 의 방침 그대로다. 최상급 질문이 엣지의 **어느 끝**을 세느냐는 질문의
// 마지막 타입 어휘가 정한다 — 한국어는 묻는 명사가 문미에 온다 ("가장 많은
// 고객을 담당하는 직원은?" 의 답은 고객이 아니라 직원이다).
const TYPE_WORDS: Record<string, string[]> = {
  employee: ["직원", "사원"],
  project: ["프로젝트"],
  client: ["고객사", "고객"],
  product: ["제품"],
  department: ["부서", "팀"],
};

const askedType = (q: string): string | null => {
  let best: string | null = null;
  let pos = -1;
  for (const [type, ws] of Object.entries(TYPE_WORDS))
    for (const w of ws) {
      const i = q.lastIndexOf(w);
      if (i > pos) { pos = i; best = type; }
    }
  return best;
};

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

/**
 * 그래프 결과에서 **사실 목록만** 꺼낸다.
 *
 * 어느 상태가 사실을 어느 필드에 담는지는 이 모듈이 안다 — 호출자가 `ok` 는 `data`,
 * `partial` 은 `adjacent_facts.data` 라는 것을 알고 분기하면 상태를 하나 더할 때마다
 * 호출자도 같이 고쳐야 한다.
 */
export function graphFacts(r: ToolResult): unknown[] {
  if (r.status === "ok") return r.data;
  if (r.status === "partial") return r.adjacent_facts.data;
  return [];
}

/**
 * 실행 실패를 **도구 안에서** 구조화로 바꾼다 (D14, edge-cases.md T6).
 *
 * `findEntities` 의 DB 실패도 이 래퍼가 덮는다 — 연결이 죽으면 어느 질의든
 * 똑같이 죽으므로 개체 식별과 관계 순회를 나눠 감쌀 이유가 없다.
 * 절단 폭 120자는 `nl2sql` 의 T1 과 맞춘 것이다.
 */
export async function knowledgeGraph(question: string): Promise<ToolResult> {
  try {
    return await knowledgeGraphInner(question);
  } catch (e) {
    return { status: "error", reason: (e as Error).message.slice(0, 120) };  // T6
  }
}

async function knowledgeGraphInner(question: string): Promise<ToolResult> {
  const { matched, unmatched } = await findEntities(question);

  if (unmatched.length && !matched.length) {
    return { status: "entity_not_found", entity: unmatched[0]!, searched: "graph" }; // T5
  }
  const wanted = requestedRelations(question);

  if (!matched.length) {
    // 개체 **언급 자체가 없는** 질문이다 (집계·최상급). 부재가 아니라 무관이다.
    if (!wanted.length) return { status: "no_result", asset: "graph" };
    // 최상급 + 타입 어휘가 걸리면 관계 총계가 아니라 **개체별 최다**를 센다 (#32).
    // "누가 가장 많이"에 `{relation, count}` 를 내면 status: ok 여도 답이 아니다.
    // 물어본 타입이 있는 쪽 끝만 세므로, 타입이 어느 끝에도 없는 관계는 여기서
    // 자연히 떨어진다 ("프로젝트를 … 이끄는 직원" 의 HAS_PROJECT). 동률은 전부
    // 싣는다 — 공동 1위에서 한 명만 내면 도구가 거짓말을 하는 셈이다.
    if (SUPERLATIVE_WORDS.some((w) => question.includes(w))) {
      const type = askedType(question);
      if (type) {
        const top = await query<{ relation: string; name: string; count: string }>(
          `WITH ends AS (
             SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.source
              WHERE e.relation = ANY($1) AND n.type = $2
             UNION ALL
             SELECT e.relation, n.name FROM edges e JOIN nodes n ON n.id = e.target
              WHERE e.relation = ANY($1) AND n.type = $2),
           counted AS (SELECT relation, name, count(*) AS n FROM ends GROUP BY relation, name)
           SELECT relation, name, n::text AS count
             FROM (SELECT relation, name, n,
                          rank() OVER (PARTITION BY relation ORDER BY n DESC) AS rk
                     FROM counted) ranked
            WHERE rk = 1 ORDER BY relation, name`,
          [wanted, type],
        );
        if (top.length) return { status: "ok", data: top };
        // 빈손이면 아래 총계로 떨어진다 — 타입 어휘 부재와 같은 보수적 폴백.
      }
    }
    // **`::text` 다 — 재 보고 기각했다.** `::int` 로 바꿔 따옴표를 없애 봤더니 `X1-01` 이
    // 5/5 정답에서 5/5 오답으로 뒤집혔다 (같은 질문·같은 행, `count` 표현만 다르게 5회씩).
    // 소형 모델은 숫자 표현에 민감하고, 그 민감함이 판정을 바꾼다.
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
