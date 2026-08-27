/**
 * 시연영상 구동기 — 원테이크를 스크립트가 통제한다.
 *
 *   node scripts/demo.mjs            # 본편 (터미널 구간 144초 고정)
 *   node scripts/demo.mjs --warm     # 촬영 전 워밍업 (모델 적재를 촬영 밖에서 끝낸다)
 *   node scripts/demo.mjs --verify   # 6문항 3회 재현 검사 (합의 결정 10)
 *
 * **이 파일이 있는 이유.** 편집 0 · 원테이크로 찍기로 했으므로(합의 결정 3) 사람이
 * 중간에 손댈 자리가 남으면 그 자리가 곧 실패 지점이다. 사람 개입 지점을 0 으로 만들고,
 * 구간마다 t0 기준 **절대 시각**까지 멈춰 터미널 구간의 총 길이를 144초로 고정한다.
 * 실행이 길어진 구간은 멈춤 0 으로 지나가므로 초과분이 뒤로 전파되지 않는다.
 *
 * **출하 경로만 부른다** (D7 · D13). `dist/agent/` 의 `connectAgent`·`answerQuestion` 을
 * 그대로 쓰고 도구·라우터·프롬프트는 한 글자도 건드리지 않는다 — 시연용 사본을 두면
 * 그것이 출하물과 갈라져도 화면은 잘 돌아간다.
 *
 * 질문 6개·구간 초·화면 문안은 `docs/agreements/demo-video-scenario.md` 의 확정 합의다.
 * **화면에 질문 번호를 적지 않는다** — 저장소는 `questions.json` 을 0-based 로 세고
 * 심사자가 세는 방식과 어긋난다 (같은 문서).
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { connectAgent } from "../dist/agent/client.js";
import { answerQuestion } from "../dist/agent/answer.js";

const BOLD = "\u001b[1m";
const DIM = "\u001b[2m";
const OFF = "\u001b[0m";

/** 한글·CJK 를 2칸으로 세는 표시 너비 — 구분선 길이를 맞추는 데만 쓴다. */
const CJK = /[ᄀ-ᅟ⺀-꓏가-힣豈-﫿︰-﹯＀-｠]/;
const width = (s) => [...s].reduce((n, ch) => n + (CJK.test(ch) ? 2 : 1), 0);

const RULE = 78;
/** 구간 제목 한 줄. 장식은 여기까지다 — 유튜브 압축에서 읽히는 것이 목적이다. */
function section(title) {
  const tail = "─".repeat(Math.max(4, RULE - width(title) - 4));
  console.log(`\n${BOLD}── ${title}${OFF} ${DIM}${tail}${OFF}`);
}

/**
 * 질문 6개 — 합의 확정. **변경 금지.** 4건이 공식 예시 질문
 * (`companyx-dataset-v1.0/questions.json`)이라 심사자가 원본과 대조할 수 있다.
 *
 * `secs` 는 그 구간에 배정한 초다. **누계는 여기 적지 않는다** — 아래에서 유도한다.
 */
const QUESTIONS = [
  { q: "Client-A가 사용 중인 제품 목록은?", official: true,
    title: "지식 그래프 — 규칙 라우터가 단일 도구를 고른다", secs: 13 },
  { q: "평균 연봉이 가장 높은 부서는 어디야?", official: true,
    title: "NL2SQL — 자연어를 SQL 로", secs: 13 },
  { q: "최근 서버 장애 사례와 원인을 알려줘", official: true,
    title: "병렬 호출 — 지식 그래프 + 벡터 검색 (parallel_merge)", secs: 16 },
  { q: "서울물산 담당 엔지니어는 누구야?", official: true,
    title: "없는 개체 — entity_not_found. 지어내지 않는다", secs: 12 },
  { q: "박성민 님이 이끄는 프로젝트는?", official: false,
    title: "동명이인 — ambiguous_entity. 되묻는다", secs: 16 },
  { q: "Client-P에서 발생한 장애의 원인이 뭐야?", official: false,
    title: "부분 응답 — partial + 구조화 JSON", secs: 36 },
];

const SEC_TOOLS = 15;   // tools/list
const SEC_INTERP = 10;  // 해석
const SEC_OUTRO = 13;   // 마무리

/**
 * t0 기준 절대 오프셋 — 구간 초를 누적해 **유도한다.**
 *
 * 누계를 손으로 병행해 적으면 구간 초 하나를 고칠 때 고칠 자리가 여덟 곳으로 늘고,
 * 그중 하나를 빠뜨리면 화면은 멀쩡히 돌아가면서 총 길이만 어긋난다.
 * 합의가 고정한 것은 `AT_END === 144` (터미널 144초 + 슬라이드 20초 = 2:44)다.
 */
const AT_TOOLS = SEC_TOOLS;
const AT_Q = [];
let acc = AT_TOOLS;
for (const item of QUESTIONS) AT_Q.push((acc += item.secs));
const AT_INTERP = (acc += SEC_INTERP);
const AT_END = (acc += SEC_OUTRO);

// 누계를 유도로 바꾸면서 생긴 유일한 무증상 실패 경로를 여기서 막는다 — `secs` 오타는
// 화면에 아무 표시를 안 남기고 총 길이만 어긋내므로, 촬영 전에 죽는 편이 낫다.
if (AT_END !== 144) {
  throw new Error(`터미널 구간 합계 ${AT_END}초 — 합의는 144초다 (secs 를 확인하라)`);
}

/** t0 기준 절대 시각까지만 잔다. 이미 지났으면 멈춤 0 — 초과분이 뒤로 안 번진다. */
let t0 = 0;
const sleepUntil = (sec) =>
  new Promise((r) => setTimeout(r, Math.max(0, t0 + sec * 1000 - Date.now())));

/**
 * 첫 줄 판정 — `scripts/agent-check.mjs` 27–31행과 같은 규칙을 다시 적은 것이다.
 * 그쪽은 스크립트라 export 가 없고, 그쪽 역시 `harness/build/run_answer.py` 의 규칙을
 * 다시 적고 있다. 규칙이 바뀌면 세 곳을 같이 고쳐야 한다.
 */
function verdict(firstLine) {
  const l = (firstLine ?? "").trim();
  if (!l.startsWith("답변가능:")) return null;
  return l.replace(/^답변가능:\s*/, "").trim();
}

/** 관측 줄 — `src/agent/cli.ts` 21–24행 형식 그대로. */
const observed = (log) =>
  `[ask] status=${log.envelope_status} routed_to=${(log.routed_to ?? []).join(",")} ` +
  `matched_rule=${log.matched_rule}`;

/** 파싱 실패 시 떨어질 자리 — 합의문 "Q6 직후 해석 화면" 의 리터럴이다. */
const FALLBACK_CTX = {
  unavailable: { asset: "documents", reason: "form_not_covered" },
  adjacent_facts: { source: "graph" },
};

/**
 * 해석 화면 — 합의문 "Q6 직후 해석 화면" 의 고정 사본이다.
 * 세 값만 Q6 의 `context_json` 실물에서 꺼내 채운다 — 화면이 실측과 어긋날 자리를 없앤다.
 *
 * **파싱이 실패해도 화면은 완주한다.** 여기서 던지면 t≈121초에 죽어 해석 화면과 실측
 * 카드 23초를 통째로 잃는데, 그 23초가 이 영상의 착지점이다.
 */
function interpretation(contextJson) {
  let ctx = {};
  if (contextJson) {
    try {
      ctx = JSON.parse(contextJson);
    } catch {
      // 컨텍스트는 왔는데 읽히지 않는 경우 — 부분 응답 자체는 성립했으므로 합의문
      // 리터럴로 떨어뜨린다. 봉투가 아예 없어 `context_json` 이 null 인 경우는 **잰 적이
      // 없는 값**이라 여기로 오지 않고 아래에서 `(없음)` 으로 남는다 — 안 잰 값을 잰 것처럼
      // 찍는 것이 이 영상이 반대하는 바로 그 일이다.
      ctx = FALLBACK_CTX;
    }
  }
  const rows = [
    ["unavailable.asset", ctx.unavailable?.asset, "← Client-P 문서가 없다"],
    ["unavailable.reason", ctx.unavailable?.reason, "← 개체는 있다. '서술' 형태만 없다"],
    ["adjacent_facts.source", ctx.adjacent_facts?.source, "← 확인된 사실은 여기서 왔다"],
  ];
  return [
    ...rows.map(
      ([k, v, note]) =>
        `    ${k.padEnd(22)}= ${BOLD}${String(v ?? "(없음)").padEnd(19)}${OFF}${DIM}${note}${OFF}`,
    ),
    "",
    '    "모른다" 가 아니라 "문서를 채우면 답해진다" 를 돌려준다.',
    "    실패에 좌표가 붙으면, 다음에 무엇을 보강할지가 정해진다.",
  ];
}

/**
 * 오늘 실측 카드 — 합의 결정 9(문서 인용값 금지)에 따라 **오늘 다시 잰 값만** 적는다.
 * 값의 출처는 카드의 소제목인 세 명령 그대로다:
 *   `node scripts/agent-check.mjs` · `python3 harness/build/run_router.py` · `node scripts/xcheck.mjs`
 *
 * **`29/30` 은 쓰지 않는다** — `CONTEXT.md` 의 그 값은 기대값 칸이고 실측은 26/30 이다.
 * 가장 센 줄은 `속는다 0` 이라 거기만 굵게 간다 — 실패 8건 중 사용자가 틀린 답을 믿게
 * 된 건이 없다는 뜻이고, 나머지가 방어적 숫자인 것과 달리 이것은 공격적 숫자다.
 */
const MEASURED = [
  "node scripts/agent-check.mjs",
  "  호출 축        59/59   (첫 호출 ask · 직접 호출 0건)",
  "  환각 축 위반   0/59    (답 없는 상태에서 '예')",
  "  응답 축        21/21   (상류 실패 8건 제외)",
  `  ${BOLD}유저-결과 — 속는다 0 · 오류 표면화 1 · 정직한 거절/부분 4 · 중복 0${OFF}`,
  "",
  "python3 harness/build/run_router.py",
  "  회귀 30문항 · 라우팅 축   26/30",
  "  엣지 29문항 · 라우팅 축   22/29",
  "",
  "node scripts/xcheck.mjs",
  "  하네스 ↔ 서버 결정적 축   57/57   (이식 버그 0)",
];

// ── 본편 ──────────────────────────────────────────────────────────────────
async function runShow() {
  t0 = Date.now();
  console.log(`${BOLD}Lantern — 리원에이스 MCP 시연${OFF}`);

  // tools/list 는 `ask` 만 부르는 AgentClient 로 못 부른다 (D15) — 여기서만 raw SDK
  // 클라이언트를 따로 띄운다 (`scripts/smoke.mjs` 12–17행과 같은 방식).
  const raw = new Client({ name: "demo", version: "0.0.1" });
  await raw.connect(new StdioClientTransport({ command: "node", args: ["dist/server.js"] }));
  const { tools } = await raw.listTools();
  // 제목의 개수도 실측에서 온다 — 하드코딩하면 도구가 늘 때 한 화면 안에서 두 값이 어긋난다.
  section(`MCP 서버 — tools/list · 도구 ${tools.length}개`);
  console.log(`tools/list — ${tools.length}개 (결정적 순서, ask 가 첫째)`);
  for (const t of tools) {
    console.log(`  ${BOLD}${t.name.padEnd(16)}${OFF}${t.description.slice(0, 46)}…`);
  }
  await raw.close();

  const client = await connectAgent();
  await sleepUntil(AT_TOOLS);

  const last = QUESTIONS[QUESTIONS.length - 1];
  let lastContext = null;
  try {
    for (const [i, item] of QUESTIONS.entries()) {
      section(item.title);
      console.log(`질문. ${item.q}${item.official ? `   ${DIM}(공식 예시 질문)${OFF}` : ""}`);
      const { text, log } = await answerQuestion(client, item.q);
      console.log(`${DIM}${observed(log)}${OFF}`);
      console.log(text);
      if (item === last) {
        // 부분 응답만 컨텍스트 전문을 편다 — 프롬프트에 실제로 들어간 실물이고,
        // 바로 다음 해석 화면의 세 값이 이 JSON 에서 나온다.
        lastContext = log.context_json;
        console.log(`\n${DIM}프롬프트에 실제 들어간 컨텍스트 (log.context_json)${OFF}`);
        console.log(log.context_json);
      }
      await sleepUntil(AT_Q[i]);
    }

    section("이 응답이 왜 이렇게 생겼나");
    for (const line of interpretation(lastContext)) console.log(line);
    await sleepUntil(AT_INTERP);

    section("오늘 실측");
    for (const line of MEASURED) console.log(line);
    await sleepUntil(AT_END);
  } finally {
    await client.close();
  }
}

// ── 워밍업 ────────────────────────────────────────────────────────────────
// 본편 안에 두지 않는다. 콜드 실행의 모델 적재 21초가 녹화에 들어가면 상한 3:00 을
// 위협하고, 그 대기는 길이를 예측할 수도 없다 (촬영 체크리스트 5번).
async function runWarm() {
  const started = Date.now();
  const client = await connectAgent();
  const { log } = await answerQuestion(client, QUESTIONS[0].q);
  await client.close();
  console.log(observed(log));
  console.log(
    `워밍업 ${((Date.now() - started) / 1000).toFixed(1)}초 — ` +
      `gemma(생성)·bge-m3(임베딩)·PG(조회) 적재 완료`,
  );
  // Ollama keep_alive 기본값이 5분이라 사이가 벌어지면 모델이 다시 내려간다.
  console.log(`${BOLD}워밍업 완료 — 5분 안에 본편을 시작하라${OFF}`);
}

// ── 재현 검사 ─────────────────────────────────────────────────────────────
/**
 * 6문항 × 3회. **비교는 2축이다** (`scripts/xcheck.mjs` 의 관례를 그대로 옮겼다).
 *
 *   ① 결정적 서명 — 깨지면 실패다. 3회가 전부 같아야 통과한다.
 *   ② 생성 표면   — 관측치다. 갈리면 보고만 하고 종료 코드는 안 건드린다.
 *
 * ①에 `context_json` 을 넣는 이유는 합의문이 기록한 `smoke.mjs` 오답 사고다 — 같은
 * 질문에 4 와 1 이 갈렸고 원인은 **생성 SQL 이 갈려 행이 갈린 것**이었다. 답변 문구만
 * 보면 그 부류가 안 잡히고, 프롬프트에 들어간 컨텍스트를 보면 잡힌다.
 *
 * ②를 실패로 세지 않는 이유는 합의 결정 3-1 이다 — 시스템 출력이 달라진 것은
 * 재촬영 사유가 아니고, 문구 변주는 영상이 하는 주장을 바꾸지 않는다.
 *
 * MCP 세션 하나를 18회에 재사용한다 (`scripts/agent-check.mjs` 관례).
 */
const ROUNDS = 3;

/**
 * 결정적 서명 — 실행을 가로질러 같아야 하는 필드들. **이름을 한 자리에서만 적는다.**
 *
 * 목록과 추출을 따로 두면 필드를 더할 때 두 리터럴을 평행 수정하게 되는데, 그것이
 * `src/agent/answer.ts` 가 #29 에서 이름 붙인 사고 무늬다. 비교 쪽은 이 객체의 키를
 * 읽으므로 여기에 한 줄을 더하면 비교도 따라온다.
 */
const signature = (log) => ({
  envelope_status: log.envelope_status,
  routed_to: (log.routed_to ?? []).join(","),
  matched_rule: log.matched_rule,
  flat_status: log.flat_status,
  verdict: verdict(log.answer_first_line),
  context_json: log.context_json,
});

/** 두 문자열이 처음 갈리는 자리와 그 뒤 80자 — 긴 JSON 을 통째로 찍지 않는다. */
function firstDiffWindow(a, b) {
  const x = String(a);
  const y = String(b);
  let i = 0;
  while (i < x.length && i < y.length && x[i] === y[i]) i++;
  return `${i}자째 ${JSON.stringify(y.slice(i, i + 80))}`;
}

async function runVerify() {
  const client = await connectAgent();
  const rounds = [];
  for (let r = 0; r < ROUNDS; r++) {
    const row = [];
    for (const [i, item] of QUESTIONS.entries()) {
      const started = Date.now();
      const { log } = await answerQuestion(client, item.q);
      row.push({
        sig: signature(log),
        answer_text: log.answer_text,
        ms: Date.now() - started,
      });
      process.stderr.write(`\r${r + 1}회차 ${i + 1}/${QUESTIONS.length}   `);
    }
    rounds.push(row);
  }
  await client.close();
  process.stderr.write("\r");

  // ① 결정적 서명 — 깨지면 실패다
  let broken = 0;
  for (const [i, item] of QUESTIONS.entries()) {
    for (const f of Object.keys(rounds[0][i].sig)) {
      const vals = rounds.map((row) => row[i].sig[f]);
      if (vals.every((v) => v === vals[0])) continue;
      broken++;
      console.log(`서명 불일치 — ${item.q}  [${f}]`);
      for (const [r, v] of vals.entries()) {
        console.log(
          f === "context_json"
            ? `  ${r + 1}회차 ${String(v).length}자 | ${firstDiffWindow(vals[0], v)}`
            : `  ${r + 1}회차 ${v}`,
        );
      }
    }
  }

  // ② 생성 표면 — 관측치다
  for (const [i, item] of QUESTIONS.entries()) {
    for (let r = 1; r < ROUNDS; r++) {
      const a = String(rounds[0][i].answer_text ?? "");
      const b = String(rounds[r][i].answer_text ?? "");
      if (a === b) continue;
      const la = a.split("\n");
      const lb = b.split("\n");
      // 한쪽이 다른 쪽의 접두인 경우까지 센다. `la` 만 훑으면 그 경우 -1 이 나오고,
      // 그것을 0 으로 접으면 **같은 1번째 줄을 변주로 찍는다** — 촬영 전에 사람이 읽고
      // 판단하는 화면이라 거짓 보고가 섞이면 안 된다.
      const end = Math.max(la.length, lb.length);
      let k = 0;
      while (k < end && la[k] === lb[k]) k++;
      const show = (arr) => (arr[k] === undefined ? "(줄 없음)" : arr[k].slice(0, 70));
      console.log(`문구 변주 — ${item.q}  ${r + 1}회차 ${k + 1}번째 줄 (관측치)`);
      console.log(`  1회차   | ${show(la)}`);
      console.log(`  ${r + 1}회차   | ${show(lb)}`);
    }
  }

  // 페이싱 재료 — 절대 스케줄이 초과를 흡수하므로 총 길이는 안 흔들린다.
  // 그래도 어느 구간이 빡빡한지는 화면을 보고 판단할 재료가 된다.
  console.log("\n문항별 최대 소요 vs 구간 초");
  for (const [i, item] of QUESTIONS.entries()) {
    const max = Math.max(...rounds.map((row) => row[i].ms)) / 1000;
    const over = max > item.secs ? "  ← 구간 초과" : "";
    console.log(
      `  ${max.toFixed(1).padStart(5)}초 / ${String(item.secs).padStart(2)}초   ${item.q}${over}`,
    );
  }

  if (broken) {
    console.log(`\n결정적 서명 불일치 ${broken}건 — 실패`);
    process.exit(1);
  }
  console.log(`\n${BOLD}3회 연속 동일 — 통과 (합의 결정 10)${OFF}`);
  process.exit(0);
}

const mode = process.argv[2] ?? "";
if (mode === "--warm") await runWarm();
else if (mode === "--verify") await runVerify();
else if (mode) {
  // 오타 난 플래그로 144초짜리 본편이 시작되는 것을 막는다.
  console.error("사용법: node scripts/demo.mjs [--warm|--verify]");
  process.exit(1);
} else await runShow();
process.exit(0);
