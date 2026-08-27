/**
 * 하네스 ↔ 서버 대조 — 덤프 둘을 뜨고 문항별로 비교한다.
 *
 *   node scripts/xcheck.mjs
 *
 * **이 파일이 있는 이유.** 종전에는 비교를 각자 heredoc 으로 했고, 그래서
 * 같은 "59/59" 를 서로 다른 방법으로 냈다. `docs/harness-evaluation.md` 가
 * 기록한 사고 — *사본이 출하물과 갈라졌는데 대조는 계속 59/59 를 냈다* — 의
 * 재발 조건이 정확히 그것이다. 재는 방법을 저장소에 둔다.
 *
 * **대조는 하나의 숫자가 아니다.** 병렬 합성을 대조에 넣은 뒤(2026-08-21)
 * 일부 문항은 `nl2sql` 이 `ok` 를 내느냐가 판정을 가른다 — 거기서는 LLM 생성이
 * 판정에 물린다. 그 문항의 불일치는 **이식 버그가 아니다.** 그래서 축을 나눈다.
 *
 *   결정적 축 — 깨지면 실패다 (이식 버그를 잡는 축)
 *   LLM 결합 축 — 관측치다. 실측 간헐 실패율 8회 중 1회
 *
 * 결합 문항은 **하드코딩하지 않는다.** 짝은 덤프의 `pair` 로 비교한다 — 덤프 자체가
 * 출하 경로(`compose` / `run_e2e.answer`)가 실제로 고른 짝이라, 대조용으로 후보 선정을
 * 다시 부르는 것보다 한 겹 가깝다.
 *
 * **결합 축에도 결정적 부분필드는 엄격히 본다 (#12).** 짝 선택은 정규식과 어휘 목록으로만
 * 정해져 실행 노이즈가 낄 자리가 없다. 그래서 결합 문항이라도
 * `{twoRequests, ranked, pair, pairSource}` 가 갈리면 **실패**다 — 관측치로 남는 것은
 * `state`·`tools`·`payload` 뿐이다.
 *
 * **도구 반환 payload 도 비교한다 (#25).** 종전에는 `tools`·`state`·`twoRequests`·
 * `ranked` 만 봤고, 그래서 **반환 필드를 한쪽 구현에만 더해도 대조가 통과했다** —
 * 위에 적은 사고와 같은 재발 조건이다. 결정적인 두 도구(`vector_search` ·
 * `knowledge_graph`)만 넣는다. 어느 도구를 넣을지는 양쪽 덤프가 정한다.
 */
import { execFileSync } from "node:child_process";

const run = (cmd, args) =>
  JSON.parse(execFileSync(cmd, args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 }));

console.error("하네스 덤프…");
const harness = run("python3", ["harness/build/dump_harness.py"]);
console.error("서버 덤프…");
const server = run("node", ["scripts/dump-server.mjs"]);

/** `nl2sql` 의 ok 여부가 판정을 가르는 문항인가 — 병렬 분기가 그것을 태웠는가. */
const llmCoupled = (d) => d.twoRequests === true && (d.pair ?? []).includes("nl2sql");

/** 결합 문항에서도 결정적인 부분 — 실행 결과가 물리지 않는 필드다. */
const DETERMINISTIC_FIELDS = ["twoRequests", "ranked", "pair", "pairSource"];
const pick = (d) => d && Object.fromEntries(DETERMINISTIC_FIELDS.map((k) => [k, d[k]]));

/**
 * 키 순서에 무관한 구조 비교 — 정렬 직렬화로 정규화한다.
 * `JSON.stringify` 직접 비교는 두 덤프의 키 순서가 우연히 같아야만 성립하고,
 * 어느 쪽의 무해한 키 재배열도 가짜 불일치로 읽는다 (재배열 실측으로 확인).
 */
const canon = (v) => Array.isArray(v) ? v.map(canon)
  : v !== null && typeof v === "object"
    ? Object.fromEntries(Object.keys(v).sort().map((k) => [k, canon(v[k])]))
    : v;
const same = (a, b) => JSON.stringify(canon(a)) === JSON.stringify(canon(b));

const deterministic = [];
const coupled = [];
for (const sect of ["edge", "regression"]) {
  for (const [id, h] of Object.entries(harness[sect])) {
    const s = server[sect][id];
    (llmCoupled(h) || (s && llmCoupled(s)) ? coupled : deterministic).push({ id: `${sect}:${id}`, h, s });
  }
}
const mismatches = (rows) => rows.filter((r) => !same(r.h, r.s));
const detBad = mismatches(deterministic);
const coupledBad = mismatches(coupled);
const coupledFieldBad = coupled.filter((r) => !same(pick(r.h), pick(r.s)));

console.log(`대조 — 하네스 ↔ 서버  (총 ${deterministic.length + coupled.length}문항)`);
console.log(`  결정적 축   ${deterministic.length - detBad.length}/${deterministic.length}   ← 이식 버그를 잡는 축. 깨지면 실패다`);
console.log(`  LLM 결합 축 ${coupled.length - coupledBad.length}/${coupled.length}   ← nl2sql 의 ok 여부가 판정을 가른다. 관측치다`);
console.log(`              ${coupled.map((c) => c.id).join(" · ")}`);
console.log(`  결합 축 결정적 부분필드 ${coupled.length - coupledFieldBad.length}/${coupled.length}   ← ${DETERMINISTIC_FIELDS.join("·")}. 깨지면 실패다`);
for (const [label, rows] of [["결정적", detBad], ["LLM 결합", coupledBad]]) {
  for (const r of rows) {
    console.log(`  [${label}] ${r.id}`);
    console.log(`      하네스 ${JSON.stringify(r.h)}`);
    console.log(`      서버   ${JSON.stringify(r.s)}`);
  }
}
for (const r of coupledFieldBad) {
  console.log(`  [결합-결정적부분] ${r.id}`);
  console.log(`      하네스 ${JSON.stringify(pick(r.h))}`);
  console.log(`      서버   ${JSON.stringify(pick(r.s))}`);
}
process.exit(detBad.length + coupledFieldBad.length ? 1 : 0);
