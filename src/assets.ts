/**
 * 하네스 자산 로더.
 *
 * 프롬프트·시그니처·게이트 어휘·모델 옵션은 `harness/assets/` 한 곳에 있고
 * 코드는 그것을 **읽기만 한다** (docs/design.md D13). 측정 러너와 서버가
 * 같은 자산을 읽으므로, 하네스에서 잰 수치가 서버에서도 그대로 나온다.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ASSETS = join(HERE, "..", "harness", "assets");

const read = (...p: string[]) => readFileSync(join(ASSETS, ...p), "utf8");
const readJson = <T>(...p: string[]) => JSON.parse(read(...p)) as T;

export interface ModelConfig {
  llm: { name: string; options: Record<string, number>; think: boolean };
  embedding: { name: string; dim: number };
  router: { reject_threshold: number };
}

export const model = readJson<ModelConfig>("model.json");

/** 도구 3종의 능력 서술. 밑줄로 시작하는 키는 메타데이터이므로 건너뛴다. */
export const toolSignatures: Record<string, string> = Object.fromEntries(
  Object.entries(readJson<Record<string, string>>("tool-signatures.json"))
    .filter(([k]) => !k.startsWith("_")),
);

const gate = readJson<{ tables: Record<string, string[]>; column_values_ko: string[] }>(
  "surface-gate.json",
);
/** 거절 게이트용 어휘. "어느 식별자에 걸렸는가"는 보지 않고 "걸렸는가"만 본다. */
export const gateWords: string[] = [
  ...Object.values(gate.tables).flat(),
  ...gate.column_values_ko,
];

const patterns = readJson<{ company_suffix: string[]; id_prefixes: string[] }>(
  "entity-patterns.json",
);
/** 개체 한정어. 라우터와 knowledge_graph 가 **같은 목록**을 쓴다. */
export const entityPattern = new RegExp(
  `(${patterns.id_prefixes.join("|")})[-_ ]?[A-Za-z0-9]+` +
    `|[가-힣]{2,5}(?:${patterns.company_suffix.join("|")})`,
);
export const companySuffix = patterns.company_suffix;
export const idPrefixes = patterns.id_prefixes;

/** 제품 × 기술주제 격자 (#13). `vector_search` 의 T4-form 판정과 하네스가 **같은 파일**을 읽는다. */
export const docTopics = readJson<{ topics: string[]; coverage: Record<string, string[]> }>(
  "doc-topics.json",
);

export const annotatedSchema = read("schema-annotated.sql");

/** 프롬프트 실물은 마크다운의 첫 코드블록이다. 코드에 두 번째 사본을 두지 않는다. */
function promptTemplate(file: string): string {
  const md = read("prompts", file);
  const m = /```\n([\s\S]*?)```/.exec(md);
  if (!m?.[1]) throw new Error(`${file} 에서 프롬프트 코드블록을 찾지 못했다`);
  return m[1];
}

export const nl2sqlPrompt = promptTemplate("nl2sql.md");
export const agentAnswerPrompt = promptTemplate("agent-answer.md");
