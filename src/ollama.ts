/** Ollama 호출. 외부 API 는 쓰지 않는다 (과제 제약). */
import { model } from "./assets.js";

const HOST = process.env["OLLAMA_HOST"] ?? "http://localhost:11434";

export async function embed(text: string): Promise<number[]> {
  const res = await fetch(`${HOST}/api/embed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: model.embedding.name, input: text }),
  });
  if (!res.ok) throw new Error(`embed 실패: ${res.status}`);
  const json = (await res.json()) as { embeddings: number[][] };
  const v = json.embeddings[0];
  if (!v) throw new Error("embed 응답이 비었다");
  return v;
}

export async function generate(prompt: string): Promise<string> {
  const body: Record<string, unknown> = {
    model: model.llm.name,
    prompt,
    stream: false,
    options: model.llm.options,
  };
  // think 를 끄지 않으면 숨은 추론 토큰이 num_predict 를 소진해 **빈 문자열**이 온다.
  // 그 빈 응답은 T1(무효 SQL 생성)으로 오분류된다 (docs/edge-cases.md T1).
  if (!model.llm.think) body["think"] = false;
  const res = await fetch(`${HOST}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`generate 실패: ${res.status}`);
  return ((await res.json()) as { response: string }).response;
}
