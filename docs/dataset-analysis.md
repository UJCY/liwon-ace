# 데이터셋 실측 분석

> 조사 시점 2026-08-12. `companyx-dataset-v1.0` 실물과 과제 출처 3곳을 직접 대조한 **사실 기록**이다.
> 이 문서는 판단을 담지 않는다 — 여기서 도출한 설계 결정은 [design.md](./design.md), 케이스는 [edge-cases.md](./edge-cases.md)에 있다.

## 1. 자산 규모

| 자산 | 규모 |
|---|---|
| 테이블 8개 | departments 6 / employees 45 / clients 30 / products 12 / contracts 65 / projects 40 / sales 500 / support_tickets 120 = **818행** |
| 그래프 | 노드 **133** (employee 45, project 40, client 30, product 12, department 6) / 엣지 **354** |
| 문서 | **40건** — incident_report 10 / technical_doc 10 / meeting_note 10 / proposal 10 |
| 예시 질문 | **30개** — nl2sql 10 / vector_search 10 / knowledge_graph 10 |

## 2. 그래프는 테이블에서 100% 도출된다

관계 7종 전부를 테이블에서 도출해 **집합 단위로 대조**했다. 7종 모두 일치한다.

| 관계 | 엣지 수 | 도출 원본 | 대조 결과 |
|---|---:|---|---|
| BELONGS_TO | 45 | `employees.dept_id` (45행) | **집합 일치** |
| HEAD_IS | 6 | `departments.head_id` (UPDATE 6건) | **집합 일치** |
| HAS_PROJECT | 40 | `projects.client_id` (40행) | **집합 일치** |
| LEADS | 40 | `projects.manager_id` (40행) | **집합 일치** |
| USES | 61 | `contracts` DISTINCT(client_id, product_id) | **집합 일치** |
| MANAGES_ACCOUNT | 63 | `contracts` DISTINCT(manager_id, client_id) | **집합 일치** |
| REPORTED_ISSUE | 99 | `support_tickets` DISTINCT(client_id, product_id) | **집합 일치** |

노드도 마찬가지다. 5개 유형(employee / project / client / product / department)이 **전부 동명 테이블로 존재**하고, `properties`는 컬럼의 부분집합이다 (`client_1`의 industry·region·size ↔ `clients` 테이블 컬럼). 노드 `name` 값도 테이블 `name`과 완전히 동일하다.

**결론: 그래프는 새 정보를 담고 있지 않다. 테이블 관계의 비정규화 재표현이다.** knowledge_graph 질문 10개는 전부 SQL로도 답할 수 있다.

### 재현

```bash
cd companyx-dataset-v1.0
python3 -c "
import re,json
s=open('sql/02-data.sql').read()
e=json.load(open('graph/edges.json')); e=e['edges'] if isinstance(e,dict) else e
eset=lambda r:{(x['source'],x['target']) for x in e if x['relation']==r}
c=[tuple(map(int,re.match(r'\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)',m.group(1)).groups()))
   for m in re.finditer(r'INSERT INTO contracts \([^)]*\) VALUES \(([^;]*)\);', s)]
print('USES           :', {('client_%d'%a,'product_%d'%b) for _,a,b,_ in c}==eset('USES'))
print('MANAGES_ACCOUNT:', {('employee_%d'%d,'client_%d'%a) for _,a,b,d in c}==eset('MANAGES_ACCOUNT'))
"
```

## 3. 문서는 유일하게 고유한 자산이다 — 단 개체는 겹친다

문서가 담은 것은 **서술**이다: 장애 원인·조치, 설치 절차, 회의 결정, 제안 내용. 테이블·그래프 어디에도 없다.

그런데 **문서 40건 전부가 그래프 개체를 언급한다.**

| 문서 유형 | client | product | employee | department | 고정 구조 |
|---|---|---|---|---|---|
| incident_report | 10/10 | 10/10 | 10/10 | 10/10 | 기본정보·장애내용·원인분석·조치사항·복구시간·담당자 |
| technical_doc | 0 | 10/10 | 0 | 0 | 제품별 5개 주제(설치/아키텍처/운영/성능/API) × 2 |
| meeting_note | 10/10 | 0 | 10/10 | 0 | 기본정보·안건·결정사항·다음회의 |
| proposal | 10/10 | 10/10 | 0 | 0 | 현황분석·솔루션·구축계획·투자비용·기대효과 |

### 문서 커버리지는 "개체 × 형태" 격자로 봐야 한다

개체 단위로 세면 절반이다.

| | 문서가 커버 | 전체 | 커버 안 되는 것 |
|---|---|---|---|
| 고객사 | **15** (Client-A ~ Client-O) | 30 | Client-P ~ Client-AD |
| 제품 | **10** | 12 | 2건 |

그런데 **커버된 개체도 형태는 한 칸씩만** 갖는다.

| 격자 | 채워진 칸 | 전체 | 밀도 |
|---|---:|---:|---:|
| 제품 × 기술문서 주제 (설치·아키텍처·운영·성능·API) | **10** | 12 × 5 = 60 | **17%** |
| 고객사 × 문서 유형 (장애보고·회의록·제안서) | **30** | 30 × 3 = 90 | **33%** |

**주제를 2개 이상 가진 제품은 0개다.** Product-C1은 설치 가이드만, Product-D1은 API 레퍼런스만 있다.

→ `"Product-C1의 API 인증 방식은?"`은 **문서 자산이 이 제품을 커버하는데 요구된 형태만 없는** 상태다. 개체 단위 커버리지(제품 10/12)로는 잡히지 않는다.

빈 칸의 개체도 **테이블·그래프에는 전부 있다.** → "요구한 형태만 없고 인접 사실은 있다"는 상태가 **상시** 발생한다 ([edge-cases.md](./edge-cases.md) X5).

### 격자 희소성은 문서만의 성질이 아니다

같은 방식으로 나머지 두 자산도 쟀다. 밀도만 다르고 **구조는 같다.**

| 자산 | 격자 | 채워진 칸 | 밀도 | 결손 개체 |
|---|---|---:|---:|---|
| 문서 | 제품 × 기술주제 | 10 / 60 | **17%** | 제품 12개 **전부** 주제 4개씩 결손 |
| 문서 | 고객사 × 문서유형 | 30 / 90 | **33%** | 고객사 15개는 0칸 |
| 그래프 | 개체 × (그 유형이 가질 수 있는 관계) | 322 / 416 | **77%** | **직원 43/45**, 고객사 11/30 |
| 테이블 | 고객사 × 사실 테이블 4종 | 106 / 120 | **88%** | `projects` 8개, `contracts`·`sales` 3개 |

그래프 격자는 **스키마 제약과 데이터 결손을 구분해서** 셌다. `product`가 `BELONGS_TO`를 갖지 않는 것은 스키마상 불가능한 칸이므로 분모에서 뺐다(노드유형 × 관계 = 35칸 중 14칸만 스키마상 가능). 위 322/416은 **같은 유형 안에서 어떤 개체는 갖고 어떤 개체는 못 가진** 칸만 센 것이다.

→ `"이 직원이 이끄는 프로젝트는?"`은 노드도 있고 `BELONGS_TO`도 있는데 `LEADS`만 없는 상태다. `"Client-X의 진행 중인 프로젝트는?"`은 `projects` 0행인데 계약·매출·티켓은 있는 상태다. **문서에서 발견한 것과 같은 구조가 세 도구 전부에 있다.**

### 재현

```bash
cd companyx-dataset-v1.0
python3 -c "
import json
from collections import defaultdict
e=json.load(open('graph/edges.json')); e=e['edges'] if isinstance(e,dict) else e
n=json.load(open('graph/nodes.json')); n=n['nodes'] if isinstance(n,dict) else n
ty={x['id']:x['type'] for x in n}
have=defaultdict(set)
for x in e: have[x['source']].add(x['relation']); have[x['target']].add(x['relation'])
poss=defaultdict(set)
for i,t in ty.items(): poss[t]|=have[i]
tot=f=0
for t in sorted(poss):
    ids=[i for i in ty if ty[i]==t]
    tot+=len(ids)*len(poss[t]); f+=sum(len(have[i]&poss[t]) for i in ids)
    print(t, sum(1 for i in ids if have[i]&poss[t]!=poss[t]), '/', len(ids), '개체 일부 결손')
print('그래프 격자:', f, '/', tot)
"
# employee 43 / 45 · client 11 / 30 · 나머지 0 결손
# 그래프 격자: 322 / 416
```

### 재현

```bash
cd companyx-dataset-v1.0/documents
python3 -c "
import glob,re
from collections import defaultdict
grid=defaultdict(set); cli=defaultdict(set)
T=['설치','아키텍처','운영','성능','API']
for f in sorted(glob.glob('DOC-*.md')):
    s=open(f,encoding='utf-8').read(); h=re.findall(r'^#\s*(.+)\$',s,re.M)[0].strip()
    if h.startswith('Product'):
        grid[re.findall(r'Product-[A-Z]\d+',h)[0]] |= {t for t in T if t in h}
    k='incident' if '장애' in h else 'meeting' if '회의록' in h else 'proposal'
    for c in set(re.findall(r'Client-[A-Z]+',s)): cli[c].add(k)
print('제품 격자:', sum(len(v) for v in grid.values()), '/ 60   주제 2개 이상:', sum(1 for v in grid.values() if len(v)>1))
print('고객사 격자:', sum(len(v) for v in cli.values()), '/ 90')
"
# 제품 격자: 10 / 60   주제 2개 이상: 0
# 고객사 격자: 30 / 90
```

## 4. `support_tickets`에는 서술이 없다

| 항목 | 값 |
|---|---|
| 행 수 | 120 |
| `title` | **28종** (컨테이너 OOM 발생, SSL 인증서 만료 알림, Pod 재시작 반복 …) |
| `description` | **5종 템플릿 문구뿐** ("정기 점검 중 발견된 이슈입니다…" 등) |

즉 티켓은 **사건 목록**이고, 그 사건의 원인·조치는 **문서에만** 있다.

그리고 **title 28종 중 18종이 문서 본문과 주제어가 겹친다** (SSL, Pod, 로드밸런서, DB 연결, 디스크, 보안 패치, 스테이징, API …). 같은 주제를 티켓은 *목록*으로, 문서는 *서술*로 갖는다 — **상보적 중복**이다.

## 5. questions.json의 성격과 결함

### 스키마가 상정하는 것

- `tool`이 **단수 문자열**. 30개 전부 질문당 도구 1개.
- 복수 도구 케이스 **0건** → 병렬을 검증할 수단이 없다.
- 무매칭·스몰토크 **0건** → 거절(D6)을 검증할 수단이 없다.
- `hint`는 라우팅 근거가 아니라 **실행 명세**다 (nl2sql은 SQL 초안, knowledge_graph는 순회 경로, vector_search는 대상 문서 유형).

### 결함 2건

| # | 질문 | 배정 | 문제 |
|---|---|---|---|
| **#5** | "가장 많은 프로젝트를 진행 중인 고객사는?" | `nl2sql` | **#25·#29와 구조가 동일한데 반대 도구.** 셋 다 *관계 카운트의 최대*다 (HAS_PROJECT / REPORTED_ISSUE / MANAGES_ACCOUNT). 어떤 원칙적 규칙도 셋을 동시에 만족시킬 수 없다 |
| **#23** | "서울물산 담당 엔지니어는 누구야?" | `knowledge_graph` | **"서울물산"이 DB·그래프·문서 어디에도 없다.** hint는 `client_2`를 가리키는데 `client_2`의 실제 이름은 `Client-B`다. 개체명 30개는 전부 `Client-A`~`Client-AD` 합성 패턴이다 |

전수 검사 결과 미존재 개체를 참조하는 질문은 #23 하나뿐이다.

#23은 라우팅이 맞더라도 실행하면 개체 부재(T5)가 된다. 회귀 기준을 2축으로 나눈 근거다 ([design.md](./design.md) D7).

## 6. 출처 3곳 전수 확인 — "Parallel"이 정의된 곳은 없다

| 출처 | "병렬" | "Parallel" |
|---|---|---|
| KOSSA 요강 ([원문](https://www.kossa.kr/materials/2026/ossp/tasks-liwonace.html), 2026-08-13 재확인) | **0회** | **1회** — `규칙 기반 라우터를 통한 도구 자동 선택 (MCP Parallel 패턴)` |
| 블로그 `liwonace.co.kr/blog/9` | **0회** | 0회 |
| 공지 `liwonace.co.kr/notice/2` | **0회** | 0회 (라우터 언급 자체 없음) |
| 데이터셋 전체 | **0회** | 0회 |

**어느 출처도 "무엇이 병렬인지"를 정의하지 않는다.** 유일한 출현은 괄호 안 별칭이고, 문법적으로는 앞 구절("규칙 기반 라우터를 통한 도구 자동 선택")에 붙은 이름이다.

블로그의 라우터 서술은 이렇다:

> **도구 자동 선택** — 규칙 기반 라우터가 질문 유형을 분석하여 **적합한 도구를 자동 매칭**합니다.

**이 문장은 수를 명시하지 않는다.** 한국어는 복수 표지(`-들`)가 선택적이라 "적합한 도구를"은 단수·복수 어느 쪽으로도 읽힌다 — 조사 `를`은 수 표지가 아니다. 문면에서 읽어낼 수 있는 것은 "매칭"이지 "호출"이 아니라는 **어휘 선택**뿐이다.

수를 결정하는 것은 문면이 아니라 스키마다.

| 확인한 것 | 결과 |
|---|---|
| questions.json `tool` 필드 타입 | **`str` 30/30** |
| `tool`이 배열인 것 | **0 / 30** |
| 질문 객체 키 | `q` · `tool` · `hint` — 도구를 여럿 담을 필드가 없다 |

→ 기대 출력이 도구 1개라는 것은 **스키마가 못 박은 사실**이다.

→ 출처 어디에도 병렬 호출 요구는 없다. 이 사실을 근거로 병렬을 설계 선택으로 규정한 결정은 [design.md](./design.md) D3.

### 재현

블로그·공지는 WebFetch가 403을 받는다. curl은 통과하며 본문이 HTML에 포함된다.

```bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
curl -sS -L -A "$UA" https://liwonace.co.kr/blog/9 | grep -c "병렬"   # 0

# KOSSA 요강은 UA 없이도 통과한다
K=https://www.kossa.kr/materials/2026/ossp/tasks-liwonace.html
curl -sS -L "$K" | grep -c "병렬"              # 0
curl -sS -L "$K" | grep -o "Parallel" | wc -l  # 1
```

```bash
cd companyx-dataset-v1.0
python3 -c "
import json
qs=json.load(open('questions.json'))
print('타입:', {type(q['tool']).__name__ for q in qs})        # {'str'}
print('배열:', sum(1 for q in qs if isinstance(q['tool'],list)), '/', len(qs))   # 0 / 30
"
```
