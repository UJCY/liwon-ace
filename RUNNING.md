# 실행 안내 — 처음부터, 그리고 지우고 다시

이 문서는 **아무것도 없는 상태에서 시연까지** 가는 길과, **이미 돌려 본 뒤 지우고 다시** 하는 길을 따로 적는다.

`README.md` 의 재현 절은 요약이고, 여기가 전문이다.

---

## 0. 사전 준비 — 한 번만 하면 되는 것

### 0-1. 필요한 것

| | 버전 | 확인 |
|---|---|---|
| Docker | — | `docker --version` |
| Node.js | 22+ (측정은 22.17.0) | `node -v` |
| Python | 3.14 (표준 라이브러리만) | `python3 -V` |
| Ollama | 0.31.2 | `ollama --version` |

### 0-2. 모델 두 개를 받는다

```bash
ollama pull gemma4:e2b-it-qat     # 생성 LLM · 약 1.7GB
ollama pull bge-m3                # 임베딩 · 약 1.2GB
```

받았는지 확인:

```bash
curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"'
```

`gemma4:e2b-it-qat` 과 `bge-m3` 가 둘 다 보여야 한다.

### 0-3. 저장소 의존성

```bash
cd ~/workspace/alt/liwon-ace
npm install
npm run build
```

`npm run build` 는 `src/*.ts` 를 `dist/` 로 컴파일한다. **`dist/` 가 없으면 시연 스크립트가 안 돈다** — `scripts/demo.mjs` 는 `dist/agent/*.js` 를 부른다.

---

## 1. 처음부터 — 데이터베이스 세우기

### 1-1. 컨테이너를 띄운다

```bash
docker run -d --name cx-pg \
  -e POSTGRES_PASSWORD=cx \
  -e POSTGRES_DB=companyx \
  -p 55432:5432 \
  pgvector/pgvector:pg16
```

포트가 **55432** 인 것에 주의한다. 기본 5432 가 아니다 (`src/db.ts` 의 기본값과 맞춰져 있다).

**준비될 때까지 기다린다** — 컨테이너가 뜨자마자 접속되지 않는다:

```bash
until docker exec cx-pg pg_isready -U postgres -d companyx >/dev/null 2>&1; do sleep 1; done
echo "준비 완료"
```

### 1-2. 스키마와 데이터를 넣는다

> **README 에 이 단계가 빠져 있다.** `load_pg.py` 는 기본 테이블이 이미 있다고 전제하므로,
> 이걸 건너뛰면 다음 단계에서 실패한다.

```bash
docker exec -i cx-pg psql -U postgres -d companyx -v ON_ERROR_STOP=1 \
  < companyx-dataset-v1.0/sql/01-schema.sql

docker exec -i cx-pg psql -U postgres -d companyx -v ON_ERROR_STOP=1 \
  < companyx-dataset-v1.0/sql/02-data.sql
```

확인:

```bash
docker exec cx-pg psql -U postgres -d companyx -c "\dt"
```

`clients` · `contracts` · `departments` · `document_chunks` · `employees` · `products` ·
`projects` · `sales` · `support_tickets` **9개**가 보여야 한다.
(`nodes` · `edges` 는 다음 단계에서 생긴다.)

### 1-3. 문서 임베딩과 그래프를 적재한다

```bash
python3 harness/build/load_pg.py
```

**Ollama 가 떠 있어야 한다** — 문서 40건을 `bge-m3` 로 임베딩한다. 1~2분 걸린다.

이 스크립트가 하는 일 셋:

1. `document_chunks.embedding` 을 `vector(768)` → `vector(1024)` 로 바꾼다
   (배포 스키마의 768 은 `nomic-embed-text` 기준이고 우리는 `bge-m3` 를 쓴다)
2. 문서 40건을 600자 · stride 500 으로 잘라 임베딩해 넣는다
3. `nodes` · `edges` 테이블을 만들고 그래프 JSON 을 넣는다

확인:

```bash
docker exec cx-pg psql -U postgres -d companyx -tAc \
  "select 'chunks='||(select count(*) from document_chunks)
        ||' nodes='||(select count(*) from nodes)
        ||' edges='||(select count(*) from edges)"
```

**`chunks=40 nodes=133 edges=354`** 가 나와야 한다.

---

## 2. 돌아가는지 확인

### 2-1. MCP 프로토콜이 오가는가 (30초)

```bash
node scripts/smoke.mjs
```

`tools/list — 4개` 와 `연기 시험 통과` 가 나오면 된다. 정확도는 여기서 재지 않는다.

### 2-2. 질문 하나 던져 보기

```bash
npm run agent -- "Client-A가 사용 중인 제품 목록은?"
```

```
[ask] status=single routed_to=knowledge_graph matched_rule=...
답변가능: 예
확인된 답: Product-C3, Product-S1
```

**첫 실행은 20초쯤 걸린다** — 모델을 메모리에 올리는 시간이다. 두 번째부터 2~3초다.

---

## 3. 시연 스크립트

### 3-1. 재현 검사 — 촬영 전에 반드시 (약 1분)

```bash
node scripts/demo.mjs --verify
```

6문항을 **회차마다 새 세션으로** 3번 돌려 같은 답이 나오는지 본다.

**정답인지는 안 본다.** 이 검사가 답하는 것은 *"녹화할 때 화면이 점검할 때와 같겠는가"* 하나다.
재현되면서 틀릴 수 있고, 실제로 그런 사고가 있었다 — `smoke.mjs` 의 `서울 지역 고객사` 는
한 세션 안에서 일관되게 **틀린 답**을 냈다. 정확성은 원본 데이터와 따로 대조해야 한다.

통과하면 **무엇을 몇 개 쟀는지**가 함께 찍힌다:

```
대조 — 문항 6 × 3회 (회차마다 새 세션)
  결정적 축   36/36   ← envelope_status · routed_to · matched_rule · flat_status · verdict · context_json
  생성 표면   변주 0건
```

`36 = 문항 6 × 필드 6` 이다. 분모가 보여야 "다 대조하고 통과"와 "아무것도 안 쟀다"가 구별된다.

- `3회 연속 동일 — 통과` 가 나와야 촬영한다.
- `서명 불일치` 가 나오면 **그 문항을 바꾸지 말고 원인부터 본다.** 갈린다는 건 우리가 모르는 게 있다는 뜻이다.
- `문구 변주` 는 실패가 아니다 — 판정을 바꾸지 않는 문장 표현 차이라 보고만 한다.

**첫 문항이 12초쯤 나오면 콜드 실행이다.** 다음 단계로 해결된다.

### 3-2. 워밍업 — 촬영 직전 (약 6초, **조건부**)

> **`--verify` 를 방금 돌렸으면 건너뛰어도 된다.** verify 는 18회(6문항 × 3회)를 출하 경로로
> 태우므로 그 자체가 워밍업이다. 다만 Ollama 는 마지막 호출로부터 5분 뒤 모델을 내리므로,
> **verify 끝나고 5분이 지났으면** 다시 돌린다. 애매하면 그냥 돌려라 — 6초고 손해가 없다.

```bash
node scripts/demo.mjs --warm
```

모델 적재를 **촬영 밖에서** 끝낸다. 이걸 건너뛰면 첫 구간이 모델 적재 21초를 먹고,
스크립트는 절대 시각 스케줄이라 기다려 주지 않아 **그 구간의 읽을 시간이 사라진다.**

> **5분 안에 본편을 시작한다.** Ollama 의 `keep_alive` 기본값이 5분이라 사이가 벌어지면
> 모델이 다시 내려간다. 늦어졌으면 `--warm` 을 한 번 더 돌린다.

### 3-3. 본편

```bash
node scripts/demo.mjs
```

키 입력 없이 끝까지 자동으로 흐른다. **터미널 구간 정확히 120초** (슬라이드 4장 약 48초를 더해 약 2:48).

---

## 4. 측정 러너 — 보고서 수치를 다시 재고 싶을 때

| 명령 | 재는 것 | 소요 |
|---|---|---|
| `node scripts/agent-check.mjs` | 호출 축 · 환각 축 · 응답 축 · 유저-결과 4분류 | **5~8분** |
| `python3 harness/build/run_router.py` | 라우팅 축 (도구를 안 태운다) | 1분 |
| `python3 harness/build/run_e2e.py --set both` | 라우팅 + 실행 축 (도구를 태운다) | **8~12분** |
| `node scripts/xcheck.mjs` | 하네스 ↔ 서버가 같은 판정을 내는가 | 2분 |

**두 라우팅 숫자가 다른 것은 정상이다.** `run_router.py` 는 라우터 함수만 재고,
`run_e2e.py` 는 도구를 실제로 태운다. 엣지 세트는 병렬을 기대 라벨로 가지므로
도구를 태워야 판정이 성립한다 — 그래서 엣지 점수는 `run_e2e` 쪽이 정본이다.

---

## 5. 지우고 다시 하기

### 5-1. 어디까지 지울지 정한다

| 상황 | 지울 것 | 방법 |
|---|---|---|
| 적재만 다시 | 청크·그래프 | **5-2** |
| DB 를 통째로 | 컨테이너 + 볼륨 | **5-3** |
| 빌드가 꼬였다 | `dist/` | **5-4** |
| 모델이 이상하다 | Ollama 적재 상태 | **5-5** |

### 5-2. 적재만 다시 — 가장 흔한 경우

`load_pg.py` 는 **멱등**이다. 그냥 다시 돌리면 된다:

```bash
python3 harness/build/load_pg.py
```

안에서 `TRUNCATE document_chunks` 와 `DROP TABLE IF EXISTS edges, nodes` 를 하므로
중복이 쌓이지 않는다. **기본 테이블(`clients` 등)은 건드리지 않는다.**

### 5-3. DB 를 통째로 다시

**볼륨까지 지워야 진짜 초기화다.** `docker rm` 만 하면 익명 볼륨이 남는다.

```bash
docker rm -f cx-pg          # 컨테이너 제거
docker volume prune -f      # 딸린 익명 볼륨 제거 (주의: 다른 프로젝트 볼륨도 지운다)
```

> **`docker volume prune` 이 부담스러우면** 이 컨테이너의 볼륨만 지운다:
> ```bash
> VOL=$(docker inspect cx-pg --format '{{range .Mounts}}{{.Name}}{{end}}')
> docker rm -f cx-pg && docker volume rm "$VOL"
> ```

그다음 **1-1 → 1-2 → 1-3 을 순서대로 다시** 한다. 전부 합쳐 3~4분이다.

### 5-4. 빌드 초기화

```bash
rm -rf dist/ && npm run build
```

`node_modules` 까지 다시 하려면:

```bash
rm -rf node_modules dist/ && npm install && npm run build
```

### 5-5. 모델 적재 상태 초기화

메모리에서 내리기 (모델 파일은 남는다):

```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"gemma4:e2b-it-qat","keep_alive":0}' >/dev/null
curl -s http://localhost:11434/api/embed \
  -d '{"model":"bge-m3","input":"x","keep_alive":0}' >/dev/null
```

지금 무엇이 올라와 있는지:

```bash
curl -s http://localhost:11434/api/ps
```

모델 파일까지 지우려면 `ollama rm gemma4:e2b-it-qat` — **다시 받는 데 시간이 걸리니 꼭 필요할 때만.**

### 5-6. 로그 비우기

```bash
rm -f logs/agent-calls.jsonl
```

`logs/` 는 `.gitignore` 에 있어 저장소를 더럽히지 않는다. 지워도 코드는 다시 만든다.

---

## 6. 안 될 때

| 증상 | 원인 | 조치 |
|---|---|---|
| `psql 실패` / `relation "clients" does not exist` | **1-2 를 건너뛰었다** | 1-2 를 하고 1-3 을 다시 |
| `embed 실패` / `ECONNREFUSED 11434` | Ollama 가 안 떠 있다 | `ollama serve` 또는 서비스 시작 |
| `connect ECONNREFUSED ...:55432` | 컨테이너가 안 떠 있다 | `docker start cx-pg` |
| 첫 질문이 20초 넘게 걸린다 | 콜드 — 모델 적재 | 정상. `--warm` 으로 촬영 밖에서 끝낸다 |
| `--verify` 가 `서명 불일치` | 실행 간 판정이 갈린다 | **문항을 바꾸지 말고 원인부터.** `logs/agent-calls.jsonl` 의 `context_json` 을 본다 |
| `Cannot find module '../dist/agent/client.js'` | 빌드 안 함 | `npm run build` |
| 답이 맞는데 숫자가 이상하다 | 생성 SQL 의 값 접지 실패 | `logs/agent-calls.jsonl` 에 SQL 이 남는다. `ungrounded` 상태로 걸러지는지 확인 |

---

## 7. 한 번에 다 하기 (복사용)

아무것도 없는 상태에서 시연까지:

```bash
cd ~/workspace/alt/liwon-ace

# 모델
ollama pull gemma4:e2b-it-qat && ollama pull bge-m3

# DB
docker run -d --name cx-pg -e POSTGRES_PASSWORD=cx -e POSTGRES_DB=companyx \
  -p 55432:5432 pgvector/pgvector:pg16
until docker exec cx-pg pg_isready -U postgres -d companyx >/dev/null 2>&1; do sleep 1; done
docker exec -i cx-pg psql -U postgres -d companyx -v ON_ERROR_STOP=1 < companyx-dataset-v1.0/sql/01-schema.sql
docker exec -i cx-pg psql -U postgres -d companyx -v ON_ERROR_STOP=1 < companyx-dataset-v1.0/sql/02-data.sql
python3 harness/build/load_pg.py

# 빌드
npm install && npm run build

# 확인
node scripts/smoke.mjs
node scripts/demo.mjs --verify

# 시연
node scripts/demo.mjs --warm && node scripts/demo.mjs   # verify 직후 5분 안이면 --warm 생략 가능
```

지우고 처음부터 다시:

```bash
VOL=$(docker inspect cx-pg --format '{{range .Mounts}}{{.Name}}{{end}}')
docker rm -f cx-pg && docker volume rm "$VOL"
rm -rf dist/ logs/agent-calls.jsonl
# 그다음 위 블록을 `ollama pull` 부터 다시
```
