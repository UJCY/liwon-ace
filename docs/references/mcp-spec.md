# 필수 참조 [3] — Model Context Protocol 사양

> Anthropic (2024~). https://modelcontextprotocol.io
> 정리 시점(2026-07-30) **스펙 문서상** 최신 리비전: **2026-07-28**. 권위 정의는 TypeScript 스키마(schema.ts).
>
> **⚠️ 구현은 스펙보다 뒤처져 있다.** 실측 결과(2026-07-30) `@modelcontextprotocol/sdk` **1.30.0**(2026-07-27 릴리스)의 `LATEST_PROTOCOL_VERSION`은 **`2025-11-25`**이고, `SUPPORTED_PROTOCOL_VERSIONS`는 `2025-11-25 / 2025-06-18 / 2025-03-26 / 2024-11-05 / 2024-10-07`이다. **2026-07-28 리비전은 SDK에 아직 없다.** 따라서 우리가 실제로 구현·주장할 수 있는 리비전은 `2025-11-25`이며, 아래 "리비전 주의" 절의 무상태 모델은 **스펙 문서에만 존재하는 미래 상태**다. 검증 내역은 [air-evaluation.md 8.2절](../air-evaluation.md#82-검증-2--스펙-리비전-리스크였던-판단이-무효).

## 한 줄 요약

LLM 애플리케이션과 외부 도구·데이터를 연결하는 개방 표준. JSON-RPC 2.0 기반, **무상태(stateless) 자기완결 요청**, 요청 단위 capability 협상.

## 아키텍처

- **Host**: 연결을 시작하는 LLM 애플리케이션 (우리 과제의 AI 에이전트)
- **Client**: Host 안의 커넥터
- **Server**: 컨텍스트·기능을 제공하는 서비스 (우리 과제의 MCP 서버)

LSP(Language Server Protocol)에서 영감 — 도구 통합을 생태계 수준에서 표준화.

## 서버가 제공하는 기능 3종

| 기능 | 용도 | 우리 사용 |
|------|------|----------|
| **Tools** | 모델이 실행하는 함수 | 핵심 — 라우터(`ask` 또는 `route`) + 3종 |
| **Resources** | 사용자/모델용 컨텍스트·데이터 | 선택 |
| **Prompts** | 템플릿화된 메시지·워크플로 | 선택 |

(클라이언트 측 기능으로 Elicitation — 서버가 사용자에게 추가 입력 요청. 우리 범위 밖.)

## Transport

프로토콜 의미는 transport와 무관 — transport는 메시지 프레이밍·전달 방식만 정의.

- **stdio**: 클라이언트가 서브프로세스로 서버 실행, 표준 입출력에 개행 구분 JSON-RPC. 로컬 단일 클라이언트에 적합.
- **Streamable HTTP**: 단일 MCP 엔드포인트에 POST, 응답은 JSON 또는 요청 단위 SSE 스트림. 원격·다중 클라이언트에 적합.
- 메시지는 UTF-8 필수. 서버는 JSON-RPC 요청을 시작하지 않는다(응답·알림만).

## Tools 세부 (우리 과제 핵심)

### 도구 정의
- `name`(1~128자, 영숫자·`_`·`-`·`.`), `description`, **`inputSchema`(JSON Schema, 필수·null 불가)**, `outputSchema`(선택), `annotations`(선택).
- 서버는 `tools` capability를 선언해야 하며(MUST), `tools/list`에 결정적 순서로 응답해야 함 — 순서 고정이 클라이언트 캐시·프롬프트 캐시 적중률에 유리.

### 도구 결과
- 비구조화: `content` 배열 (text / image / audio / resource_link / embedded resource).
- **구조화: `structuredContent`** — `outputSchema` 정의 시 서버는 스키마 준수 결과를 반환해야 함(MUST). 하위 호환 위해 직렬화 JSON을 text content로도 병행 반환 권장(SHOULD).

### 에러 2계층 (스펙이 명시적으로 구분)
1. **Protocol Error** — 요청 구조 자체 문제(없는 도구, 스키마 위반). JSON-RPC error로 반환. 모델이 자가 수정하기 어려움.
2. **Tool Execution Error** — 실행 중 실패(입력 검증, 비즈니스 로직). 정상 result에 **`isError: true`** + 설명 텍스트. 클라이언트는 이를 모델에 전달해 자가 교정 유도(SHOULD).

### 보안 (서버 MUST 4개)
입력 검증 / 접근 제어 / 도구 호출 rate limit / 출력 sanitize.

### 상태 관리
프로토콜 수준 세션 없음. 호출 간 상태가 필요하면 도구 결과로 명시적 핸들을 반환하고 후속 호출 인자로 받는 패턴 (비규범 가이드).

## 리비전 주의

2026-07-28 리비전은 **무상태 모델** — 이전 리비전의 `initialize` 핸드셰이크 기반 연결 세션을 대체했고, 요청마다 `_meta.io.modelcontextprotocol/*`에 프로토콜 버전·클라이언트 정보를 실어야 한다. 구 리비전과의 하위 호환 매트릭스가 스펙에 있음.

## 우리 설계에 주는 시사점

| 스펙 내용 | 우리 설계 연결 |
|----------|--------------|
| 에러 2계층 (protocol vs execution) | edge-cases.md의 **"데이터에 없음 ≠ 시스템 오류" 규약과 정확히 대응**: 도구 실행 실패(T1·T6)는 `isError: true`, 데이터 부재(T3~T5·T7)와 거절(R1)은 `isError` 없는 정상 결과 + 구조화 필드(`out_of_scope` 등)로 — 모델이 읽고 "모른다" 답변을 생성해야 하므로 에러가 아니라 데이터다 |
| `outputSchema` + `structuredContent` | 도구 4종 모두 출력 스키마 정의 — 출처 메타데이터(Q1), 거절 타입(D6)을 스키마에 명시. Pylon-7의 L3 "구조화 출력"을 스펙 기능으로 구현 |
| 도구 이름 규칙 | `ask`/`route`, `nl2sql`, `vector_search`, `knowledge_graph` 모두 규칙 부합 |
| stdio vs Streamable HTTP | 열린 항목 "transport"의 판단 기준: 에이전트가 서버를 로컬 서브프로세스로 띄우면 stdio로 충분, 데모·심사에서 별도 프로세스/원격 접근 보이려면 Streamable HTTP |
| 서버 보안 MUST | D4 SELECT-only(입력 검증), rate limit — 구현 요구사항 목록에 포함 필요 |
| 결정적 tools/list 순서 | 구현 시 도구 등록 순서 고정 |
| 리비전 확인 | 채택한 SDK 1.30.0의 최신 지원 리비전은 2025-11-25 (D8에서 확인 완료) |
