/**
 * 답변 규약 픽스처를 출하 경로에서 뜬다 (#21).
 *
 *   node scripts/dump-fixtures.mjs harness/tests/answer-protocol-dev.json [...]
 *   node scripts/dump-fixtures.mjs --check harness/tests/answer-protocol-dev.json [...]
 *
 * 에이전트가 실제로 받는 것은 도구 반환이 아니라 `ask` 봉투를 `flatten` 으로 편
 * 결과다 (D15) — 그것이 `tool_result` 가 된다. 손으로 쓴 봉투는 반환 형태가
 * 바뀌어도 조용히 갈라진다: 실제로 종전 8문항 중 5개가 어느 구현도 내지 않는
 * 모양이었다 (`near_names`, `source: "documents"`, `out_of_data_range` …).
 *
 * **저작 필드(`q`·`expected`·`required_regex`·`forbidden_regex`)는 보존하고
 * 파생 필드(`tool`·`tool_result`)만 갱신한다.**
 *
 * `--check` 는 결정적 문항만 다시 떠서 파일과 다르면 실패한다 — 대조 덤프의
 * `DETERMINISTIC` 과 같은 경계다: `nl2sql` 은 생성 SQL 이 실행마다 흔들려
 * 캡처 시점에 동결하고, 여기서 다시 뜨지 않는다.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { pool } from "../dist/db.js";
import { ask } from "../dist/gateway.js";
import { flatten } from "../dist/agent/context.js";

// `null` 은 도구를 안 태운 거절(R1) — 라우터 판정뿐이라 결정적이다.
const DETERMINISTIC = new Set(["vector_search", "knowledge_graph", null]);

const args = process.argv.slice(2);
const check = args[0] === "--check";
const files = check ? args.slice(1) : args;
if (!files.length) {
  console.error("사용법: node scripts/dump-fixtures.mjs [--check] <테스트 파일...>");
  process.exit(2);
}

/** 출하 경로 그대로 — `ask`(선별 포함) → `flatten`. 사본을 두지 않는다. */
async function capture(question) {
  const env = await ask(question);
  const { flat } = flatten(env);
  return { tool: env.routed_to[0] ?? null, flat };
}

const deepEq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

let drift = 0;
for (const file of files) {
  const items = JSON.parse(readFileSync(file, "utf8"));
  const out = [];
  for (const it of items) {
    if (check) {
      if (!DETERMINISTIC.has(it.tool ?? null) || !("tool_result" in it)) continue;
      const { tool, flat } = await capture(it.q);
      if (tool !== (it.tool ?? null) || !deepEq(flat, it.tool_result)) {
        drift += 1;
        console.error(`갈라짐 ${it.id} (${file})`);
        console.error(`  파일: ${JSON.stringify({ tool: it.tool ?? null, tool_result: it.tool_result })}`);
        console.error(`  실측: ${JSON.stringify({ tool, tool_result: flat })}`);
      }
      continue;
    }
    const { tool, flat } = await capture(it.q);
    if (flat.status === "parallel_merge") {
      // 이 세트는 단일 도구 봉투를 재는 세트다 — 병렬로 흘러간 문항은 저작을 고쳐야 한다.
      console.error(`경고 ${it.id}: parallel_merge 로 흘러갔다 — 문항을 다시 써라`);
    }
    const next = { id: it.id, q: it.q, tool, tool_result: flat, expected: it.expected };
    if (it.required_regex) next.required_regex = it.required_regex;
    if (it.forbidden_regex) next.forbidden_regex = it.forbidden_regex;
    out.push(next);
  }
  if (!check) {
    writeFileSync(file, JSON.stringify(out, null, 1) + "\n");
    console.error(`갱신 ${file} — ${out.length}문항`);
  }
}
await pool.end();
if (check) {
  console.error(drift ? `표류 ${drift}건` : "표류 없음");
  process.exit(drift ? 1 : 0);
}
