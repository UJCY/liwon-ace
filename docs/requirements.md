# 과제 요구사항 — MCP 기반 지능형 데이터 플랫폼 클러스터

> 2026 오픈소스 개발자대회 지정과제 (리원에이스).
> 이 문서는 **과제가 요구하는 것**만 기록한다. 우리 팀의 설계 결정은 [design.md](./design.md)에 있다.

## 출처

| 문서 | URL | 성격 |
|------|-----|------|
| 리원에이스 기술 블로그 | https://liwonace.co.kr/blog/9 | 과제 상세 (가장 자세함) |
| KOSSA 과제 페이지 | https://www.kossa.kr/materials/2026/ossp/tasks-liwonace.html | 공식 과제 요강 |
| 리원에이스 공지 | https://liwonace.co.kr/notice/2 | 데이터셋 배포 안내 |

## 미션

> "사람이 말로 질문하면, AI가 스스로 DB를 뒤져서 정답을 찾아주는 시스템"

PostgreSQL + pgvector 위에 벡터 검색, NL2SQL, 지식 그래프를 **MCP(Model Context Protocol)** 로 통합한다. 기존 RAG 파이프라인(청킹→임베딩→인덱싱→검색→리랭킹)의 운영 복잡도를 MCP 표준으로 낮추는 것이 핵심 취지다.

## 구현해야 하는 컴포넌트 4개

1. **벡터 데이터베이스** — PostgreSQL + pgvector. 문서를 벡터 변환·저장하고 유사도 기반 의미 검색. 임베딩 적재는 참가자 직접 구현 (`document_chunks` 테이블이 빈 상태로 스키마에 포함됨).
2. **MCP 서버 (도구 3종)** — 벡터 검색, NL2SQL, 지식 그래프. "3개의 MCP 도구를 구현합니다." (블로그 문면)
3. **도구 자동 선택** — **규칙 기반 라우터**가 질문 유형을 분석해 적합한 도구를 자동 매칭. KOSSA 요강은 이를 "MCP Parallel 패턴"이라 부름.
4. **AI 에이전트 연동** — Ollama 소형 LLM이 MCP로 도구를 호출하고 답변 생성.

### 과제 흐름도 (블로그)

```
사용자 질문 → AI 에이전트 → 라우터 → MCP 서버 → PostgreSQL → 답변 반환
```

## 데이터셋 (companyx-dataset-v1.0)

가상 IT 솔루션 기업 Company-X의 운영 데이터 (2024-01 ~ 2026-06).

| 데이터 | 형식 | 규모 | 대응 도구 |
|--------|------|------|----------|
| 테이블 데이터 | SQL (DDL + INSERT) | 8개 테이블, 약 800행 | NL2SQL |
| 문서 데이터 | Markdown 40건 (장애보고·기술문서·회의록·제안서) | + index.json | 벡터 검색 |
| 관계 데이터 | JSON (노드 + 엣지) | 133노드, 354관계 | 지식 그래프 |
| 예시 질문 | JSON | 30개 (도구별 10개) | 라우터 자체 테스트 |

- questions.json의 도구 식별자: `nl2sql`, `vector_search`, `knowledge_graph` (각 10개, 질문당 1개).
- 그래프 노드 유형: client(30) / product(12) / employee(45) / project(40) / department(6). 관계 7종 (BELONGS_TO, HEAD_IS, USES, MANAGES_ACCOUNT, HAS_PROJECT, LEADS, REPORTED_ISSUE).

## 제약 조건

- **외부 API 사용 불가** (OpenAI, Claude 등). 모든 모델은 Ollama 로컬 실행. GPU 없이 CPU만으로 구동 가능해야 함.
- PostgreSQL 15+ / pgvector.
- RAM 최소 4GB, Linux 권장 (macOS / WSL2 가능).
- `air` 프레임워크(리원에이스 오픈소스, Apache-2.0)는 **권장이지 의무 아님**. https://airmcp.dev / https://docs.airmcp.dev
- LLM 권장: 블로그·공지는 **Gemma 4 E2B**, KOSSA 요강은 "온프레미스 소형 LLM(7B)"로 표기 — 문서 간 차이 있음. 공통분모는 "Ollama 로컬 소형 LLM".

## KOSSA 요강의 추가 요구 (개발과제 예시)

- 규칙 기반 라우터를 통한 도구 자동 선택 — **MCP Parallel 패턴**
- **온톨로지 기반** 지식 그래프
- **선택적 컨텍스트 큐레이션 (TACC 적용)** — 필수 논문 [1]의 기법: 컨텍스트를 무조건 많이 주지 말고 모델 특성·과업 유형에 따라 선별 구성

## 참고 자료

**필수 참조** (건별 정리: `docs/references/`)
1. 전현우, 김태성, 강현 (2026). MCP 컨텍스트 구성이 소형 언어모델 성능에 미치는 영향. https://zenodo.org/records/18842478 → [정리](./references/tacc-context-composition.md)
2. Jeon, H. (2026). Pylon-7: A 7-Layer Reference Model for AI Agent Workflows. https://zenodo.org/records/18808598 → [정리](./references/pylon-7.md)
3. Anthropic (2024). Model Context Protocol Specification. https://modelcontextprotocol.io → [정리](./references/mcp-spec.md)

**권장 참조**: pgvector, Ollama, Lewis et al. (2020) RAG, Liu et al. (2024) Lost in the Middle, Hou et al. (2025) MCP Landscape, air 프레임워크.

## 검증 기준 (과제가 제공하는 것)

- questions.json 30개로 자체 테스트: 질문별 기대 도구(`tool`)와 힌트(`hint`) 제공 → 라우터의 도구 선택 정확도 검증 가능.
- 공지 문구: "정답은 하나가 아닙니다" — 설계 자유도 명시.

## 수상

1개 팀, 상금 200만원, 선정팀 정규직 채용 검토.
