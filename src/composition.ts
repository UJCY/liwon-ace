/**
 * 판별 결과를 실행으로 잇는 공통부 — A안·B안이 **둘 다** 쓴다.
 *
 * 두 안이 갈리는 곳은 "누가 이것을 부르는가"뿐이다.
 *   A안: 서버의 `ask` 가 부른다 (MCP 왕복 1회)
 *   B안: 에이전트가 부른다 (MCP 왕복 2회)
 */
import { route, type Routing, type ToolName } from "./router.js";
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

export interface Composed {
  tools: ToolName[];
  state: string;
  results: Partial<Record<ToolName, ToolResult>>;
  routing: Routing;
}

/** 병렬 후보를 고른다 — 유사도 상위 N + 서술 쪽 후보. */
export function parallelCandidates(r: Routing): ToolName[] {
  const cands = r.ranked.slice(0, MAX_PARALLEL);
  if (!cands.includes("vector_search")) return [cands[0]!, "vector_search"];
  return cands;
}

export async function compose(question: string): Promise<Composed> {
  const qvec = await embed(question);
  const r = await route(question, qvec);
  if (!r.tools.length) return { tools: [], state: r.state, results: {}, routing: r };

  if (r.twoRequests) {
    const cands = parallelCandidates(r);
    const results: Partial<Record<ToolName, ToolResult>> = {};
    for (const t of cands) results[t] = await runTool(t, question, qvec);
    const alive = cands.filter((t) => HAS_CONTENT.has(results[t]!.status));
    if (alive.length >= 2) return { tools: alive.sort(), state: "parallel_merge", results, routing: r };
    // 한쪽만 살면 병렬이 아니다 — 라우터의 원래 선택으로 되돌아간다
    const chosen = r.tools[0]!;
    const res = results[chosen];
    if (res) return { tools: r.tools, state: normalize(res.status), results, routing: r };
  }
  const chosen = r.tools[0]!;
  const res = await runTool(chosen, question, qvec);
  return { tools: r.tools, state: normalize(res.status), results: { [chosen]: res }, routing: r };
}

const normalize = (s: string) =>
  ({ ok: "single", no_result: "single", error: "single" })[s] ?? s;
