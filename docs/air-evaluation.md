# air 프레임워크 채택 검토

> 열린 항목 **구현 스택** 판단용. 조사 시점 2026-07-30. 공식 문서(docs.airmcp.dev)와 npm 레지스트리 실측 기준.
> 결론 요약: **air는 공식 SDK 래퍼이므로 선택이 비가역적이지 않다.** 프로토타입 반나절로 3가지만 검증하고 결정한다.

## 1. 실물 확인 결과

| 항목 | 확인된 사실 |
|---|---|
| 패키지 | `@airmcp-dev/core` **0.3.0**, `@airmcp-dev/cli` **0.2.1** (npm 공개) |
| 라이선스 | Apache-2.0 (과제 문서와 일치) |
| 저작 | "Air Foundation, Built by CodePedia Labs" — **필수 참조 [1][2] 논문 저자 소속과 동일** |
| 저장소 | github.com/airmcp-dev/air |
| 이력 | 최초 공개 2026-04-10, 최종 수정 2026-06-30. **2.5개월에 9개 버전** |
| 런타임 | Node.js 18+, TypeScript ESM |
| **핵심 의존성** | **`@modelcontextprotocol/sdk` ^1.29.0**, `zod` ^3.25.0 |

**가장 중요한 사실**: air는 MCP를 새로 구현한 것이 아니라 **공식 SDK를 감싼 래퍼**다. 따라서 "air vs 직접 구현"은 배타적 선택이 아니고, air를 쓰면 SDK 위에 레이어가 하나 얹히는 것이다. 이 구조 때문에 나중에 air를 벗기는 비용이 낮다 — `defineTool` → `server.tool` 변환은 기계적이다.

## 2. air가 제공하는 것

| 기능 | 내용 | 우리에게 실제 유용한가 |
|---|---|---|
| `defineTool` / `defineServer` | string shorthand params, 자동 Zod 검증, 자동 MCP content 변환 | 도구가 4개뿐이라 절감량이 작다. 있으면 편하지만 없어서 못 할 일은 아니다 |
| **7-Layer Meter** | 호출을 L1~L7로 자동 분류하고 호출량·레이턴시·성공률 추적. `@airmcp-dev/core`에 포함, 기본 활성 | **이것이 진짜 차별점.** 아래 3절 참조 |
| Transport 3종 | stdio / SSE / Streamable HTTP — 설정 한 줄로 전환, 자동 감지 | 실질적 이점. 열린 항목 "transport" 결정을 나중으로 미룰 수 있다 |
| 플러그인 19종 | timeout·retry·circuitBreaker·fallback / cache·dedup·queue / auth·sanitizer·validator / cors 등 | 대부분 우리 규모에 불필요. 아래 4절 참조 |
| CLI | `npx @airmcp-dev/cli create` 스캐폴딩, `dev` 서버, 템플릿 4종(basic/api/crud/agent) | 초기 셋업 시간 절약 |

## 3. 7-Layer Meter — 채택을 정당화하는 유일한 기능

Meter는 도구 호출을 Pylon-7의 7계층으로 자동 분류하고 계측한다. **필수 참조 [2]가 제안한 계층 모델을 우리 시스템에서 실제로 측정할 수 있게 해준다** — "논문의 참조 모델을 구현했을 뿐 아니라 계측했다"는 서술은 심사에서 값이 있다. 직접 구현하면 이 계측 인프라를 우리가 만들어야 한다.

**단서 하나**: 자동 분류는 **도구 이름 패턴** 기반이다.

| Layer | 매칭 패턴 |
|---|---|
| L2 | `get`, `read`, `find`, `lookup`, `list`, `show` |
| L4 | `compute`, `calculate`, `aggregate`, `analyze`, `summarize` (**미매칭 시 기본값**) |
| L6 | `generate`, `complete`, `chat`, `embed`, `infer`, `predict` |
| L7 | `agent`, `think`, `plan`, `execute`, `reason`, `chain`, `orchestrate` |

우리 도구명(`ask`, `nl2sql`, `vector_search`, `knowledge_graph`)은 어느 패턴에도 걸리지 않아 **전부 L4 기본값으로 떨어진다.** `defineTool`의 `layer` 속성으로 수동 지정해야 의미 있는 계측이 된다. 이건 결함이 아니라 우리가 해야 할 일 — 어차피 우리 도구가 어느 계층인지는 우리가 판단해야 하고, Pylon-7 논문의 계층 정의(L5 Routing = `ask`, L3 Resource = 3종 정도)에 맞춰 명시하는 편이 정확하다.

## 4. 플러그인 19종의 실제 가치 — 기대보다 낮다

| 플러그인 | 우리에게 |
|---|---|
| `timeoutPlugin` | ○ 유용. 다만 PostgreSQL `statement_timeout`으로도 커버된다 |
| `dedupPlugin` | ○ 동일 질문 동시 호출 제거. 있으면 좋음 |
| **`retryPlugin`** | **✗ 우리 T1 제약과 충돌.** 아래 참조 |
| `cachePlugin` | △ 문서 40건·800행 규모라 캐시 이득이 작다. 시연에서 응답 속도를 보이려면 쓸 수 있음 |
| `authPlugin` | ✗ 로컬 실행이라 불필요 |
| `sanitizerPlugin` | ✗ HTML/스크립트 제거용. 우리 SQL 안전성(SELECT-only)과 무관 |
| `circuitBreaker`·`fallback`·`queue`·`cors` 등 | ✗ 이 규모에서 불필요 |

**retryPlugin이 쓸 수 없다는 점이 중요하다.** air의 retry는 "exponential backoff로 실패한 호출 재시도" — 같은 입력으로 다시 호출하는 것이다. 우리 T1 제약(design.md)은 Huang et al. (ICLR 2024)에 근거해 **재시도가 실행 오류 메시지 같은 외부 신호를 반드시 물어야 한다**고 정했다. SQL 생성 실패에 단순 retry를 걸면 같은 프롬프트로 재생성하는 것이므로 외부 피드백 없는 반복이 된다. 즉 **nl2sql 재시도는 air 플러그인이 아니라 도구 핸들러 안에서 직접 구현해야 한다.**

air의 대표 세일즈 포인트("retry·cache·auth를 한 줄씩") 중 우리에게 맞는 것이 사실상 timeout·dedup 둘뿐이다.

## 5. 리스크

| 리스크 | 내용 | 심각도 |
|---|---|---|
| **0.x 버전** | 0.3.0. semver상 minor 올림에 breaking change가 허용된다. 2.5개월에 9버전 = 빠르게 변한다 | 중 — 버전 고정(`0.3.0` 정확히)으로 완화 |
| **MCP 스펙 리비전 지연** | air가 참조하는 SDK는 **^1.29.0 (2026-03-30 릴리스)**. SDK 최신은 1.30.0(2026-07-27)이고, **우리가 정리한 스펙 최신 리비전은 2026-07-28**. air 문서의 transport 설명이 "각 세션이 고유 ID를 받는다"는 **세션 기반 모델**이라, 세션을 없앤 2026-07-28 무상태 리비전은 반영되지 않았을 가능성이 높다 | **높음 — 검증 필요** |
| 디버깅 레이어 | 문제 발생 시 air / SDK / 우리 코드 3층을 분리해야 한다. 신생 프레임워크라 이슈 검색 자료가 거의 없다 | 중 |
| 문서 완결성 | 사이드바에 있는 일부 경로(`guide`, `reference`, `examples` 루트, `migrate-from-mcp-sdk`)가 404다. 문서가 아직 정리 중 | 낮 |

## 6. 비교 결론

| 축 | air | 공식 SDK 직접 |
|---|---|---|
| 보일러플레이트 | 적음 (도구 4개라 차이 작음) | 많음 (하지만 감당 가능한 양) |
| Pylon-7 계측 | **내장 (Meter)** | 직접 구현 필요 |
| transport 전환 | 설정 한 줄 | 코드 수정 |
| 스펙 최신성 | SDK ^1.29.0 경유 — **지연 가능성** | SDK 최신 직접 선택 가능 |
| 심사 어필 | 주최사 자체 프레임워크 사용 | 표준 준수 강조 |
| 디버깅 | 3층 | 2층 |
| 학습 비용 | air 문서 추가 학습 | 스펙 이미 [정독함](./references/mcp-spec.md) |
| 이탈 비용 | **낮음 (SDK 래퍼라 기계적 변환)** | — |

**판단**: 도구 4개 규모에서 프레임워크의 보일러플레이트 절감은 결정 근거가 되지 못한다. 채택을 정당화하는 것은 **7-Layer Meter(필수 참조 논문 계측)와 주최사 권장이라는 심사 요소** 둘이다. 반대로 가장 큰 리스크는 **스펙 리비전 지연** 하나다.

이탈 비용이 낮으므로 지금 확정할 필요가 없다. **프로토타입으로 검증하고 결정한다.**

## 7. 다음 작업 — 검증 항목 3개 (반나절)

air로 도구 1개(`vector_search` 스켈레톤, DB 연결 없이 고정 응답)만 만들어 확인한다.

1. **설치·실행되는가** — `npx @airmcp-dev/cli create`, `npm install`, stdio로 기동, MCP 클라이언트에서 `tools/list`·`tools/call` 응답 확인
2. **어느 스펙 리비전으로 말하는가** — 실제 주고받는 JSON-RPC 메시지를 캡처해 `_meta.io.modelcontextprotocol/*` 필드 유무와 `initialize` 핸드셰이크 여부 확인. 무상태(2026-07-28) vs 세션 기반(구 리비전) 판별
3. **Meter가 우리 도구명에서 동작하는가** — `layer` 수동 지정이 되는지, 계측 출력을 꺼낼 수 있는지

**1이 실패하거나 2가 구 리비전으로 확인되고 그것이 심사 기준에 걸린다고 판단되면 공식 SDK로 전환한다.** air가 SDK 래퍼이므로 전환 시 도구 로직은 그대로 재사용된다.
