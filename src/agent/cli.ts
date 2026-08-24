#!/usr/bin/env node
/**
 * 에이전트 진입점 — 질문 한 문장을 넣으면 최종 답변이 나온다 (#16 AC).
 *
 *   npm run agent -- "Client-A가 사용 중인 제품 목록은?"
 *
 * 답변은 stdout, 라우팅 관측 줄은 stderr 로 나눈다 — 답변만 파이프로 받을 수 있어야 한다.
 */
import { connectAgent } from "./client.js";
import { answerQuestion } from "./answer.js";

const question = process.argv[2];
if (!question) {
  console.error('사용법: npm run agent -- "<질문 한 문장>"');
  process.exit(1);
}

const client = await connectAgent();
try {
  const { text, log } = await answerQuestion(client, question);
  console.error(
    `[ask] status=${log.envelope_status} routed_to=${(log.routed_to ?? []).join(",")} ` +
      `matched_rule=${log.matched_rule}`,
  );
  console.log(text);
} finally {
  await client.close();
}
process.exit(0);
