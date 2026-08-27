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
 * isError 가드에 걸려 고정 문자열이 나간다 — 응답 축에서 `오류` 로 제외되므로 점수가
 * 아니라 분모와 제외 줄이 흔들린다. `docs/harness-evaluation.md` 6절의 실행 간 변동과
 * 같은 성질이다.
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

/**
 * 요구된 답이 없는 상태들 — 여기서 `예` 가 나오면 환각이다.
 * `ungrounded` 도 여기다 (D18): 행이 안 온 데다 질문의 값 조건이 데이터와 대조되지
 * 않았으므로, 답이 없는 정도가 `no_result` 보다 강하다. 어휘 출처는 D18 (D17 허용 범위).
 */
const NO_ANSWER = new Set([
  "out_of_scope", "entity_not_found", "partial", "no_result", "ambiguous_entity",
  "ungrounded",
]);

const client = await connectAgent();
const rows = [];

/**
 * 인프라 일과성 실패(Ollama 500 · MCP 타임아웃)만 재시도한다 — 문항 하나의
 * 히컵으로 8분짜리 실행 전체가 죽는 것을 막는다 (부하평균 20+ 실측에서 3회 사망).
 * 채점은 답 **내용**으로만 하므로 재시도는 축을 움직이지 않는다. nl2sql T1 은
 * 서버 안에서 isError 가드로 돌아오지 여기로 던져지지 않는다 — 재시도 대상이 아니다.
 */
async function answerWithRetry(q) {
  for (let attempt = 1; ; attempt++) {
    try {
      return await answerQuestion(client, q);
    } catch (e) {
      if (attempt >= 4) throw e;
      process.stderr.write(`\n재시도 ${attempt}/3 (${String(e.message).slice(0, 40)})\n`);
      await new Promise((r) => setTimeout(r, 45_000));
    }
  }
}

for (const [i, x] of edge.entries()) {
  const { log } = await answerWithRetry(x.q);
  rows.push({ id: x.id, expected: x.expected, log, set: "edge" });
  process.stderr.write(`\r엣지 ${i + 1}/${edge.length}   `);
}
for (const [i, x] of base.entries()) {
  const { log } = await answerWithRetry(x.q);
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
// `ungrounded` 도 상류 실패다 — 컨텍스트에 답의 재료가 없는 것은 `no_result` 와 같고,
// 제외 사유로 상태명이 그대로 찍힌다 (D18).
const upstreamFail = (r) =>
  r.log.guard !== null ? "오류"
  : r.log.flat_status === "no_result" || r.log.flat_status === "ungrounded" ? r.log.flat_status
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

// ── 유저-결과 내역 — 자동층 (docs/design.md D17) — 문항당 한 범주 ─────────
// 서열: 속는다 > 오류 표면화 > 정직한 거절/부분 > 중복·토큰 낭비. 어휘는 응답
// 상태 규약(D6·D10·D14). 분류 대상은 환각 위반 ∪ 응답 축 실패 ∪ 제외 행이고,
// 축 점수는 위에서 그대로 센다 — 여기는 같은 실패를 유저-결과로 다시 갠 것이다.
// "상태 ok + 답변 아니오" 칸은 로그 서명이 같아(X5-02 옳은 거절 vs X3-02 라벨
// 불성립) 사람 판정으로 넘긴다. 판정 결과는 harness-evaluation.md 에 적는다.
function outcome(r) {
  const s = r.log.flat_status ?? "";
  const v = verdict(r.log.answer_first_line);
  if (r.set === "regression")
    return NO_ANSWER.has(s) && v === "예" ? ["속는다", `${s}+예`] : null;
  const fail = upstreamFail(r);
  if (fail === "오류") return ["오류 표면화", "isError 가드"];
  if (fail === "라우팅" && !NO_ANSWER.has(s)) {
    const routed = r.log.routed_to ?? [];
    const sup = r.expected.routing.every((t) => routed.includes(t));
    if (sup)
      return v === "예" ? ["중복·토큰 낭비", "초집합 병렬+예"]
        : v === "아니오" ? ["정직한 거절/부분", "초집합 병렬+아니오"]
        : ["사람 판정 필요", "초집합 병렬+판정 불가"];
    // 부분 겹침 — 기대 도구 중 일부가 병합에 살아 있으면 맞는 내용이 나갔을 수
    // 있다 (#5 와 같은 무늬). 속는다는 겹침 0 + `예` 에서만 자동 확정한다.
    const inter = r.expected.routing.some((t) => routed.includes(t));
    if (v === "예")
      return inter ? ["사람 판정 필요", "부분 겹침 병렬+예"] : ["속는다", "오답 도구 ok+예"];
    return ["사람 판정 필요", `${inter ? "부분 겹침 병렬" : "오답 도구 ok"}+${v ?? "판정 불가"}`];
  }
  if (fail)  // no_result, 혹은 라우팅 불일치가 답 없는 상태로 귀결된 행
    return v === "예" ? ["속는다", `${s}+예`]
      : v === "아니오" ? ["정직한 거절/부분", s]
      : ["사람 판정 필요", `${s}+판정 불가`];
  const want = label(r.expected.response);
  if (v === want) return null;                       // 상류 건전 + 라벨 일치 — 실패가 아니다
  if (v === "예") return ["속는다", `${s}+예(기대 아니오)`];
  if (v === "아니오") return ["정직한 거절/부분", `${s}+아니오(기대 예)`];
  return ["사람 판정 필요", "첫 줄 형식 불일치"];
}

const inv = [];
for (const r of rows) {
  const o = outcome(r);
  if (o) inv.push([r.id, ...o]);
}
// 0건 범주도 항상 찍는다 — D17 강제 한 줄("속는다를 늘리는 변경은 기각")의
// 관측 대상이 속는다 줄이라, 생략하면 실행마다 감시 대상이 안 보인다.
const SEVERITY = ["속는다", "오류 표면화", "정직한 거절/부분", "중복·토큰 낭비"];
const manual = inv.filter((x) => x[1] === "사람 판정 필요");
const autoCls = inv.filter((x) => x[1] !== "사람 판정 필요");
const detail = (rs) => (rs.length ? "   " + rs.map(([id, , sig]) => `${id}(${sig})`).join(" ") : "");
console.log(`유저-결과 내역 — 실패 ${inv.length}건 (자동 ${autoCls.length} · 사람 판정 ${manual.length})`);
for (const cat of SEVERITY) {
  const rs = autoCls.filter((x) => x[1] === cat);
  console.log(`  ${cat} ${rs.length}${detail(rs)}`);
}
console.log(`  ── 사람 판정 필요 ${manual.length}${detail(manual)}`);
console.log(`  회귀 30문항은 기대 라벨이 없어 환각 위반만 잡힌다 (D7 · #18 범위)`);

// 호출 축은 설계 불변식이므로 깨지면 실패다. 나머지 둘은 측정치다 (문서에 적는 수치).
process.exit(callOk === rows.length ? 0 : 1);
