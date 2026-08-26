# 한국어 활용형 매칭 문헌 조사 — 표층 사전 · 형태소 분석 · 문자 n-gram · 소형 임베딩

> 조사 문서 (2026-08-26, 이슈 #32 의 `이끄`↔`이끌고` 활용형 누락에 대응). 핵심 1차 출처:
> Popovič & Willett (1992, JASIS) · Larkey et al. (2002, SIGIR) · Lee, Cho & Park (1999, IP&M) ·
> McNamee & Mayfield (2004, Information Retrieval) · Park et al. (2018, ACL) · Park et al. (2020, AACL) ·
> Casanueva et al. (2020, NLP4ConvAI) · 국립국어원 한글 맞춤법 제18항.
> 인용 수는 **OpenAlex / Semantic Scholar, 2026-08-26 조회** 기준이며 출처가 다르면 병기한다.
> 확인 못 한 값은 "미확인"으로 적는다. 전체 서지는 말미 [출처 목록](#출처-목록).

## 한 줄 요약

문헌은 검토 중인 세 갈래 중 **① 어간을 불변 접두사로 축소하고 ㄹ 탈락 동사만 짝을 추가하는 쪽을 지지한다** — 형태 변화가 많은 언어에서 얕은 어간 축약·절단이 검색 효과를 크게 올리고(Popovič & Willett 1992), 깊은 형태소 분석은 얕은 방법 대비 우위가 없거나 오히려 밀리며(Larkey 2002 · Lee/Cho/Park 1999), ㄹ 탈락은 규범에 명문화된 **닫힌 규칙**이라 짝 추가가 휴리스틱이 아니라 규칙의 전개이기 때문이다(한글 맞춤법 제18항). ② 형태소 분석기는 문서 검색 규모의 업계 표준이지만 관계 어휘 22개·질문 59개 규모에선 분석기 자체 오류율(6~13%)이 새 오류원이 되고, ③ 현상 유지는 결함이 한 줄 수정으로 닫히는 이상 비용-효과 논거가 성립하지 않는다 — 단 ① 이후에도 남는 교체 부류(ㅡ 탈락 등)의 문서화는 ③의 몫이다.

## 조사 질문과 우리 판단 기준

소형 모델(num_ctx 4096) + 규칙 기반 도구에서, 한국어 질문을 `q.includes(w)` 문자열 포함으로 지식그래프 관계 7종에 매칭한다. 실측 결함: `RELATION_WORDS.LEADS` 의 `이끄` 가 `이끌고` 를 못 잡는다 (`knowledge-graph.ts:13-24`, 이슈 #32). 활용(活用)이란 동사·형용사가 어미에 따라 모양을 바꾸는 것이고, 어간(stem)은 그때 변하지 않(는다고 기대되)는 앞부분이다.

비교 대상 4접근:

| | 접근 | 한 줄 정의 |
|---|---|---|
| (a) | 부분문자열/어간 사전 | 표층형·어간 목록을 두고 문자열 포함으로 매칭. "불변 접두사 축소"는 활용해도 변하지 않는 최장 앞부분만 사전에 남기는 것 |
| (b) | 형태소 분석기 | MeCab-ko·Kiwi 등으로 질문을 형태소(뜻을 가진 최소 단위)로 쪼갠 뒤 기본형으로 매칭 |
| (c) | 문자 n-gram / 서브워드 | 글자를 n개씩 겹쳐 자른 조각(n-gram)이나, 자주 나오는 글자 조합 단위(서브워드)로 매칭 |
| (d) | 소형 임베딩 | 문장을 숫자 벡터로 바꾸는 모델(임베딩)로 질문과 관계 설명의 유사도를 재서 매칭 |

## 접근별 문헌 근거

각 논문에 **[설계 판정]** 을 붙인다 — 베이스라인·데이터 규모·공개 여부·절제 실험(ablation, 구성 요소를 하나씩 빼고 재보는 것)·재현 가능성, 그리고 결론이 비교 설계의 어떤 약점에 기대는지.

### (a) 어간·접두사 사전 매칭 — LLM 이전 정보검색이 이미 결론 낸 자리

**Popovič & Willett (1992). "The effectiveness of stemming for natural-language access to Slovene textual data." JASIS 43(5).** 셰필드대·슬로베니아 국립도서관. 인용 167 (OpenAlex). 같은 문서·질의 세트를 영어판과 슬로베니아어판으로 병렬 구축해 어간 축약(stemming)의 효과를 비교했다. 영어에서는 유의한 개선이 없고, 형태 변화가 많은 슬로베니아어에서는 **크고 통계적으로 유의한 개선**이 났다. 결정적으로 **수동 우측 절단(단어 앞부분만 남기고 자르는 것)도 비슷한 효과**를 냈다 — 우리 "불변 접두사 축소"가 바로 이 조작이다. 결론: "어간 축약 알고리즘의 효과는 그 언어의 형태론적 복잡도가 결정한다."
**[설계 판정]** 강점 — 같은 내용을 두 언어로 비교해 언어 요인만 분리한 드문 설계, 유의성 검정 보고. 약점 — 컬렉션 규모 미확인(당시 관행상 소규모), 1990년대 검색 모델. 수치는 이전 불가, **방향(형태 복잡도↑ → 어간 축약 효과↑)은 이후 독일어에서 재확인**됐다(Braschler & Ripplinger 2004, 인용 112 — 독일어 검색에서 어간 축약·복합어 분해가 유의한 개선).

**Larkey, Ballesteros & Connell (2002). "Improving stemming for Arabic information retrieval: light stemming and co-occurrence analysis." SIGIR 2002.** UMass Amherst. 인용 361 (OpenAlex). TREC-2001 아랍어 컬렉션에서 접사 몇 개만 떼는 **가벼운(light) 어간 축약이, 어근까지 파고드는 형태소 분석기를 이겼다**.
**[설계 판정]** 강점 — 표준 벤치마크(TREC-2001), 여러 어간 축약기 절제 비교. 약점 — 아랍어는 내부 굴절(단어 속이 변함) 언어라 접미 교착(어미가 뒤에 붙음)인 한국어와 형태론이 다르다. 이전되는 것은 수치가 아니라 **"얕은 방법이 깊은 분석과 대등하거나 우위"라는 방향**이다.

곁가지: Kraaij & Pohlmann (1996, SIGIR, 인용 163)은 어간 축약을 "재현율(놓치지 않는 비율) 확장 장치"로 규정했다 — 우리 결함이 정확히 재현율 구멍(활용형을 놓침)이라는 진단과 맞는다.

### (b) 형태소 분석기 — 업계 표준이지만, 문헌은 "필수"를 지지하지 않는다

**Lee, Cho & Park (1999). "n-Gram-based indexing for Korean text retrieval." Information Processing & Management 35(4).** KAIST·숭실대. 인용 34 (OpenAlex). 한국어 색인의 두 전통(어절 어간 색인 vs 형태소 색인)을 정리하고 n-gram 색인과 비교했다. 초록의 결론: **"n-gram 색인이 형태소 색인보다 상당히 빠르고, 검색 효과도 더 좋다"** — 사전도 언어 지식도 없이. 형태소 색인의 강점(복합명사 분해)조차 n-gram이 사전 없이 대체했다.
**[설계 판정]** 강점 — 한국어 대상 직접 비교, 세 색인 방식 동일 조건. 약점 — **결론이 당시 형태소 분석기의 사전 커버리지에 의존한다**. 분석기가 좋아진 지금(아래 Kiwi) 뒤집힐 여지가 있고, 사용 컬렉션 규모는 미확인. 그래도 "형태소 분석 없이는 안 된다"는 주장의 반례로는 충분하다.

**이민철 (2024). "Kiwi: 통계 언어 모델과 Skip-Bigram을 이용한 한국어 형태소 분석기." 한국디지털인문학회지 1(1):109-136.** 소속 미확인(오픈소스 개인 프로젝트), 인용 미확인. 현세대 분석기의 실측 상한을 보여준다: 문어 정확도 약 94%, 웹 텍스트 약 87%, 모호성 해소 평균 86.7% (세종 말뭉치·모두의 말뭉치 평가). 0.12.0부터 불규칙 활용 표지를 태그에 부착 — **ㄹ 탈락·불규칙 활용을 분석기가 원리적으로 다 잡는다**는 뜻이다.
**[설계 판정]** 강점 — 코드·평가 스크립트 공개(GitHub bab2min/Kiwi)로 재현 가능. 약점 — 개발자 자체 평가, 국내 신생 저널. 우리 맥락에 중요한 숫자는 정확도가 아니라 **오류율**이다: 6~13%의 분석 오류가 59문항 규모에선 문항 수 개 단위의 새 오류원이 될 수 있다.

업계 관행 참고: Lucene/Elasticsearch 의 공식 한국어 분석기 nori 는 mecab-ko-dic(세종 말뭉치 계열 사전) 기반 형태소 분석이다(LUCENE-8231, Elastic 공식 문서). 즉 **열린 어휘·문서 수백만 건** 규모에서는 형태소 분석이 표준이다 — 다만 이것은 관행 증거이지 통제 비교가 아니고, 규모 전제가 우리와 다르다. 파이썬 접근층 KoNLPy(Park & Cho 2014, 한글 및 한국어 정보처리 학술대회)는 도구 논문이라 비교 설계 판정 대상이 아니다 (인용 수 OpenAlex/S2 검색 실패, 미확인).

### (c) 문자 n-gram / 서브워드 — 한국어에서 가장 오래 검증된 우회로

**Lee & Ahn (1996). "Using n-grams for Korean text retrieval." SIGIR 1996.** 한국과학기술정보연구원(KISTI, OpenAlex 표기). 인용 73 (S2) / 81 (OpenAlex). 한국어 n-gram 검색 계열의 출발점. 초록을 직접 확보하지 못해 실질 비교는 위 1999년 후속(IP&M)으로 인용한다.

**McNamee & Mayfield (2004). "Character N-Gram Tokenization for European Language Text Retrieval." Information Retrieval 7(1-2):73-97.** 존스홉킨스대 응용물리연구소. 인용 385 (S2) / 332 (OpenAlex). CLEF 다국어 컬렉션 8개 유럽어에서, 겹치는 문자 n-gram 색인이 **언어별 맞춤 기법(어간 축약 등)의 최고 성능에 필적**함을 보였다. 대가는 저장 공간·시간 증가.
**[설계 판정]** 강점 — 표준 다국어 컬렉션에서 동일 파이프라인으로 언어 간 일관 비교. 약점 — 유럽어·문서 검색이라 교착어 단문 매칭엔 방향만 이전. 같은 저자의 NTCIR-3 실험(McNamee 2002, 인용 7)이 한국어 포함 아시아어에도 같은 "언어 지식 없는" 접근을 적용했다.

**Park, Byun, Baek, Cho & Oh (2018). "Subword-level Word Vector Representations for Korean." ACL 2018.** KAIST·서울대. 인용 45 (OpenAlex). 한국어 단어를 음절이 아니라 **자모 수준까지 분해**하면 서브워드 정보가 체계적으로 쓰여, word2vec·음절 단위 모델을 유사도·유추·감성 분석에서 이겼다. 우리 결함의 기제를 정확히 설명한다: `이끌고`와 `이끄는`은 **음절 문자로는 둘째 글자부터 다르지만(끌≠끄) 자모로는 ㅇㅣㄲㅡ 를 공유**한다. 음절 단위 부분문자열 매칭은 이 공통 접두사를 원리적으로 볼 수 없다.
**[설계 판정]** 강점 — 문자 단위 대비 자모 단위의 절제 비교, 코드·평가셋 공개. 약점 — 평가셋을 저자들이 직접 만들었다(공개했으니 검증 가능하나 자작 벤치마크 일반의 주의). 결론의 방향은 아래 2020 논문이 독립적으로 재확인.

**Park, Lee, Jang & Jung (2020). "An Empirical Study of Tokenization Strategies for Various Korean NLP Tasks." AACL-IJCNLP 2020.** Kakao Brain·Scatter Lab (논문 기재 기준 — OpenAlex 기관 매칭은 이 논문에서 오류라 신뢰하지 않는다). 인용 31+19 (OpenAlex, 학회판+arXiv판 분산). 자모·음절·형태소·BPE(자주 나오는 글자 쌍을 병합해 단위를 만드는 서브워드 알고리즘)·형태소+BPE 를 KorQuAD·KorNLI·KorSTS·NSMC·PAWS-X·기계번역에서 전면 비교했다. 결과: **형태소 분석 후 BPE를 얹는 혼합이 대부분 과업에서 최선**, KorQuAD 만 BPE 단독이 최선.
**[설계 판정]** 강점 — 공개 과업 6종, 어휘 크기 통제, 코드·모델 공개(kakaobrain/kortok) — 이번 조사에서 비교 설계가 가장 건전한 논문. 약점 — 사전학습 트랜스포머 설정이라 어휘 매칭 파이프라인으로 수치가 직접 이전되지 않는다. 이전되는 것은 "**형태소 정보와 서브워드는 배타가 아니라 병용이 최선**"이라는 구도다.

### (d) 소형 임베딩 유사도 — 의도 분류에선 강하지만, 예시가 있어야 한다

**Reimers & Gurevych (2019). "Sentence-BERT." EMNLP 2019.** TU Darmstadt. 인용 11,702 (OpenAlex). 문장 임베딩 유사도 비교의 기반 기법 — (d) 계열의 공통 토대라 서지만 둔다.

**Casanueva, Temčinas, Gerz, Henderson & Vulić (2020). "Efficient Intent Detection with Dual Sentence Encoders." NLP4ConvAI 워크샵 @ ACL 2020.** PolyAI. 인용 661 (S2 — OpenAlex 는 23으로 레코드 분산, S2 쪽을 신뢰). BANKING77(단일 도메인 77개 의도, 13,083 예시) 공개와 함께, 고정 문장 인코더 + 얕은 분류기가 **의도당 예시 10개만으로 85.19%** (USE+ConveRT, BANKING77), BERT 고정 인코더(67.55%)를 크게 이김을 보였다. CPU 로 수 분 안에 학습.
**[설계 판정]** 강점 — 데이터·코드 공개, 3개 데이터셋, few-shot(적은 예시) 프로토콜 명확. 약점 — 영어 전용, 워크샵 논문(피어리뷰는 통과), 그리고 **의도당 예시 10개가 전제**다. 우리는 관계당 라벨된 질문 예시가 사실상 0개다(59문항은 평가 세트라 튜닝에 못 쓴다 — harness-evaluation 6절의 오염 방침).

**Chen et al. (2024). "M3-Embedding." Findings of ACL 2024.** BAAI. 인용 536+59 (OpenAlex, 학회판+arXiv판). 한국어를 포함한 다국어 검색 벤치마크(MIRACL)에서 검증된 임베딩 — **우리가 이미 라우터 도구 선택에 쓰는 bge-m3 의 원 논문**이다. 사내 실측이 이 접근의 우리 규모 성능을 이미 재 놨다: 시그니처 임베딩 argmax 단독 24/30, 규칙 게이트 병용 26/30 (design.md D12, harness-evaluation 4절) — **임베딩 단독은 규칙 병용보다 낮았다**.

곁가지: 지식그래프 관계 링킹 자체를 규칙+n-gram 으로 푼 선례로 Falcon(Sakor et al. 2019, NAACL, 인용 86)이 있다 — 영어 단문에서 형태 규칙과 n-gram 타일링만으로 당시 학습 기반을 이겼다. 영어 한정이라 방향 증거로만 둔다.

## 한국어 특수성 — ㄹ 탈락은 예외가 아니라 닫힌 규칙이다

**규범 근거.** 한글 맞춤법 **제18항 1호** "어간의 끝 'ㄹ'이 줄어질 적": 갈다 → 가니·간·갑니다·가시다·가오 (국립국어원, 한국어 어문 규범). ㄹ 말음 어간은 ㄴ·ㅂ·시·오 계열 어미 앞에서 ㄹ이 떨어진다. 이 교체는 **조건이 완전히 예측 가능**해서 학교문법이 규칙 활용으로 다루는 부류다. 따라서:

- ㄹ 말음 동사의 표층형은 음절 표기에서 정확히 **두 가지 접두사**로 갈린다 — `이끌-`(이끌고·이끌면·이끌어) / `이끄-`(이끄는·이끄니·이끕니다의 이끕 제외). 사전에 `이끌`·`이끄` 짝을 두면 이 부류의 활용을 (ㅂ니다 계열 제외) 전부 덮는다. **짝 추가는 휴리스틱이 아니라 제18항의 전개다.**
- 음절 문자가 문제의 근원이다: 자모 공통 접두사 ㅇㅣㄲㅡ 가 음절로 합쳐지며 끌/끄 로 갈라져, 음절 단위 부분문자열 매칭이 보지 못한다(Park et al. 2018 의 자모 분해가 이 기제의 체계적 해법).
- 접두사 짝으로도 못 잡는 교체 부류가 남는다: ㅡ 탈락(쓰다 → 써·씁니다), 하다 축약(관리하다 → 관리해·관리합니다), ㅂ 불규칙(돕다 → 도와). 이들은 자모 수준 매칭이나 형태소 분석이 있어야 완전히 잡힌다.

## 우리 맥락으로의 사상 — 관계 7종 · 표층 22개 · 질문 59개

**전수 실측 (2026-08-26, 이 조사에서 직접 확인).** 두 질문 세트 59문항의 용언 활용형을 현행 사전과 대조한 결과: 누락은 **X1-01 `이끌고` 단 1건**이다. `이끄는` 2건(X5-03, companyx)은 현행 `이끄` 가 잡고, `쓰고` 2건은 `쓰고` 가, `사용하고/사용하는/사용 중` 4건은 `사용` 이, `담당하는/담당하고` 6건은 `담당` 이 잡는다. `써·씁니다·관리해·속해` 형은 세트에 등장하지 않는다. 즉 **①의 남은 구멍(ㅡ 탈락 등)은 이 세트에서 실측 0건**이다.

| 갈래 | 문헌 판정 | 이 규모에서의 비용/효과 |
|---|---|---|
| **① 불변 접두사 축소 + ㄹ 탈락 짝** | **지지** — 형태 복잡 언어에서 절단·얕은 축약이 유효(Popovič & Willett), 깊은 분석 대비 대등 이상(Larkey), ㄹ 짝은 닫힌 규칙(제18항) | 수정 몇 줄, 의존성 0. 위험은 접두사 과단축의 과매칭(예: `관리하`→`관리` 로 줄이면 "관리자" 류에도 걸림) — 정밀도 하락 여부는 59문항+xcheck 로 즉시 측정 가능 |
| **② 형태소 분석기 도입** | **이 규모에선 기각** — 문헌이 "필수"를 지지하지 않고(1999 IP&M · Larkey · McNamee), 분석기 오류율 6~13%(Kiwi 실측)가 새 오류원. 관행 근거(nori)는 열린 어휘·문서 규모 전제 | 네이티브 의존성 + `harness/build/tools.py` 대조 구현 동시 수정 + 소형 환경 메모리. 얻는 것은 실측 결함 1건 수정 — ①과 같다. 어휘가 열리면(임의 문서 색인) 그때 표준 답 |
| **③ 현상 유지 + 문서화** | **단독으론 기각** — 결함이 닫힌 규칙의 짝 추가로 닫히는 이상 "고치지 않을 이유"가 없다 | 단, ① 적용 후에도 남는 교체 부류(ㅡ 탈락·하다 축약·ㅂ 불규칙, 현 세트 실측 0건)는 ③이 옳다 — known-unmatched 로 문서화 |

**논문 결과가 이 규모로 이전되는가.** 그대로는 아니다 — (a)(b)(c)의 IR 결과는 문서 수천~수백만 건 색인의 재현율/정밀도 트레이드오프고, 우리는 고정 어휘 22개로 질문 한 문장을 판별한다. 이전되는 것은 세 가지 방향 명제다: 형태 복잡 언어에서 활용형 정규화는 생략하면 실제로 깨진다(우리 실측 1건이 그 실물), 정규화의 깊이는 얕아도 된다, 형태소 정보와 표층 매칭은 배타가 아니다. 반대로 (d)의 few-shot 수치(85%@예시 10개)는 **예시가 있어야** 성립하므로, 관계당 예시 0개 + 평가 세트를 튜닝에 못 쓰는 우리 제약(D12 오염 방침)에서는 전제부터 안 맞는다 — 사내 실측(임베딩 단독 24/30 < 규칙 병용 26/30)도 같은 방향이다.

**성장 경로.** 관계·표층 어휘가 수십·수백으로 자라면 ①의 짝 관리가 수작업 한계에 닿는다. 그때의 체계적 일반화는 (b)가 아니라 **(c) 자모 수준 접두사 매칭**이 먼저다 — ①과 같은 원리를 자모 분해로 자동화한 것이고(Park et al. 2018), 의존성 없이 순수 문자열 처리로 구현된다. 임베딩(d)은 관계당 라벨 예시가 쌓인 뒤의 선택지다.

**주의 — 이 수정 단독으로는 점수가 안 변한다.** 이슈 #32가 밝혔듯 X1-01 은 활용형 누락(결함 ①)과 최상급 집계 미구현(결함 ②)이 겹쳐 있고, LEADS 40 = HAS_PROJECT 40 엣지의 우연이 ① 단독 수정의 효과를 가린다. 이 문서는 매칭 접근의 근거만 다룬다.

## 출처 목록

| 저자 (연도) | 제목 | 발표처 · 기관 | 인용 수 | URL |
|---|---|---|---|---|
| Popovič & Willett (1992) | The effectiveness of stemming for natural-language access to Slovene textual data | JASIS 43(5) · U. Sheffield | 167 (OpenAlex) | https://doi.org/10.1002/(SICI)1097-4571(199206)43:5%3C384::AID-ASI6%3E3.0.CO;2-L |
| Kraaij & Pohlmann (1996) | Viewing stemming as recall enhancement | SIGIR 1996 · TNO/Utrecht | 163 (OpenAlex) | https://doi.org/10.1145/243199.243209 |
| Lee & Ahn (1996) | Using n-grams for Korean text retrieval | SIGIR 1996 · KISTI | 73 (S2) / 81 (OpenAlex) | https://doi.org/10.1145/243199.243269 |
| Lee, Cho & Park (1999) | n-Gram-based indexing for Korean text retrieval | IP&M 35(4):427–441 · KAIST·숭실대 | 34 (OpenAlex) | DOI 미확인 — https://dblp.uni-trier.de/db/journals/ipm/ipm35.html#LeeCP99 |
| Larkey et al. (2002) | Improving stemming for Arabic information retrieval | SIGIR 2002 · UMass Amherst | 361 (OpenAlex) | https://doi.org/10.1145/564376.564425 |
| McNamee & Mayfield (2004) | Character N-Gram Tokenization for European Language Text Retrieval | Information Retrieval 7(1-2) · JHU/APL | 385 (S2) / 332 (OpenAlex) | https://doi.org/10.1023/B:INRT.0000009441.78971.be |
| Braschler & Ripplinger (2004) | How Effective is Stemming and Decompounding for German Text Retrieval? | Information Retrieval 7 · Eurospider·Neuchâtel | 112 (OpenAlex) | https://doi.org/10.1023/B:INRT.0000011208.60754.a1 |
| Bojanowski et al. (2017) | Enriching Word Vectors with Subword Information (fastText) | TACL 5 · FAIR | 9,889 (OpenAlex) | https://doi.org/10.1162/tacl_a_00051 |
| Park et al. (2018) | Subword-level Word Vector Representations for Korean | ACL 2018 · KAIST·서울대 | 45 (OpenAlex) | https://aclanthology.org/P18-1226/ |
| Sakor et al. (2019) | Old is Gold: Linguistic Driven Approach for Entity and Relation Linking (Falcon) | NAACL 2019 · L3S 등 | 86 (OpenAlex) | https://doi.org/10.18653/v1/N19-1243 |
| Reimers & Gurevych (2019) | Sentence-BERT | EMNLP 2019 · TU Darmstadt | 11,702 (OpenAlex) | https://doi.org/10.18653/v1/D19-1410 |
| Park et al. (2020) | An Empirical Study of Tokenization Strategies for Various Korean NLP Tasks | AACL-IJCNLP 2020 · Kakao Brain·Scatter Lab | 31+19 (OpenAlex, 판 분산) | https://aclanthology.org/2020.aacl-main.17/ |
| Casanueva et al. (2020) | Efficient Intent Detection with Dual Sentence Encoders | NLP4ConvAI 워크샵 2020 · PolyAI | 661 (S2) | https://aclanthology.org/2020.nlp4convai-1.5/ |
| Chen et al. (2024) | M3-Embedding (bge-m3) | Findings of ACL 2024 · BAAI | 536+59 (OpenAlex, 판 분산) | https://doi.org/10.18653/v1/2024.findings-acl.137 |
| 이민철 (2024) | Kiwi: 통계 언어 모델과 Skip-Bigram을 이용한 한국어 형태소 분석기 | 한국디지털인문학회지 1(1) · 미확인 | 미확인 | https://doi.org/10.23287/KJDH.2024.1.1.6 · https://github.com/bab2min/Kiwi |
| Park & Cho (2014) | KoNLPy: 쉽고 간결한 한국어 정보처리 파이썬 패키지 | 한글 및 한국어 정보처리 학술대회 | 미확인 | https://konlpy.org |
| 국립국어원 | 한글 맞춤법 제18항 (어간 끝 'ㄹ' 탈락) | 한국어 어문 규범 | — | https://korean.go.kr/kornorms/regltn/regltnView.do |
| Apache Lucene / Elastic | nori — mecab-ko-dic 기반 공식 한국어 분석기 | LUCENE-8231 · Elastic 공식 문서 | — | https://issues.apache.org/jira/browse/LUCENE-8231 |
