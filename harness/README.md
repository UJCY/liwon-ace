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
│   ├── run_answer.py       ← 답변 규약 8문항을 두 축으로 채점한다
│   ├── router.py           ← 판별 함수 (두 러너가 공유)
│   ├── tools.py            ← vector_search · knowledge_graph 실행부
│   ├── load_pg.py          ← 문서 청크·임베딩·그래프를 PostgreSQL 에 적재
│   └── run_e2e.py          ← 도구까지 태워 실행 축을 잰다
├── assets/                 ← 파생 자산은 손으로 고치지 않는다. 저작 자산은 _provenance 로 표시
│   ├── schema-annotated.sql
│   ├── column-values.json
│   ├── surface-gate.json
│   ├── tool-signatures.json
│   ├── model.json
│   └── prompts/
│       ├── nl2sql.md
│       └── agent-answer.md
└── tests/
    ├── nl2sql-dev.json      ← 48문항. 하네스 튜닝은 이것만 보고 한다
    ├── nl2sql-holdout.json  ← 48문항. 하네스마다 한 번씩만 잰다
    └── answer-protocol.json ←  8문항. 인접 사실이 답처럼 보이도록 만든 유혹 케이스
```

## 자산

| 파일 | 무엇인가 | 쓰이는 곳 |
|---|---|---|
| `schema-annotated.sql` | DDL 각 컬럼 줄 끝에 **실제 값 목록과 단위**를 `--` 주석으로 붙인 것 | `nl2sql` 프롬프트 |
| `column-values.json` | 저카디널리티 컬럼의 실제 값 (19개 컬럼) | 위 생성 입력 · 라우터 게이트 |
| `surface-gate.json` | 테이블 표층형 8개 + 컬럼의 한국어 값 | 라우터 **거절 게이트** |
| `tool-signatures.json` | 도구 3종의 능력 서술 각 1문장. **사람이 썼다** — D11-1 표를 문장화한 것이고 데이터셋에서 도출된 것이 아니다 | 라우터 **도구 선택** (임베딩) |
| `model.json` | 모델명·호출 옵션·임계값 | 전 호출 지점 |

**`surface-gate.json`은 도구 선택에 쓰지 않는다.** 게이트는 "스키마 어휘가 걸렸는가"만 본다 —
어느 식별자에 걸렸는지는 보지 않으므로 정밀할 필요가 없다.
도구 선택은 `tool-signatures.json` 임베딩이 한다 ([design.md](../docs/design.md) D12).

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

## 자산 재생성

```bash
python3 harness/build/build_assets.py
```

**파생 자산의** 입력은 `companyx-dataset-v1.0/` 의 스키마와 데이터뿐이다. 저작 자산(`tool-signatures.json` · `model.json` · 게이트의 `tables`)은 사람이 쓴 것을 그대로 덤프하며, 그 오염은 [harness-evaluation.md](../docs/harness-evaluation.md) 6절에 기록돼 있다.
`questions.json` 과 `edge-set/` 은 입력에 들어가지 않는다 ([design.md](../docs/design.md) D7).

## 채점

```bash
python3 harness/build/run_nl2sql.py --set holdout --harness annotated
```

```bash
python3 harness/build/run_router.py     # 회귀 26/30 · 엣지 라우팅 21/29
                                        # 실행 축 16/29 는 포화 상한이다 — 러너가 함께 출력한다
python3 harness/build/run_answer.py     # 형식 축 8/8 · 판정 축 7/8
python3 harness/build/load_pg.py        # 측정 전 1회 — 청크·그래프 적재
python3 harness/build/run_e2e.py        # 라우팅 22/29 · 실행 22/29 (상한 23)
```

`--harness bare | blocks | annotated` 로 세 구성을 비교할 수 있다.
PostgreSQL 컨테이너와 Ollama 가 떠 있어야 한다 — 준비 절차는
[`docs/harness-evaluation.md`](../docs/harness-evaluation.md) 5절.

## 테스트 세트를 쓰는 규칙

- **`nl2sql-dev.json` 만 보고 하네스를 고친다.**
- **`nl2sql-holdout.json` 은 하네스 하나당 한 번만 돌린다.** 실패를 보고 고치면 그 순간 홀드아웃이 아니다.
- 두 세트의 점수 **격차**를 기록한다. 격차가 벌어지면 과적합이다.
- 기준 SQL은 사람이 쓴 것이다. 틀렸다고 판단되면 **하네스가 아니라 기준을 고치고**, 고친 사실을 커밋에 남긴다.
