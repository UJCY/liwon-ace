# 자체 엣지 세트

> 구조 엣지케이스를 검증하기 위해 **우리가 직접 작성**하는 질문 세트다. 케이스 유형에서 만들고 데이터셋 인스턴스에서 역산하지 않는다 ([design.md](../docs/design.md) **D7**, [edge-cases.md](../docs/edge-cases.md)).
>
> `companyx-dataset-v1.0/questions.json` 30개는 **회귀 전용**이고 이 세트와 용도가 다르다. 30개는 "기존 동작이 깨졌는가"를, 이 세트는 "케이스 유형을 처리하는가"를 잰다.

| 파일 | 내용 |
|---|---|
| `README.md` | 스키마 · 케이스 매트릭스 · 작성 절차 · 역산 방지 규약 · 채점 규약 · 검증 스니펫 |
| `persona-cards.md` | 문면 생성 입력 — 페르소나 카드 4장 |
| `edge-questions.json` | 문항 실물 (1차 29문항) |

---

## 1. 스키마

`questions.json`의 `{q, tool, hint}`로는 이 세트를 담을 수 없다. **R1 거절**(도구 0개)·**X5 부분 응답**·**병렬 병합**(도구 2개)·**T5 개체 부재**는 "기대 도구 1개"로 표현되지 않기 때문이다. 그래서 기대값을 **도구 배열 + 응답 상태** 두 필드로 나눈다.

```jsonc
{
  "id": "X5-03",
  "q": "…",                          // 한국어 1문장
  "case": "X5",                      // X1 X2 X3 X4 X5 R1 R5 T5 OP
  "subcase": "T7",                   // 아래 어휘표. 없으면 null
  "expected": {
    "routing": ["knowledge_graph"],  // 기대 도구 배열. 병렬=2개, 거절=[]
    "response": "partial"            // 아래 어휘표
  },
  "provenance": {
    "structure_basis": "그래프 격자: employee 43/45 LEADS 결손 (dataset-analysis 3장)",
    "written_by": "generated",       // manual | generated
    "notes": null
  }
}
```

### `case` 어휘

| 값 | 뜻 | 카탈로그 |
|---|---|---|
| `X1` | 관계를 세는 집계 (동일 중복) | [edge-cases.md](../docs/edge-cases.md) X1 |
| `X2` | 관계를 따라가는 조회 (동일 중복) | X2 |
| `X3` | 사건 목록 + 원인 서술 (상보 중복) | X3 |
| `X4` | 개체 지목 서술 (상보 중복) | X4 |
| `X5` | 요구 형태 미충족 → 부분 응답 | X5 |
| `R1` | 무매칭 → 거절 | R1 |
| ~~`R4`~~ | ~~의존(멀티홉) 질문~~ — **폐기 (2026-08-19)**. 두 문항은 `X3`·`X2`로 재라벨됐다 | [edge-cases.md](../docs/edge-cases.md) R4 |
| `R5` | 표층 문자열 충돌 | R5 |
| `T5` | 개체 자체가 없음 | T5 |
| `OP` | 연산 축 (최상급·비교·시간·부정) | [question-taxonomy.md](../docs/references/question-taxonomy.md) 10.3 |

### `subcase` 어휘

| `case` | 허용 값 |
|---|---|
| `X5` | `T4-entity`(문서에 개체 없음) · `T4-form`(개체는 있고 형태만 없음) · `T7`(관계 부재) · `T3`(테이블 0행) |
| `OP` | `superlative` · `comparison` · `temporal` · `negation` |
| 그 외 | `null` |

### `expected.response` 어휘

| 값 | 뜻 | 근거 |
|---|---|---|
| `single` | 도구 1개가 정상 결과를 낸다 | D3 |
| `parallel_merge` | 후보 2개를 병렬 호출하고 병합한다 | D3 · X3 · X4 |
| `partial` | 도구·개체는 맞고 요구 형태만 없다 → 부분 응답 | D10 · X5 |
| `out_of_scope` | 후보 도구가 없다 → 구조화 거절 | D6 · R1 |
| `entity_not_found` | 개체 자체가 그래프에 없다 | T5 |
| `ambiguous_entity` | 개체 이름이 여럿을 가리킨다 (동명이인) | T8 |
| ~~`r4_defined_state`~~ | ~~의존 탐지 상태~~ — **폐기 (2026-08-19)**. 이 값을 쓰는 문항은 없다 | — |

> **`r4_defined_state`는 폐기됐다 (2026-08-19).** 열린 항목이 닫히기를 기다리던 이 라벨은 **케이스 자체가 폐기**되면서 함께 사라졌다. R4의 두 소재가 멀티홉이 아니었고(테이블 조인 1회), 표층으로도 임베딩으로도 X4와 구분되지 않았다 ([edge-cases.md](../docs/edge-cases.md) R4 행). **문면은 고치지 않았다** — 바뀐 것은 라벨뿐이고 그 근거를 `provenance.notes`에 남겼다.

---

## 2. 채점 규약

엣지 세트는 **2축으로 잰다** — 라우팅 축과 실행 축. 하나의 점수로 합치지 않는다. **2축 채점은 엣지 세트 고유다** — 회귀(`questions.json`)는 라우팅 축만 채점하고 실행 상태는 라벨 없이 관측한다 ([design.md](../docs/design.md) D18).

| 축 | 채점 방법 |
|---|---|
| **라우팅 축** | `expected.routing`과 실제 호출 도구의 **집합 일치**. 순서는 보지 않는다. 빈 배열(`[]`)이면 "도구를 호출하지 않았는가"를 본다 |
| **실행 축** | `expected.response`와 실제 응답 상태의 **문자열 일치** |

**LLM 판정자(judge)를 쓰지 않는다.** 기대값이 결정적 라벨이라 검증이 집합·문자열 비교로 끝난다. LLM 판정은 position·verbosity·self-enhancement bias(MT-Bench, NeurIPS 2023 D&B)와 self-preference(Panickssery et al., NeurIPS 2024)를 끌어들이는데, 우리는 그 문제를 **스키마 설계로 원천 회피**한다 ([related-work.md](../docs/references/related-work.md) 6.2·6.6).

**회귀 러너는 이 범위가 아니다.** 규칙을 고칠 때마다 29+30을 다시 돌리는 결정적 스크립트는 **판별 함수가 생기는 시점**에 만든다.

---

## 3. 케이스 매트릭스 (골격)

**골격이 문면보다 먼저 확정된다.** 아래 표는 어떤 케이스를 몇 개 만들지와 **소재를 무엇으로 고를지**를 정한 것이고, 문면(`q`)은 여기서 나온다.

소재 선택 규칙은 **재량을 없애려고** 쓴 것이다 — "적당한 직원", "적당한 고객사"를 고르는 순간 그 선택의 출처가 흐려진다. 규칙은 전부 `dataset-analysis.md`의 재현 스니펫으로 확정했다 (§7 참조).

| id | 소재 선택 규칙 | routing | response |
|---|---|---|---|
| `X1-01` `X1-02` | 관계 카운트 최대. 관계는 `LEADS`·`USES` 고정 | `[knowledge_graph]` | `single` |
| `X2-01` | 관계 단독 순회. `BELONGS_TO` 고정 | `[knowledge_graph]` | `single` |
| `X2-02` | 관계 + 정형 속성 동반 (`MANAGES_ACCOUNT` + `amount`) — D9 우선순위 검증 | `[nl2sql]` | `single` |
| `X3-01` `X3-02` | 사건 목록 + 원인 서술 동시 요구. 주제는 **`support_tickets.title` 28종 중 첫 토큰이 장애보고서 본문에 등장하는 10종을 사전순 정렬해 앞에서 2개** → `API 응답 지연` · `DB 연결 타임아웃` | `[nl2sql, vector_search]` | `parallel_merge` |
| `X3-03` | **존재 확인 단독** (경계 대조 — 요구 원소 1개면 병렬이 아니다, D11-4). 위 목록의 3번째 → `Pod 재시작 반복` | `[vector_search]` | `single` |
| `X4-01` `X4-02` | 개체 지목: 관계 사실 + 서술 동시 요구. 개체는 **문서가 커버하는 고객사 15개 중 앞에서 2개** → `Client-A` · `Client-B` | `[knowledge_graph, vector_search]` | `parallel_merge` |
| `X5-01` | 문서 미커버 고객사의 서술 요구. **미커버 구간(`Client-P`~`Client-AD`)의 첫 개체** → `Client-P` | `[vector_search]` | `partial` (`T4-entity`) |
| `X5-02` | 커버된 개체의 없는 형태. `Product-C1`은 **설치 가이드만** 보유 → API를 묻는다 | `[vector_search]` | `partial` (`T4-form`) |
| `X5-03` `X5-04` | 관계 부재(T7). **`LEADS` 결손 직원 중 그래프 격자 스니펫 출력 순 첫 2명** → `employee_1`(윤소연) · `employee_4`(박성민) | `[knowledge_graph]` | `partial` (`T7`) |
| `X5-05` | 테이블 0행(T3). **`projects` 결손 고객사 8개 중 알파벳 순 첫 개체** → `Client-A` | `[nl2sql]` | `partial` (`T3`) |
| `R1-01` `R1-02` `R1-03` | 스몰토크 1 · 일반 지식 1 · 데이터 인접이나 범위 밖 1 | `[]` | `out_of_scope` |
| ~~`R4-01`~~ `R4-02` | ~~2홉 의존~~ → **재라벨 (2026-08-19)**: `R4-01`은 `X3`, `R4-02`는 `X2`. 두 소재 모두 테이블 조인 한 번으로 닿아 멀티홉이 아니었다 | `[nl2sql, vector_search]` / `[nl2sql]` | `parallel_merge` / `single` |
| `R5-01` `R5-02` `R5-03` | 표층 충돌. `REPORTED_ISSUE`의 "이슈"(서술 요구) · `HAS_PROJECT`의 "프로젝트"(속성 요구) · `status`의 "상태"(서술 요구) | `[vector_search]` / `[nl2sql]` / `[vector_search]` | `single` |
| `T5-01` `T5-02` | 미존재 개체. 한국어 상호형 1 (**`#23`의 "서울물산"은 재사용 금지** — 그 인스턴스를 피한다) · 합성 패턴 초과형 `Client-ZZ` 1 | `[knowledge_graph]` | `entity_not_found` |
| `OP-01` | 최상급 단독 (집계 없는 argmax — 속성 정렬) | `[nl2sql]` | `single` (`superlative`) |
| `OP-02` | 속성 비교 (>, <) | `[nl2sql]` | `single` (`comparison`) |
| `OP-03` | 시간 제약 + 정형 속성 | `[nl2sql]` | `single` (`temporal`) |
| `OP-04` | **시간 + 사건 + 서술 복합** — question-taxonomy 10.2 (3)이 지적한 "최근"이 걸리는 지점. 구조상 X3 정의와 일치한다. 주제는 `X3`와 **같은 기계 목록의 4번째** → `SSL 인증서 만료 알림` | `[nl2sql, vector_search]` | `parallel_merge` (`temporal`) |
| `OP-05` | 부정·차집합 ("~않은 / 없는") | `[nl2sql]` | `single` (`negation`) |

**합계 29문항** — `X1` 2 · `X2` **3** · `X3` **4** · `X4` 2 · `X5` 5 · `R1` 3 · `R5` 3 · `T5` 2 · `OP` 5.
(2026-08-19 재라벨 후. `R4` 2문항이 `X2`·`X3`로 옮겨졌고 문항 수와 문면은 그대로다.)

### 1차 범위에서 뺀 것

`T1`(유효하지 않은 SQL) · `T2`(SELECT 외 구문) · `T6`(DB 연결 실패) · `Q1`~`Q4`(응답 품질·라우터 우회)는 **질문 세트로 검증되는 유형이 아니다.** 질문을 아무리 잘 써도 T1은 LLM이 SQL을 어떻게 뽑느냐에 달렸고, Q4는 에이전트의 호출 로그로 재는 항목이다. 이들은 **구현·통합 테스트**로 옮긴다. 1차 기준은 **규칙 판별 함수에 직접 걸리는 유형**이다.

---

## 4. 작성 절차

1. **골격 선커밋** — 이 README + `persona-cards.md`. 위 매트릭스에 `q`는 없다.
2. **문면 생성** — 문항마다 프롬프트 = 페르소나 카드 1장 + 골격 의미 명세 + "한국어 구어 1문장". 모델은 로컬 `exaone3.5:2.4b` 1차, 품질 미달 시 `gemma4:e2b-it-qat`, 그래도 미달이면 수동(`written_by: "manual"`). **프롬프트에 `questions.json`을 넣지 않는다.** 문항당 후보 3개를 뽑는다.
3. **선별** — 기준은 둘뿐이다: ① 골격 의미를 보존하는가 ② 자연스러운가. **표층이 회귀 30개와 닮았는지로 고르거나 버리지 않는다** — 그 판단 자체가 30개를 다시 보는 일이고 역산이다. **라벨(`expected`)은 생성 후 수정하지 않는다.** 문면이 라벨과 안 맞으면 라벨이 아니라 문면을 버린다.
4. **검증** — 아래 스니펫 3종을 돌리고 결과를 기록한 뒤 커밋.

### 생성 프롬프트 템플릿 (실물)

```
너는 사내 데이터 검색 시스템에 질문하는 사용자다.

[사용자]
{persona_card}

[물어볼 것]
{skeleton_spec}

위 사람이 할 법한 질문을 한국어 한 문장으로 써라.
- 질문만 출력한다. 설명·번호·따옴표를 붙이지 않는다.
- [물어볼 것]의 의미를 바꾸지 않는다. 조건을 더하거나 빼지 않는다.
- 스키마 용어를 그대로 베끼지 말고 사람이 쓰는 말로 바꿔라.
```

`{skeleton_spec}`은 매트릭스 행의 **의미 명세**다 (예: *"직원 '윤소연'이 이끄는 프로젝트가 무엇인지"*). 라벨(`expected`)은 프롬프트에 넣지 않는다 — 모델이 정답 형태를 알 필요가 없다.

---

## 5. 역산 방지 규약

D7이 금지하는 것은 **개별 질문에서 규칙을 역산하는 일**이다. 이 세트가 그 규칙을 지켰다는 것을 아래 다섯으로 남긴다.

1. **입력 감사** — 생성 입력 전체(페르소나 카드 · 골격 매트릭스 · 프롬프트 템플릿)가 커밋에 실물로 있고, 그 안에 `questions.json`이 없다.
2. **커밋 순서** — 골격 → 문면 → (미래) 규칙 판별 함수. git 히스토리가 증거다. 골격이 문면보다 먼저 커밋됐다는 사실은 나중에 바꿀 수 없다.
3. **출처 필드 강제** — 전 문항이 `provenance.structure_basis`를 갖는다. **스키마·격자 사실만** 인용할 수 있고 `questions.json` 참조는 금지다. 검증 스니펫 ①이 빈 값을 거부한다.
4. **기계 대조** — 회귀 30개와의 문자 3-gram 자카드 최대값을 재고 **0.5 미만**을 요구한다(스니펫 ③). 초과 쌍은 문면을 재생성한다.
5. **한계 정직 기록** — **골격 작성자가 30개를 이미 읽었다는 오염은 제거되지 않았다.** D9-a 주의 항과 같은 한계다. 위 넷이 배제하는 것은 **표절형 역산**(문면을 베끼는 것)이고, "케이스 유형을 떠올린 머리가 30개를 본 적 있다"는 사실은 남는다. 그래서 주장은 **"골격의 출처는 스키마와 케이스 카탈로그다"**까지만 한다.

---

## 6. 검증 스니펫

```bash
cd /path/to/liwon-ace
python3 - <<'EOF'
import json
from collections import Counter
qs=json.load(open('edge-set/edge-questions.json'))
CASES={'X1','X2','X3','X4','X5','R1','R5','T5','OP'}
RESP={'single','parallel_merge','partial','out_of_scope','entity_not_found'}
TOOLS={'nl2sql','vector_search','knowledge_graph'}
for x in qs:  # ① 스키마·어휘 검사
    assert x['case'] in CASES and x['expected']['response'] in RESP
    assert all(t in TOOLS for t in x['expected']['routing'])
    assert x['provenance']['structure_basis'], x['id']
print('① 스키마 OK,', len(qs), '문항')
print('② 커버리지:', dict(Counter(x['case'] for x in qs)))
b=json.load(open('companyx-dataset-v1.0/questions.json'))
ng=lambda s,n=3:{s[i:i+n] for i in range(len(s)-n+1)}
w=max(((x['q'],y['q'],len(ng(x['q'])&ng(y['q']))/max(1,len(ng(x['q'])|ng(y['q']))))
       for x in qs for y in b),key=lambda t:t[2])
print('③ 회귀 세트 최대 3-gram 자카드:', round(w[2],3), '(0.5 미만이어야 함)', w[:2])
EOF
```

| 스니펫 | 통과 조건 |
|---|---|
| ① 스키마·어휘 | 전 문항이 `case`·`response`·`routing`·`structure_basis` 어휘를 지킨다 |
| ② 커버리지 | 케이스 분포가 위 매트릭스 배분과 일치한다 |
| ③ 역산 대조 | 회귀 30개와의 최대 3-gram 자카드 < 0.5 |

### 실행 결과 (2026-08-14, 1차 29문항)

```
① 스키마 OK, 29 문항
② 커버리지: {'X1': 2, 'X2': 3, 'X3': 4, 'X4': 2, 'X5': 5, 'R1': 3, 'R5': 3, 'T5': 2, 'OP': 5}
③ 회귀 세트 최대 3-gram 자카드: 0.212 (0.5 미만이어야 함)
   ('지난 분기에 SSL 인증서 만료 때문에 어떤 장애가 있었고, 그 원인이 뭐였는지 알려줘',
    'SSL 인증서 관련 장애가 있었어?')
```

**최대값 쌍이 같은 주제를 다루면서도 0.212에 그친다** — 주제가 겹치는 것과 문면을 베끼는 것은 다르다. 임계 0.5를 넘은 쌍은 없었다.

## 7. 1차 작성 기록 (2026-08-14)

| 출처 | 문항 수 | 비고 |
|---|---:|---|
| `gemma4:e2b-it-qat` 생성 | 11 | X1-01 · X1-02 · X2-01 · X3-03 · X5-04 · R5-03 · T5-01 · OP-01 · OP-03 · OP-04 · OP-05 |
| `exaone3.5:2.4b` 생성 | 10 | X2-02 · X3-01 · X3-02 · X4-01 · R1-01 · R1-02 · R1-03 · R5-02 · T5-02 · OP-02 |
| 수동 작성 (폴백) | 8 | X4-02 · X5-01 · X5-02 · X5-03 · X5-05 · R4-01 · R4-02 · R5-01 |

문항마다 후보 3개를 뽑아 골격 의미 보존·자연스러움으로 골랐다. 1차 모델(`exaone3.5:2.4b`)이 골격을 보존하지 못한 19문항은 `gemma4:e2b-it-qat`로 재생성했고, 그래도 실패한 8문항은 수동으로 썼다. **라벨은 한 건도 고치지 않았다** — 버린 것은 전부 문면이다. 실패 사유는 문항별 `provenance.notes`에 남겼고, 대부분 두 가지였다:

1. **개체명 음차** — `Client-B`를 "클라이언트 B"로 바꿔 개체 지목이 흐려졌다 (X4-02 · X5-01 · X5-02 · X5-05 · R4-01 · R4-02).
2. **관계·표층어 교체** — "이끄는"을 "담당하는"으로(X5-03), "이슈"를 "문제"로(R5-01) 바꿔 그 문항이 재려던 것 자체가 사라졌다.

**프롬프트 템플릿은 고치지 않았다.** 위 두 실패는 "개체명을 그대로 쓰라"는 지시를 템플릿에 넣으면 줄겠지만, 템플릿은 골격과 함께 선커밋된 생성 입력이라 문면을 본 뒤에 고치면 감사 대상이 흐려진다. 대신 폴백(수동 작성)을 썼다.
