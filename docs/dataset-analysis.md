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

**문서 격자**


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

**그래프 격자**


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

## 4. `support_tickets`에는 서술이 없다

| 항목 | 값 |
|---|---|
| 행 수 | 120 |
| `title` | **28종** (컨테이너 OOM 발생, SSL 인증서 만료 알림, Pod 재시작 반복 …) |
| `description` | **5종 템플릿 문구뿐** ("정기 점검 중 발견된 이슈입니다…" 등) |

즉 티켓은 **사건 목록**이고, 그 사건의 원인·조치는 **문서에만** 있다.

그리고 **title 28종 중 18종이 문서 본문과 주제어가 겹친다** (SSL, Pod, 로드밸런서, DB 연결, 디스크, 보안 패치, 스테이징, API …). 같은 주제를 티켓은 *목록*으로, 문서는 *서술*로 갖는다 — **상보적 중복**이다.

## 5. questions.json의 성격과 결함

> **번호 규약**: 이 저장소의 `#N`은 **0-indexed 배열 위치**다. `#5`는 여섯 번째 질문(*"가장 많은 프로젝트를 진행 중인 고객사는?"*)이고, `#23`은 스물네 번째(*"서울물산 담당 엔지니어는 누구야?"*)다. `questions.json`에 `id` 필드가 없어 위치로 참조한다. **1-indexed로 읽으면 전부 한 칸씩 어긋난다.**

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

### 연산 축 전수 분류

30개는 "단순한 조회"가 아니다. 아래 분류 **규칙은 우리가 정한 것**이고(스니펫에 전부 있다), 그 규칙을 30개에 적용한 결과가 아래 수치다.

| 연산 축 | 건수 | 해당 `#N` |
|---|---:|---|
| **집계** (SUM·COUNT·AVG·GROUP BY) | **10 / 30** | 0·1·2·3·5·7·8·9·25·29 |
| **최상급·정렬** (ORDER BY·LIMIT·"가장"·"상위") | **6 / 30** | 0·5·7·9·25·29 |
| **시간 제약** (연도·분기·월·"최근"·"현재") | **5 / 30** | 1·2·3·8·10 |
| **존재 확인** (답이 boolean) | 2 / 30 | 14·19 |
| **부정** ("아직 해결되지 않은") | 1 / 30 | 6 |
| **멀티홉** (hint에 홉 수 명시) | 1 / 30 | 24 |

**집계가 3분의 1, 최상급이 5분의 1이다.** [design.md](./design.md) D9 규칙 문면에는 최상급·시간·부정·존재 확인이라는 말이 없다.

### 집계의 도구 배정은 피연산자로 갈린다 — 예외 1건

집계 10건을 **피연산자**로 나누면 이렇다.

| 피연산자 | 건수 | 배정된 도구 |
|---|---:|---|
| **속성** (금액·연봉·행 수) | 7 (`#0·1·2·3·7·8·9`) | **전부 `nl2sql`** — 예외 0 |
| **관계** (HAS_PROJECT · REPORTED_ISSUE · MANAGES_ACCOUNT) | 3 (`#5·25·29`) | `nl2sql` 1 / `knowledge_graph` 2 |

**피연산자 축이 완벽히 가르고, 유일한 예외가 `#5`다** — 위 "결함 2건"의 그 건이다. 출력 형태 축으로는 `#9`("평균 연봉이 가장 높은 부서는?" — 답이 개체)와 `#25`("이슈가 가장 많은 제품은?" — 답이 개체)가 같은 칸에 들어가는데 도구는 다르다. 가르는 것은 답의 형태가 아니라 **무엇을 세는가**다 ([design.md](./design.md) D11).

### 재현

```bash
cd companyx-dataset-v1.0
python3 -c "
import json,re
qs=json.load(open('questions.json'))
AX={
 '집계'       : lambda q,h: re.search(r'SUM\(|\bCOUNT|AVG\(|GROUP BY|집계', h) or re.search(r'몇 개|수는|총 |평균', q),
 '최상급·정렬' : lambda q,h: re.search(r'ORDER BY|LIMIT', h) or re.search(r'가장|상위|큰 순서', q),
 '시간 제약'   : lambda q,h: re.search(r'20\d\d|분기|월 |최근|현재', q+h),
 '부정'       : lambda q,h: re.search(r'않은|않는|없는|아닌', q),
 '멀티홉'      : lambda q,h: re.search(r'\d홉', h),
 '존재 확인'   : lambda q,h: re.search(r'있어\?|있었어\?|있나\?', q) and not re.search(r'어떻게|무엇|뭐야|누구|어디', q),
}
hit={k:[i for i,x in enumerate(qs) if f(x['q'],x['hint'])] for k,f in AX.items()}
for k,v in hit.items(): print(f'{k:11s} {len(v):2d}/30  {v}')
agg=sorted(hit['집계'])
rel=[i for i in agg if re.search(r'관계 카운트|GROUP BY client_id', qs[i]['hint'])]
print('집계 x 관계:', rel, '->', [qs[i]['tool'] for i in rel])
att=[i for i in agg if i not in rel]
print('집계 x 속성:', att, '-> 전부 nl2sql:', all(qs[i]['tool']=='nl2sql' for i in att))
"
# 집계 10/30 · 최상급 6/30 · 시간 5/30 · 부정 1/30 · 멀티홉 1/30 · 존재확인 2/30
# 집계 x 관계: [5, 25, 29] -> ['nl2sql', 'knowledge_graph', 'knowledge_graph']
# 집계 x 속성: [0, 1, 2, 3, 7, 8, 9] -> 전부 nl2sql: True
```

`\bCOUNT`의 단어 경계가 필요하다 — 없으면 `MANAGES_ACCOUNT`가 걸린다. 존재 확인에서 `어떻게`를 제외하지 않으면 `#15`("백업 정책은 어떻게 되어 **있어?**")가 걸린다.

### 표층 신호 후보 2건 대조 — 하나는 실패, 하나는 유망

라우터 규칙(D9)은 **의미**로 쓰여 있다. 코드가 무엇을 보고 판정할지 후보 둘을 30개에 대조했다. **부정 결과도 기록한다** — 같은 시도를 반복하지 않기 위해서다.

**① 의문사 매핑 — 실패**

`어떻게/왜/방법` → 서술, `얼마/몇/평균` → 수치, `누구/어디/목록` → 개체.

| 태그 | 건수 | 배정된 도구 |
|---|---:|---|
| 서술 | 8 | `vector_search` 7 / **`knowledge_graph` 1** (`#28` 오분류) |
| 수치 | 6 | `nl2sql` 6 — 일치 |
| **개체** | 8 | **`nl2sql` 2 / `knowledge_graph` 6 — 양쪽에 걸침** |
| 무태그 | **9** | `#0·5·6·16·17·19·24·25·29` |

**의문사만으로는 도구가 정해지지 않는다.** 개체 태그가 두 도구에 걸치고 30%가 무태그다. 의문사는 **출력 형태** 축의 신호인데, `nl2sql`과 `knowledge_graph`는 출력 형태로 갈리지 않기 때문이다 ([design.md](./design.md) D11).

**② 스키마 어휘 매칭 — 28/30**

관계 7종(`USES`·`BELONGS_TO`·`HAS_PROJECT`·`LEADS`·`MANAGES_ACCOUNT`·`REPORTED_ISSUE`·`HEAD_IS`)과 테이블 컬럼명의 한국어 표층형으로 매칭. 관계만 걸리면 `knowledge_graph`, 속성이 걸리면 `nl2sql`, 둘 다 없으면 `vector_search`.

| 미스 | 성격 |
|---|---|
| `#5` "가장 많은 프로젝트를 진행 중인 고객사는?" | **알려진 데이터셋 불일치** (위 결함 2건) |
| `#17` "고객사 미팅에서 논의된 일정 지연 **이슈**는?" | **표층 문자열 충돌** — `REPORTED_ISSUE`의 "이슈"가 일반 명사와 겹친다 (edge-cases.md **R5**) |

> **이 28/30을 실력으로 치지 않는다.** 한국어 표층형 매핑을 사람이 썼고 그 사람이 30개를 이미 읽은 뒤였다 — **출처가 스키마인지 질문인지 방향이 흐려졌을 위험**이 있다. D7이 막으려는 지점이 정확히 여기다. 자체 엣지 세트로 다시 재기 전까지는 "방향이 맞다"까지만 주장한다.

```bash
cd companyx-dataset-v1.0
# ① 의문사 — 실패
python3 -c "
import json,re
from collections import Counter
qs=json.load(open('questions.json'))
W=[(r'어떻게|어떤|왜|방법|내용|사례|현황','서술'),(r'얼마|몇|평균|총|수는','수치'),(r'누구|어디|누가|목록|무엇','개체')]
tag={i:[n for p,n in W if re.search(p,x['q'])] for i,x in enumerate(qs)}
for n in ['서술','수치','개체']:
    ids=[i for i,t in tag.items() if n in t]
    print(n, len(ids), dict(Counter(qs[i]['tool'] for i in ids)))
print('무태그:', [i for i,t in tag.items() if not t])
"
# 서술 8 {'vector_search': 7, 'knowledge_graph': 1} / 수치 6 {'nl2sql': 6}
# 개체 8 {'nl2sql': 2, 'knowledge_graph': 6} / 무태그 9건

# ② 스키마 어휘 — 28/30
python3 -c "
import json,re
qs=json.load(open('questions.json'))
REL={r'사용|쓰는|쓰고':'USES',r'소속':'BELONGS_TO',r'담당':'MANAGES_ACCOUNT',r'이끄는|리드':'LEADS',r'팀장|장은':'HEAD_IS',r'프로젝트':'HAS_PROJECT',r'이슈':'REPORTED_ISSUE'}
ATTR={r'매출|금액|예산':'amount',r'연봉':'salary',r'상태|활성':'status',r'지역':'region',r'분기':'quarter',r'카테고리':'category',r'우선순위':'priority',r'등록':'registered_at'}
miss=[]
for i,x in enumerate(qs):
    r=[v for p,v in REL.items() if re.search(p,x['q'])]; a=[v for p,v in ATTR.items() if re.search(p,x['q'])]
    g='knowledge_graph' if (r and not a) else ('nl2sql' if a else 'vector_search')
    if g!=x['tool']: miss.append((i,g,x['tool'],r))
print('일치:', 30-len(miss),'/30   미스:', miss)
"
# 일치: 28 /30   미스: [(5,'knowledge_graph','nl2sql',['HAS_PROJECT']),
#                      (17,'knowledge_graph','vector_search',['REPORTED_ISSUE'])]
```

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

## 7. 권장 개발 환경 문면 확인 (2026-08-14 재확인)

같은 출처 3곳에서 **모델 관련 문면**을 다시 확인했다. 문면은 시점에 따라 바뀔 수 있으므로 확인 날짜를 함께 적는다.

| 출처 | LLM 표기 | 임베딩 표기 | `nomic` 출현 |
|---|---|---|---|
| 블로그 `liwonace.co.kr/blog/9` — "권장 개발 환경" 표 | **`Gemma 4 E2B (Ollama 로컬 실행)`** | 표에 항목 없음 | **0회** |
| 공지 `liwonace.co.kr/notice/2` — 동일 표 | **`Gemma 4 E2B (Ollama 로컬 실행)`** | *"Ollama의 임베딩 모델을 활용하여 적재하시면 됩니다"* — **모델명 없음** | **0회** |
| KOSSA 요강 | `온프레미스 소형 LLM(7B)과의 연동 (Ollama)` | 언급 없음 | **0회** |

- 리원에이스 2출처(블로그·공지)는 **문면이 동일**하다.
- KOSSA 요강의 `7B` 표기와의 차이는 **존속한다**.
- 공지의 임베딩 문면은 *"Ollama의 임베딩 모델"*까지이고 **특정 모델명을 지정하지 않는다.** 2026-08-14 기준 **출처 3곳 어디에도 `nomic`은 없다**. (과거 문면에 있었는지는 확인 수단이 없다.)

### 권장 개발 환경 표 전 항목 대조 (2026-08-18) — RAM·GPU 문면은 **블로그에만** 있다

앞 표는 LLM·임베딩 행만 봤다. 표 전체를 대조하면 **출처마다 항목 수가 다르다**.

| 항목 | 블로그 `blog/9` | 공지 `notice/2` | KOSSA 요강 |
|---|---|---|---|
| LLM | `Gemma 4 E2B (Ollama 로컬 실행)` | 동일 | — (본문에 `소형 LLM(7B)`) |
| **LLM 실행** | **`Ollama (로컬, GPU 선택)`** | **`Ollama (로컬 실행, GPU 선택)`** | — |
| 데이터베이스 | `PostgreSQL 15+ / pgvector` | 동일 | — |
| MCP 서버 | `air 프레임워크 권장 (선택사항)` | 동일 | — |
| OS | `Linux 권장 (macOS / WSL2 가능)` | **항목 없음** | — |
| **RAM** | **`최소 4GB`** | **항목 없음** | — |

`grep` 계수로도 확인된다: `RAM` 출현은 블로그 **1회**, 공지 **0회**, 요강 **0회**. `권장 개발 환경`이라는 표제 자체가 요강에는 없다(0회).

**두 문면을 정확히 옮긴다.** 표 아래 본문은 다음과 같다.

> 모든 모델은 Ollama로 로컬 실행합니다. 외부 API(OpenAI, Claude 등) 사용은 불가합니다. **GPU 없이 CPU만으로도 구동 가능합니다.**

- 표의 `LLM 실행` 값이 **`GPU 선택`**이다 — 두 출처 모두.
- 본문은 *"CPU만으로**도** 구동 가능합니다"*이다. **가능 서술이지 의무 서술이 아니다.**
- `RAM 최소 4GB`가 실린 표의 표제는 **"권장 개발 환경"**이다. 심사 실행 환경의 사양을 적은 문면은 출처 3곳 어디에도 없다(미확인).

이 세 문면과 아래 CPU 전용 실측을 함께 놓으면 **동시에 만족할 수 없는 조합**이 나온다: 권장 모델 `Gemma 4 E2B` + `RAM 최소 4GB` + *"GPU 없이 CPU만으로도 구동"* — 셋 중 둘까지만 성립한다(CPU 전용 단독 4.0GB). 어떻게 읽을지는 판단이고 [design.md](./design.md) 열어둔 항목 **RAM 4GB 하한**에 있다.

```bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
strip() { python3 -c "
import sys,re,html
t=sys.stdin.read(); t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(t); print(re.sub(r'\\s+',' ',t))
"; }
for u in https://liwonace.co.kr/blog/9 https://liwonace.co.kr/notice/2 \
         https://www.kossa.kr/materials/2026/ossp/tasks-liwonace.html; do
  echo "== $u"
  curl -sS -L -A "$UA" "$u" | strip \
    | grep -o 'RAM 최소 [0-9]\+GB\|GPU 선택\|CPU만으로도 구동 가능\|권장 개발 환경' || echo '  (해당 없음)'
done
# blog/9  : 권장 개발 환경 · GPU 선택 · RAM 최소 4GB · CPU만으로도 구동 가능
# notice/2: 권장 개발 환경 · GPU 선택          (RAM·CPU 문면 없음)
# kossa   : (해당 없음)
```

### `nomic-embed-text`가 나오는 곳은 출처 3곳이 아니라 **데이터셋 README**다

전수 검색 결과 `nomic`의 유일한 출현은 데이터셋 안이다.

| 위치 | 문면 |
|---|---|
| `companyx-dataset-v1.0/README.md:64` | `# 5. 문서 임베딩은 참가자가 직접 구현` / `# Ollama + nomic-embed-text 또는 다른 임베딩 모델 사용` |

문면 자체가 **"또는 다른 임베딩 모델"**이라고 적어 예시임을 명시한다. 지정이 아니다.

### 스키마는 임베딩 차원을 **768로 못 박고 있다**

| 위치 | 선언 |
|---|---|
| `companyx-dataset-v1.0/sql/01-schema.sql:123` | `embedding vector(768)` (테이블 `document_chunks` — *"참가자가 임베딩 후 적재"*) |

| 모델 | 차원 |
|---|---:|
| `nomic-embed-text` | **768** — 위 DDL과 그대로 일치 |
| `bge-m3` | **1024** — DDL을 `vector(1024)`로 바꿔야 적재된다 |

`document_chunks`는 빈 상태로 배포되고 적재는 참가자 몫이므로 DDL 변경 자체를 막는 문면은 없다. **차원이 스키마에 박혀 있다는 사실만 기록한다** — 어느 모델을 쓸지는 판단이고 [design.md](./design.md) 열어둔 항목에 있다.

### Ollama 레지스트리 실물 (2026-08-14 조회)

| 모델 | 태그 | 크기 | 컨텍스트 | 비고 |
|---|---|---:|---|---|
| `gemma4` | `e2b` | **7.2GB** | 128K | 기본 태그(q4_K_M), Text+Image |
| `gemma4` | **`e2b-it-qat`** | **4.3GB** | 128K | 최소 태그 |
| `gemma4` | `e2b-it-q8_0` | 8.1GB | 128K | |
| `gemma4` | `e4b` · `12b` · `26b` · `31b` | 9.6 / 7.6 / 18 / 20GB | — | 참고 |
| `nomic-embed-text` | `latest` | **274MB** | **2K** | |
| `bge-m3` | `latest` | **1.2GB** | **8K** | |

- `nomic-embed-text`의 HF 모델카드(`nomic-ai/nomic-embed-text-v1.5`)의 언어 태그는 **`en` 하나**다 (`cardData.language == ['en']`).
- `bge-m3`의 원 논문 M3-Embedding은 **Findings of ACL 2024** 게재본이 존재한다 ([서지](./references/related-work.md) 2.4). 한국어(ko) 개별 수치도 원문 표에 있다 — 같은 문서 2.10 참조.

### 로컬 환경 실측 (2026-08-14)

| 항목 | 값 |
|---|---|
| RAM | 15Gi (available 11Gi) |
| CPU | 22 |
| GPU | NVIDIA RTX 4070 Laptop 8188MiB — **과제 제약(CPU 전용)과 다르다**. 아래 실행 실측의 단서 |
| 디스크 여유 | 925G |
| ollama | 0.31.2 |

### 재현

블로그·공지는 WebFetch가 403을 받는다. curl은 통과한다 (6장 재현 절과 동일한 UA).

```bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
curl -sS -L -A "$UA" https://liwonace.co.kr/blog/9   | grep -o 'Gemma[^<"]*'   # Gemma 4 E2B (Ollama 로컬 실행)
curl -sS -L -A "$UA" https://liwonace.co.kr/notice/2 | grep -o 'Gemma[^<"]*'   # 동일
curl -sS -L -A "$UA" https://liwonace.co.kr/notice/2 | grep -c nomic           # 0
curl -sS -L -A "$UA" https://liwonace.co.kr/blog/9   | grep -c nomic           # 0
curl -sS -L -A "$UA" https://liwonace.co.kr/notice/2 | grep -o '[^<>]*임베딩[^<>]*' | sort -u
# Ollama의 임베딩 모델을 활용하여 적재하시면 됩니다.
# 문서 데이터의 임베딩 및 벡터 저장은 참가자가 직접 구현하는 영역입니다.

K=https://www.kossa.kr/materials/2026/ossp/tasks-liwonace.html
curl -sS -L "$K" | grep -o '소형 LLM(7B)'    # 소형 LLM(7B)  — UA 없이도 통과
```

```bash
# 레지스트리 실물
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
curl -sS -L -A "$UA" https://ollama.com/library/gemma4/tags | grep -oE '(gemma4:[a-z0-9._-]+|[0-9.]+GB)' | uniq
curl -sS -L -A "$UA" https://ollama.com/library/bge-m3           | grep -oE '([0-9.]+GB|[0-9]+K context)' | sort -u  # 1.2GB · 8K context
curl -sS -L -A "$UA" https://ollama.com/library/nomic-embed-text | grep -oE '([0-9]+MB|[0-9]+K context)' | sort -u   # 274MB · 2K context

# nomic 모델카드 언어 태그
curl -sS -L https://huggingface.co/api/models/nomic-ai/nomic-embed-text-v1.5 \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['cardData']['language'])"   # ['en']
```

```bash
# 데이터셋 안의 nomic 언급과 스키마 차원
cd companyx-dataset-v1.0
grep -rn "nomic" .                       # README.md:64 한 줄뿐
grep -n "embedding" sql/01-schema.sql    # 123:    embedding       vector(768),
```

### 실행 실측 (2026-08-14, pull 후)

세 모델을 받아 동시에 적재한 상태에서 쟀다. **파일 크기와 실행 풋프린트는 다르다.**

| 모델 | 파일 크기 | `ollama ps` SIZE | 컨텍스트 | 임베딩 차원 |
|---|---:|---:|---:|---:|
| `gemma4:e2b-it-qat` | 4.3GB | **1.7GB** | 4096 | — |
| `bge-m3` | 1.2GB | **664MB** | 4096 | **1024** |
| `nomic-embed-text` | 274MB | **323MB** | 2048 | **768** |
| 3종 동시 적재 합 | 5.8GB | **약 2.7GB** | | |

`gemma4:e2b-it-qat`는 한국어로 답한다. 프롬프트 *"Company-X의 매출 데이터를 요약하는 역할을 한 문장으로 설명해줘"* → *"이 문서는 회사 X의 총매출액 추이와 주요 재무 성과를 분석하여 이해하기 쉽게 요약한 데이터 보고서입니다."* (36 토큰, 1.2초).

**이 표의 SIZE는 CPU 전용 조건의 값이 아니다.** 측정 환경에 GPU가 있어 `ollama ps`의 `PROCESSOR`가 3종 모두 `100% GPU`로 나왔다 (NVIDIA RTX 4070 Laptop 8GB, RAM 15Gi). **CPU 전용 실측은 아래 「CPU 전용 실측 (2026-08-18)」 절에서 따로 했고, 값이 크게 다르다** — `gemma4:e2b-it-qat` 단독이 1.7GB가 아니라 **4.0GB**다(약 2.4배). 따라서 **이 표를 필요 메모리의 근사로도 쓰면 안 된다.** 남겨 두는 이유는 GPU/CPU 대조의 한쪽 항이기 때문이다.

```bash
ollama pull gemma4:e2b-it-qat && ollama pull bge-m3 && ollama pull nomic-embed-text

curl -sS localhost:11434/api/generate -d '{"model":"gemma4:e2b-it-qat","prompt":"Company-X의 매출 데이터를 요약하는 역할을 한 문장으로 설명해줘","stream":false,"think":false}' \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['response']);print(d['eval_count'],'토큰')"

for m in bge-m3 nomic-embed-text; do
  curl -sS localhost:11434/api/embed -d "{\"model\":\"$m\",\"input\":\"서울 지역 매출\"}" \
    | python3 -c "import json,sys;print('$m', len(json.load(sys.stdin)['embeddings'][0]))"
done       # bge-m3 1024 · nomic-embed-text 768

ollama ps  # SIZE·PROCESSOR·CONTEXT — PROCESSOR가 GPU면 CPU 전용 실측이 아니다
```

### CPU 전용 실측 (2026-08-18)

바로 위 수치는 GPU 적재 상태라 원문의 *"GPU 없이 CPU만으로**도** 구동 가능합니다"*를 검증한 것이 아니었다 (문면은 위 「권장 개발 환경 표 전 항목 대조」 절). `options.num_gpu = 0`으로 GPU를 끄고 다시 쟀다. 측정마다 `nvidia-smi`로 VRAM `0 MiB`를 확인해 CPU 전용임을 검증했다.

| 모델 | 파일 크기 | `ollama ps` SIZE (**`100% CPU`**) | 컨텍스트 |
|---|---:|---:|---:|
| `gemma4:e2b-it-qat` | 4.3GB | **4.0GB** | 2048 |
| `gemma4:e2b-it-qat` | 4.3GB | **4.0GB** | 4096 |
| `bge-m3` | 1.2GB | **1.2GB** | 4096 |
| `nomic-embed-text` | 274MB | **376MB** | 2048 |

동시 적재 조합:

| 조합 | 합계 |
|---|---:|
| LLM 단독 | **4.0GB** |
| LLM + `nomic-embed-text` | **약 4.4GB** |
| LLM + `bge-m3` | **5.2GB** |

제약은 *"RAM 최소 4GB"*다 ([requirements.md](./requirements.md) 제약 조건). **LLM 단독 4.0GB로 이미 그 하한과 같다.**

시스템 메모리로도 같은 값이 나온다 — LLM + `bge-m3` 적재 전후로 `MemAvailable`이 **7301MB → 1851MB**(Δ 약 5450MB)로 줄었다. `ollama ps` 합계 5.2GB와 정합한다.

**컨텍스트는 변수가 아니다.** 2048과 4096에서 SIZE가 4.0GB로 같다. 다만 `e2b`의 기본 컨텍스트는 **131072**이므로 위 값은 **하한**이다.

#### GPU 수치는 CPU 요구량의 대리값이 될 수 없다

같은 모델·같은 컨텍스트(2048)로 대조했다.

| 적재 | `ollama ps` SIZE | `nvidia-smi` VRAM |
|---|---:|---:|
| `100% GPU` | **1.7GB** | 2831MiB |
| `100% CPU` | **4.0GB** | 0MiB |

두 가지가 관측된다. ① GPU 적재 시 `ollama ps`의 SIZE(1.7GB)는 실제 VRAM 점유(2831MiB)보다 **작다** — SIZE는 전량 회계가 아니다. ② 같은 조건에서 CPU 적재는 GPU 적재의 **약 2.4배**다. **원인은 미확인이다.** 참고로 모델 메타데이터는 아래와 같다 (`ollama show`).

| 항목 | 값 |
|---|---|
| architecture | `gemma4` |
| parameters | **4.6B** |
| quantization | `Q4_0` |
| context length | **131072** |
| embedding length | 1536 |
| capabilities | completion · vision · audio · tools · thinking |
| projector | `clip` 475.73M |

측정 환경: WSL2 (당시 VM 메모리 상한 16GB, 호스트 63.5GB) · CPU 22 · ollama 0.31.2. **호스트에 GPU가 있어도 `num_gpu:0`이면 `PROCESSOR`가 `100% CPU`로 바뀌고 VRAM 점유가 0이 된다** — CPU 전용 측정에 GPU 없는 기계가 필요하지는 않다.

### 재현

```bash
# CPU 전용 강제: options.num_gpu = 0
load() { curl -sS localhost:11434/api/generate -d "{\"model\":\"$1\",\"prompt\":\"안녕\",\"stream\":false,\"keep_alive\":\"120s\",\"options\":{\"num_gpu\":$2,\"num_ctx\":$3,\"num_predict\":4}}" >/dev/null; }
unload() { curl -sS localhost:11434/api/generate -d "{\"model\":\"$1\",\"keep_alive\":0}" >/dev/null; sleep 2; }

free -m | awk '/Mem:/{print "적재 전 available:", $7, "MB"}'      # 7301 MB

load gemma4:e2b-it-qat 0 2048
ollama ps                                                        # 4.0 GB · 100% CPU · 2048
nvidia-smi --query-gpu=memory.used --format=csv,noheader          # 0 MiB  ← CPU 전용 검증

curl -sS localhost:11434/api/embed -d '{"model":"bge-m3","input":"서울 지역 매출","keep_alive":"120s","options":{"num_gpu":0}}' >/dev/null
ollama ps                                                        # + 1.2 GB · 100% CPU → 합 5.2 GB
free -m | awk '/Mem:/{print "적재 후 available:", $7, "MB"}'      # 1851 MB  (Δ 약 5450 MB)

# GPU/CPU 대조 — 컨텍스트를 2048로 고정해 변수 제거
unload gemma4:e2b-it-qat; load gemma4:e2b-it-qat 99 2048
ollama ps; nvidia-smi --query-gpu=memory.used --format=csv,noheader   # 1.7 GB · 100% GPU / 2831 MiB
unload gemma4:e2b-it-qat; load gemma4:e2b-it-qat 0 2048
ollama ps; nvidia-smi --query-gpu=memory.used --format=csv,noheader   # 4.0 GB · 100% CPU / 0 MiB

ollama show gemma4:e2b-it-qat | head -8    # architecture·parameters·quantization·context length
```
