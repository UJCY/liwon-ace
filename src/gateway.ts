/**
 * A안 — 게이트웨이형. `ask` 하나가 판별·실행·병합까지 하고 결과를 돌려준다.
 * MCP 왕복 1회. 에이전트는 질문을 넘기고 컨텍스트를 받는다.
 *
 * **라우팅 판단을 반드시 실어 보낸다** — A안이 파는 것이 관측성이므로
 * `routed_to`·`matched_rule`·`why` 를 응답에 넣어 값싸게 회수한다
 * (routing-topology.md 4.4).
 */
import { compose } from "./composition.js";
import { curateResults } from "./curation.js";

export async function ask(question: string) {
  const c = await compose(question);
  return {
    status: c.state,
    routed_to: c.tools,
    matched_rule: explain(c),
    why: {
      two_requests: c.routing.twoRequests,
      ranked: c.routing.ranked,
    },
    // 선별은 이 경로에만 건다 — 도구 3종 직접 호출은 원본을 그대로 낸다 (D15).
    results: curateResults(c.results),
  };
}

function explain(c: Awaited<ReturnType<typeof compose>>): string {
  if (!c.tools.length) return "무매칭 — 스키마 어휘도 개체 한정어도 없고 문서와도 닮지 않았다 (R1)";
  if (c.state === "parallel_merge") return "요구 원소가 둘이고 두 도구가 모두 내용을 냈다 (X3·X4)";
  if (c.state === "partial") return "도구와 개체는 맞고 요구한 형태의 자료만 없다 (X5)";
  if (c.state === "entity_not_found") return "질문의 개체가 그래프에 없다 (T5)";
  if (c.state === "ambiguous_entity") return "그 이름이 여럿을 가리킨다 — 어느 쪽인지 물어야 한다";
  return "요구 원소가 하나이고 시그니처 유사도가 가장 높은 도구가 답했다";
}
