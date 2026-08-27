/**
 * 판별 결과를 실행으로 잇는 계층. **D1 은 게이트웨이형으로 닫혔다 (2026-08-21)** —
 * 이것을 부르는 곳은 `gateway.ts` 의 `ask` 하나다. 기각된 조언자형에서는
 * 에이전트가 이 자리를 대신했겠지만 그 경로는 남기지 않았다.
 *
 * 대조 덤프(`scripts/dump-server.mjs`)도 **같은 함수**를 부른다 — 대조용 사본을
 * 따로 두면 그것이 출하 경로와 갈라져도 대조가 통과한다.
 */
import { listSideTool, route, type Routing, type ToolName } from "./router.js";
import { embed } from "./ollama.js";
import { vectorSearch } from "./tools/vector-search.js";
import { nl2sql } from "./tools/nl2sql.js";
import { knowledgeGraph } from "./tools/knowledge-graph.js";
import type { ToolResult } from "./tools/types.js";

export const MAX_PARALLEL = 2;
/** `ok` 만 살아 있는 갈래로 센다 — partial 은 "요구 형태가 없다"는 뜻이다. */
const HAS_CONTENT = new Set(["ok"]);

export async function runTool(
  tool: ToolName, question: string, qvec: number[],
): Promise<ToolResult> {
  if (tool === "knowledge_graph") return knowledgeGraph(question);
  if (tool === "vector_search") return vectorSearch(question, qvec);
  return nl2sql(question);
}

/** 합성이 낼 수 있는 응답 상태 전부. 채점 라벨과 같은 어휘다 (edge-set/README.md). */
export type ComposedState =
  | "single" | "parallel_merge" | "out_of_scope"
  | "partial" | "entity_not_found" | "ambiguous_entity";

export interface Composed {
  tools: ToolName[];
  state: ComposedState;
  results: Partial<Record<ToolName, ToolResult>>;
  routing: Routing;
  /** 병렬 분기가 **태운** 후보 둘. 분기를 안 탔으면 null (#12 결정 5). */
  pair: ToolName[] | null;
  /** 그 짝을 축 신호가 정했는가, 유사도 폴백이 정했는가. */
  pairSource: "signal" | "fallback" | null;
}

/**
 * 태운 도구 중 **실행에 실패한** 것이 있는가.
 *
 * MCP 에러 2계층 판정의 입력이다 — 실행 실패(T1·T6)만 `isError` 이고
 * 데이터 부재(`no_result`·`partial`·`entity_not_found`)는 정상 결과다
 * (docs/edge-cases.md 공통 규약).
 *
 * **`status` 만 읽는다.** 그래서 받는 타입도 그만큼이다 — `ask` 는 선별을 거쳐 필드가
 * 줄어든 결과(`curation.ts` 의 `CuratedResult`)를 넘기는데, 실행 실패 판정에 필요한 것은
 * 그때도 `status` 뿐이다.
 */
export const hasExecutionError = (
  results: Partial<Record<ToolName, { status: string }>>,
): boolean => Object.values(results).some((r) => r?.status === "error");

export interface PairChoice {
  pair: ToolName[];
  source: "signal" | "fallback";
}

/**
 * 병렬 후보 둘을 고른다.
 *
 * 서술 변(`vector_search`)은 **고정 멤버**다 — D3 의 병렬 정의 두 유형(X3·X4) 모두
 * 한쪽이 서술이라 설계에서 유도된다. 규칙이 정하는 것은 목록 변 한 자리고, 그것을
 * **첫 요구 안 축 어휘의 위치**가 정한다 (`listSideTool`). 신호가 침묵하면 유사도
 * 폴백이다 — 종전 규칙 그대로이고 동작이 같다 (#12 결정 4).
 * 근거·대가·노출은 docs/agreements/issue-12-parallel-pair-selection.md 와
 * docs/design.md D3 · docs/harness-evaluation.md 4.3·6절에 있다.
 */
export function parallelCandidates(question: string, r: Routing): PairChoice {
  const side = listSideTool(question);
  if (side) {
    const pair: ToolName[] = ["vector_search", side];
    return { pair: pair.sort(), source: "signal" };
  }
  const cands = r.ranked.slice(0, MAX_PARALLEL);
  const pair: ToolName[] = cands.includes("vector_search") ? cands : [cands[0]!, "vector_search"];
  return { pair: [...pair].sort(), source: "fallback" };
}

export async function compose(question: string): Promise<Composed> {
  const qvec = await embed(question);
  const r = await route(question, qvec);
  let pair: ToolName[] | null = null;
  let pairSource: "signal" | "fallback" | null = null;
  if (!r.tools.length) {
    return { tools: [], state: r.state, results: {}, routing: r, pair, pairSource };
  }

  if (r.twoRequests) {
    const choice = parallelCandidates(question, r);
    ({ pair, source: pairSource } = choice);
    const cands = choice.pair;
    const results: Partial<Record<ToolName, ToolResult>> = {};
    for (const t of cands) results[t] = await runTool(t, question, qvec);
    const alive = cands.filter((t) => HAS_CONTENT.has(results[t]!.status));
    if (alive.length >= 2) {
      return { tools: alive.sort(), state: "parallel_merge", results, routing: r, pair, pairSource };
    }
    // 한쪽만 살면 병렬이 아니다 — 라우터의 원래 선택으로 되돌아간다.
    // **신호가 고른 짝은 그대로 싣는다** — 확정 상태와 따로 봐야 실패의 출처가 보인다.
    const chosen = r.tools[0]!;
    const res = results[chosen];
    if (res) {
      return { tools: r.tools, state: normalize(res.status), results, routing: r, pair, pairSource };
    }
  }
  const chosen = r.tools[0]!;
  const res = await runTool(chosen, question, qvec);
  return {
    tools: r.tools, state: normalize(res.status), results: { [chosen]: res }, routing: r,
    pair, pairSource,
  };
}

/**
 * 도구 응답 상태를 채점 어휘로 옮긴다.
 *
 * `error` 도 `single` 로 접는 것은 **채점 축의 규약**이다 — 라우팅이 맞았는지를
 * 실행 실패가 가리면 안 된다. 실행 실패 자체는 `results` 안에 남고 MCP 응답의
 * `isError` 로 올라간다 (hasExecutionError).
 *
 * `ungrounded` 도 같이 접는다 — 독립 `ComposedState` 로 두면 기대가 `single` 인
 * `OP-02`·`R4-02` 가 엣지 실행 축에서 −2 다 (D19). `HAS_CONTENT` 는 `{"ok"}` 그대로다:
 * `ungrounded` 는 내용 있는 갈래가 아니므로 병렬 생존으로 세지 않는다.
 */
const normalize = (s: ToolResult["status"]): ComposedState =>
  s === "ok" || s === "no_result" || s === "error" || s === "ungrounded" ? "single" : s;
