# 오픈소스 라이브러리 목록 (SBOM)

2026 오픈소스 개발자대회 결과보고서 붙임1과 같은 내용이다.
GPL·AGPL·LGPL 계열은 0건이고, Python 쪽은 표준 라이브러리만 써서 외부 패키지가 없다.
프로젝트가 쓰는 AI 모델 2종과 그 라이선스는 [README.md](README.md) 「사용 모델과 그 라이선스」에 따로 적었다.

| 번호 | 라이브러리명 | 버전 | 라이선스 | 공식 저장소 URL | 사용 목적 및 주요 기능 |
|---|---|---|---|---|---|
| 1 | @modelcontextprotocol/sdk | 1.30.0 | MIT | github.com/modelcontextprotocol/typescript-sdk | MCP 서버·클라이언트 프로토콜 구현 / 라이브러리로 불러 씀 |
| 2 | pg | 8.23.0 | MIT | github.com/brianc/node-postgres | PostgreSQL 연결 및 질의 실행 / 라이브러리로 불러 씀 |
| 3 | zod | 3.25.76 | MIT | github.com/colinhacks/zod | MCP 도구 입출력 스키마 정의·검증 / 라이브러리로 불러 씀 |
| 4 | PostgreSQL | 16.15 | PostgreSQL License | github.com/postgres/postgres | 문서 청크·정형 테이블·그래프 저장 및 질의 / 컨테이너로 구동해 접속 |
| 5 | pgvector | 0.8.6 | PostgreSQL License | github.com/pgvector/pgvector | 임베딩 저장과 코사인 유사도 검색 / PostgreSQL 확장으로 설치 |
| 6 | Ollama | 0.31.2 | MIT | github.com/ollama/ollama | 로컬 LLM·임베딩 모델 구동 / 별도 프로세스에 HTTP 호출 |
| 7 | Node.js | 22.17.0 | MIT | github.com/nodejs/node | MCP 서버·에이전트 실행 런타임 / 실행 환경 |
| 8 | TypeScript | 5.7.2 | Apache-2.0 | github.com/microsoft/TypeScript | 소스 타입 검사 및 빌드 / 빌드 도구 |
