# Lantern

대회 접수명 `liwon-ace` — 2026 오픈소스 개발자대회 지정과제(리원에이스) 출품작.

## 소개

사내 문서·데이터베이스·관계 데이터를 자연어 한 문장으로 물으면 규칙 기반 라우터가 적합한 MCP 도구를
골라 답하고, 요구한 형태의 자료가 없으면 없다고 답하는 로컬 실행 검색 시스템.
외부 API 없이 소형 로컬 모델만으로 동작한다.

## 어떻게 도는가

MCP 도구는 **4개**다. 평소에는 `ask` 하나만 부른다 — 판별부터 병합까지 `ask` 가 하므로 **MCP 왕복이 1회**다.

```
질문 ──▶ ask ──┬──▶ 라우터 판별 ──▶ 도구 1~2개 실행 ──▶ 병합 ──▶ 결과 + 라우팅 판단
               │                                                (routed_to · matched_rule · why)
               └──▶ 무매칭이면 도구를 부르지 않고 거절한다
```

| 도구 | 돌려주는 것 | 데이터 |
|---|---|---|
| `ask` | 위 전부 — 라우터이자 실행자 | — |
| `vector_search` | **서술** — 원인·방법·절차·결정 | 문서 40건 |
| `nl2sql` | **정형 속성·수치** — 금액·연봉·기간·상태·건수 | 테이블 8개 · 818행 |
| `knowledge_graph` | **개체 식별·연결** — 누가 무엇을 쓰는가 | 노드 133 · 엣지 354 |

도구 3종도 함께 등록한다 — 개별 검증·시연 창구를 남기기 위해서다.

**도구는 "질문이 어느 자산에 있는가"가 아니라 "어떤 형태의 답을 요구하는가"로 가른다.** 세 자산이
같은 사실을 다른 형태로 담고 있어서다 — 그래프는 정형 테이블에서 100% 도출되고, 문서 40건은 전부
그래프 개체를 언급한다. 두 형태를 **함께** 요구하는 질문만 두 도구를 병렬 호출해 병합한다.

**도구를 고르는 것은 LLM 이 아니다.** 스키마 어휘·개체 한정어가 걸리는지 보는 게이트와, 도구 능력
서술문과의 임베딩 유사도 — 둘 다 결정적 함수다. LLM 은 SQL 생성과 최종 답변에만 쓴다.

### 답이 없을 때를 상태로 가른다

응답은 두 층이다 — 봉투의 `status` 가 합성 결과(`single`·`parallel_merge`·`out_of_scope` …),
`results[도구].status` 가 도구별 결과다.

| 상태 | 뜻 |
|---|---|
| `ok` | 답이 있다 |
| `no_result` | 자료가 없다 |
| `partial` | 도구도 개체도 맞는데 **요구한 형태만** 없다 — 없는 것과 인접 사실을 별도 필드로 나눠 준다 |
| `ungrounded` | 실행은 됐고 빈손인데 **질문의 값 조건을 데이터와 대조하지 못했다** — "0건입니다"로 답하면 자신 있는 오답이 된다 |
| `entity_not_found` · `ambiguous_entity` | 개체가 없다 · 그 이름이 여럿을 가리킨다 |
| `out_of_scope` | 무매칭 — 도구를 부르지 않고 거절한다 |
| `error` | 실행 실패. **이것만** `isError: true` 다 |

**데이터 부재는 오류가 아니다.** 모델이 읽고 "모른다"고 답해야 하는 정보이므로 정상 결과로 준다 —
이 구분이 없으면 모델이 인접 사실로부터 답을 지어낸다.

판단의 경위는 [docs/design.md](docs/design.md), 그림 한 장은 [docs/overview/architecture.html](docs/overview/architecture.html) 에 있다.

## MCP 클라이언트에 등록

stdio 서버다. 아래 [재현 방법](#재현-방법)으로 DB 를 세우고 `npm run build` 한 뒤, 클라이언트 설정에 넣는다.
**경로는 절대경로**로 적는다 — 자산을 실행 파일 기준으로 찾으므로 작업 디렉터리는 상관없다.

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

PostgreSQL `localhost:55432` 과 Ollama `localhost:11434` 를 기본값으로 찾는다. 다르면
`PGHOST`·`PGPORT`·`PGUSER`·`PGPASSWORD`·`PGDATABASE`·`OLLAMA_HOST` 로 덮는다.

붙이기 전에 저장소 루트에서 확인한다.

```bash
node scripts/smoke.mjs      # tools/list 4개 + 대표 질문 7건 (30초)
npm start                   # 직접 띄워 보기 (stdio 라 터미널에서는 대기만 한다)
```

## 재현 방법

사전 준비

- Docker — PostgreSQL 16 + pgvector 컨테이너를 띄운다.
- Node.js 22 — MCP 서버와 에이전트 런타임. 측정은 22.17.0 에서 했다.
- Python 3.14 — 하네스 러너. 표준 라이브러리만 쓰므로 따로 설치할 패키지가 없다.
- Ollama 0.31.2 — 떠 있어야 하고, 모델 둘을 미리 받아 둔다.

```bash
ollama pull gemma4:e2b-it-qat
ollama pull bge-m3
```

세우기

```bash
# ① 컨테이너 — 포트는 55432 다 (기본 5432 가 아니다)
docker run -d --name cx-pg -e POSTGRES_PASSWORD=cx -e POSTGRES_DB=companyx \
  -p 55432:5432 pgvector/pgvector:pg16
until docker exec cx-pg pg_isready -U postgres -d companyx >/dev/null 2>&1; do sleep 1; done

# ② 스키마와 데이터 — 이 두 줄을 건너뛰면 ③ 이 죽는다
docker exec -i cx-pg psql -U postgres -d companyx -v ON_ERROR_STOP=1 \
  < companyx-dataset-v1.0/sql/01-schema.sql
docker exec -i cx-pg psql -U postgres -d companyx -v ON_ERROR_STOP=1 \
  < companyx-dataset-v1.0/sql/02-data.sql

# ③ 문서 청크·임베딩·그래프 적재 (1~2분, Ollama 를 쓴다)
python3 harness/build/load_pg.py

# ④ 빌드
npm install && npm run build
```

돌려 보기

```bash
node scripts/smoke.mjs                              # MCP 프로토콜이 오가는가 (30초)
npm run agent -- "Client-A가 사용 중인 제품 목록은?"   # 질문 하나 (첫 실행 20초 — 모델 적재)
npm run agent:check                                 # 엣지 29 + 회귀 30 종단 채점 (5~8분)
node scripts/demo.mjs                               # 시연영상 그대로 재현 (촬영 전 --verify · 직전 --warm)
```

**지우고 다시 하기, 안 될 때, 측정 러너 네 종은 [RUNNING.md](RUNNING.md) 에 있다** — 이 절은 요약이고 그쪽이 전문이다.

## 라이선스

MIT. 전문은 [LICENSE](LICENSE) 에 있다.

## 사용 모델과 그 라이선스

| 용도 | Ollama 태그 | 모델명 및 개발사 | 라이선스 |
|---|---|---|---|
| LLM | `gemma4:e2b-it-qat` | Gemma 4 E2B IT (QAT) (Google) | Gemma Terms of Use |
| 임베딩 | `bge-m3` | BGE-M3 (Beijing Academy of Artificial Intelligence) | MIT License |

모델 가중치는 저장소에 포함되지 않으며 Ollama로 내려받는다.

## 문서 안내

- [RUNNING.md](RUNNING.md) — 아무것도 없는 상태에서 시연까지, 그리고 지우고 다시 하는 길.
- [CONTEXT.md](CONTEXT.md) — 이 프로젝트에서 쓰는 용어를 한곳에 정의한 용어집.
- [docs/requirements.md](docs/requirements.md) — 과제 원문 요구사항과 그 해석.
- [docs/design.md](docs/design.md) — 설계 결정과 그렇게 정한 근거 기록.
- [docs/harness-evaluation.md](docs/harness-evaluation.md) — 모델을 바꾸지 않고 구조만 바꿔 잰 실측표.
- [docs/overview/architecture.html](docs/overview/architecture.html) — 구조 한 장 그림.
- [harness/README.md](harness/README.md) — 프롬프트·컨텍스트 구성 등 모델 바깥 자산의 안내.
- [THIRD_PARTY.md](THIRD_PARTY.md) — 쓰고 있는 오픈소스 라이브러리 목록(SBOM).
