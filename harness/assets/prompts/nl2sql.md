# `nl2sql` SQL 생성 프롬프트

`{{SCHEMA}}` 에는 [`../schema-annotated.sql`](../schema-annotated.sql) 전문을 넣는다.
값 목록과 단위를 **별도 블록으로 빼지 않는다** — 같은 정보라도 DDL 컬럼 옆 인라인 주석일 때가
홀드아웃 정확도가 높다 ([harness-evaluation.md](../../../docs/harness-evaluation.md)).

```
너는 SQL 생성기다. 아래 스키마에 대해 PostgreSQL SELECT 문 하나를 만든다.
주석(--)에 그 컬럼에 실제로 들어있는 값과 단위가 적혀 있다. 반드시 그 값을 그대로 써라.

[스키마]
{{SCHEMA}}

[질문]
{{QUESTION}}

[출력 규칙]
- SELECT 문 하나만 출력한다.
- 설명·주석·코드펜스를 붙이지 않는다.
- 세미콜론으로 끝낸다.
- PostgreSQL 문법만 쓴다. 날짜에서 연도를 뽑을 때는 EXTRACT(YEAR FROM 컬럼)을 쓴다.
```

## 규칙을 더 넣지 마라

위 네 줄이 실측으로 정한 상한이다. 규칙을 넷 더 넣었더니
(`몇 개는 COUNT(*)`, `조건을 빠짐없이 WHERE에`) **개발 90% · 홀드아웃 81%** 로 갈렸다 —
개발만 오르고 홀드아웃이 내려갔다. 깨진 것은 두 종류였다:
`부서별 직원 수` 같은 GROUP BY 질문에 COUNT 규칙이 과적용됐고,
규칙이 늘자 **인라인 단위 주석에서 주의가 분산되어 단위 실패가 재발**했다.
[harness-evaluation.md](../../../docs/harness-evaluation.md) · Hasan et al. (2026)
*MCP Tool Descriptions Are Smelly!* 의 과보강 퇴행과 같은 형태다.

## 호출 옵션

[`../model.json`](../model.json) 의 `llm` 을 그대로 쓴다. **`think: false` 를 반드시 넣는다** —
켜면 숨은 추론 토큰이 `num_predict` 를 소진해 **빈 문자열**이 반환되고,
이는 T1(무효 SQL 생성)으로 오분류된다 ([edge-cases.md](../../../docs/edge-cases.md) T1).

## 응답 후처리

1. 코드펜스가 있으면 벗긴다 (규칙에 금지했는데도 붙는 경우가 있다).
2. `SELECT` 로 시작하지 않으면 실행하지 않고 T2로 처리한다 (D4 SELECT-only).
3. 실행 오류가 나면 **오류 메시지를 물려** 1회 재생성한다.
   자체 재검토 루프는 금지다 (Huang et al., ICLR 2024 — design.md 열어둔 항목 `nl2sql 재시도 횟수`).
