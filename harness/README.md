# 하네스 자산

> 모델 바깥의 구조 — 프롬프트 배치, 컨텍스트 구성, 호출 옵션, 출력 형식.
> **모델을 바꾸지 않고 구조만 바꿔서** `nl2sql` 실행 정확도를 홀드아웃 기준 50% → 90%로 올린 것이 이 디렉토리다.
> 측정 근거는 [`docs/harness-evaluation.md`](../docs/harness-evaluation.md).

```
harness/
├── build/
│   ├── build_assets.py     ← 데이터셋에서 자산을 결정적으로 생성한다
│   ├── run_nl2sql.py       ← 생성 SQL을 PostgreSQL에 실행해 채점한다
│   ├── run_router.py       ← 엣지 세트 29 + 회귀 30 을 나란히 채점한다
│   ├── run_answer.py       ← 답변 규약을 두 축으로 채점한다 (--set dev|holdout)
│   ├── router.py           ← 판별 함수 (두 러너가 공유)
│   ├── tools.py            ← vector_search · knowledge_graph 실행부
│   ├── load_pg.py          ← 문서 청크·임베딩·그래프를 PostgreSQL 에 적재
│   ├── run_e2e.py          ← 도구까지 태워 실행 축을 잰다
│   ├── build_unit_grid.py  ← 단위 어형 격자 76문항 생성 + 기준 단언 (#39)
│   ├── check_grounding.py  ← 0행 접지 **판정 정의의 원본** — tools.py 와 서버 nl2sql 이
│   │                          같은 판정을 쓴다 (#6). 기록된 SQL 위 오프라인 평가도 겸한다
│   ├── check_pair_signal.py ← 병렬 짝 신호 동결 검사 — 합의문 책상 검증 표 6행 (#12)
│   └── retry_unit.py       ← 접지 재시도 시뮬레이션 (dev 기각 — 위장 2)
├── assets/                 ← 파생 자산은 손으로 고치지 않는다. 저작 자산은 _provenance 로 표시
│   ├── schema-annotated.sql
│   ├── column-values.json
│   ├── column-ranges.json
│   ├── surface-gate.json
│   ├── pair-axes.json
│   ├── tool-signatures.json
│   ├── model.json
│   └── prompts/
│       ├── nl2sql.md
│       └── agent-answer.md
└── tests/
    ├── nl2sql-dev.json              ← 48문항. 하네스 튜닝은 이것만 보고 한다
    ├── nl2sql-holdout.json          ← 48문항. 하네스마다 한 번씩만 잰다
    ├── answer-protocol-dev.json     ← 16문항(아니오 8 · 예 8). 튜닝은 이것만 보고 한다
    └── answer-protocol-holdout.json ←  8문항(예 4 · 아니오 4). 하네스마다 한 번씩만 잰다
```

## 자산

| 파일 | 무엇인가 | 쓰이는 곳 |
|---|---|---|
| `schema-annotated.sql` | DDL 각 컬럼 줄 끝에 **실제 값 목록과 단위**를 `--` 주석으로 붙인 것 | `nl2sql` 프롬프트 |
| `column-values.json` | 저카디널리티 컬럼의 실제 값 (19개 컬럼) | 위 생성 입력 · 라우터 게이트 |
| `surface-gate.json` | 테이블 표층형 9낱말 + 컬럼의 한국어 값. **둘 다 파생이다** — 표층형은 `01-schema.sql` 의 `-- N. 라벨` 주석에서 **우핵 규칙**(라벨 조각의 마지막 어절을 쓴다 — `기술 지원 티켓` → `티켓`)으로 뽑는다 (이슈 #19) | 라우터 **거절 게이트** |
| `pair-axes.json` | 병렬 짝의 **목록 변**(`nl2sql` vs `knowledge_graph`)을 가르는 두 축의 어휘 (테이블 20 · 그래프 19). **새 낱말이 없다** — 게이트 표층형(파생) + `nl2sql` 시그니처 명사(저작) + `RELATION_WORDS`(저작)를 모은 것이고, 양쪽 축에 걸리는 `프로젝트` 는 기계적으로 배제한다 (이슈 #12) | 병렬 **짝 선택** (`run_e2e.py` · `src/composition.ts`) |
| `tool-signatures.json` | 도구 3종의 능력 서술 각 1문장. **사람이 썼다** — D11-1 표를 문장화한 것이고 데이터셋에서 도출된 것이 아니다 | 라우터 **도구 선택** (임베딩) |
| `model.json` | 모델명·호출 옵션·임계값 | 전 호출 지점 |
| `column-ranges.json` | 금액 4컬럼의 실측 최소·최대 (만원). **파생** — `build_unit_grid.py` 가 생성한다 | 접지 검출 — 서버 `nl2sql` 과 하네스가 **같은 파일**을 읽는다 (#6) |

**`surface-gate.json`은 거절 판단에만 관여한다 — 구조적으로.** 게이트는 "스키마 어휘가 걸렸는가"만
본다. 게이트 히트가 도구를 직접 반환하는 경로는 없다 — R5 구제가 거절 직전에 있기 때문이다
(2026-08-27, 이슈 #19). 도구 선택은 `tool-signatures.json` 임베딩이 한다
([design.md](../docs/design.md) D12).

## 세 가지 결정적 사실

**① 배치가 정보량보다 중요하다.** 값 목록과 단위를 별도 블록에 두면 홀드아웃 75%,
같은 정보를 DDL 컬럼 옆 인라인 주석으로 옮기면 90%다. 단위 문항만 보면 2/7 → 7/7이다.

**② 규칙을 더 넣으면 과적합한다.** 개발 실패를 보고 규칙 넷을 더했더니
개발 77% → 90%, 홀드아웃 88% → 81%였다 (탐색 측정). 개발·홀드아웃 격차가 그 자체로 지표다.

**③ 프롬프트는 러너가 자산에서 읽는다.** `run_nl2sql.py` 와 `run_answer.py` 는 채택안 프롬프트를
`assets/prompts/*.md` 의 첫 코드블록에서 추출한다 — 코드에 두 번째 사본을 두지 않는다.
`bare`·`blocks` 는 대조군이라 자산이 아니고 러너 안에 있다.

**④ 실행 축을 여는 것은 도구다.** `partial` 과 `entity_not_found` 는 라우터가 낼 수 없다 —
도구를 태워 빈손인지, 개체가 있는지 봐야 안다. `run_router.py` 의 실행 축은 16/29 에서
포화하고, `run_e2e.py` 는 22/29(상한 23)다.

**⑤ `think: false`를 반드시 넣는다.** 켜면 숨은 추론 토큰이 `num_predict`를 소진해
**빈 문자열**이 반환된다. 이는 T1(무효 SQL 생성)으로 오분류된다.
정확도 이득은 작고(+2/27) 지연은 6.6배다.

**⑥ `seed` 를 박는다.** `temperature: 0` 만으로는 생성이 고정되지 않는다 — 같은 프롬프트
5회에서 고유 SQL **2/5**, 답변 라벨도 뒤집힌다. `options.seed` 를 주면 둘 다 **1/5** 다.
개발 48문항 41→42, 답변 규약 8/8 · 7/8 불변. **잡음을 없앨 뿐 정답 쪽으로 붙여 주지 않는다** —
점수는 범위의 바닥으로 고정되고, 우연한 회복도 함께 사라진다
([harness-evaluation.md](../docs/harness-evaluation.md) 6절).

## 자산 재생성

```bash
python3 harness/build/build_assets.py
```

**파생 자산의** 입력은 `companyx-dataset-v1.0/` 의 스키마와 데이터뿐이다. 저작 자산(`tool-signatures.json` · `model.json`)은 사람이 쓴 것을 그대로 덤프하며, 그 오염은 [harness-evaluation.md](../docs/harness-evaluation.md) 6절에 기록돼 있다.
`questions.json` 과 `edge-set/` 은 입력에 들어가지 않는다 ([design.md](../docs/design.md) D7).

## 채점

```bash
python3 harness/build/run_nl2sql.py --set holdout --harness annotated
```

```bash
python3 harness/build/run_router.py     # 회귀 26/30 · 엣지 라우팅 22/29
                                        # 실행 축 16/29 는 포화 상한이다 — 러너가 함께 출력한다
python3 harness/build/run_answer.py     # dev 16 — 형식 16/16 · 판정 15/16 (예 8/8 · 아니오 7/8)
                                        # (--set holdout 은 하네스당 1회 — 아래 규칙)
node scripts/dump-fixtures.mjs --check harness/tests/answer-protocol-dev.json \
                               harness/tests/answer-protocol-holdout.json
                                        # 픽스처가 출하 경로와 갈라졌는지 — 결정적 문항만
python3 harness/build/check_pair_signal.py  # 병렬 짝 신호 6/6 — 합의문 책상 검증 표. 인프라 불필요
python3 harness/build/load_pg.py        # 측정 전 1회 — 청크·그래프 적재
python3 harness/build/run_e2e.py        # 엣지 라우팅 27/29 · 실행 27/29 · 회귀 24~25/30
                                        # 회귀가 구간인 것은 #10 의 nl2sql 이 실행마다 갈려서다 (6절 · 4.3)
                                        # 병렬 짝 로그도 함께 낸다 — 신호가 고른 짝 / 실행 후 확정 (#12)
node scripts/agent-check.mjs            # 에이전트 3축 — 호출·환각·응답. 수치는 docs/harness-evaluation.md 7절
node scripts/xcheck.mjs                 # 하네스↔서버 대조 — 결정적 52/52 · LLM 결합 7 (결정적 부분필드 7/7)
```

`--harness bare | blocks | annotated` 로 세 구성을 비교할 수 있다.
PostgreSQL 컨테이너와 Ollama 가 떠 있어야 한다 — 준비 절차는
[`docs/harness-evaluation.md`](../docs/harness-evaluation.md) 5절.

## 테스트 세트를 쓰는 규칙

- **`*-dev.json` 만 보고 하네스를 고친다** — `nl2sql`·`answer-protocol` 공통이다.
- **`*-holdout.json` 은 하네스 하나당 한 번만 돌린다.** 실패를 보고 고치면 그 순간 홀드아웃이 아니다.
  `run_answer.py` 의 기본값이 dev 인 것이 이 규칙의 집행 장치다 — holdout 은 `--set holdout` 으로만 돈다.
- 두 세트의 점수 **격차**를 기록한다. 격차가 벌어지면 과적합이다.
- 기준 SQL은 사람이 쓴 것이다. 틀렸다고 판단되면 **하네스가 아니라 기준을 고치고**, 고친 사실을 커밋에 남긴다.

### answer-protocol 전용 — 픽스처는 출하 경로에서 뜬다

- 문항에서 **저작 필드는 `q`·`expected`·`required_regex`·`forbidden_regex`** 다.
  **`tool_result` 와 `tool` 은 파생이다** — 손으로 쓰지 않고
  `node scripts/dump-fixtures.mjs <파일>` 로 뜬다. 출하 경로(`ask` → `flatten`)가
  실제로 내는 봉투가 픽스처가 된다 (#21). 손으로 쓴 봉투는 반환 형태가 바뀌어도
  조용히 갈라진다 — 실제로 8문항 중 5개가 어느 구현도 내지 않는 모양이었다.
- `node scripts/dump-fixtures.mjs --check <파일>` 은 결정적 도구
  (`vector_search`·`knowledge_graph`·무도구 거절) 문항을 다시 떠서 파일과 다르면
  실패한다. `nl2sql` 문항은 생성 SQL 이 흔들려 check 에서 뺀다 — 대조의
  `DETERMINISTIC` 과 같은 이유고, 봉투는 캡처 시점에 동결된다.
- holdout 을 저작할 때 생성기로 봉투를 보는 것은 허용이다 — 봉투는 측정 대상이
  아니라 입력이다. 금지는 holdout **점수**를 보고 하네스를 고치는 것이다.
