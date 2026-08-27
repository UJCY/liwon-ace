/**
 * NL2SQL — 도구 안에서 LLM 이 SQL 을 만들고 실행한다 (D4). SELECT 만 허용한다.
 *
 * 프롬프트는 자산에서 읽는다 (D13). 스키마는 **인라인 주석본**이다 —
 * 값 목록과 단위가 컬럼 옆에 붙어 있어야 한다. 같은 정보를 별도 블록으로 주면
 * 홀드아웃 정확도가 90% 에서 75% 로 떨어진다 (docs/harness-evaluation.md 1절).
 */
import { annotatedSchema, columnRanges, nl2sqlPrompt } from "../assets.js";
import { generate } from "../ollama.js";
import { query } from "../db.js";
import type { GroundingHit, ToolResult } from "./types.js";

const SELECT_ONLY = /^\s*SELECT\b/i;

// ── 접지 검출 (D19) ────────────────────────────────────────────────────────
// **원본은 `harness/build/check_grounding.py` 다.** 여기는 그 이식이고, 두 구현은
// 같은 SQL 에 같은 판정을 내야 한다 (상수·정규식·판정 순서까지 자구 동일). 정의를
// 늘릴 일이 생기면 py 를 고치고 이쪽을 맞춘다 — 판정이 갈리면 하네스 수치가
// 서버에서 재현되지 않는다 (D13).
//
// **동일성은 정상 실행 경로 위의 약속이다.** 문자열 탐색 중 인프라 오류가 나면 갈린다 —
// py 는 `RuntimeError` 만 잡으므로 그 밖(타임아웃 등)은 전파돼 하네스가 죽고, 아래
// `catch` 는 전부 삼켜 `found=[]` → `string` hit → 채택 정책 필터로 소거 → `no_result`
// 로 조용히 흐른다. 인프라가 성한 동안은 같은 판정이고, 갈리는 구간은 여기뿐이다.
//
// 실행 **후, 결과가 빈손일 때만** 돈다. SQL 파서를 쓰지 않는다.

/** dev 실측: 정당한 최댓값 위 질문은 ≤×2, 관측된 최소 오류는 ×27. 10은 그 틈에 선다. */
const OVER_FACTOR = 10;

const NUM_RE =
  /\b(?:(\w+)\.)?(salary|price_monthly|amount|budget)\b\s*(?:>=|<=|<>|!=|=|>|<)\s*(\d+(?:\.\d+)?)/g;
const STR_RE = /(\w+(?:\.\w+)?)\s*(?:=|ILIKE|LIKE)\s*'([^']+)'/gi;
const SKIP_LITERAL = /^\d{4}-\d{2}(-\d{2})?$|^\d{4}-Q\d$|^\d+(\.\d+)?$/;
const ALIAS_RE =
  /\b(?:FROM|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(?!ON\b|WHERE\b|JOIN\b|LEFT\b|RIGHT\b|INNER\b|GROUP\b|ORDER\b)(\w+))?/gi;

/**
 * 컬럼 이름(테이블 없이) → 실측 범위의 합집합 — py `load_ranges`.
 *
 * 동명 컬럼(`contracts.amount` / `sales.amount`)은 합집합을 쓴다. 별칭 해소 없이
 * 보수적으로 판정하기 위해서다 — 단위 실수는 ×1000 이상이라 합집합으로도 갈린다.
 * 자산은 불변이므로 모듈 로드 시 1회 계산한다.
 */
const RANGES: Map<string, [number, number]> = (() => {
  const merged = new Map<string, [number, number]>();
  for (const [key, [lo, hi]] of Object.entries(columnRanges)) {
    const col = key.split(".")[1]!;
    const m = merged.get(col);
    if (!m) merged.set(col, [lo, hi]);
    else merged.set(col, [Math.min(m[0], lo), Math.max(m[1], hi)]);
  }
  return merged;
})();

/** FROM/JOIN 절의 별칭 → 테이블 — py `alias_map`. 최소 해소다: 파서를 만들지 않는다. */
function aliasMap(sql: string): Map<string, string> {
  const out = new Map<string, string>();
  for (const m of sql.matchAll(ALIAS_RE)) {
    const tbl = m[1]!;
    out.set(tbl, tbl);
    if (m[2]) out.set(m[2], tbl);
  }
  return out;
}

/**
 * DB 의 전 텍스트 컬럼 — py `text_columns`. 스키마는 실행 중 안 바뀌므로 1회만 묻는다.
 * 캐시하지 않으면 문자열 갈래 한 번에 컬럼 수만큼 질의가 두 배로 는다.
 */
let txtColsCache: [string, string][] | null = null;
async function textColumns(): Promise<[string, string][]> {
  if (txtColsCache) return txtColsCache;
  const rows = await query<{ table_name: string; column_name: string }>(
    "SELECT table_name, column_name FROM information_schema.columns " +
      "WHERE table_schema='public' AND data_type IN " +
      "('character varying','text','character') ORDER BY 1,2;",
  );
  txtColsCache = rows.map((r) => [r.table_name, r.column_name] as [string, string]);
  return txtColsCache;
}

/**
 * 검출기 원본 hit — `string`(어디에도 없음)까지 세 갈래 전부 낸다.
 * **채택 정책 필터는 호출부에 있다** (D19) — 정의는 py 한 곳에 남기고, 소비자가
 * `string` 을 뺀다. 하네스 `tools.py` 도 같은 자리에서 같은 필터를 건다.
 */
export type RawGroundingHit =
  | GroundingHit
  | { kind: "string"; column: string; literal: string; found_in: string[] };

/** 접지 실패 목록. 비면 통과다 — py `detect` 와 같은 판정 순서·같은 hit 모양. */
export async function detectGrounding(sql: string): Promise<RawGroundingHit[]> {
  const hits: RawGroundingHit[] = [];
  for (const m of sql.matchAll(NUM_RE)) {
    const col = m[2]!;
    const lit = m[3]!;
    const range = RANGES.get(col);
    if (range && Number(lit) >= OVER_FACTOR * range[1]) {
      hits.push({ kind: "number", column: col, literal: lit, observed_range: range });
    }
  }
  const amap = aliasMap(sql);
  const txtCols = await textColumns();
  for (const m of sql.matchAll(STR_RE)) {
    const used = m[1]!;
    const raw = m[2]!;
    const lit = raw.replace(/^%+|%+$/g, "");
    if (!lit || SKIP_LITERAL.test(lit)) continue;
    const opLike = raw.includes("%");
    const found: string[] = [];
    for (const [t, c] of txtCols) {
      // 리터럴은 `[^']+` 라 파라미터 바인딩과 의미가 같다. 식별자는 카탈로그 산출물이다.
      const cond = opLike ? `${c} LIKE $1` : `${c} = $1`;
      try {
        const rows = await query<{ count: string }>(
          `SELECT COUNT(*) FROM ${t} WHERE ${cond};`, [opLike ? `%${lit}%` : lit],
        );
        if (Number(rows[0]!.count)) found.push(`${t}.${c}`);
      } catch {
        // 질의 실패는 무시하고 다음 컬럼으로. py 는 `RuntimeError` 만 잡는 자리라
        // 인프라 오류에서는 갈린다 (위 머리 주석) — 정상 경로에서는 같은 판정이다.
        continue;
      }
    }
    const parts = used.split(".");
    const usedCol = parts[parts.length - 1]!;
    const usedTbl = parts.length === 2 ? amap.get(parts[0]!) : undefined;
    if (!found.length) {
      hits.push({ kind: "string", column: used, literal: lit, found_in: [] });
    } else if (usedTbl && !found.includes(`${usedTbl}.${usedCol}`)) {
      hits.push({ kind: "string_misplaced", column: `${usedTbl}.${usedCol}`,
                  literal: lit, found_in: found });
    } else if (!usedTbl && !found.some((f) => f.endsWith(`.${usedCol}`))) {
      hits.push({ kind: "string_misplaced", column: usedCol, literal: lit, found_in: found });
    }
  }
  return hits;
}

/**
 * 접지 검사를 돌릴 **빈손**인가 — 0행, 또는 집계 0/NULL 한 행 (D19).
 *
 * 격자 `zero_result` 정의 그대로다. 적발 22/22 · 오인 0 이 정확히 이 정의 위에서
 * 검증됐으므로 **넓히지 않는다**. pg 는 COUNT 를 문자열 `"0"` 으로 준다 —
 * 하네스 CSV 의 `""` 가 여기서는 `null` 이다.
 */
function isEmptyHanded(rows: Record<string, unknown>[]): boolean {
  if (!rows.length) return true;
  if (rows.length !== 1) return false;
  const vals = Object.values(rows[0]!);
  if (vals.length !== 1) return false;
  const v = vals[0];
  return v === null || v === "0" || v === 0;
}

export function extractSql(raw: string): string {
  const fenced = /```(?:sql)?\s*([\s\S]*?)```/.exec(raw);
  const body = fenced?.[1] ?? raw;
  const m = /(SELECT\b[\s\S]*?)(?:;|$)/i.exec(body);
  return (m?.[1] ?? body).trim();
}

export async function nl2sql(question: string): Promise<ToolResult> {
  const prompt = nl2sqlPrompt
    .replace("{{SCHEMA}}", annotatedSchema)
    .replace("{{QUESTION}}", question);

  const raw = await generate(prompt);
  if (!raw.trim()) {
    // 빈 응답은 T1 이 아니다 — think 가 켜져 num_predict 를 추론이 소진한 것이다.
    return { status: "error", reason: "empty_generation_check_think_option" };
  }
  const sql = extractSql(raw);
  if (!SELECT_ONLY.test(sql)) {
    return { status: "error", reason: "not_select" };            // T2 — 무조건 차단
  }
  let rows: Record<string, unknown>[];
  try {
    rows = await query(sql);
  } catch (e) {
    return { status: "error", reason: (e as Error).message.slice(0, 120) };  // T1
  }
  // 빈손이면 리터럴이 데이터에 접지됐는지 본다 — 0행의 이중 의미를 가른다 (D19).
  // **채택 정책 필터**: 숫자 ×10 과 문자열 오배치만. `string`(어디에도 없음)은
  // "값이 진짜 없는 정직한 질문"과 못 갈라서 뺀다 — 하네스 `tools.py` 와 같은 자리다.
  if (isEmptyHanded(rows)) {
    const hits = (await detectGrounding(sql))
      .filter((h): h is GroundingHit => h.kind !== "string");
    if (hits.length) return { status: "ungrounded", sql, hits };  // T9
  }
  // 집계 0 한 행 + 미적발은 여기 안 걸리고 `ok` 로 남는다 — "0건"이 정답인 질문이다.
  if (!rows.length) return { status: "no_result", asset: "tables", sql };  // T3 — 실패가 아니다
  return { status: "ok", data: rows, sql };
}
