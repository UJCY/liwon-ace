# Lantern

대회 접수명 `liwon-ace` — 2026 오픈소스 개발자대회 지정과제(리원에이스) 출품작.

## 소개

사내 문서·데이터베이스·관계 데이터를 자연어 한 문장으로 물으면 규칙 기반 라우터가 적합한 MCP 도구를
골라 답하고, 요구한 형태의 자료가 없으면 없다고 답하는 로컬 실행 검색 시스템.
외부 API 없이 소형 로컬 모델만으로 동작한다.

## 재현 방법

사전 준비

- Docker — PostgreSQL 16 + pgvector 컨테이너를 띄운다.
- Node.js 22 — MCP 서버와 에이전트 런타임. 측정은 22.17.0 에서 했다.
- Python 3.14 — 하네스 러너. 표준 라이브러리만 쓰므로 따로 설치할 패키지가 없다.
- Ollama 0.31.2 — 모델 둘을 미리 받아 둔다.

```
ollama pull gemma4:e2b-it-qat
ollama pull bge-m3
```

구동

```
docker run -d --name cx-pg -e POSTGRES_PASSWORD=cx -e POSTGRES_DB=companyx \
  -p 55432:5432 pgvector/pgvector:pg16
python3 harness/build/load_pg.py       # 문서 청크·임베딩·그래프 적재
npm install && npm run build
npm run agent                          # 대화형 에이전트
npm run agent:check                    # 엣지 29 + 회귀 30 종단 채점 (5~8분)
node scripts/demo.mjs                  # 시연영상 그대로 재현 (사전 워밍업: --warm)
```

## 라이선스

MIT. 전문은 [LICENSE](LICENSE) 에 있다.

## 사용 모델과 그 라이선스

| 용도 | Ollama 태그 | 모델명 및 개발사 | 라이선스 |
|---|---|---|---|
| LLM | `gemma4:e2b-it-qat` | Gemma 4 E2B IT (QAT) (Google) | Gemma Terms of Use |
| 임베딩 | `bge-m3` | BGE-M3 (Beijing Academy of Artificial Intelligence) | MIT License |

모델 가중치는 저장소에 포함되지 않으며 Ollama로 내려받는다.

## 문서 안내

- [CONTEXT.md](CONTEXT.md) — 이 프로젝트에서 쓰는 용어를 한곳에 정의한 용어집.
- [docs/requirements.md](docs/requirements.md) — 과제 원문 요구사항과 그 해석.
- [docs/design.md](docs/design.md) — 설계 결정과 그렇게 정한 근거 기록.
- [docs/harness-evaluation.md](docs/harness-evaluation.md) — 모델을 바꾸지 않고 구조만 바꿔 잰 실측표.
- [harness/README.md](harness/README.md) — 프롬프트·컨텍스트 구성 등 모델 바깥 자산의 안내.
- [THIRD_PARTY.md](THIRD_PARTY.md) — 쓰고 있는 오픈소스 라이브러리 목록(SBOM).
