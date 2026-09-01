# Lantern

대회 접수명 `liwon-ace` — 2026 오픈소스 개발자대회 지정과제(리원에이스) 출품작.
사내 문서·데이터베이스·관계 데이터를 자연어 한 문장으로 묻는 로컬 실행 검색 시스템. 외부 API 를 쓰지 않는다.

## 구조와 동작

MCP 도구는 **4개**. 평소에는 `ask` 하나만 부른다 — 판별부터 병합까지 `ask` 가 하므로 왕복이 1회다.

```
질문 ──▶ ask ──┬──▶ 라우터 판별 ──▶ 도구 1~2개 실행 ──▶ 병합 ──▶ 결과 + 라우팅 판단
               └──▶ 무매칭이면 도구를 부르지 않고 거절
```

| 도구 | 돌려주는 것 | 데이터 |
|---|---|---|
| `ask` | 위 전부 — 라우터이자 실행자 | — |
| `vector_search` | 서술 — 원인·방법·절차·결정 | 문서 40건 |
| `nl2sql` | 정형 속성·수치 — 금액·연봉·기간·건수 | 테이블 8개 · 818행 |
| `knowledge_graph` | 개체 식별·연결 | 노드 133 · 엣지 354 |

- **가르는 기준은 "어느 자산에 있는가"가 아니라 "어떤 형태의 답을 요구하는가"다.** 두 형태를 함께 요구하는 질문만 두 도구를 병렬 호출해 병합한다.
- **도구 선택은 LLM 이 아니다** — 어휘 게이트 + 시그니처 임베딩, 둘 다 결정적 함수다. LLM 은 SQL 생성과 최종 답변에만 쓴다.
- **답이 없을 때를 상태로 가른다** — `ok` · `no_result` · `partial`(형태만 없음) · `ungrounded`(값 조건을 데이터와 대조 못 함) · `entity_not_found` · `ambiguous_entity` · `out_of_scope`. **실행 실패(`error`)만 `isError` 다** — 데이터 부재는 모델이 읽고 "모른다"고 답해야 할 정보다.

설계 근거는 [design.md](docs/design.md), 그림 한 장은 [architecture.html](docs/overview/architecture.html).

## 실행

Docker · Node.js 22 · Python 3.14(표준 라이브러리만) · Ollama 가 필요하다.

```bash
ollama pull gemma4:e2b-it-qat && ollama pull bge-m3

docker run -d --name cx-pg -e POSTGRES_PASSWORD=cx -e POSTGRES_DB=companyx \
  -p 55432:5432 pgvector/pgvector:pg16
until docker exec cx-pg pg_isready -U postgres -d companyx >/dev/null 2>&1; do sleep 1; done

# 스키마·데이터 — 건너뛰면 다음 줄이 죽는다
docker exec -i cx-pg psql -U postgres -d companyx -v ON_ERROR_STOP=1 \
  < companyx-dataset-v1.0/sql/01-schema.sql
docker exec -i cx-pg psql -U postgres -d companyx -v ON_ERROR_STOP=1 \
  < companyx-dataset-v1.0/sql/02-data.sql

python3 harness/build/load_pg.py     # 문서 청크·임베딩·그래프 (1~2분)
npm install && npm run build
```

물어본다. 첫 실행은 모델 적재로 20초쯤 걸리고, 두 번째부터 2~3초다.

```bash
npm run agent -- "Client-A가 사용 중인 제품 목록은?"
```

지우고 다시 하기와 안 될 때는 [RUNNING.md](RUNNING.md) 에 있다.

## 테스트

```bash
node scripts/smoke.mjs        # MCP 프로토콜 + 대표 질문 7건 (30초)
npm run agent:check           # 엣지 29 + 회귀 30 종단 채점 (5~8분)
node scripts/demo.mjs         # 시연 재현 (--verify 로 3회 동일성 검사)
```

측정 러너 네 종은 [RUNNING.md](RUNNING.md) 4절, 수치는 [harness-evaluation.md](docs/harness-evaluation.md).

## MCP 등록

stdio 서버다. 위 실행 절을 마친 뒤 **절대경로**로 등록한다 — 자산을 실행 파일 기준으로 찾으므로 작업 디렉터리는 상관없다.

```json
{
  "mcpServers": {
    "companyx": {
      "command": "node",
      "args": ["/절대/경로/liwon-ace/dist/server.js"]
    }
  }
}
```

DB `localhost:55432` 와 Ollama `localhost:11434` 를 기본값으로 찾는다. 다르면
`PGHOST`·`PGPORT`·`PGUSER`·`PGPASSWORD`·`PGDATABASE`·`OLLAMA_HOST` 로 덮는다.

## 라이선스와 모델

MIT — 전문은 [LICENSE](LICENSE). 모델 가중치는 저장소에 없고 Ollama 로 받는다.

| 용도 | Ollama 태그 | 모델 · 개발사 | 라이선스 |
|---|---|---|---|
| LLM | `gemma4:e2b-it-qat` | Gemma 4 E2B IT (QAT) · Google | Gemma Terms of Use |
| 임베딩 | `bge-m3` | BGE-M3 · BAAI | MIT |

## 문서

[RUNNING.md](RUNNING.md) 실행 전문 · [CONTEXT.md](CONTEXT.md) 용어집 ·
[requirements.md](docs/requirements.md) 요구사항 해석 · [design.md](docs/design.md) 설계 결정 ·
[harness-evaluation.md](docs/harness-evaluation.md) 실측 · [harness/README.md](harness/README.md) 하네스 자산 ·
[THIRD_PARTY.md](THIRD_PARTY.md) SBOM
