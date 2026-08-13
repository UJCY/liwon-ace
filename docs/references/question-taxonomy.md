# 질문 분해 축 — 질문 유형 분류 체계 서지

> **조사 질문**: 질문을 도구로 라우팅하기 위한 분해 축이 **(개체 × 요구 출력 형태) 2축**으로 충분한가?
>
> 대조 대상은 [design.md](../design.md) **D9**(도구 경계는 "요구 출력 형태"로 가른다 — 4클래스 단일 축)다.
> 서지 수집 기준은 [related-work.md](./related-work.md) "수집 기준"과 동일하다. 발표처를 직접 확인하지 못한 항목은 추측하지 않고 **"미확인"**으로 적었다.

## 이 문서를 읽는 법

- **1~6장은 사실이다.** 각 문헌이 실제로 쓴 축만 적었다. 원문 PDF 본문을 열어 확인한 항목은 신뢰도 칸에 **`본문 확인`**, 초록·서지 정보까지만 본 항목은 **`초록만`**으로 구분했다.
- **7장은 대조표**다. 축의 유무는 각 논문의 자기 서술 기준이며, 우리가 재분류하지 않았다.
- **9장은 확인 실패 기록**, **10장이 우리 판단**이다. 10장 안에서도 사실과 판단을 절로 나눴다.

**지정 발표처 목록 밖 항목 표기**: ISWC, WWW Companion, SIGIR Forum, Foundations and Trends는 [related-work.md](./related-work.md) 수집 기준의 열거 목록에 없다. 피어리뷰이지만 `목록 밖`으로 명시했다.

---

# 1. 답 유형(answer type) 단일 축 — 고전 QA 분류

| 저자(연도) | 제목 | 발표처 | URL | 핵심 내용 | 신뢰도 |
|---|---|---|---|---|---|
| Li & Roth (2002) | Learning Question Classifiers | COLING 2002 | https://aclanthology.org/C02-1150/ | **답의 의미 유형 1축, 2계층** — 6 coarse(ABBREVIATION·ENTITY·DESCRIPTION·HUMAN·LOCATION·NUMERIC VALUE) × 50 fine. TREC-10 500문항 분포 제시 | 피어리뷰 · **본문 확인** |
| Rajpurkar et al. (2018) | Know What You Don't Know: Unanswerable Questions for SQuAD | ACL 2018 (Short) | https://aclanthology.org/P18-2124/ | **답변 가능성**을 답 유형과 별개의 판정 축으로 세움 (related-work 4.7과 중복) | 피어리뷰 · 초록만 |
| Rogers, Gardner & Augenstein (2023) | QA Dataset Explosion: A Taxonomy of NLP Resources for Question Answering and Reading Comprehension | ACM Computing Surveys 55(10), Art. 197 | https://dl.acm.org/doi/10.1145/3560260 | **QA 데이터셋 200여 건을 다축으로 정리한 서베이.** 형식(질문/답/근거) · 대화성 · 도메인 · 언어 · 스킬 5계열을 분리하고, 스킬 축을 다시 5차원으로 제안 | 피어리뷰 · **본문 확인** |

## 1.1 확인된 사실

**Li & Roth (2002) — 단일 축 분류의 원형이 스스로 단일 라벨을 포기했다.**

논문 §2.3 "The Ambiguity Problem"의 서술이다.

> "One difficulty in the question classification task is that there is no completely clear boundary between classes."

예시 셋을 든다. *"What is bipolar disorder?"* 는 `definition`과 `disease/medicine` 둘 다일 수 있고, *"What do bats eat?"* 는 `food`·`plant`·`animal`, *"What is the PH scale?"* 는 `numeric value`와 `definition` 둘 다다. 결론은 이렇다.

> "To avoid this problem, we allow our classifiers to assign multiple class labels for a single question. This method is better than only allowing one label because we can apply all the classes in the later processing steps without any loss."

즉 **답 유형 축의 표준 참조 문헌이 "한 질문 = 한 클래스"를 명시적으로 기각했다.** 계층(coarse/fine)을 도입한 이유는 "각 coarse 클래스가 서로 겹치지 않는 fine 클래스 집합을 갖게" 하기 위함이지, 질문이 한 클래스에만 속하기 때문이 아니다.

**Rogers et al. (2023) — 차원의 직교성을 명시한다.**

§8.2에서 스킬 축을 5차원으로 제안한다: **Inference · Retrieval · Input interpretation & manipulation · World modeling · Multi-step**. 그리고 다음을 명시한다.

> "A key feature of our taxonomy is that these dimensions are orthogonal: the same question can be described in terms of their linguistic form, the kind of inference required to arrive at the answer, retrievability of the evidence, compositional complexity, and the level of world modeling."

§3에는 **출력 형식과 추론 유형을 혼동하지 말라는 경고**가 따로 있다.

> "One should also not conflate format with reasoning types (§8). For example, 'extractive QA' is often discussed as if were a cohesive problem — however, extractive QA is an output format, and datasets using this format can differ wildly in the nature of the problems they encapsulate."

§8.2.2 Retrieval은 다시 **하위 축 2개**로 쪼갠다.

> "We are considering two sub-dimensions of the retrieval problem: determining whether an answer exists, and where to look for it."

"where to look for it"이 **소스 선택 축**에 해당하는 유일한 명시적 위치다. 이 서베이에서 그것은 답 유형 축이 아니라 검색 축의 하위 축이다.

---

# 2. 질문 분해(decomposition) — 연산 축

| 저자(연도) | 제목 | 발표처 | URL | 핵심 내용 | 신뢰도 |
|---|---|---|---|---|---|
| Wolfson et al. (2020) | Break It Down: A Question Understanding Benchmark | TACL 8, 183–198 | https://aclanthology.org/2020.tacl-1.13/ | **QDMR — 13 연산 타입.** SELECT·FILTER·PROJECT·AGGREGATE·GROUP·SUPERLATIVE·COMPARATIVE·UNION·INTERSECTION·DISCARD·SORT·BOOLEAN·ARITHMETIC. 10개 데이터셋·3 모달리티 83,978건 | 피어리뷰 · **본문 확인** |
| Cao et al. (2022) | KQA Pro: A Dataset with Explicit Compositional Programs for Complex Question Answering over Knowledge Base | ACL 2022 (Long) | https://aclanthology.org/2022.acl-long.422/ | **KoPL — 27 함수.** 생성 단계를 *locating*(7 전략) / *asking*(9 전략) 2단으로 분리. 진단 축은 별도 7종 | 피어리뷰 · **본문 확인** |
| Dua et al. (2019) | DROP: A Reading Comprehension Benchmark Requiring Discrete Reasoning Over Paragraphs | NAACL-HLT 2019 | https://aclanthology.org/N19-1246/ | 답 유형(number·span·spans·date)과 별개로 **이산 연산**(덧셈·카운트·정렬·비교·상호참조)을 요구 축으로 세움 | 피어리뷰 · 초록만 |
| Sugawara et al. (2018) | What Makes Reading Comprehension Questions Easier? | EMNLP 2018 | https://aclanthology.org/D18-1453/ | 독해 질문의 요구 스킬을 분해해 난이도와 대응시킴 (Rogers et al.이 선행 스킬 분류로 인용) | 피어리뷰 · 초록만 |
| Dunietz et al. (2020) | To Test Machine Comprehension, Start by Defining Comprehension | ACL 2020 | https://aclanthology.org/2020.acl-main.701/ | 이해를 먼저 정의하고 질문 유형을 그로부터 도출하자는 방법론 (Rogers et al.의 선행 분류) | 피어리뷰 · 초록만 |

## 2.1 확인된 사실

**QDMR은 연산 축을 정보 소스와 명시적으로 분리한다.** 이것이 이 문서에서 우리 질문에 가장 직접적인 문장이다.

> "Our goal is to develop a meaning representation that is agnostic to the information source."

> "QDMR abstracts away the context needed to answer the question, allowing in principle to query multiple sources for the same question."

> "This abstraction enables QDMR to be unrestricted to a particular modality, with its operators to be executed also against text and images, while allowing in principle to query multiple modalities for the same question."

Break는 이 설계를 실증한다 — **DB(semantic parsing) · 텍스트(reading comprehension) · 이미지(VQA) 3개 모달리티의 10개 데이터셋에 같은 13개 연산을 붙였다.** 주석자에게는 질문만 보여줘 원 모달리티를 모르게 했다("workers are agnostic to the original modality of the question").

**연산 분포** (Table 4, QDMR 60,150건 기준): SELECT 100% · PROJECT 69.0% · FILTER 53.2% · **AGGREGATE 38.1%** · BOOLEAN 30.0% · **COMPARATIVE 17.0%** · **GROUP 9.7%** · SUPERLATIVE 6.3% · UNION 5.5% · ARITHMETIC 5.4% · **DISCARD 3.2%** · INTERSECTION 2.7% · SORT 0.9%.

**KQA Pro는 연산을 두 단계로 나눈다.** 질문 생성이 *locating*(대상 개체집합을 제약으로 좁힘 — 7 전략, 비교 연산자 `=` `!=` `<` `>` 및 qualifier 제약 포함)과 *asking*(좁혀진 대상에 무엇을 물을지 — 9 전략)으로 분리된다. §5.3의 진단 축은 또 별개다.

> "Multi-hop means multi-hop questions, Qualifier means questions containing qualifier knowledge, Comparison means quantitative or temporal comparison between two or more entities, Logical means logical union or intersection, Count means questions that ask the number of target entities, Verify means questions that take 'yes' or 'no' as the answer, Zero-shot means questions whose answer is not seen in the training set."

**진단 축 7종(Multi-hop·Qualifier·Comparison·Logical·Count·Verify·Zero-shot)은 서로 배타적이지 않다** — 같은 질문이 여러 축에 동시에 해당한다. 멀티홉 질문은 KQA Pro의 73.7%이고 4.7%는 5홉 이상이다.

---

# 3. Text-to-SQL — 난이도·복잡도 축

| 저자(연도) | 제목 | 발표처 | URL | 핵심 내용 | 신뢰도 |
|---|---|---|---|---|---|
| Yu et al. (2018) | Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task | EMNLP 2018 | https://aclanthology.org/D18-1425/ | **난이도 1축 4단**(easy/medium/hard/extra hard). 기준은 **SQL 구성요소 개수**뿐 — 질문 쪽은 안 본다 | 피어리뷰 · **본문 확인** |
| Li et al. (2023) | Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs (BIRD) | NeurIPS 2023 Datasets & Benchmarks | https://proceedings.neurips.cc/paper_files/paper/2023/hash/83fc8fab1710363050bbd1d4b8cc0021-Abstract-Datasets_and_Benchmarks.html | **Spider의 1축을 명시적으로 기각하고 4차원으로 교체.** 각 1–3점 → 합산해 simple(30%)/moderate(60%)/challenging(10%) | 피어리뷰 · **본문 확인** |
| Shao et al. (2025) | Enhancing Text-to-SQL with Question Classification and Multi-Agent Collaboration (QCMA-SQL) | Findings of NAACL 2025 | https://aclanthology.org/2025.findings-naacl.245/ | 질문을 난이도로 분류해 에이전트를 배정. **ablation에서 분류 도입이 실행 정확도 +2.8%** (원문 표기 "2.8% increase" — %p 아님) | 피어리뷰 · 초록만 |

## 3.1 확인된 사실

**Spider의 난이도 기준은 질문이 아니라 SQL을 본다.**

> "We define the difficulty based on the number of SQL components, selections, and conditions, so that queries that contain more SQL keywords (`GROUP BY`, `ORDER BY`, `INTERSECT`, nested subqueries, column selections and aggregators, etc) are considered to be harder."

**BIRD는 이 단일 축이 부족하다고 명시하고 4차원으로 바꿨다.**

> "Previous work, such as SPIDER, computed difficulty mainly based on SQL complexity. However, we find that additional factors, such as question comprehension, schema linking, and external knowledge reasoning, also influence model and human performance."

4차원은 각각 1–3점 척도다: **① Question Understanding**(질문 의도의 모호성) **② Knowledge Reasoning**(외부 지식 요구량) **③ Data Complexity**(스키마 관계·데이터 규모) **④ SQL Complexity**(대상 SQL의 구문 복잡도). "Each dimension is considered equally important."

**이것이 "1축 → 다축" 전환의 가장 깨끗한 선례다.** 같은 태스크·같은 커뮤니티에서 5년 만에 축이 1개에서 4개로 늘었고, 늘린 쪽이 이유를 명시했다.

---

# 4. KGQA — 질문 유형 축

| 저자(연도) | 제목 | 발표처 | URL | 핵심 내용 | 신뢰도 |
|---|---|---|---|---|---|
| Talmor & Berant (2018) | The Web as a Knowledge-Base for Answering Complex Questions (ComplexWebQuestions) | NAACL-HLT 2018 | https://aclanthology.org/N18-1059/ | 단순 질의에서 **4 유형**을 규칙 생성: conjunction · superlative · comparative · composition | 피어리뷰 · **본문 확인** |
| Dubey et al. (2019) | LC-QuAD 2.0: A Large Dataset for Complex Question Answering over Wikidata and DBpedia | ISWC 2019 (Springer LNCS) | https://link.springer.com/chapter/10.1007/978-3-030-30796-7_5 | **10 유형 × 22 템플릿**, 30,000문항. 단일 fact / 타입 제약 단일 fact / multi-fact / qualifier fact / **two intention** / boolean / count / ranking / string operation / temporal | 피어리뷰 (**목록 밖**) · **본문 확인** |
| Gu et al. (2021) | Beyond I.I.D.: Three Levels of Generalization for Question Answering on Knowledge Bases (GrailQA) | WWW 2021 | https://dl.acm.org/doi/10.1145/3442381.3449992 | **일반화 축**(i.i.d. / compositional / zero-shot)을 **함수 축**(count · superlative argmax/argmin · comparative ≥≤ · 없음)과 별도로 둔다 | 피어리뷰 · 초록만 |
| Cao et al. (2022) | KQA Pro | ACL 2022 (Long) | https://aclanthology.org/2022.acl-long.422/ | 2장 참조 — KoPL 27 함수 + 진단 축 7종 | 피어리뷰 · **본문 확인** |
| Jia et al. (2018) | TempQuestions: A Benchmark for Temporal Question Answering | WWW 2018 **Companion** | https://dl.acm.org/doi/10.1145/3184558.3191536 | **시간 축을 독립 분류로 세운 벤치마크** — explicit temporal / implicit temporal / temporal answer / ordinal constraint 4범주, 1,271문항 | 피어리뷰 (**목록 밖·Companion**) · 초록만 |
| Saxena, Chakrabarti & Talukdar (2021) | Question Answering Over Temporal Knowledge Graphs (CronQuestions) | ACL 2021 (Long) | https://aclanthology.org/2021.acl-long.520/ | **축을 셋으로 분리해 보고한다** — 복잡도(simple/complex) · **답 유형**(entity/time) · 추론 유형(simple entity·simple time·before/after·first/last·time join) | 피어리뷰 · **본문 확인** |

## 4.1 확인된 사실

**LC-QuAD 2.0의 10 유형은 서로 다른 종류의 것이 섞여 있다.** 원문 §4.3의 이름 그대로다.

| # | 유형 | 축 성격 |
|---|---|---|
| 1 | Single fact | 홉 수 |
| 2 | Single fact with type | 홉 수 + 타입 제약 |
| 3 | Multi-fact (6 변형) | 홉 수 |
| 4 | Fact with qualifiers | 제약 종류 |
| 5 | **Two intention** | 의도 개수 |
| 6 | Boolean | 답 유형 |
| 7 | Count | 연산 |
| 8 | Ranking (3 변형) | 연산(최상급) |
| 9 | String operation | 연산 |
| 10 | Temporal aspect | 시간 |

이 목록 자체가 **단일 축이 아니다.** 홉 수·제약 종류·의도 개수·답 유형·연산·시간이 한 목록에 나란히 놓여 있다. 논문도 이를 "types of questions"라 부르고 축이라 부르지 않는다.

**"Two intention"은 우리 문헌 조사에서 나온 유일한 "한 질문에 요구가 둘" 명시 유형이다.**

> "This is a new category of query in KGQA, where the user question poses two intentions. ... such as 'Who is the wife of Barack Obama and where did he get married?' or 'When and where did Barack Obama get married to Michelle Obama?'"

**CronQuestions는 답 유형 축과 복잡도 축을 같은 표에서 따로 보고한다.** Table 7은 행이 `Simple / Complex / Entity Answer / Time Answer / Overall`이다 — 앞 둘과 뒤 둘이 다른 축이며, 같은 질문이 양쪽에 동시에 집계된다. Table 6의 추론 유형 5종별 Hits@1은 CronKGQA 기준 `Simple Entity 0.988 · Simple Time 0.985 · Time Join 0.511 · First/Last 0.371 · Before/After 0.288`로, **같은 시스템이 축의 위치에 따라 3배 넘게 갈린다.**

---

# 5. 비팩토이드 / 검색 의도 — 서술 요구를 쪼갠 축

| 저자(연도) | 제목 | 발표처 | URL | 핵심 내용 | 신뢰도 |
|---|---|---|---|---|---|
| Bolotova et al. (2022) | A Non-Factoid Question-Answering Taxonomy | SIGIR 2022, pp. 1196–1207 (**Best Paper**) | https://dl.acm.org/doi/10.1145/3477495.3531926 | **비팩토이드 질문을 6 범주로 쪼갠 최초의 종합 분류.** 범주와 함께 **기대되는 답의 구조**를 별도 차원으로 다룬다 | 피어리뷰 · 초록만 (본문 접근 실패 — 9장) |
| Broder (2002) | A Taxonomy of Web Search | ACM SIGIR Forum 36(2), 3–10 | https://dl.acm.org/doi/10.1145/792550.792552 | **검색 의도 1축 3클래스** — informational / navigational / transactional | 피어리뷰 (**목록 밖·Forum**) · 초록만 |
| Rose & Levinson (2004) | Understanding User Goals in Web Search | WWW 2004, pp. 13–19 | https://dl.acm.org/doi/10.1145/988672.988675 | Broder 3분류를 **계층으로 확장**하고 **resource-seeking**을 추가. navigational이 통념보다 적다고 보고 | 피어리뷰 · 초록만 |
| Qu et al. (2018) | Analyzing and Characterizing User Intent in Information-seeking Conversations | SIGIR 2018 | https://dl.acm.org/doi/10.1145/3209978.3210124 | MSDialog — 발화 단위 의도 주석. **의도 공기(co-occurrence)와 흐름 패턴을 분석 대상으로 삼는다** = 발화당 의도 하나를 가정하지 않음 | 피어리뷰 · 초록만 |

## 5.1 확인된 사실

**NF-CATS 범주 목록.** 저자들이 배포한 분류기 카드(`Lurunchik/nf-cats`)에 실린 라벨은 8개다: `NOT-A-QUESTION, FACTOID, DEBATE, EVIDENCE-BASED, INSTRUCTION, REASON, EXPERIENCE, COMPARISON`. 이 중 비팩토이드 범주는 6개(DEBATE·EVIDENCE-BASED·INSTRUCTION·REASON·EXPERIENCE·COMPARISON)이고 나머지 둘은 보조 라벨이다.

> **출처 주의**: 이 라벨 목록은 SIGIR 원문 PDF가 아니라 **저자 배포 모델 카드**에서 확인했다. 원문 본문은 접근하지 못했다(9장). 범주 개수·이름은 이 근거 수준에서만 쓴다.

**COMPARISON이 비팩토이드 범주 안에 별도로 존재한다**는 점이 우리 논의에 걸린다 — 비교는 서술 요구 안에서도 다른 범주로 취급된다.

---

# 6. 이종 소스 QA — 소스 선택 컴포넌트는 실제로 무엇을 쓰는가

우리 질문의 4번(라우팅 컴포넌트의 특징량)에 해당한다. **결론부터 적으면: 대표 시스템 다수가 질문→소스 라우팅을 하지 않는다.**

| 저자(연도) | 제목 | 발표처 | URL | 핵심 내용 | 신뢰도 |
|---|---|---|---|---|---|
| Chen et al. (2020) | HybridQA: A Dataset of Multi-Hop Question Answering over Tabular and Textual Data | Findings of EMNLP 2020 | https://aclanthology.org/2020.findings-emnlp.91/ | 표+텍스트 하이브리드 최초 데이터셋. 답 위치를 **In-Table / In-Passage**로 분리 보고 = 소스 축을 평가 축으로 씀 | 피어리뷰 · **본문 확인** |
| Chen et al. (2021) | Open Question Answering over Tables and Text (OTT-QA) | ICLR 2021 | https://openreview.net/forum?id=MmCRswl1UYl | HybridQA의 오픈도메인화. 표 40만·패시지 500만에서 **검색까지 요구**. fusion retriever로 표·텍스트를 한 공간에서 검색 | 피어리뷰 · **본문 확인** |
| Zhu et al. (2021) | TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance | ACL 2021 (Long) | https://aclanthology.org/2021.acl-long.254/ | **답 유형 × 답 소스를 교차표로 명시**(Table 2). 답 유형 4종(Span·Spans·Counting·Arithmetic) × 답 소스 3종(Table·Text·Table-text) | 피어리뷰 · **본문 확인** |
| Talmor et al. (2021) | MultiModalQA: Complex Question Answering over Text, Tables and Images | ICLR 2021 | https://openreview.net/forum?id=ee6W5UgQLa | 29,918문항, **35.7%가 교차 모달리티**. 단일 모달리티 질문을 형식 언어로 결합해 교차 질문을 생성 | 피어리뷰 · 초록만 |
| Oguz et al. (2022) | UniK-QA: Unified Representations of Structured and Unstructured Knowledge for Open-Domain Question Answering | Findings of NAACL 2022 | https://aclanthology.org/2022.findings-naacl.115/ | **소스 선택을 없앤다** — 표·리스트·KB를 전부 텍스트로 동질화한 뒤 단일 retriever-reader. KBQA에서 그래프 기반 대비 +11점 | 피어리뷰 · 초록만 |
| Christmann, Saha Roy & Weikum (2022) | Conversational Question Answering on Heterogeneous Sources (CONVINSE) | SIGIR 2022 | https://dl.acm.org/doi/10.1145/3477495.3531815 | **소스 무관 4슬롯 프레임(SR)** → 전 소스 균일 검색 → FiD 생성. 벤치마크 ConvMix 동시 공개 | 피어리뷰 · **본문 확인** |
| Christmann, Saha Roy & Weikum (2023) | Explainable Conversational Question Answering over Heterogeneous Sources via Iterative Graph Neural Networks (EXPLAIGNN) | SIGIR 2023 | https://dl.acm.org/doi/abs/10.1145/3539618.3591682 | CONVINSE 후속. 이종 근거를 하나의 그래프로 합쳐 GNN으로 반복 축약 | 피어리뷰 · 초록만 |
| Ma et al. (2023) | Chain-of-Skills: A Configurable Model for Open-Domain Question Answering | ACL 2023 (Long) | https://aclanthology.org/2023.acl-long.89/ | **스킬 5종**(single retrieval · expanded query retrieval · entity span proposal · entity linking · reranking)을 모듈화. 조합은 **질문이 아니라 대상 데이터셋/도메인 단위**로 고른다 | 피어리뷰 · **본문 확인** |
| Jeong et al. (2024) | Adaptive-RAG: Learning to Adapt Retrieval-Augmented LLMs through Question Complexity | NAACL 2024 (Long) | https://aclanthology.org/2024.naacl-long.389/ | **복잡도 축 하나만으로 라우팅** — 무검색 / 단일 스텝 / 다중 스텝 3분류. 분류기는 별도 소형 LM | 피어리뷰 · **본문 확인** |
| Shokouhi & Si (2011) | Federated Search | Foundations and Trends in Information Retrieval 5(1), 1–102 | https://dl.acm.org/doi/10.1561/1500000010 | 분산 IR의 **resource selection / collection selection** 정식화 — 소스 선택을 독립 문제로 다룬 계보의 표준 참조 | 피어리뷰 (**목록 밖·FnTIR**) · 초록만 |
| Callan, Lu & Croft (1995) | Searching Distributed Collections with Inference Networks (CORI) | SIGIR 1995, pp. 21–28 | https://dl.acm.org/doi/10.1145/215206.215328 | 컬렉션 선택의 고전 — **컬렉션을 큰 문서로 보고 쿼리 용어 통계로 순위**를 매긴다. 질문 유형 분류가 아니다 | 피어리뷰 · 초록만 |

## 6.1 확인된 사실 — CONVINSE의 4슬롯 프레임

CONVINSE의 structured representation(SR)이 **문헌에서 우리 "개체 × 요구 출력 형태" 2축에 가장 가까운 선례**다. 원문 §3의 정의다.

> "Specifically, an SR is a 4-tuple holding a slot for each of: **Context entities · Question entities · Question predicates · Expected answer types**."

각 슬롯의 역할을 원문이 이렇게 쓴다.

- **Question predicate**: *"the counterpart to the relation or attribute of interest in a logical form. However, it is merely a surface phrase, without any normalization or mapping to a KB. This way, it is easy to match it against any kind of information source."*
- **Answer type**: *"Expected answer types assist the answering model in detecting and eliminating spurious answer candidates."* 답의 **입도(granularity)**도 여기서 결정된다 — *"When is his birth date?"*는 `date`, *"When did they win their last world cup?"*는 `year`.

그리고 SR의 목적이 명시적으로 소스 무관이다.

> "SRs can be viewed as concise gists of user intents, intended to be in a form independent of any specific answering source."

> "The representation is purely on the question-level, and thus agnostic to the information sources that are used during the answering process."

**슬롯 제거 ablation 결과** (§ 실험, Table 11):

> "Question entities clearly are the most pivotal; answer types do not help much at retrieval time, but justify their importance during answering."

> **읽기 주의 (우리 판단으로 표시)**: 이 문장은 **소스 선택**이 아니라 **근거 검색(evidence retrieval)** 단계에 대한 것이다. CONVINSE는 애초에 소스를 고르지 않고 전 소스에서 검색한다. "답 유형이 검색에 별 도움이 안 된다"를 "답 유형이 라우팅에 쓸모없다"로 옮기면 과잉 해석이다.

## 6.2 확인된 사실 — ConvMix: 단일 소스 질문이 소수다

CONVINSE가 함께 공개한 ConvMix 벤치마크 통계다.

> "out of 3000 conversations, only 374 used exactly one source. A majority (1280) touched three sources, 572 touched four, while 774 used two inputs."

즉 **단일 소스로 끝난 대화는 12.5%**다. 그리고 논문은 이 라벨이 정답의 유일한 소재지가 아니라고 못 박는다.

> "note that this is only the source that the annotator used during her search process: it is quite possible that the answer can be located in other information sources ... thereby enabling future benchmark users to exploit answer redundancy."

**소스 중복은 성능을 올린다.** 상위 4개 근거 중 정답을 포함한 근거가 1·2·3·4개일 때 P@1이 각각 **0.428 → 0.658 → 0.713 → 0.763**이다. 그리고 전 소스 결합이 단일 소스·쌍 조합보다 체계적으로 높다.

> "Combining heterogeneous sources helps. ... These numbers are systematically and substantially higher than those in the columns for individual source types and even for pair-wise combinations."

## 6.3 확인된 사실 — TAT-QA의 교차표

Table 2가 **답 유형 × 답 소스**를 그대로 교차 집계한다 (총 16,552문항).

| 답 유형 \ 답 소스 | Table | Text | Table-text | 계 |
|---|---:|---:|---:|---:|
| Span | 1,801 | 3,496 | 1,842 | 7,139 |
| Spans | 777 | 258 | 1,037 | 2,072 |
| Counting | 106 | 5 | 266 | 377 |
| Arithmetic | 4,747 | 143 | 2,074 | 6,964 |
| **계** | **7,431** | **3,902** | **5,219** | **16,552** |

**어느 답 유형도 한 소스에 갇히지 않는다.** Arithmetic조차 Text 143건, Table-text 2,074건을 갖는다. 그리고 `Table-text` 열(5,219건, 31.5%)은 **두 소스를 동시에 요구하는 칸**이다.

## 6.4 확인된 사실 — 소스 선택을 하지 않는 두 갈래

| 접근 | 대표 | 무엇을 하나 |
|---|---|---|
| **동질화** | UniK-QA (Findings of NAACL 2022) | 표·리스트·KB를 전부 텍스트로 선형화한 뒤 단일 retriever-reader. 소스 선택 문제가 사라진다 |
| **균일 검색 후 융합** | CONVINSE / EXPLAIGNN (SIGIR 2022·2023), OTT-QA fusion retriever (ICLR 2021) | 소스 무관 표현으로 전 소스를 검색하고 점수로 상위 k개만 남긴다 |
| **도메인 단위 구성** | Chain-of-Skills (ACL 2023) | 스킬 조합을 질문마다가 아니라 **대상 데이터셋마다** 탐색해 고정한다 |
| **복잡도 단일 축 라우팅** | Adaptive-RAG (NAACL 2024) | 소스가 아니라 **검색 깊이**(무검색/단일/다중)를 고른다. 소스는 하나다 |

**질문 단위로 이종 소스 중 하나를 고르는 규칙 기반 라우터**를 정면으로 다룬 피어리뷰 문헌은 이번 조사에서 확인하지 못했다. 가장 가까운 것은 arXiv 단계 문헌이다(8장).

---

# 7. 축 대조표

각 체계가 **스스로** 별도 축·별도 유형으로 세운 것만 표시했다. 우리가 재분류하지 않았다.

범례: **●** 최상위 축으로 분리 / **○** 한 축 안의 클래스·연산으로 존재 / **–** 없음 / **n/a** 해당 없음

| 체계 (연도·발표처) | 축 개수 | 축 목록 | 답 유형 | 집계 | 비교·최상급 | 시간 | 멀티홉 | 부정·차집합 | 소스/모달리티 |
|---|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Li & Roth** (2002 COLING) | 1 (2계층) | 답의 의미 유형 | ● | – | – | ○(date) | – | – | – |
| **QDMR / Break** (2020 TACL) | 1 | 연산 시퀀스 (13종) | – | ○ AGGREGATE·GROUP | ○ COMPARATIVE·SUPERLATIVE·SORT | – | ○ 스텝 수 | ○ DISCARD | **명시적 비대상** (source-agnostic) |
| **KoPL / KQA Pro** (2022 ACL) | 2+ | locating / asking + 진단축 7종 | ○ | ● Count | ● Comparison | ○ Comparison 내 | ● Multi-hop | ○ 논리 연산 | – |
| **DROP** (2019 NAACL) | 2 | 답 유형 / 이산 연산 | ● | ● | ● | ○ | ○ | – | n/a (단일 소스) |
| **Spider** (2018 EMNLP) | 1 | SQL 복잡도 | – | ○ 키워드 개수 | ○ 키워드 개수 | – | ○ 조인·중첩 | ○ EXCEPT | n/a |
| **BIRD** (2023 NeurIPS D&B) | 4 | 질문 이해 / 지식 추론 / 데이터 복잡도 / SQL 복잡도 | – | ○ | ○ | – | ○ | ○ | n/a |
| **ComplexWebQ** (2018 NAACL) | 1 | 합성 유형 4종 | – | – | ● superlative·comparative | – | ● composition | – | – |
| **LC-QuAD 2.0** (2019 ISWC) | 1 (혼성 10종) | 질문 유형 | ● boolean | ● Count | ● Ranking | ● Temporal | ● Multi-fact | – | – |
| **GrailQA** (2021 WWW) | 2 | 일반화 수준 / 함수 | – | ● count | ● superlative·comparative | – | ○ 관계 수 | – | – |
| **TempQuestions** (2018 WWW Comp.) | 1 | 시간 범주 4종 | ○ temporal answer | – | ○ ordinal | ● | – | – | – |
| **CronQuestions** (2021 ACL) | 3 | 복잡도 / 답 유형 / 추론 유형 | ● entity·time | – | ● first/last, before/after | ● | ● time join | – | – |
| **NF-CATS** (2022 SIGIR) | 2 | 질문 범주 6종 / 기대 답 구조 | ● | – | ● COMPARISON | – | – | – | – |
| **Broder** (2002 SIGIR Forum) | 1 | 검색 의도 3종 | – | – | – | – | – | – | – |
| **Rose & Levinson** (2004 WWW) | 1 (계층) | 사용자 목표 + resource-seeking | – | – | – | – | – | – | – |
| **TAT-QA** (2021 ACL) | 2 | 답 유형 / **답 소스** | ● | ● Counting | ○ Arithmetic 내 | – | ○ | – | ● |
| **HybridQA** (2020 F-EMNLP) | 1+ | 답 위치 (In-Table/In-Passage) | – | – | – | – | ● | – | ● |
| **Adaptive-RAG** (2024 NAACL) | 1 | 질의 복잡도 3단 | – | – | – | – | ● | – | – (단일 소스) |
| **CONVINSE SR** (2022 SIGIR) | 4 슬롯 | 문맥 개체 / 질문 개체 / **질문 술어** / 기대 답 유형 | ● | – | – | ○ 답 입도 | – | – | **명시적 비대상** |
| **Rogers et al.** (2023 CSUR) | 5 (직교 명시) | 추론 / **검색** / 입력 해석·조작 / 세계 모델링 / 다단계 | ○ 형식 축 별도 | ○ 수치 스킬 | ○ 집합 연산 | ○ 세계 모델링 | ● 다단계 | ○ 집합 연산 | ○ 검색 축의 하위축 |
| **(참고) D9 현행** | 1 | 요구 출력 형태 4클래스 | ● | ○ 규칙 4 | – | – | – | – | – |

## 7.1 표에서 바로 읽히는 것 (사실)

1. **D9를 뺀 19개 체계 중 축이 1개인 것은 9개**다 (Li & Roth · QDMR · Spider · ComplexWebQ · LC-QuAD 2.0 · TempQuestions · Broder · Rose & Levinson · Adaptive-RAG). 그런데 **그 1축이 답 유형인 것은 Li & Roth 하나뿐이다.** 나머지 8개의 1축은 연산(QDMR), SQL 복잡도(Spider), 합성 유형(ComplexWebQ), 혼성 목록(LC-QuAD 2.0), 시간(TempQuestions), 검색 의도(Broder·Rose & Levinson), 질의 복잡도(Adaptive-RAG)다.
2. **집계·비교/최상급을 답 유형의 하위 클래스로 둔 체계는 하나도 없다.** 전부 별도 축이거나 별도 연산이다. LC-QuAD 2.0만 답 유형(boolean)과 연산(Count·Ranking)을 같은 목록에 나란히 놓는데, **그 목록 자체가 단일 축이 아니다**(4.1).
3. **시간을 최상위 유형·축으로 세운 체계가 셋**이다 (LC-QuAD 2.0, TempQuestions, CronQuestions). 어느 것도 답 유형의 하위 클래스로 두지 않았다.
4. **소스/모달리티를 축으로 세운 것은 셋**이다 (TAT-QA, HybridQA, Rogers et al.). 그리고 그중 어느 것도 그 축을 **입력 질문의 분류 축**으로 쓰지 않는다 — 전부 **정답이 어디 있었는지를 사후 집계**하는 평가 축이다.
5. **소스 무관을 설계 목표로 명시한 것이 둘**이다 (QDMR, CONVINSE SR).

---

# 8. arXiv-only / 신뢰도 미달 — 분리 기재

> **본 서지 표에 올리지 않는다.** 아래는 우리 문제 설정(질문 → 이종 소스 도구 중 택일)에 가장 가까운 문헌인데, 전부 피어리뷰 게재본을 확인하지 못했다. **인용 논거로 쓰지 않고, 우리가 놓친 것이 있는지 확인하는 용도로만 남긴다.**

| 저자(연도) | 제목 | 발표처 | URL | 핵심 내용 | 신뢰도 |
|---|---|---|---|---|---|
| Rathore et al. (2026) | Conversational Query Engine for Mixed-Modality Heterogeneous Enterprise Data Sources (COGNI) | arXiv:2606.28370 (2026-06-15) | https://arxiv.org/abs/2606.28370 | **라우터가 2축 출력을 낸다 — "modality decision and complexity assessment".** 정형 웨어하우스 vs 비정형 문서 저장소. LoRA 파인튜닝 Qwen-2.5-1.5B-Instruct, **라우팅 정확도 93.8%**, 프런티어 모델 대비 약 7배 저비용 | **arXiv-only** |
| Baek et al. (2026) | OmniRetrieval: Unified Retrieval across Heterogeneous Knowledge Sources | arXiv:2605.29250 (2026-05-28) | https://arxiv.org/abs/2605.29250 | 자연어 질의에서 **적합한 지식 소스를 식별해 소스 고유 질의를 각 실행 엔진에 디스패치.** 텍스트·관계형 테이블·지식 그래프·프로퍼티 그래프. 13 데이터셋·309 지식베이스 | **arXiv-only** |

**두 편의 공통점 (사실)**: 둘 다 2026년 프리프린트이고, 둘 다 **라우터를 학습 모델로 둔다.** 규칙 기반 라우터로 이 문제를 푼 피어리뷰 문헌은 이번 조사에서 확인하지 못했다.

---

# 9. 확인 실패·주의 (조사 중 확인된 사실)

| 항목 | 상태 |
|---|---|
| **Bolotova et al. (2022) SIGIR 원문 본문** | ACM DL이 PDF 접근을 차단(403). 대체 경로(QUT eprints, RMIT 저장소) 전부 실패. **범주 6종의 이름은 저자 배포 분류기 카드(`huggingface.co/Lurunchik/nf-cats`)에서만 확인했고, 각 범주의 정의와 "기대 답 구조" 차원의 내용은 확인하지 못했다.** 발표처·페이지(SIGIR '22, pp. 1196–1207)·Best Paper 수상은 확인됨 |
| **Ferrucci et al. (2010), Building Watson: An Overview of the DeepQA Project (AI Magazine 31(3))** | DeepQA의 질문 분석이 LAT·focus·question classification·relation detection·decomposition을 병렬로 수행한다는 것이 다축 분석의 유력한 선례로 보였으나, **AAAI OJS·Wiley 어느 경로에서도 본문을 확보하지 못했다.** 내용 주장을 하지 않고 이 문서에서 뺐다 |
| **MultiModalQA의 질문 유형 개수·템플릿 구조** | OpenReview가 봇 검증 화면을 반환해 본문 미확인. 초록 수준 사실(29,918문항, 교차 모달리티 35.7%, ICLR 2021)만 기재 |
| **GrailQA의 함수 축 원문 표기** | WWW 2021 게재본(dl.acm) 접근 실패. 함수 4종(count·superlative·comparative·없음)과 3단계 일반화는 검색 결과 및 저자 배포본 기준이며 **본문 대조는 하지 못했다** |
| **dl.acm.org URL 전반** | curl HEAD가 403을 반환한다(봇 차단). URL 자체는 검색 결과에서 **제목과 짝지어 반환된 정식 DOI 경로**이며, [related-work.md](./related-work.md)가 이미 같은 형식으로 쓰고 있다. 브라우저 접근은 정상으로 판단하나 **자동 확인은 불가**했다 |
| **"질문 유형 → 도구 선택" 규칙을 다룬 피어리뷰 문헌** | **찾지 못했다.** 6장의 시스템들은 전부 소스 선택을 회피(동질화·균일 검색)하거나 다른 축(복잡도·도메인)으로 고른다. 8장의 두 편이 우리 문제에 가장 가깝지만 arXiv-only다. **"없다"가 아니라 "이번 조사 범위에서 확인하지 못했다"** |

---

# 10. 우리 설계와의 연결

## 10.1 사실 요약 — D9와 문헌의 대조

| 문헌이 말한 것 | D9 현행 |
|---|---|
| 답 유형 1축의 원형(Li & Roth)이 **경계 불명확을 이유로 다중 라벨을 허용**했다 | 4클래스 배타 단일 선택 (X3·X4만 병렬 예외) |
| 분해 형식주의(QDMR·KoPL)는 연산 축을 **정보 소스와 명시적으로 분리**한다 | 형태 축 하나로 소스(도구)를 결정 |
| **집계·비교/최상급·시간을 답 유형에 흡수한 체계가 없다** | 규칙 4로 집계만 특별 취급, 비교·최상급·시간은 규칙에 없음 |
| Spider의 1축 난이도를 **BIRD가 4차원으로 교체**하며 이유를 명시 | 축을 늘린 적 없음 |
| 이종 소스 QA에서 소스는 **답 유형과 교차표**로 다뤄진다 (TAT-QA) | 형태 → 도구 단사(單射) 가정 |
| ConvMix 3,000 대화 중 **단일 소스는 374건(12.5%)** | questions.json 30/30이 도구 1개 (`tool`이 문자열) |
| 소스 무관 표현의 표준형은 **4슬롯**(문맥 개체·질문 개체·**질문 술어**·기대 답 유형) — CONVINSE | (개체 × 요구 출력 형태) 2축 검토 중 |
| Rogers et al.: **"출력 형식과 추론 유형을 혼동하지 말라"** | 도구 경계 = 출력 형태 |

## 10.2 우리 판단

> **아래는 문헌의 주장이 아니라 우리 해석이다.**

### (1) 2축은 문헌 표준보다 한 슬롯 부족하다 — 빠진 것은 **술어/관계**다

문헌에서 "개체 × 요구 출력 형태"에 가장 가까운 선례는 CONVINSE의 SR이고, 그것은 4슬롯이다. 슬롯을 우리 언어로 옮기면 이렇다.

| CONVINSE 슬롯 | 우리 2축 | 상태 |
|---|---|---|
| Question entities | 개체 | 있음 |
| Context entities | (대화 문맥 — 우리는 단일 턴) | 해당 없음 |
| **Question predicates** | — | **없음** |
| Expected answer types | 요구 출력 형태 | 있음 |

우리에게 술어 슬롯이 왜 필요한가는 **D9 규칙 3·4가 이미 답하고 있다.** 규칙 3("개체 식별·연결")과 규칙 4("관계를 세는 집계")는 둘 다 **관계(술어)를 명시적으로 언급한다.** 형태만 보는 규칙이 아니다.

### (2) D9는 이미 2축을 쓰고 있는데 1축 4클래스로 표기돼 있다

규칙 4를 분해하면 이렇다.

> **"관계를 세는 집계"** = **연산 축**(집계) × **피연산자 축**(관계) 의 교차 조건

이것은 규칙 1~3과 **같은 종류의 술어가 아니다.** 규칙 1~3은 "무엇을 요구하는가"이고, 규칙 4는 "어떤 연산을 무엇 위에서 하는가"다. D9 본문이 규칙 4를 *"세는 대상이 관계이므로 규칙 3에 귀속"*이라고 적은 것 자체가, **규칙 4가 형태 축의 독립 클래스가 아님을 우리 손으로 인정한 서술**이다.

**이것이 #5 불일치가 원칙적 규칙으로 해소되지 않는 구조적 이유일 수 있다.** #5·#25·#29는 셋 다 *관계 카운트의 최대*다 — 문헌 어휘로는 **AGGREGATE(count) + SUPERLATIVE(argmax)** 합성이고, QDMR에서 최소 3~4 스텝이다(SELECT → PROJECT → GROUP → SUPERLATIVE). 단일 축 위의 클래스 하나로는 이 합성을 표현할 자리가 없고, 그래서 규칙을 어느 쪽으로 뒤집어도 상한이 29/30에서 멈춘다([design.md](../design.md) D9 검증 항).

> **주의**: 이것은 **재기술(re-description)이지 반증이 아니다.** 축을 늘려도 #5는 여전히 맞지 않는다 — #5의 문제는 축 부족이 아니라 데이터셋 내부 비일관성이기 때문이다(D7). **축을 늘리면 29/30이 30/30이 된다는 주장은 성립하지 않는다.**

### (3) 그러면 축을 늘려야 하는가 — **라우팅 규칙은 그대로 두고, 엣지 세트 설계에만 쓴다**

"이걸 하면 무엇이 달라지는가"에 답할 수 있는 지점은 하나뿐이다.

| 후보 | 무엇이 달라지나 | 판단 |
|---|---|---|
| D9 규칙 자체를 2축으로 재작성 | **29/30 그대로.** 같은 판정을 다르게 적는 것 | ❌ 하지 않는다 |
| 라우터 구현을 2축 격자로 | 도구 3종에 대한 출력이 동일. 복잡도만 증가 | ❌ 하지 않는다 |
| **자체 엣지 세트(D7)의 케이스 격자에 사용** | **어느 칸을 안 써봤는지가 드러난다.** 지금 엣지 세트는 자산 중복·도구 실패 축으로만 짜여 있고, **연산 축(집계·비교·최상급·시간·멀티홉)으로 훑은 적이 없다** | ✅ **여기만 값이 있다** |
| 도구 설명(description) 문안 | D9 마지막 항이 이미 형태 축으로 못 박았고 근거(Hasan et al.)도 있다 | ❌ 건드리지 않는다 |

**구체적으로 엣지 세트에서 비어 있을 가능성이 높은 칸** (우리 판단). "검증됐나" 칸의 근거는 [dataset-analysis.md](../dataset-analysis.md) §5뿐이며, **questions.json 30개를 연산 축으로 전수 분류한 적은 없다** — 아래는 그 분류를 하기 전의 추정이다.

| 연산 축 | 우리 데이터셋에서 가능한가 | 현행 D9가 보내는 곳 | 검증됐나 |
|---|---|---|---|
| 집계 (count) | 예 — 관계 카운트·행 카운트 둘 다 | 규칙 4 → `knowledge_graph` / 규칙 2 → `nl2sql` | **#5 불일치 지점.** #5·#25·#29 3건이 이 형태 |
| **최상급 (argmax/argmin)** | 예 — "가장 많은", "상위 5개" | 규칙 2 또는 4 (**규칙 문면에 최상급이라는 말이 없다**) | 집계와 겹친 형태로 3건 존재. **최상급 단독**(집계 없는 argmax) 케이스는 미확인 |
| **비교 (>, <)** | 예 — 금액·기간·연봉 비교 | 규칙 2 추정 | **규칙에 없음** |
| **시간 제약** | 예 — `contracts` 기간, `sales` 날짜, 티켓 시각 | 규칙 2 추정. 단 *"최근 서버 장애 사례와 원인"*은 규칙 1 → `vector_search` | **규칙에 없음. 서술+시간 복합이 규칙 1과 2에 동시에 걸린다** |
| **멀티홉** | 예 — 그래프 재귀 CTE가 이 용도다 (D5) | 규칙 3 → `knowledge_graph` | 단일 홉만 검증됨 |
| 부정·차집합 | 예 — "계약 없는 고객사" | 미정 | **규칙에 없음** |

**"시간 제약" 행이 가장 걸린다.** *"최근 서버 장애 사례와 원인을 알려줘"*는 [design.md](../design.md)의 도구별 예시 표에 **규칙 1(서술) → `vector_search`**로 실려 있다. 그런데 이 질문은 시간 제약(`최근`) + 사건 목록 + 원인 서술의 복합이고, **구조적으로 X3(상보 중복 — 티켓 목록 + 문서 서술)의 정의와 일치한다.** 형태 축 하나로는 "최근"이 어디로 가는지가 보이지 않는다.

### (4) 데이터셋을 문헌보다 먼저 대조해야 한다

위 표의 "가능한가" 칸은 **스키마에서 추정한 것이고, 실측이 아니다.** [reading-priority.md](../reading-priority.md) 티어 3 방침대로, 연산 축을 실제로 열려면 **문헌이 아니라 `companyx-dataset-v1.0`을 먼저 대조**해야 한다 — 구체적으로 각 연산이 성립하는 칼럼·관계가 실제로 있는지, 그리고 그것이 [dataset-analysis.md](../dataset-analysis.md) 3장의 격자 희소성과 어떻게 겹치는지.

**이 조사는 그 대조를 대체하지 않는다.** 문헌이 말해주는 것은 *"이런 축들이 존재하고, 어느 체계도 이것들을 답 유형에 흡수하지 않았다"* 까지다.

### (5) 심사 답변에 쓸 수 있는 형태

> D9는 **답 유형(요구 출력 형태) 축**을 라우팅 축으로 쓴다. 이는 Li & Roth(COLING 2002) 이래 QA 분류의 표준 축이다. 문헌의 다축 체계(QDMR 13연산, BIRD 4차원, CronQuestions 3축)는 **평가·진단용 축**이지 소스 선택 축이 아니며, 이종 소스 QA의 대표 시스템들은 소스 선택 자체를 **회피**한다 — UniK-QA는 전부 텍스트로 동질화하고, CONVINSE는 소스 무관 4슬롯 표현으로 전 소스를 균일 검색한다. **우리가 소스를 고르는 이유는 도구 3종이 MCP 도구로 분리 등록돼야 한다는 과제 요건이고**, 그 조건에서 형태 축이 이 데이터셋에서 29/30을 낸다는 것이 실측 결과다.

이 서술의 장점은 **"왜 다축을 안 썼는가"에 방어적으로 답하지 않는다**는 점이다. 다축 체계들이 애초에 다른 문제(평가·진단)를 푼다는 것이 사실이기 때문이다.

## 10.3 다음에 열어야 할 것

| 항목 | 무엇을 하나 | 선행 조건 |
|---|---|---|
| **자체 엣지 세트에 연산 축 추가** (D7) | 10.2 (3)의 6개 연산 칸별로 케이스 작성 | **데이터셋 대조 먼저** (10.2 (5)) |
| **"최근/기간" 같은 시간 표현의 라우팅** | 규칙 1과 2에 동시에 걸리는 구간을 X3에 포함할지 판정 | 위와 동일 |
| Bolotova et al. 원문 확보 | 규칙 1(서술 요구)이 6 범주로 쪼개지는지 확인 | ACM DL 접근 경로 |
| 술어 슬롯의 실효성 | 술어를 추출하면 규칙 3·4 판정이 더 안정되는지 | 공통부 구현 후 |
