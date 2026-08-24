/**
 * 에이전트 3축 채점기 — 호출 · 환각 · 응답.
 *
 *   node scripts/agent-check.mjs
 *
 * **출하 경로를 그대로 부른다** (`scripts/dump-server.mjs` 와 같은 관례) —
 * `dist/agent/` 의 `connectAgent`·`answerQuestion` 을 쓰고 채점용 사본을 만들지 않는다.
 * 사본을 두면 그것이 출하물과 갈라져도 채점이 통과한다.
 *
 * 59문항에 MCP 세션 하나를 재사용한다 — 문항마다 스폰하면 시그니처 임베딩 워밍이
 * 반복된다. `ask` 합계 실측 61초, 종단(답변 포함)은 5~8분이다.
 *
 * **알려진 변동**: `nl2sql` T1(무효 SQL 생성)이 96문항 중 1~3건 확률로 나고, 그 문항은
 * isError 가드에 걸려 고정 문자열이 나간다 — 응답 축이 1~2점 흔들린다.
 * `docs/harness-evaluation.md` 6절이 적은 실행 간 변동과 같은 성질이다.
 */
import { readFileSync } from "node:fs";
import { connectAgent } from "../dist/agent/client.js";
import { answerQuestion } from "../dist/agent/answer.js";

const j = (p) => JSON.parse(readFileSync(p, "utf8"));
const edge = j("edge-set/edge-questions.json");
const base = j("companyx-dataset-v1.0/questions.json");

/** 첫 줄 파싱 — `harness/build/run_answer.py` 의 규칙과 같아야 한다. */
function verdict(firstLine) {
  const l = (firstLine ?? "").trim();
  if (!l.startsWith("답변가능:")) return null;
  return l.replace(/^답변가능:\s*/, "").trim();
}

/** 요구된 답이 없는 상태들 — 여기서 `예` 가 나오면 환각이다. */
const NO_ANSWER = new Set([
  "out_of_scope", "entity_not_found", "partial", "no_result", "ambiguous_entity",
]);

const client = await connectAgent();
const rows = [];
for (const [i, x] of edge.entries()) {
  const { log } = await answerQuestion(client, x.q);
  rows.push({ id: x.id, expected: x.expected, log, set: "edge" });
  process.stderr.write(`\r엣지 ${i + 1}/${edge.length}   `);
}
for (const [i, x] of base.entries()) {
  const { log } = await answerQuestion(client, x.q);
  rows.push({ id: `#${i}`, expected: null, log, set: "regression" });
  process.stderr.write(`\r회귀 ${i + 1}/${base.length}   `);
}
await client.close();
process.stderr.write("\r");

// ── 호출 축 — 첫 호출이 ask 인가, 도구 3종 직접 호출이 0건인가 (Q4) ─────────
const DIRECT = ["vector_search", "nl2sql", "knowledge_graph"];
let callOk = 0;
let direct = 0;
for (const r of rows) {
  const c = r.log.calls;
  const first = c[0]?.tool === "ask";
  const d = c.filter((x) => DIRECT.includes(x.tool)).length;
  direct += d;
  if (first && d === 0) callOk++;
}
console.log(`호출 축 ${callOk}/${rows.length} (첫 호출 ask · 직접 호출 ${direct}건)`);

// ── 환각 축 — 답이 없는 상태인데 '예' 라고 했는가 (단방향) ────────────────
// `status: ok` 는 "행이 왔다"이지 "질문에 답한다"가 아니다. 그래서 반대 방향
// (답이 있는데 '아니오')은 여기서 세지 않는다 — 그것은 응답 축의 몫이다.
const bad = rows.filter(
  (r) => NO_ANSWER.has(r.log.flat_status ?? "") && verdict(r.log.answer_first_line) === "예",
);
console.log(`환각 축 위반 ${bad.length}/${rows.length} (답 없는 상태에서 '예')`);
for (const r of bad) {
  console.log(`  ${r.id.padEnd(8)} ${r.log.flat_status.padEnd(16)} ${r.log.question.slice(0, 26)}`);
}

// ── 응답 축 — 엣지 29문항 중 상류가 건전한 문항만, 양방향 ─────────────────
// 기대 라벨은 `expected.response` 에서 유도한다. **새 라벨을 만들지 않는다** —
// `questions.json` 30문항에 답변가능 라벨을 붙이는 것은 D7 위반이고 #18 의 범위다.
//
// **조건부 채점 (#20)** — 이 축이 재는 것은 "본 것에 옳게 라벨했는가"다. 오류 가드 ·
// `no_result`(컨텍스트에 아무것도 없음) · 라우팅 불일치(기대와 다른 도구가 답함)는
// 상류 실패라 기대 라벨 자체가 성립하지 않는다 — 실패 6건 사람 판정이 근거다
// (`docs/harness-evaluation.md`). 제외는 로그 필드로만 정해진다: 문항 예외를 두는
// 순간 D7 위반이다. 상류 실패가 status ok 로 위장하면 여기서 못 가른다 (X3-02).
const label = (resp) => (resp === "single" || resp === "parallel_merge" ? "예" : "아니오");
const sameSet = (a, b) =>
  JSON.stringify([...(a ?? [])].sort()) === JSON.stringify([...(b ?? [])].sort());
const upstreamFail = (r) =>
  r.log.guard !== null ? "오류"
  : r.log.flat_status === "no_result" ? "no_result"
  : !sameSet(r.log.routed_to, r.expected.routing) ? "라우팅"
  : null;
const edgeRows = rows.filter((r) => r.set === "edge");
const excluded = [];
let respOk = 0;
const respFail = [];
for (const r of edgeRows) {
  const skip = upstreamFail(r);
  if (skip) {
    excluded.push([r.id, skip]);
    continue;
  }
  const got = verdict(r.log.answer_first_line);
  const want = label(r.expected.response);
  if (got === want) respOk++;
  else respFail.push([r.id, want, got ?? "-", (r.log.answer_first_line ?? "").slice(0, 26)]);
}
const scored = edgeRows.length - excluded.length;
console.log(`응답 축 ${respOk}/${scored} (엣지 세트만 · 양방향 · 상류 실패 ${excluded.length}건 제외)`);
for (const f of respFail) {
  console.log(`  ${f[0].padEnd(8)} 기대 ${f[1].padEnd(4)} 실제 ${f[2].padEnd(4)} | ${f[3]}`);
}
if (excluded.length) {
  console.log(`  제외: ${excluded.map(([id, why]) => `${id}(${why})`).join(" ")}`);
}

// 호출 축은 설계 불변식이므로 깨지면 실패다. 나머지 둘은 측정치다 (문서에 적는 수치).
process.exit(callOk === rows.length ? 0 : 1);
