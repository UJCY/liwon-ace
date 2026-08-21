/** Ollama 호출. 외부 API 는 쓰지 않는다 (과제 제약). */
import { model } from "./assets.js";

const HOST = process.env["OLLAMA_HOST"] ?? "http://localhost:11434";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/**
 * 일시 오류에 재시도한다. Ollama 가 400 을 한 번 내면 그 요청만 죽는 것이 아니라
 * 그 요청에 걸린 도구 호출 전체가 죽는다 — 측정 도중 두 번 겪었다.
 *
 * **T1 재시도 정책과 무관하다.** 저것은 생성 품질(외부 피드백 없는 자기교정 금지)의
 * 문제이고, 이것은 전송 실패다. 같은 입력을 다시 보내는 것이 맞다.
 */
export async function embed(text: string, attempts = 3): Promise<number[]> {
  for (let i = 0; i < attempts; i++) {
    try {
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
    } catch (e) {
      if (i === attempts - 1) throw e;
      await sleep(2000 * (i + 1));
    }
  }
  throw new Error("unreachable");
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
