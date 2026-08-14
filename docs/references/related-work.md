# 관련 연구 서지 목록

> 우리가 구현하는 기능 영역별로 공신력 있는 연구·표준·공식 문서를 모은 **서지 목록**이다. 내용 정독은 하지 않았다 — 제목/초록 수준의 한 줄 주제와 우리 결정과의 연결 지점만 기록한다. 정독한 문헌은 과제 필수 참조 3건뿐이며 별도 파일에 있다: [TACC](./tacc-context-composition.md) · [Pylon-7](./pylon-7.md) · [MCP 스펙](./mcp-spec.md).

## 수집 기준

**포함**
- 상위 학회·저널 피어리뷰 게재본 (NeurIPS, ICLR, ICML, ACL, EMNLP, NAACL, TACL, JMLR, TMLR, SIGIR, VLDB/PVLDB, SIGMOD, ICDE, WWW, ICSE, IEEE TPAMI/TKDE, ACM Computing Surveys 등)
- **COLM** (Conference on Language Modeling, 2024 신설 — LLM 전문 신흥 학회)
- 상위 학회 워크샵 (인용 시 워크샵임을 명시)
- 공식 문서·표준 (PostgreSQL, pgvector, Apache AGE, W3C Recommendation, ISO/IEC)

**제외**
- arXiv-only 프리프린트. 학회 게재본이 있으면 학회 정보로 기재하고 arXiv 번호를 부기한다. 영향력이 크지만 게재본을 확인할 수 없는 문헌은 각 영역 하단에 신뢰도를 명시해 분리 기재.
- 블로그, 기업 마케팅 자료.

발표처를 직접 확인하지 못한 항목은 추측하지 않고 "미확인"으로 표기했다.

---

# 1. NL2SQL / Text-to-SQL

## 1.1 벤치마크 (원 논문)

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Yu et al. (2018) | Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task | EMNLP 2018 | https://aclanthology.org/D18-1425/ | 200개 DB·138 도메인 크로스도메인 벤치마크. 학습/평가 DB 분리로 미지 스키마 일반화 요구 |
| Li et al. (2023) | Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs (BIRD) | NeurIPS 2023 Datasets & Benchmarks (arXiv:2305.03111) | https://proceedings.neurips.cc/paper_files/paper/2023/hash/83fc8fab1710363050bbd1d4b8cc0021-Abstract-Datasets_and_Benchmarks.html | 실제 규모(33.4GB, 95 DB) DB 값·외부 지식·쿼리 효율성까지 포함 |
| Lei et al. (2025) | Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows | ICLR 2025 (Oral) | https://iclr.cc/virtual/2025/oral/31826 | 3000+ 컬럼·다중 SQL 방언·에이전트형 상호작용을 요구하는 엔터프라이즈 벤치마크 |
| Yu et al. (2019) | CoSQL: A Conversational Text-to-SQL Challenge Towards Cross-Domain Natural Language Interfaces to Databases | EMNLP-IJCNLP 2019 | https://aclanthology.org/D19-1204/ | 다중 턴 대화형 Text-to-SQL 코퍼스, 상태 추적·응답 생성 포함 |
| Chang et al. (2023) | Dr.Spider: A Diagnostic Evaluation Benchmark towards Text-to-SQL Robustness | ICLR 2023 | https://openreview.net/forum?id=Wc5bmZZU9cy | DB·질문·SQL에 17종 섭동을 준 강건성 진단 벤치마크 |

## 1.2 LLM 기반 SQL 생성 기법

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Pourreza & Rafiei (2023) | DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction | NeurIPS 2023 | https://openreview.net/forum?id=p53QDxSIc5 | 태스크를 하위 문제로 분해하는 in-context 프롬프팅 + 자기교정 |
| Gao et al. (2024) | Text-to-SQL Empowered by Large Language Models: A Benchmark Evaluation (DAIL-SQL) | PVLDB 17(5):1132–1145 | https://dl.acm.org/doi/10.14778/3641204.3641221 | 질문 표현·예시 선택·예시 배치 등 프롬프트 설계 공간의 체계적 비교 |
| Chang & Fosler-Lussier (2023) | How to Prompt LLMs for Text-to-SQL: A Study in Zero-shot, Single-domain, and Cross-domain Settings | Table Representation Learning **워크샵** @ NeurIPS 2023 (Oral) | https://openreview.net/forum?id=5sOZNkkKh3 | 스키마 표현 방식·테이블 내용 포함 여부·프롬프트 길이의 영향 측정 |
| Wang et al. (2025) | MAC-SQL: A Multi-Agent Collaborative Framework for Text-to-SQL | COLING 2025 (arXiv:2312.11242) | https://aclanthology.org/2025.coling-main.36/ | Selector(서브스키마 선별)·Decomposer·Refiner(실행 오류 기반 재시도) 3-에이전트 |
| Pourreza et al. (2025) | CHASE-SQL: Multi-Path Reasoning and Preference Optimized Candidate Selection in Text-to-SQL | ICLR 2025 | https://openreview.net/forum?id=CvGqMD5OtX | 다중 경로로 SQL 후보 생성 후 선택 모델로 쌍대 비교 랭킹 |
| Li et al. (2025) | Alpha-SQL: Zero-Shot Text-to-SQL using Monte Carlo Tree Search | ICML 2025 | https://proceedings.mlr.press/v267/li25dt.html | 파인튜닝 없이 MCTS로 SQL 구성 액션 탐색 (32B 오픈 모델) |

## 1.3 스키마 선별 / 링킹

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Wang et al. (2020) | RAT-SQL: Relation-Aware Schema Encoding and Linking for Text-to-SQL Parsers | ACL 2020 | https://aclanthology.org/2020.acl-main.677/ | 관계 인식 self-attention으로 스키마 인코딩과 질문-스키마 링킹 통합 |
| Li et al. (2023) | RESDSQL: Decoupling Schema Linking and Skeleton Parsing for Text-to-SQL | AAAI 2023 | https://ojs.aaai.org/index.php/AAAI/article/view/26535 | 스키마 항목을 랭킹해 상위만 주입하고 골격(skeleton)을 먼저 디코딩 |
| Kothyari et al. (2023) | CRUSH4SQL: Collective Retrieval Using Schema Hallucination For Text2SQL | EMNLP 2023 | https://aclanthology.org/2023.emnlp-main.868/ | 수만 컬럼 규모 DB에서 "가상 스키마 환각 생성 → 실제 스키마 검색"으로 서브세팅 |
| Chen et al. (2024) | TableRAG: Million-Token Table Understanding with Language Models | NeurIPS 2024 | https://proceedings.neurips.cc/paper_files/paper/2024/hash/88dd7aa6979e352fda7c4952ca8eac59-Abstract-Conference.html | 쿼리 확장 + 스키마/셀 단위 검색으로 대규모 테이블을 프롬프트에 압축 투입 |
| Talaei et al. (2025) | CHESS: Contextual Harnessing for Efficient SQL Synthesis | ICML 2025 **워크샵** (Multi-Agent Systems in the Era of Foundation Models) — 본회의 아님, arXiv:2405.16755 | https://icml.cc/virtual/2025/49375 | 정보 검색·스키마 선별·후보 생성·단위 테스트 4 에이전트로 대규모 카탈로그 처리 |

## 1.4 생성된 SQL 검증 · 실행 안전성

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Scholak et al. (2021) | PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding from Language Models | EMNLP 2021 | https://aclanthology.org/2021.emnlp-main.779/ | 증분 파싱으로 디코딩 단계마다 문법·스키마 위반 토큰을 거부해 유효 SQL만 생성 |
| Zhong, Yu & Klein (2020) | Semantic Evaluation for Text-to-SQL with Distilled Test Suites | EMNLP 2020 | https://aclanthology.org/2020.emnlp-main.29/ | 무작위 생성 DB에서 테스트 스위트를 증류해 실행 기반 의미 동등성 판정 |
| Chen et al. (2024) | Teaching Large Language Models to Self-Debug | ICLR 2024 (arXiv:2304.05128) | https://openreview.net/forum?id=KuPixIqPiq | 실행 결과와 자기 설명을 피드백으로 생성 코드/SQL을 반복 수정 |
| Pedro et al. (2025) | Prompt-to-SQL Injections in LLM-Integrated Web Applications: Risks and Defenses | ICSE 2025 (arXiv:2308.01990) | https://dl.acm.org/doi/10.1109/ICSE55347.2025.00007 | LangChain 기반 앱의 P2SQL 인젝션 공격면 실증(7 LLM) 및 방어 기법 4종 |
| Chen et al. (2025) | Reliable Text-to-SQL with Adaptive Abstention | SIGMOD 2025 / PACMMOD | https://dl.acm.org/doi/10.1145/3709719 | 스키마 링킹 단계에서 conformal 보장 하에 기권(abstain)하고 사람 개입 유도 |
| Wang et al. (2023) | Know What I don't Know: Handling Ambiguous and Unknown Questions for Text-to-SQL | Findings of ACL 2023 | https://aclanthology.org/2023.findings-acl.352/ | 모호·응답불가 질문을 6 범주로 정리하고 탐지-설명 모델로 오답 생성 차단 |
| PostgreSQL GDG | PostgreSQL Documentation: SET TRANSACTION | 공식 문서 (v18) | https://www.postgresql.org/docs/current/sql-set-transaction.html | `READ ONLY` 트랜잭션이 INSERT/UPDATE/DELETE/MERGE/DDL/GRANT/TRUNCATE를 거부 |
| PostgreSQL GDG | PostgreSQL Documentation: 19.11. Client Connection Defaults | 공식 문서 (v18) | https://www.postgresql.org/docs/current/runtime-config-client.html | `default_transaction_read_only`, `statement_timeout` |
| PostgreSQL GDG | PostgreSQL Documentation: GRANT | 공식 문서 (v18) | https://www.postgresql.org/docs/current/sql-grant.html | 롤에 `SELECT`만 부여하는 권한 모델 |

## 1.5 소형 / 로컬 LLM 기반 Text-to-SQL

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Li et al. (2024) | CodeS: Towards Building Open-source Language Models for Text-to-SQL | SIGMOD 2024 / PACMMOD (arXiv:2402.16347) | https://dl.acm.org/doi/10.1145/3654930 | 1B~15B 오픈 모델 계열 + 스키마 링킹·양방향 데이터 증강으로 도메인 적응 |
| Pourreza & Rafiei (2024) | DTS-SQL: Decomposed Text-to-SQL with Small Large Language Models | Findings of EMNLP 2024 | https://aclanthology.org/2024.findings-emnlp.481/ | 스키마 링킹/SQL 생성 2단계 파인튜닝으로 7B 로컬 모델이 BIRD 60.31% (프라이버시 동기) |
| Yang et al. (2024) | Synthesizing Text-to-SQL Data from Weak and Strong LLMs (SENSE) | ACL 2024 (Long) | https://aclanthology.org/2024.acl-long.425/ | 강한 모델의 정답 + 약한 모델의 오류를 선호학습에 써 오픈 모델 격차 축소 |
| Li et al. (2025) | OmniSQL: Synthesizing High-quality Text-to-SQL Data at Scale | PVLDB 18(11):4695–4709 (arXiv:2503.02240) | https://dl.acm.org/doi/10.14778/3749646.3749723 | 250만 규모 합성 데이터로 학습한 7B/14B/32B 오픈 모델 |
| Fan et al. (2024) | Combining Small Language Models and Large Language Models for Zero-Shot NL2SQL (ZeroNL2SQL) | PVLDB 17(11):2750–2763 | https://dl.acm.org/doi/10.14778/3681954.3681960 | 소형 모델로 SQL 스케치·스키마 정렬, 대형 모델로 결측 정보 보완하는 하이브리드 |

## 1.6 신뢰도 미달로 분리한 문헌

| 문헌 | 상태 |
|---|---|
| Zhong, Xiong & Socher (2017), Seq2SQL / WikiSQL (arXiv:1709.00103) | **arXiv-only.** DBLP상 CoRR 등재만. ICLR 2018 투고했으나 본회의·워크샵 목록에 없음. 벤치마크 자체는 널리 쓰이므로 참고용으로만 기재 |
| TrustSQL (Text-to-SQL 신뢰성·기권 벤치마크) | arXiv 프리프린트만 확인. 유사 주제는 Reliable Text-to-SQL (SIGMOD 2025)로 대체 |

## 1.7 우리 설계와의 연결

| 우리 결정 / 열린 항목 | 관련 문헌 |
|---|---|
| **D4** 도구 내부 LLM SQL 생성 | DIN-SQL, DAIL-SQL, CHASE-SQL (프롬프팅 설계 공간) |
| **D4** SELECT-only 강제 | PostgreSQL `SET TRANSACTION READ ONLY`·`default_transaction_read_only`·`GRANT SELECT` — **애플리케이션 파싱보다 DB 권한 레벨 강제가 근거 있는 접근**. Pedro et al. (ICSE 2025)이 P2SQL 인젝션 공격면과 방어를 실증 |
| **T1** SQL 생성 실패 재시도 정책 (열린 항목) | Self-Debug (ICLR 2024), MAC-SQL Refiner — 실행 오류를 피드백으로 재시도하는 선행 사례 |
| **T2** SELECT 외 구문 차단 | PICARD (EMNLP 2021) — 디코딩 단계에서 위반 토큰을 거부하는 제약 디코딩 |
| **R1 / D6** 무매칭 거절, **Q3** 모름 답변 | Reliable Text-to-SQL with Adaptive Abstention (SIGMOD 2025), Know What I don't Know (Findings of ACL 2023) — **기권(abstention)을 정식 설계 요소로 다룬 피어리뷰 근거** |
| TACC — nl2sql 스키마 선별은 적용 지점이 아님 (테이블 8개뿐) | RESDSQL, CRUSH4SQL, TableRAG, MAC-SQL Selector — 대규모 스키마 선별 기법군. 우리 규모에서는 불필요함을 보여주는 대비 근거 |
| 권장 LLM(소형·로컬) 실현 가능성 | DTS-SQL (7B로 BIRD 60.31%), CodeS, OmniSQL, ZeroNL2SQL |
| questions.json 회귀 검증 (**D7**) | Test-suite 기반 실행 동등성 평가 (EMNLP 2020), Dr.Spider 강건성 섭동 |

---

# 2. 벡터 검색 / RAG

## 2.1 RAG 원 논문 및 기반 연구

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Lewis et al. (2020) | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | NeurIPS 2020 | https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html | **RAG 원 논문** — 파라메트릭 메모리와 비파라메트릭 벡터 인덱스 결합 |
| Guu et al. (2020) | REALM: Retrieval-Augmented Language Model Pre-Training | ICML 2020 (PMLR v119) | https://proceedings.mlr.press/v119/guu20a.html | 검색기를 사전학습 단계에 통합해 end-to-end 학습 |
| Izacard & Grave (2021) | Leveraging Passage Retrieval with Generative Models for Open Domain Question Answering | EACL 2021 | https://aclanthology.org/2021.eacl-main.74/ | Fusion-in-Decoder — 다수 패시지를 인코더에서 개별 처리, 디코더에서 융합 |
| Izacard et al. (2023) | Atlas: Few-shot Learning with Retrieval Augmented Language Models | JMLR 24, 251:1–251:43 | https://www.jmlr.org/papers/v24/23-0037.html | 검색 증강 LM의 few-shot 학습, 문서 인덱스 구성의 영향 분석 |

## 2.2 RAG 후속 주요 연구

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Ram et al. (2023) | In-Context Retrieval-Augmented Language Models | TACL 11 | https://aclanthology.org/2023.tacl-1.75/ | 모델 수정 없이 프롬프트에 검색 문서를 넣는 in-context RALM |
| Gao et al. (2023) | Precise Zero-Shot Dense Retrieval without Relevance Labels (HyDE) | ACL 2023 (Long) | https://aclanthology.org/2023.acl-long.99/ | LLM이 생성한 가상 문서를 임베딩해 제로샷 검색 |
| Asai et al. (2024) | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | ICLR 2024 (Oral) | https://iclr.cc/virtual/2024/oral/19736 | 반영 토큰으로 검색 여부·생성 품질을 스스로 판단하는 적응적 RAG |
| Sarthi et al. (2024) | RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval | ICLR 2024 | https://proceedings.iclr.cc/paper_files/paper/2024/hash/8a2acd174940dbca361a6398a4f9df91-Abstract-Conference.html | 청크를 재귀 클러스터링·요약해 다층 트리 인덱스 구성 |
| Liu et al. (2024) | Lost in the Middle: How Language Models Use Long Contexts | TACL 12 | https://aclanthology.org/2024.tacl-1.9/ | 컨텍스트 내 관련 문서 위치가 성능 좌우 (과제 권장 참조에도 포함) |
| Wang et al. (2024) | Searching for Best Practices in Retrieval-Augmented Generation | EMNLP 2024 (Main) | https://aclanthology.org/2024.emnlp-main.981/ | RAG 파이프라인 각 구성요소(청킹·임베딩·리랭킹)의 기여도 실험 비교 |

## 2.3 밀집 검색기

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Karpukhin et al. (2020) | Dense Passage Retrieval for Open-Domain Question Answering | EMNLP 2020 | https://aclanthology.org/2020.emnlp-main.550/ | DPR — 듀얼 인코더 밀집 검색이 BM25 상회 |
| Khattab & Zaharia (2020) | ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT | SIGIR 2020 | https://dblp.org/rec/conf/sigir/KhattabZ20.html | 토큰 단위 late interaction으로 표현력·효율 절충 |
| Santhanam et al. (2022) | ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction | NAACL 2022 | https://aclanthology.org/2022.naacl-main.272/ | 잔차 압축 + 노이즈 제거 지도학습으로 저장공간 6–10배 절감 |
| Izacard et al. (2022) | Unsupervised Dense Information Retrieval with Contrastive Learning (Contriever) | TMLR | https://openreview.net/forum?id=jKN1pXi7b0 | 라벨 없는 대조학습만으로 BEIR에서 BM25 상회 |
| Ni et al. (2022) | Large Dual Encoders Are Generalizable Retrievers (GTR) | EMNLP 2022 (Main) | https://aclanthology.org/2022.emnlp-main.669/ | 듀얼 인코더 규모 확대가 out-of-domain 일반화 개선 |

## 2.4 문장 / 텍스트 임베딩 및 벤치마크

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Reimers & Gurevych (2019) | Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks | EMNLP-IJCNLP 2019 | https://aclanthology.org/D19-1410/ | 시아미즈 구조로 코사인 비교 가능한 문장 임베딩 |
| Gao, Yao & Chen (2021) | SimCSE: Simple Contrastive Learning of Sentence Embeddings | EMNLP 2021 (Main) | https://aclanthology.org/2021.emnlp-main.552/ | 드롭아웃만 노이즈로 쓰는 비지도 대조학습 문장 임베딩 |
| Muennighoff et al. (2023) | MTEB: Massive Text Embedding Benchmark | EACL 2023 | https://aclanthology.org/2023.eacl-main.148/ | 8태스크·58데이터셋 종합 벤치마크 — **만능 임베딩은 없음** |
| Xiao et al. (2024) | C-Pack: Packed Resources For General Chinese Embeddings | SIGIR 2024 | https://dl.acm.org/doi/10.1145/3626772.3657878 | BGE 임베딩 모델군 + C-MTP 학습셋 + C-MTEB |
| Wang et al. (2024) | Improving Text Embeddings with Large Language Models (E5-Mistral) | ACL 2024 (Long) | https://aclanthology.org/2024.acl-long.642/ | 합성 데이터만으로 1k 스텝 미만 학습해 SOTA 임베딩 |
| Chen, Xiao, Zhang, Luo, Lian & Liu (2024) | M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation | Findings of ACL 2024, pp. 2318–2335 | https://aclanthology.org/2024.findings-acl.137/ | **`bge-m3`의 원 논문** — 100+ 언어를 하나의 임베딩으로 지원, dense·sparse·multi-vector 동시 수행, 8192 토큰까지 |

## 2.5 ANN 인덱스 알고리즘 (pgvector 근거)

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Malkov & Yashunin (2020) | Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs | IEEE TPAMI 42(4), 824–836 | https://dl.acm.org/doi/10.1109/TPAMI.2018.2889473 | **HNSW 원 논문 — pgvector `hnsw` 인덱스의 알고리즘 근거** |
| Malkov et al. (2014) | Approximate nearest neighbor algorithm based on navigable small world graphs | Information Systems 45, 61–68 | https://doi.org/10.1016/j.is.2013.10.006 | NSW — HNSW 직전 세대 그래프 기반 ANN |
| Sivic & Zisserman (2003) | Video Google: A Text Retrieval Approach to Object Matching in Videos | ICCV 2003 | https://www.robots.ox.ac.uk/~vgg/publications/2003/Sivic03/ | 벡터 양자화 + inverted file — **IVF 계열 인덱스의 기원** |
| Jégou, Douze & Schmid (2011) | Product Quantization for Nearest Neighbor Search | IEEE TPAMI 33(1), 117–128 | https://inria.hal.science/inria-00514462 | PQ 원 논문 — 부공간 분해 양자화, 비대칭 거리 계산, IVFADC |
| Ge et al. (2013/2014) | Optimized Product Quantization | CVPR 2013 / IEEE TPAMI 36(4) | https://openaccess.thecvf.com/content_cvpr_2013/html/Ge_Optimized_Product_Quantization_2013_CVPR_paper.html | 공간 분해와 코드북 동시 최적화로 PQ 왜곡 최소화 |
| Subramanya et al. (2019) | DiskANN: Fast Accurate Billion-point Nearest Neighbor Search on a Single Node | NeurIPS 2019 | https://www.microsoft.com/en-us/research/publication/diskann-fast-accurate-billion-point-nearest-neighbor-search-on-a-single-node/ | SSD 기반 십억 규모 ANN, Vamana 그래프 인덱스 |
| Guo et al. (2020) | Accelerating Large-Scale Inference with Anisotropic Vector Quantization (ScaNN) | ICML 2020 (PMLR v119) | https://proceedings.mlr.press/v119/guo20h.html | 내적 검색에 맞춘 비등방 양자화 손실 |
| Johnson, Douze & Jégou (2021) | Billion-Scale Similarity Search with GPUs (Faiss) | IEEE Trans. on Big Data 7(3), 535–547 | https://www.semanticscholar.org/paper/2cbb8de53759e75411bc528518947a3094fbce3a | IVF/PQ 대규모 검색의 표준 참조 구현 |
| Aumüller, Bernhardsson & Faithfull (2020) | ANN-Benchmarks: A benchmarking tool for approximate nearest neighbor algorithms | Information Systems 87 | https://dl.acm.org/doi/10.1016/j.is.2019.02.006 | ANN recall–QPS 트레이드오프 표준 비교 프레임워크 |

## 2.6 청킹 전략 / 검색 단위

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Qu, Tu & Bao (2025) | Is Semantic Chunking Worth the Computational Cost? | Findings of NAACL 2025 | https://aclanthology.org/2025.findings-naacl.114/ | **시맨틱 청킹의 추가 연산비용이 고정 길이 청킹 대비 일관된 이득을 주지 못함** |
| Callan (1994) | Passage-Level Evidence in Document Retrieval | SIGIR 1994 | https://dl.acm.org/doi/10.1145/188490.188589 | 패시지 정의 방식이 검색 성능에 미치는 영향 — 청킹 논의의 원형 |
| Kaszkiel & Zobel (1997) | Passage Retrieval Revisited | SIGIR 1997 | https://dl.acm.org/doi/10.1145/258525.258561 | 임의 위치 고정 길이 창(sliding window)이 구조 기반 분할보다 강건 |
| Koshorek et al. (2018) | Text Segmentation as a Supervised Learning Task | NAACL 2018 (Short) | https://aclanthology.org/N18-2075/ | 텍스트 분할을 지도학습으로 정식화 + Wiki-727K |
| Chen et al. (2024) | Dense X Retrieval: What Retrieval Granularity Should We Use? | EMNLP 2024 (Main) | https://aclanthology.org/2024.emnlp-main.845/ | 검색 단위를 proposition(원자적 사실)으로 두면 패시지 단위보다 우수 |
| Duarte et al. (2024) | LumberChunker: Long-Form Narrative Document Segmentation | Findings of EMNLP 2024 | https://aclanthology.org/2024.findings-emnlp.377/ | LLM으로 내용 전환점을 찾아 가변 길이 청크 생성 + GutenQA |

## 2.7 검색 품질 평가 / 벤치마크

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Thakur et al. (2021) | BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models | NeurIPS 2021 Datasets & Benchmarks | https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html | 18개 이종 데이터셋 제로샷 검색 벤치마크 — BM25가 강건한 베이스라인 |
| Nguyen et al. (2016) | MS MARCO: A Human Generated MAchine Reading COmprehension Dataset | NIPS 2016 CoCo **워크샵** | https://dblp.org/rec/conf/nips/NguyenRSGTMD16.html | 밀집 검색 학습·평가의 사실상 표준 대규모 패시지 랭킹 데이터셋 |
| Petroni et al. (2021) | KILT: a Benchmark for Knowledge Intensive Language Tasks | NAACL 2021 (Main) | https://aclanthology.org/2021.naacl-main.200/ | 단일 위키 스냅샷 기반 11개 지식집약 태스크 통합 평가 |
| Es et al. (2024) | RAGAs: Automated Evaluation of Retrieval Augmented Generation | EACL 2024 System Demos | https://aclanthology.org/2024.eacl-demo.16/ | 참조 정답 없이 faithfulness·answer/context relevance 자동 측정 |
| Saad-Falcon et al. (2024) | ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems | NAACL 2024 (Long) | https://aclanthology.org/2024.naacl-long.20/ | 합성 데이터로 LLM 심판 파인튜닝, PPI로 신뢰구간 제공 |
| Tang & Yang (2024) | MultiHop-RAG: Benchmarking Retrieval-Augmented Generation for Multi-Hop Queries | COLM 2024 | https://colmweb.org/2024/AcceptedPapers.html | 다중 문서 근거를 요구하는 멀티홉 질의 RAG 벤치마크 (개별 논문 URL 미확인) |
| Hsia et al. (2025) | RAGGED: Towards Informed Design of Scalable and Stable RAG Systems | ICML 2025 (PMLR v267) | https://proceedings.mlr.press/v267/hsia25a.html | 검색기·리더·검색 깊이 조합을 체계적으로 스윕하는 RAG 설계 분석 |

## 2.8 pgvector · PostgreSQL 공식 문서

| 출처 | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| pgvector 프로젝트 (v0.8.6) | pgvector README | 공식 GitHub | https://github.com/pgvector/pgvector | 타입(`vector`/`halfvec`/`bit`/`sparsevec`), 연산자, 인덱싱, 성능 튜닝 |
| pgvector 프로젝트 | HNSW 인덱스 절 | 공식 GitHub | https://github.com/pgvector/pgvector#hnsw | `m`(기본 16), `ef_construction`(기본 64), `hnsw.ef_search`(기본 40), `maintenance_work_mem` 내 빌드 권장 |
| pgvector 프로젝트 | IVFFlat 인덱스 절 | 공식 GitHub | https://github.com/pgvector/pgvector#ivfflat | `lists` 권장값(<1M행: 행수/1000, >1M행: sqrt(행수)), `ivfflat.probes`로 recall 조정 |
| pgvector 프로젝트 | Iterative Index Scans / Filtering | 공식 GitHub | https://github.com/pgvector/pgvector#iterative-index-scans | `WHERE` 필터 over-filtering 대응 — 반복 인덱스 스캔, 부분 인덱스·파티셔닝 |
| PostgreSQL GDG (2024) | pgvector 0.8.0 Released! | postgresql.org 공식 뉴스 | https://www.postgresql.org/about/news/pgvector-080-released-2952/ | 필터 질의 성능 개선, `hnsw.iterative_scan` 도입 |
| PostgreSQL GDG | 19.4. Resource Consumption | 공식 문서 | https://www.postgresql.org/docs/current/runtime-config-resource.html | `maintenance_work_mem`, `max_parallel_maintenance_workers` — 인덱스 빌드 튜닝 |
| PostgreSQL GDG | Chapter 11. Indexes | 공식 문서 | https://www.postgresql.org/docs/current/indexes.html | 인덱스 종류·연산자 클래스·부분 인덱스 등 기반 개념 |
| Pan, Wang & Li (2024) | Survey of vector database management systems | The VLDB Journal 33, 1591–1615 | https://link.springer.com/article/10.1007/s00778-024-00864-x | 벡터 DBMS 설계 공간 피어리뷰 서베이 — pgvector 위치 파악용 |

## 2.9 신뢰도 미달로 제외한 문헌

| 문헌 | 제외 이유 |
|---|---|
| Günther et al., Late Chunking (arXiv:2409.04701) | OpenReview 제출본만 확인, 학회 게재 여부 불명 |
| Zhao et al., Meta-Chunking (arXiv:2410.12788) | ICLR 2025 제출 기록만, 게재 여부 불명 |
| Gao et al., RAG for LLMs: A Survey (arXiv:2312.10997) | arXiv-only |
| Douze et al., The Faiss Library | IEEE TBD 게재로 보이나 권/호/연도 미확인 — Johnson et al. (2021)로 대체 |

## 2.10 우리 설계와의 연결

| 우리 결정 / 열린 항목 | 관련 문헌 |
|---|---|
| **청킹 전략** (열린 항목 — 단순 전략으로 시작, 문서별 튜닝 금지) | **Qu, Tu & Bao (Findings of NAACL 2025)** — 시맨틱 청킹이 비용만큼의 이득을 주지 못함. 우리 방침의 피어리뷰 근거. 반대 방향 참고로 Dense X Retrieval, LumberChunker |
| **임베딩 모델** (열린 항목 — **`bge-m3` 후보**, 적재 후 실측으로 확정) | **M3-Embedding (Findings of ACL 2024)** — `bge-m3`의 원 논문. **한국어(ko) 개별 수치를 원문 표에서 확인했다**: MIRACL dev nDCG@10 ko = **69.9**(dense) / **72.1**(all), 같은 표 최고 베이스라인 mE5large 66.5 · BM25 37.1 (Table 1). MKQA Recall@100 ko = **71.6**(dense) / **71.8**(all), mE5large 68.1 · OpenAI-3 63.9 (Table 2). 단 논문 Limitations가 *"언어별 성능 편차는 충분히 논의되지 않았다"*고 명시하므로 ko 수치는 이 두 벤치마크 한정으로 인용한다. 대비: MTEB (EACL 2023) — "만능 임베딩 없음", 태스크별 선택 필요. 후보에서 내린 `nomic-embed-text`는 HF 모델카드 언어 태그가 `en` 하나여서 한국어 1차 출처가 없다 ([dataset-analysis.md](../dataset-analysis.md) 7장) |
| **T4** 유사도 임계값 / "관련 문서 없음" 판정 (열린 항목) | BEIR — 제로샷 환경에서 BM25가 강건한 베이스라인. 임계값을 데이터셋에서 역산하지 않으려면 일반 벤치마크 관행 참조 |
| **벡터 DB 인덱스 선택** (HNSW vs IVFFlat) | pgvector 공식 문서 파라미터 + HNSW 원 논문(TPAMI 2020), IVF 기원(ICCV 2003), ANN-Benchmarks. 문서 40건 규모면 인덱스 없이도 동작 — 인덱스는 시연·확장성 논거용 |
| **Q2** 컨텍스트 초과 / TACC 적용 지점 ① | Lost in the Middle (TACL 2024, 과제 권장 참조와 동일) — 반환 청크 순서·개수 설계 근거 |
| **자체 엣지 세트 평가** (**D7**) | RAGAs (EACL 2024 Demo), ARES (NAACL 2024) — 참조 정답 없이 faithfulness를 자동 측정하는 프레임워크. 우리 Q1(환각 방지) 검증에 적용 가능 |
| 하이브리드 검색 고려 시 | BEIR의 BM25 베이스라인, ColBERT/ColBERTv2 (late interaction) |

---

# 3. 지식 그래프 / GraphRAG

## 3.1 GraphRAG / 그래프 기반 검색 증강 생성

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Gutiérrez et al. (2024) | HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models | NeurIPS 2024 | https://papers.nips.cc/paper_files/paper/2024/hash/6ddc001d07ca4f319af96a3024f6dbd1-Abstract-Conference.html | LLM으로 만든 지식 그래프 위에서 Personalized PageRank로 단일 검색에 멀티홉 통합 |
| He et al. (2024) | G-Retriever: Retrieval-Augmented Generation for Textual Graph Understanding and Question Answering | NeurIPS 2024 | https://papers.nips.cc/paper_files/paper/2024/hash/efaf1c9726648c8ba363a5c927440529-Abstract-Conference.html | 서브그래프 검색을 Prize-Collecting Steiner Tree 최적화로 정식화 |
| Sarthi et al. (2024) | RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval | ICLR 2024 | https://proceedings.iclr.cc/paper_files/paper/2024/hash/8a2acd174940dbca361a6398a4f9df91-Abstract-Conference.html | 청크를 재귀 클러스터링·요약해 트리 인덱스 구성 (2.2와 중복) |
| Hu et al. (2025) | GRAG: Graph Retrieval-Augmented Generation | Findings of NAACL 2025, pp. 4145–4157 | https://aclanthology.org/2025.findings-naacl.232/ | 단일 노드가 아닌 서브그래프 단위 검색 |
| Guo et al. (2025) | LightRAG: Simple and Fast Retrieval-Augmented Generation | Findings of EMNLP 2025 | https://aclanthology.org/2025.findings-emnlp.568/ | 그래프 인덱싱 + 저수준/고수준 이중 단계 검색으로 비용·커버리지 균형 |
| Mavromatis & Karypis (2025) | GNN-RAG: Graph Neural Retrieval for Efficient Large Language Model Reasoning on Knowledge Graphs | Findings of ACL 2025 | https://aclanthology.org/2025.findings-acl.856/ | GNN 검색기로 KG 경로를 뽑아 LLM에 넘겨 KG 토큰 9배 절감 |
| Liu, Wang & Li (2025) | Knowledge Graph Retrieval-Augmented Generation via GNN-Guided Prompting | **COLM 2025** | https://openreview.net/forum?id=R1NWMExESj | GNN이 유도한 프롬프트로 KG 기반 RAG 구성 |
| Luo et al. (2025) | Graph-constrained Reasoning: Faithful Reasoning on Knowledge Graphs with Large Language Models | ICML 2025 (PMLR v267) | https://proceedings.mlr.press/v267/luo25t.html | KG-Trie 인덱스로 LLM 디코딩을 제약해 환각 없는 경로 생성 |
| Luo et al. (2025) | GFM-RAG: Graph Foundation Model for Retrieval Augmented Generation | NeurIPS 2025로 표기됨 — **프로시딩 페이지 미확인** | https://openreview.net/forum?id=0QNmAvQQqj | 8M 파라미터 그래프 파운데이션 모델 사전학습, 파인튜닝 없이 미확인 데이터셋 검색 |

## 3.2 KGQA (자연어 질문 → 그래프 질의)

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Berant et al. (2013) | Semantic Parsing on Freebase from Question-Answer Pairs | EMNLP 2013 | https://aclanthology.org/D13-1160/ | 논리형 라벨 없이 QA 쌍만으로 Freebase 의미 파싱 학습 (WebQuestions) |
| Yih et al. (2015) | Semantic Parsing via Staged Query Graph Generation: Question Answering with Knowledge Base | ACL-IJCNLP 2015 | https://aclanthology.org/P15-1128/ | 질의 그래프를 단계적으로 생성하는 KBQA 고전 baseline |
| Yih et al. (2016) | The Value of Semantic Parse Labeling for Knowledge Base Question Answering | ACL 2016 (Short) | https://aclanthology.org/P16-2033/ | 정답 라벨 대비 의미 파스 라벨의 가치 측정 (WebQuestionsSP) |
| Talmor & Berant (2018) | The Web as a Knowledge-Base for Answering Complex Questions | NAACL-HLT 2018 | https://aclanthology.org/N18-1059/ | 복합 질문을 단순 질문 조합으로 규칙 분해 (ComplexWebQuestions) |
| Gu et al. (2021) | Beyond I.I.D.: Three Levels of Generalization for Question Answering on Knowledge Bases | WWW 2021 | https://dl.acm.org/doi/10.1145/3442381.3449992 | i.i.d./조합적/제로샷 3단계 일반화 평가 체계 + GrailQA |
| Cao et al. (2022) | KQA Pro: A Dataset with Explicit Compositional Programs for Complex Question Answering over Knowledge Base | ACL 2022 (Long) | https://aclanthology.org/2022.acl-long.422/ | 120K 문항에 KoPL 프로그램과 SPARQL 병기한 복합 KBQA 벤치마크 |
| Agarwal, Kumar & Bedathur (2024) | SymKGQA: Few-Shot Knowledge Graph Question Answering via Symbolic Program Generation and Execution | ACL 2024 (Long) | https://aclanthology.org/2024.acl-long.545/ | LLM 퓨샷으로 심볼릭 프로그램을 생성·실행하는 KGQA |

## 3.3 관계형 DB에서의 그래프 질의

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| PostgreSQL GDG | 7.8. WITH Queries (Common Table Expressions) | PostgreSQL 공식 문서 (v18) | https://www.postgresql.org/docs/current/queries-with.html | **`WITH RECURSIVE`의 작업 테이블 기반 반복 평가 절차 — D5의 1차 문헌** |
| Apache Software Foundation | Apache AGE Manual — Overview | Apache AGE 공식 문서 (2022-05 Apache TLP) | https://age.apache.org/age-manual/master/intro/overview.html | PostgreSQL 확장으로 ANSI SQL과 openCypher를 한 스토리지에서 병용 |
| Zhao & Yu (2017) | All-in-One: Graph Processing in RDBMSs Revisited | SIGMOD 2017 | https://doi.org/10.1145/3035918.3035943 | 선형/상호/비선형 재귀 SQL로 광범위한 그래프 알고리즘을 RDBMS 내부에서 처리 |
| Hassan et al. (2018) | GRFusion: Graphs as First-Class Citizens in Main-Memory Relational Database Systems | SIGMOD 2018 (demo) | https://dl.acm.org/doi/10.1145/3183713.3193541 | 그래프 뷰를 선언하고 관계형·그래프 연산자를 섞은 실행계획 생성 |
| Tian et al. (2019) | Synergistic Graph and SQL Analytics Inside IBM Db2 | PVLDB 12(12), p. 1782 (VLDB 2019 demo) | http://www.vldb.org/pvldb/vol12/p1782-tian.pdf | 기존 관계형 스키마 위에 그래프 뷰를 얹는 retrofit 방식 |
| Tian et al. (2020) | IBM Db2 Graph: Supporting Synergistic and Retrofittable Graph Queries Inside IBM Db2 | SIGMOD 2020 | https://dl.acm.org/doi/10.1145/3318464.3386138 | 위 데모의 정식 논문 — 상용 RDBMS의 그래프 질의 아키텍처 |
| Hirn & Grust (2021) | One WITH RECURSIVE is Worth Many GOTOs | SIGMOD 2021 | https://dl.acm.org/doi/10.1145/3448016.3457272 | 임의 중첩 반복 제어흐름을 recursive CTE로 컴파일 |
| Deutsch et al. (2022) | Graph Pattern Matching in GQL and SQL/PGQ | SIGMOD 2022 | https://dl.acm.org/doi/abs/10.1145/3514221.3526057 | SQL 테이블 위에 그래프 뷰를 정의하는 SQL/PGQ와 GQL의 공통 코어(GPML) |

## 3.4 온톨로지 / 스키마 표준

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Cyganiak, Wood & Lanthaler (eds., 2014) | RDF 1.1 Concepts and Abstract Syntax | **W3C Recommendation**, 2014-02-25 | https://www.w3.org/TR/rdf11-concepts/ | 트리플과 RDF 그래프/데이터셋의 추상 구문 정의 |
| Brickley & Guha (eds., 2014) | RDF Schema 1.1 | **W3C Recommendation**, 2014-02-25 | https://www.w3.org/TR/rdf-schema/ | 클래스·프로퍼티·도메인·레인지의 최소 스키마 어휘 |
| W3C OWL Working Group (2012) | OWL 2 Web Ontology Language Document Overview (2nd ed.) | **W3C Recommendation**, 2012-12-11 | https://www.w3.org/TR/owl2-overview/ | 추론 가능한 형식 의미론을 RDF 위에 추가 |
| Harris & Seaborne (eds., 2013) | SPARQL 1.1 Query Language | **W3C Recommendation**, 2013-03-21 | https://www.w3.org/TR/sparql11-query/ | RDF 그래프 질의 언어 — 그래프 패턴, property path, 집계 |
| Knublauch & Kontokostas (eds., 2017) | Shapes Constraint Language (SHACL) | **W3C Recommendation**, 2017-07-20 | https://www.w3.org/TR/shacl/ | RDF 그래프의 구조 제약 선언·검증 |
| RDF & SPARQL WG (2026) | RDF 1.2 Concepts and Abstract Data Model | **W3C Candidate Recommendation Snapshot**, 2026-04-07 — **REC 미승격** | https://www.w3.org/TR/rdf12-concepts/ | triple term, 방향성 언어 태그 문자열 추가 |
| ISO/IEC JTC 1/SC 32 WG3 (2024) | ISO/IEC 39075:2024 — Database languages — GQL | **ISO/IEC 국제표준**, 2024-04-11 | https://www.iso.org/standard/76120.html | 프로퍼티 그래프 질의의 최초 ISO 표준 |
| Angles et al. (2017) | Foundations of Modern Query Languages for Graph Databases | ACM Computing Surveys 50(5), Art. 68 | https://dl.acm.org/doi/10.1145/3104031 | edge-labelled vs 프로퍼티 그래프 모델, 그래프 패턴·내비게이션의 이론적 기초 |
| Hogan et al. (2021) | Knowledge Graphs | ACM Computing Surveys 54(4) | https://dl.acm.org/doi/10.1145/3447772 | 데이터 모델·스키마·온톨로지·품질까지 KG 전반의 표준 참조 서베이 |

## 3.5 LLM + 지식 그래프 결합

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Wu et al. (2020) | Scalable Zero-shot Entity Linking with Dense Entity Retrieval (BLINK) | EMNLP 2020 | https://aclanthology.org/2020.emnlp-main.519/ | bi-encoder 후보 검색 + cross-encoder 재순위의 제로샷 엔티티 링킹 baseline |
| De Cao et al. (2021) | Autoregressive Entity Retrieval (GENRE) | ICLR 2021 | https://openreview.net/forum?id=5k8F6UU39V | 엔티티 이름을 제약 디코딩으로 직접 생성 — BLINK 대비 메모리 14배 절감 |
| Jiang et al. (2023) | StructGPT: A General Framework for Large Language Model to Reason over Structured Data | EMNLP 2023 (Main) | https://aclanthology.org/2023.emnlp-main.574/ | KG·테이블·DB 공통 인터페이스를 두고 read-then-reason 반복 |
| Sun et al. (2024) | Think-on-Graph: Deep and Responsible Reasoning of Large Language Model on Knowledge Graph | ICLR 2024 | https://proceedings.iclr.cc/paper_files/paper/2024/hash/10a6bdcabbd5a3d36b760daa295f63c1-Abstract-Conference.html | LLM을 에이전트로 두고 KG 위에서 beam search로 추론 경로 탐색 |
| Luo et al. (2024) | Reasoning on Graphs: Faithful and Interpretable Large Language Model Reasoning | ICLR 2024 | https://proceedings.iclr.cc/paper_files/paper/2024/file/3e2aeb66481dd63a32421bf032b70384-Paper-Conference.pdf | 관계 경로 플랜을 먼저 생성하고 KG로 검증하는 plan-retrieve-reason |
| Jin et al. (2024) | Graph Chain-of-Thought: Augmenting Large Language Models by Reasoning on Graphs | Findings of ACL 2024 | https://aclanthology.org/2024.findings-acl.11/ | LLM 추론 → 그래프 상호작용 → 그래프 실행 반복 |
| Pan et al. (2024) | Unifying Large Language Models and Knowledge Graphs: A Roadmap | IEEE TKDE 36(7), pp. 3580–3599 | https://doi.org/10.1109/TKDE.2024.3352100 | KG-enhanced LLM / LLM-augmented KG / 시너지 3분류 로드맵 |

## 3.6 신뢰도 미달로 분리한 문헌

| 문헌 | 상태 |
|---|---|
| Edge et al. (2024), From Local to Global: A Graph RAG Approach to Query-Focused Summarization (arXiv:2404.16130) | **arXiv-only — 피어리뷰 게재본 미확인.** Microsoft GraphRAG 원 논문. 일부 집계 서비스가 "ACL 2025"로 표기하나 ACL Anthology에서 확인 불가. 영향력이 커서 분리 기재 |

## 3.7 표준 인용 시 주의사항 (조사 중 확인된 사실)

1. **RDF 1.2는 아직 Recommendation이 아니다** — 2026-04-07자 Candidate Recommendation Snapshot 상태. 표준 근거가 필요하면 RDF 1.1(2014 REC)을 쓰고 1.2는 "진행 중"으로 표기.
2. **프로퍼티 그래프에는 W3C 권고 매핑이 없다** — OWL→프로퍼티 그래프의 표준화된 매핑은 존재하지 않는다(OWLStar, owl2lpg 등 제안 수준). 프로퍼티 그래프 쪽 규범 문헌은 W3C가 아니라 **ISO/IEC 39075:2024(GQL)와 SQL/PGQ**다. 우리 데이터셋(노드 5유형·관계 7종 + 속성)은 프로퍼티 그래프 모델이므로, RDF 계열과 같은 "표준"으로 묶어 인용하면 부정확하다.

## 3.8 우리 설계와의 연결

| 우리 결정 / 열린 항목 | 관련 문헌 |
|---|---|
| **D5** PostgreSQL 테이블 + 재귀 CTE | PostgreSQL `WITH RECURSIVE` 공식 문서(1차 문헌), All-in-One (SIGMOD 2017), One WITH RECURSIVE is Worth Many GOTOs (SIGMOD 2021) — RDBMS 내부 그래프 처리의 피어리뷰 근거 |
| **D5** 기각한 대안 Apache AGE | Apache AGE 공식 문서 — 기각 이유(설치 복잡도·RAM) 검증용 |
| **"온톨로지 기반" 요구 대응** | ISO/IEC 39075:2024 (GQL), Graph Pattern Matching in GQL and SQL/PGQ (SIGMOD 2022), Angles et al. (CSUR 2017) — **프로퍼티 그래프 모델의 규범 근거**. RDF/OWL/SHACL은 RDF 계열 근거로 별도 |
| **T5** 그래프 개체 부재 시 유사 이름 추측 금지 | BLINK, GENRE — 엔티티 링킹을 별도 문제로 다루는 선행 연구. 우리는 링킹을 하지 않겠다는 결정의 대비 근거 |
| 그래프 결과를 LLM에 넘기는 방식 | GNN-RAG (KG 토큰 9배 절감), Graph-constrained Reasoning (KG-Trie로 환각 없는 경로) — **Q1 환각 방지·Q2 컨텍스트 절감과 직결** |
| 향후 확장 (멀티홉 질의) | HippoRAG, G-Retriever, GRAG, Think-on-Graph, Graph CoT |
| KGQA 평가 관행 | GrailQA(3단계 일반화), KQA Pro, SymKGQA — 자체 엣지 세트 설계 시 참고 |

---

# 4. 라우터 / 도구 선택

## 4.1 도구 사용 / Tool Learning

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Schick et al. (2023) | Toolformer: Language Models Can Teach Themselves to Use Tools | NeurIPS 2023 | https://proceedings.neurips.cc/paper_files/paper/2023/hash/d842425e4bf79ba039352da0f658a906-Abstract-Conference.html | 자기지도 손실로 "어떤 API를 언제 어떤 인자로 호출할지"를 학습 — 도구 사용의 출발점 |
| Shen et al. (2023) | HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face | NeurIPS 2023 | https://papers.nips.cc/paper_files/paper/2023/hash/77c33e6a367922d003ff102ffb92b658-Abstract-Conference.html | LLM을 컨트롤러로 두고 설명만 보고 전문 모델을 선택·실행·요약하는 계획-선택 파이프라인 |
| Li et al. (2023) | API-Bank: A Comprehensive Benchmark for Tool-Augmented LLMs | EMNLP 2023 | https://aclanthology.org/2023.emnlp-main.187/ | 실행 가능한 73개 API·314개 대화로 계획·검색·호출 능력을 분리 측정 |
| Qin et al. (2024) | ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs | ICLR 2024 (Spotlight) | https://openreview.net/forum?id=dHng2O0Jjr | 16,464개 API를 컨텍스트에 다 넣을 수 없다는 문제에서 API 리트리버로 후보를 좁히는 구조 정립 |
| Patil et al. (2024) | Gorilla: Large Language Model Connected with Massive APIs | NeurIPS 2024 | https://proceedings.neurips.cc/paper_files/paper/2024/hash/e4c61f578ff07830f5c37378dd3ecb0d-Abstract-Conference.html | 리트리버 인식 학습(RAT)으로 문서·버전이 바뀌는 대규모 중복 API에서도 올바른 호출 생성 |
| Qin et al. (2025) | Tool Learning with Foundation Models | ACM Computing Surveys 2025 | https://doi.org/10.1145/3704435 | 도구 학습을 의도 이해·계획·호출·응답 생성 단계로 정리한 대표 서베이 (과제 필수 참조 [1]이 인용) |
| Qu et al. (2025) | Tool Learning with Large Language Models: A Survey | Frontiers of Computer Science 2025 | https://doi.org/10.1007/s11704-024-40678-2 | 도구 검색·선택 문제를 별도 장으로 다룬 서베이 (Pylon-7이 인용) |

## 4.2 도구 선택 · 라우팅 (도구 수 확장, distractor tool)

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Huang et al. (2024) | MetaTool Benchmark for Large Language Models: Deciding Whether to Use Tools and Which to Use | ICLR 2024 (Poster) | https://openreview.net/forum?id=R0c2qtalgG | **"도구를 쓸지 말지"와 "어느 도구를 쓸지"를 함께 평가.** 유사 선택지 서브태스크에 near-miss 디스트랙터 도구를 섞어 선택 정확도 저하를 보인다 |
| Zhang et al. (2024) | ToolBeHonest: A Multi-level Hallucination Diagnostic Benchmark for Tool-Augmented Large Language Models | EMNLP 2024 | https://aclanthology.org/2024.emnlp-main.637/ | **필요한 도구가 아예 없는(missing) 상황**과 그럴듯하지만 부적합한(potential) 디스트랙터 주입 설정에서 해결 가능성 판단을 진단. 최상위 모델도 45.3/100 |
| Yakovlev et al. (2024) | Toolken+: Improving LLM Tool Usage with Reranking and a Reject Option | Findings of EMNLP 2024 | https://aclanthology.org/2024.findings-emnlp.345/ | top-k 도구를 문서 기반 재순위화하고 **REJECT 옵션**을 추가해 "도구를 쓰지 않아야 할 때"의 오호출 억제 |
| Shi et al. (2025) | Retrieval Models Aren't Tool-Savvy: Benchmarking Tool Retrieval for Large Language Models (ToolRet) | Findings of ACL 2025 | https://aclanthology.org/2025.findings-acl.1258/ | 43k 도구 코퍼스 벤치마크 — 일반 IR에서 강한 리트리버조차 대규모 도구 인벤토리에서는 nDCG@10이 33.83까지 붕괴 |
| Patil et al. (2025) | The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models | ICML 2025 | https://proceedings.mlr.press/v267/patil25a.html | AST 기반 함수 호출 평가 — **적합한 도구가 없을 때 호출을 포기하는 irrelevance 판단을 별도 항목으로 측정** |
| Wang et al. (2025) | ToolGen: Unified Tool Retrieval and Calling via Generation | ICLR 2025 | https://openreview.net/forum?id=XLMAMmowdY | 47k 도구를 전용 토큰으로 어휘에 편입해 검색과 호출을 하나의 생성 과정으로 통합 |

## 4.3 질의 라우팅 / 모델 라우팅

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Ding et al. (2024) | Hybrid LLM: Cost-Efficient and Quality-Aware Query Routing | ICLR 2024 | https://openreview.net/forum?id=02f3mUtqnM | 쿼리 난이도를 예측하는 라우터로 소형/대형 모델을 선택해 품질 저하 없이 대형 호출 40% 절감 |
| Chen et al. (2024) | FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance | TMLR 2024 | https://openreview.net/forum?id=cSimKw5p6R | 저렴한 모델부터 순차 호출하는 캐스케이드 + 품질 점수 기반 조기 종료 |
| Lu et al. (2024) | Routing to the Expert: Efficient Reward-guided Ensemble of Large Language Models (Zooter) | NAACL 2024 | https://aclanthology.org/2024.naacl-long.109/ | 보상 모델 점수를 라벨로 라우터를 증류 학습해 쿼리마다 최적 전문가 LLM에 배정 |
| Aggarwal et al. (2024) | AutoMix: Automatically Mixing Language Models | NeurIPS 2024 | https://papers.nips.cc/paper_files/paper/2024/hash/ecda225cb187b40ea8edc1f46b03ffda-Abstract-Conference.html | 소형 모델 출력을 자기검증한 뒤 POMDP 메타 라우터로 대형 모델 재질의 여부 결정 |
| Ong et al. (2025) | RouteLLM: Learning to Route LLMs from Preference Data | ICLR 2025 | https://openreview.net/forum?id=8sSqNntaMr | 사람 선호 데이터로 강/약 모델 사이 라우터를 학습해 품질 유지하며 비용 2배 이상 절감 |
| Feng et al. (2025) | GraphRouter: A Graph-based Router for LLM Selections | ICLR 2025 | https://proceedings.iclr.cc/paper_files/paper/2025/hash/41b6674c28a9b93ec8d22a53ca25bc3b-Abstract-Conference.html | 태스크·쿼리·LLM을 노드로 둔 이종 그래프의 엣지 예측으로 성능-비용 고려 선택 |

## 4.4 에이전트 추론 프레임워크

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Yao et al. (2023) | ReAct: Synergizing Reasoning and Acting in Language Models | ICLR 2023 | https://openreview.net/forum?id=WE_vluYUL-X | 추론 흔적과 도구 행동을 번갈아 생성하는 표준 인터리브드 프레임워크 (Pylon-7이 3단계 파이프라인의 기반으로 인용) |
| Wang et al. (2023) | Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models | ACL 2023 | https://aclanthology.org/2023.acl-long.147/ | 하위 과제 계획을 먼저 세우고 실행하는 제로샷 프롬프팅 |
| Yao et al. (2023) | Tree of Thoughts: Deliberate Problem Solving with Large Language Models | NeurIPS 2023 | https://proceedings.neurips.cc/paper_files/paper/2023/hash/271db9922b8d1f4dd7aaef84ed5ac703-Abstract-Conference.html | 사고 단위를 트리로 탐색하며 자기평가·전망·백트래킹 |
| Shinn et al. (2023) | Reflexion: Language Agents with Verbal Reinforcement Learning | NeurIPS 2023 | https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html | 가중치 갱신 없이 실패 피드백을 언어로 반성해 다음 시도에 반영 |
| Madaan et al. (2023) | Self-Refine: Iterative Refinement with Self-Feedback | NeurIPS 2023 | https://proceedings.neurips.cc/paper_files/paper/2023/hash/91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference.html | 하나의 LLM이 생성·피드백·수정을 반복해 출력 품질 개선 |
| Huang et al. (2024) | Large Language Models Cannot Self-Correct Reasoning Yet | ICLR 2024 | https://openreview.net/forum?id=IkmD3fKBPQ | **외부 피드백 없는 내재적 자기교정은 추론 성능을 오히려 떨어뜨린다** (부정적 결과) |

## 4.5 컨텍스트 길이와 성능

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Shi et al. (2023) | Large Language Models Can Be Easily Distracted by Irrelevant Context | ICML 2023 | https://proceedings.mlr.press/v202/shi23a.html | **무관한 문장 하나만 끼워 넣어도** 산술 추론 정확도가 크게 떨어짐 (GSM-IC). 과제 필수 참조 [1]이 인용 |
| Liu et al. (2024) | Lost in the Middle: How Language Models Use Long Contexts | TACL 2024 | https://aclanthology.org/2024.tacl-1.9/ | 정답이 컨텍스트 중간에 있을 때 성능이 급락하는 U자형 위치 편향 (과제 권장 참조) |
| Yoran et al. (2024) | Making Retrieval-Augmented Language Models Robust to Irrelevant Context | ICLR 2024 | https://openreview.net/forum?id=ZS4m74kZpH | RAG에서 무관한 문단이 정확도를 떨어뜨림을 5개 ODQA로 보이고 NLI 필터링으로 강건성 확보 |
| Levy et al. (2024) | Same Task, More Tokens: the Impact of Input Length on the Reasoning Performance of Large Language Models | ACL 2024 | https://aclanthology.org/2024.acl-long.818/ | 난이도 고정한 채 패딩으로 길이만 늘려도 최대 컨텍스트보다 훨씬 짧은 지점부터 성능 저하 |
| Hsieh et al. (2024) | RULER: What's the Real Context Size of Your Long-Context Language Models? | **COLM 2024** | https://openreview.net/forum?id=kIoBbc76Sy | 대부분 모델이 공언한 길이보다 짧은 "실효 컨텍스트"만 유지 (과제 필수 참조 [1]이 인용) |
| Zhang et al. (2024) | Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding | NeurIPS 2024 | https://proceedings.neurips.cc/paper_files/paper/2024/hash/6ffdbbe354893979367f93e2121e37dd-Abstract-Conference.html | RoPE 장거리 감쇠가 중간 손실 편향의 원인임을 분석하고 헤드별 다중 스케일 위치 인코딩으로 완화 |

## 4.6 소형 LLM의 도구 사용 / 온프레미스 에이전트

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Shen et al. (2024) | Small LLMs Are Weak Tool Learners: A Multi-LLM Agent | EMNLP 2024 | https://aclanthology.org/2024.emnlp-main.929/ | **소형 LLM은 단일 에이전트로 계획·호출·요약을 모두 못하므로 planner/caller/summarizer로 역할을 분해해야 한다** |
| Xu et al. (2023) | On the Tool Manipulation Capability of Open-source Large Language Models | NeurIPS 2023 **워크샵** (Foundation Models for Decision Making), Oral | https://neurips.cc/virtual/2023/82818 | 오픈소스 LLM의 도구 조작 격차를 측정하고 몇 가지 기법으로 8개 과제 중 4개에서 GPT-4급 달성 |
| Erdogan et al. (2024) | TinyAgent: Function Calling at the Edge | EMNLP 2024 (System Demonstrations) | https://aclanthology.org/2024.emnlp-demo.9/ | 큐레이션 데이터와 LLMCompiler로 소형 모델을 튜닝해 엣지에서 GPT-4-Turbo급 함수 호출 |
| Abdelaziz et al. (2024) | Granite-Function Calling Model: Introducing Function Calling Abilities via Multi-task Learning of Granular Tasks | EMNLP 2024 Industry Track | https://aclanthology.org/2024.emnlp-industry.85/ | 함수 이름 탐지·다음 최적 함수 등 7개 세부 태스크 멀티태스크 학습 |
| Liu et al. (2025) | ToolACE: Winning the Points of LLM Function Calling | ICLR 2025 | https://proceedings.iclr.cc/paper_files/paper/2025/hash/663865ea167425c6c562cb0b6bcf76c7-Abstract-Conference.html | 26,507개 API 풀을 자기진화로 합성해 8B 모델이 BFCL에서 GPT-4급 성능 |
| Lin et al. (2025) | Hammer: Robust Function-Calling for On-Device Language Models via Function Masking | ICLR 2025 (Spotlight) | https://openreview.net/forum?id=yVQcr4qjD6 | 학습 시 함수 이름을 무작위 문자열로 마스킹해 이름 암기 대신 설명 이해를 강제, **무관한 함수(irrelevance) 민감도**를 높인 온디바이스 7B 모델 |

## 4.7 환각 방지 / Abstention (거절 응답 설계)

| 저자(연도) | 제목 | 발표처 | URL | 한 줄 주제 |
|---|---|---|---|---|
| Wen et al. (2025) | Know Your Limits: A Survey of Abstention in Large Language Models | TACL 2025 | https://aclanthology.org/2025.tacl-1.26/ | **쿼리·모델·인간 가치 세 관점으로 abstention 기법·벤치마크·평가지표를 정리한 서베이** |
| Rajpurkar et al. (2018) | Know What You Don't Know: Unanswerable Questions for SQuAD | ACL 2018 (Short) | https://aclanthology.org/P18-2124/ | 답이 없는 적대적 질문 5만여 개를 추가한 SQuAD 2.0 — "답변 불가 판별"을 과제화 |
| Lin et al. (2022) | Teaching Models to Express Their Uncertainty in Words | TMLR 2022 | https://openreview.net/forum?id=8s8K2UZGTZ | 로짓 대신 자연어로 확신도를 말하도록 학습시켜 보정된 언어적 불확실성 표현 확보 |
| Yin et al. (2023) | Do Large Language Models Know What They Don't Know? | Findings of ACL 2023 | https://aclanthology.org/2023.findings-acl.551/ | 답할 수 없는 질문과 대응 짝으로 구성한 SelfAware로 LLM의 지식 경계 인식 평가 |
| Zhang et al. (2024) | R-Tuning: Instructing Large Language Models to Say 'I Don't Know' | NAACL 2024 (Outstanding Paper) | https://aclanthology.org/2024.naacl-long.394/ | 거부 인식(refusal-aware) 데이터로 모르는 질문에 답하지 않도록 튜닝 |
| Cheng et al. (2024) | Can AI Assistants Know What They Don't Know? | ICML 2024 | https://proceedings.mlr.press/v235/cheng24i.html | "I don't know" 데이터셋으로 정렬해 모르는 질문은 거부하면서 답하는 질문의 정확도는 오히려 상승 |

## 4.8 신뢰도 미달로 배제한 문헌 / 검증 메모

**배제 (arXiv-only, 피어리뷰 게재 확인 불가)**: RouterBench(2403.12031), Shnitzer et al. LLM Routing with Benchmark Datasets(2309.15789), Universal Model Routing(2502.08773), Octopus v2, τ-bench·ToolSandbox, "Language Models (Mostly) Know What They Know", Chain-of-Tools, NESTFUL.

**배제 (지정 학회 목록 밖)**: ToolRerank(LREC-COLING 2024), COLT / Towards Completeness-Oriented Tool Retrieval(CIKM 2024), Seal-Tools(NLPCC 2024).

**주의** — "도구 개수가 늘면 정확도가 떨어진다"를 정면으로 정량화한 논문은 대부분 arXiv-only이거나 2026년 프리프린트여서 배제했다. 지정 발표처 안에서 가장 직접적인 근거는 ToolRet(대규모 인벤토리에서 검색 성능 붕괴)과 MetaTool(유사 도구 증가 시 선택 저하) 두 편이다. 이 논지를 강하게 주장하려면 두 편에 기대거나 자체 실험으로 뒷받침하는 편이 안전하다.

**필요 시 교체 가능한 검증된 대안**: When2Call (NAACL 2025, https://aclanthology.org/2025.naacl-long.174/ — 도구 호출/역질문/불가 인정 결정을 다루는 벤치마크로 거절 응답 설계에 가장 순수하게 부합), Re-Invoke (Findings of EMNLP 2024), ConAgents (Findings of EMNLP 2024), RouterDC (NeurIPS 2024), Mixture-of-Agents (ICLR 2025).

## 4.9 우리 설계와의 연결

| 우리 결정 / 열린 항목 | 관련 문헌 |
|---|---|
| **D1** 라우터를 MCP 서버 측 도구로 (에이전트 부담 축소) | **Shen et al., Small LLMs Are Weak Tool Learners (EMNLP 2024)** — 소형 LLM은 계획·호출·요약을 단일 에이전트로 감당하지 못하므로 역할을 분해해야 한다. 우리가 도구 선택을 에이전트에서 서버로 옮긴 결정의 직접 근거 |
| **D1** 규칙 기반 선택 (LLM 도구 선택 아님) | Hybrid LLM, RouteLLM, Zooter, GraphRouter — 라우팅을 별도 컴포넌트로 두는 설계 계보. MetaTool은 LLM 도구 선택의 실패 양상을 보여줌 |
| **D2** 도구 4개만 등록 | ToolLLM(16k API), ToolGen(47k), ToolRet(43k 코퍼스에서 nDCG@10 33.83까지 붕괴) — **도구 인벤토리가 커질 때 선택이 무너진다는 반대편 증거. 우리는 도구를 4개로 유지하므로 이 문제를 구조적으로 회피한다는 논거로 쓸 수 있다** |
| **D6** 무매칭 거절 (도구를 호출하지 않음) | **Toolken+ REJECT 옵션 (Findings of EMNLP 2024)**, **BFCL의 irrelevance 판단 항목 (ICML 2025)**, MetaTool의 "도구를 쓸지 말지", ToolBeHonest의 missing-tool 설정, Hammer의 irrelevance 민감도 — 거절을 정식 설계 요소로 다룬 피어리뷰 근거가 두텁다. When2Call(NAACL 2025)이 가장 근접 |
| **D6** 무매칭에 병렬 폴백을 쓰지 않는 이유 | **Shi et al. (ICML 2023)** — 무관한 문장 하나로도 추론이 무너진다. Yoran et al. (ICLR 2024) — RAG에서 무관 문단이 정확도를 떨어뜨림. 우리가 "무관한 컨텍스트를 주면 환각" 논리로 기각한 대안의 실증 근거 |
| **Q1·Q3** 환각 방지 / 정형화된 "모름" 답변 | Abstention 서베이 (TACL 2025), R-Tuning (NAACL 2024 Outstanding), Cheng et al. (ICML 2024 — 거부 정렬이 답하는 질문의 정확도를 오히려 높임), SelfAware, SQuAD 2.0 |
| **T1** SQL 생성 실패 재시도 정책 (열린 항목) | **Huang et al., LLMs Cannot Self-Correct Reasoning Yet (ICLR 2024)** — 외부 피드백 없는 자기교정은 성능을 떨어뜨린다. **재시도는 반드시 실행 오류 메시지 같은 외부 신호를 물려야 하고, LLM 자체 검토 루프는 위험하다.** 대비: Reflexion·Self-Refine (외부 피드백 있는 경우) |
| **Q2** 컨텍스트 초과 / TACC 적용 | RULER (COLM 2024 — 실효 컨텍스트는 공언보다 짧다), Levy et al. (ACL 2024 — 길이만 늘려도 저하), Lost in the Middle, Found in the Middle. 권장 모델의 4K급 컨텍스트에서 반환량 절사가 필수임을 뒷받침 |
| **D3** 병렬 호출 병합 시 결과 절사 | 위 4.5절 전체 + Pylon-7의 L2.5 ablation(KB 단독 추가가 정확도를 떨어뜨림) |
| 에이전트 구조 (Pylon-7 Stage A/B/C) | ReAct (ICLR 2023), Plan-and-Solve (ACL 2023) — Pylon-7이 자기 파이프라인의 기반으로 인용한 원 논문들 |
| 권장 모델(소형·로컬)의 도구 호출 실현 가능성 | TinyAgent, Granite-FCM, ToolACE, Hammer — 7~8B급 온디바이스 모델이 함수 호출을 해내는 선행 사례 |

## 4.10 "MCP Parallel 패턴" 용어 소재 — 가설 (우리 판단 · **검증 시도 후 미확정**)

> **이 절은 문헌 근거가 아니다.** 근거로 삼는 자료가 벤더 엔지니어링 블로그라 위 수집 기준상 서지 표에 올릴 수 없다. **인용 논거로 쓰지 않고, 심사 답변의 프레이밍으로만 쓴다.**

### 실측된 사실

| # | 사실 | 확인처 |
|---|---|---|
| 1 | "Parallel"의 유일한 출현은 KOSSA 요강의 **괄호 별칭 1회**. 블로그·공지·데이터셋 0회 | [dataset-analysis.md](../dataset-analysis.md) 6장 |
| 2 | **어느 출처도 무엇이 병렬인지 정의하지 않는다** | 동일 |
| 3 | questions.json 정답이 전부 도구 1개 — `tool`이 배열이 아닌 문자열 (30/30) | 동일 |
| 4 | **MCP 스펙에 "Parallel" 패턴 개념이 없다** | [mcp-spec.md](./mcp-spec.md) — 0건 |
| 5 | **air 프레임워크 문서에도 없다** (리원에이스 자기 오픈소스인데도) | [air-evaluation.md](../air-evaluation.md) — 0건 |
| 6 | 필수 참조 [2] Pylon-7은 해당 계층을 **`L5 Routing`** 이라 부른다 | [pylon-7.md](./pylon-7.md) |

### 가설

**요강이 서술한 동작은 표준 에이전트 워크플로 분류의 `Routing`이고, 괄호 별칭은 그 목록에서 인접한 `Parallelization`을 집은 것이다.**

널리 인용되는 분류(Anthropic, *Building effective agents*, 2024-12)는 다섯이며 **Routing 바로 다음이 Parallelization**이다 — Prompt chaining / **Routing** / **Parallelization** / Orchestrator-workers / Evaluator-optimizer.

| 패턴 | 정의 | 요강 서술과 |
|---|---|---|
| **Routing** | 입력을 분류해 전문화된 후속 처리로 보낸다 | *"질문 유형을 분석하여 적합한 도구를 자동 매칭"* — **일치** |
| **Parallelization** | 과업을 독립 하위과업으로 쪼개 동시 실행 후 집계(sectioning), 또는 같은 과업을 반복해 투표(voting) | 쪼개는 얘기도 집계 얘기도 없음 |

### 이 가설을 지지하는 것

- **(a) 정의를 안 썼다.** 병렬을 진짜 요구했다면 무엇을 병렬로 하는지 한 줄은 썼을 것이다.
- **(b) 검증 수단을 안 만들었다.** `tool`이 문자열이라 데이터셋이 복수 정답을 **담을 수조차 없다.** 도구별 정확히 10문항에 `hint`까지 붙인 데이터셋의 꼼꼼함과 어긋난다.
- **(c) 이 판의 표준 어휘는 Routing이다.** 블로그·README·요강이 그 컴포넌트를 전부 "라우터"라 부르고, 필수 참조가 L5를 Routing이라 부른다. 오직 괄호 안에서만 Parallel이 된다.

### 대안 가설

| 대안 | 평가 |
|---|---|
| **정말로 병렬 호출을 의도했다** | (b)가 설명되지 않는다. 가장 약하다 |
| **패턴명이 아니라 비유였다** — "도구를 나란히(parallel) 등록해 두고 골라 쓴다" | 가능하다. **우리에겐 위 가설과 결론이 같다** — 동시 호출은 문면 요구가 아니다 |

### 결론

- **D3는 불변이다.** 병렬은 이미 "문면 요구가 아니라 우리 설계 선택"으로 규정돼 있고 근거는 자산 중복 실측이다. 이 가설이 맞든 틀리든 그대로다.
- **바뀌는 것은 심사 답변의 자세뿐이다.** 지금 답은 *"원문이 정의하지 않아서"* 하나이고 수세적이다.

### 표현 규칙

**"요강이 잘못 표기했다"고 쓰지 않는다.** 출제자 의도는 우리가 모른다. 사실만 서술하고 판정하지 않는다.

> 요강이 서술한 동작을 표준 워크플로 분류에 대면 **Routing**에 해당한다. 우리는 그것을 규칙 라우터로 구현했고, 추가로 상보 중복 구간(X3·X4)에서 병렬 호출을 둔다.

### 검증 결과 (2026-08-13)

요강 원문(`https://www.kossa.kr/materials/2026/ossp/tasks-liwonace.html`)을 확보해 이 절이 예고한 결정적 검증을 실행했다.

| 검증 항목 | 결과 | 가설에 |
|---|---|---|
| 요강에 분류의 다른 패턴 이름(Prompt chaining · Routing · Orchestrator-workers · Evaluator-optimizer)이 함께 등장하는가 | **0건.** 전문에서 "Parallel" 1회(괄호 별칭)뿐, "병렬" 0회 | **불리** — 이 절이 세운 확정 조건 불충족 |
| 필수 참조 [2] Pylon-7이 출처인가 (자사 참조 모델이라 더 유력한 후보였다) | **PDF 전문 23쪽에 "parallel" 0회.** 계층 이름은 `L5 Routing`이고, "concurrent" 0회, "simultaneous" 9회는 전부 *"토큰과 정확도를 동시에 개선"* 문맥 | **대안 기각** |

**가설은 확정되지 않았고, 가장 유력한 대안도 제거됐다.** 남는 것은 강화된 실측 사실 하나다:

> **"MCP Parallel 패턴"은 요강 밖 어디에서도 근거가 확인되지 않는 용어다.** 요강이 지정한 필수 참조 3건 중 확인 가능한 2건(Pylon-7 · MCP 스펙)에 없고, 자사 프레임워크 air에도, 블로그·공지·데이터셋에도 없다. (필수 참조 [1] TACC 논문은 미확인 — 우리 요약본에는 "연쇄 분석" 시나리오만 있고 병렬 개념은 없다.)

**가설의 지위**: 확정 수단을 소진했다. 반증된 것도 아니다. 분류 유래설은 여전히 가장 그럴듯한 설명이지만 **근거가 정황뿐**이므로, 발표·문서에서 **용어의 출처를 주장하지 않는다.** 위 "표현 규칙"의 문장은 유래를 언급하지 않으므로 그대로 쓸 수 있다.

**남은 확인 수단**: 주최 측 문의 — 요강 기술문의처 `sihyeon@liwonace.co.kr` (연구원 이시현). 물어보면 끝나는 문제다. **다른 문의 후보였던 "LLM 모델"(Gemma 4 E2B 대 KOSSA "7B") 행은 2026-08-14에 문의 대상에서 빠졌다** — 리원에이스 2출처가 동일 문면이라 문의로 얻을 정보가 없다고 판단했다 ([design.md](../design.md) 열어둔 항목). 이 절의 용어 문제만 남는다.

---

# 정리 — 우리 결정을 뒷받침하는 문헌 (요약)

| 결정 | 가장 직접적인 근거 |
|---|---|
| **D1** 서버 측 규칙 라우터 | Small LLMs Are Weak Tool Learners (EMNLP 2024) — 소형 LLM에게 도구 선택까지 맡기지 말고 역할을 분해하라 |
| **D2** 도구 4개 유지 | ToolRet (Findings of ACL 2025), MetaTool (ICLR 2024) — 도구 인벤토리가 커지면 선택이 붕괴한다 |
| **D3** 기본 단일, 상보 중복 구간만 병렬 + 결과 절사 | RULER (COLM 2024), Levy et al. (ACL 2024) — 실효 컨텍스트는 공언보다 짧다 |
| **D4** 도구 내부 LLM SQL 생성 | DIN-SQL (NeurIPS 2023), DAIL-SQL (PVLDB 2024), DTS-SQL (Findings of EMNLP 2024 — 7B 로컬 모델 실증) |
| **D4** SELECT-only 강제 | PostgreSQL `READ ONLY`·`GRANT SELECT` 공식 문서, Pedro et al. P2SQL 인젝션 (ICSE 2025) |
| **D5** PostgreSQL + 재귀 CTE | PostgreSQL `WITH RECURSIVE` 공식 문서, All-in-One (SIGMOD 2017), Hirn & Grust (SIGMOD 2021) |
| **D6** 무매칭 거절 | Toolken+ REJECT (Findings of EMNLP 2024), BFCL irrelevance (ICML 2025), Abstention 서베이 (TACL 2025) |
| **D6** 병렬 폴백 기각 | Shi et al. (ICML 2023), Yoran et al. (ICLR 2024) — 무관한 컨텍스트가 성능을 무너뜨린다 |
| **D7** 검증 이원화 | Dr.Spider (ICLR 2023) 섭동 기반 강건성 평가, RAGAs (EACL 2024), ARES (NAACL 2024) |
| **청킹 단순 전략** | Qu, Tu & Bao (Findings of NAACL 2025) — 시맨틱 청킹은 비용만큼의 이득이 없다 |
| **T1 재시도 정책** | Huang et al. (ICLR 2024) — 외부 피드백 없는 자기교정은 해롭다. 재시도는 실행 오류를 물려야 한다 |
| **온톨로지 근거** | ISO/IEC 39075:2024 (GQL), SQL/PGQ (SIGMOD 2022) — 프로퍼티 그래프는 W3C가 아니라 ISO 계열 |

---

# 5. 선택지 개수 → 성능 저하 정량화 (arXiv 포함)

> 앞선 4개 영역과 달리 **arXiv-only를 허용해 수집한 목록**이다. 4.8절이 지적한 갭("도구 수 증가 → 정확도 하락을 정면 정량화한 문헌이 피어리뷰 안에 거의 없다")을 메우기 위한 것이다.
>
> **정독하지 않았고, 정독 우선순위도 낮다** ([reading-priority.md](../reading-priority.md) 티어 4). D2는 이미 확정된 결정이므로 이 수치는 구현을 바꾸지 않고 서술·인용에만 쓰인다. 수치는 초록·표에서 확인된 것만 기록했고, 확인 못 한 것은 "수치 미확인"으로 남겼다.

## 5.1 도구 개수 스케일링 → 선택/호출 정확도 저하

| 저자(연도) | 제목 | 발표처 | URL | 핵심 수치 | 신뢰도 |
|---|---|---|---|---|---|
| Repantis et al. (2026) | How Many Tools Should an LLM Agent See? A Chance-Corrected Answer | arXiv:2605.24660 | https://arxiv.org/abs/2605.24660 | BFCL 370 도구·Claude Sonnet 4.6. **정답 도구가 후보에 있어도** 선택률 K=1 100.0% → K≈2.2 93.1% → **K=5 87.1%**. 인용구: "over-presentation reduces downstream choice accuracy" | arXiv-only |
| Gillespie & Perry (2026) | Scaling Enterprise Agent Routing: Degradation, Diagnosis, and Recovery | arXiv:2606.17519 | https://arxiv.org/abs/2606.17519 | 실배포 110 에이전트·584 도구. **10→110개 확대 시 라우팅 F1이 모델 3종 전부 16~23%p 하락.** 완벽 검색 가정한 oracle 상한도 10%p 하락. 임베딩 shortlisting으로 +10~11%p 회복 | arXiv-only |
| Lei et al. (2025) | MCPVerse: An Expansive, Real-World Benchmark for Agentic Tool Use | arXiv:2508.16260 | https://arxiv.org/abs/2508.16260 | 도구 수만 변화시킨 3단 모드. **Claude-4-Sonnet 62.4%(220+ 도구) → 44.2%(550+ 도구, ~140k 토큰)** | arXiv-only |
| Gan & Sun (2025) | RAG-MCP: Mitigating Prompt Bloat in LLM Tool Selection via RAG | arXiv:2505.03275 | https://arxiv.org/abs/2505.03275 | MCP stress test에서 **전체 도구를 컨텍스트에 넣는 베이스라인 선택 정확도 13.62%**, 검색 축소 시 43.13%. 프롬프트 토큰 50%+ 절감 | arXiv-only |
| Mo et al. (2025/2026) | LiveMCPBench: Can Agents Navigate an Ocean of MCP Tools? | arXiv:2508.01780 | https://arxiv.org/abs/2508.01780 | 70 서버·527 도구. Claude-Sonnet-4 78.95%, 대부분 모델 30~50%. **실패의 약 절반이 검색 오류** | arXiv-only |
| Liu et al. (2025/2026) | ToolScope: Enhancing LLM Agent Tool Use through Tool Merging and Context-Aware Filtering | arXiv:2510.20036 | https://arxiv.org/abs/2510.20036 | 초록이 원인 명시 — 중복·유사 도구가 "introducing ambiguity and reducing selection accuracy". 병합+필터링으로 선택 정확도 **8.38~38.6% 향상** | **ACL 2026 Main** |
| Bandi et al. (2026) | MCP-Atlas: A Large-Scale Benchmark for Tool-Use Competency with Real MCP Servers | arXiv:2602.00933 | https://arxiv.org/abs/2602.00933 | 36 실서버·220 도구. pass rate 최대 82.2%. **실패의 63.3%가 호출 오류가 아닌 "인지적" 실패** = 스키마는 맞지만 판단이 틀림 | arXiv-only |
| Fei et al. (2025) | MCP-Zero: Active Tool Discovery for Autonomous LLM Agents | arXiv:2506.01056 | https://arxiv.org/abs/2506.01056 | 308 서버·2,797 도구 전량 투입 시 248.1k 토큰. APIBank에서 토큰 98% 절감하며 정확도 유지 (저하 곡선 수치 미확인) | arXiv-only |
| Wang et al. (2026) | Beyond Accuracy: A Cognitive Load Framework for Mapping the Capability Boundaries of Tool-use Agents | arXiv:2601.20412 | https://arxiv.org/abs/2601.20412 | 인지 부하를 파라미터로 조절하는 ToolLoad-Bench, "distinct performance cliffs as cognitive load increases" (수치 미확인) | **AAAI 2026** |
| Dong et al. (2025/2026) | MSC-Bench: 5-Level Benchmark for Tool Orchestration in the MCP Ecosystem | arXiv:2510.19423 | https://arxiv.org/abs/2510.19423 | 기능 중첩·크로스서버 오케스트레이션이 기존 벤치마크의 "overly optimistic" 평가를 만든다 (수치 미확인) | **Findings of EACL 2026** |

## 5.2 디스트랙터 주입 → 성능 저하

| 저자(연도) | 제목 | 발표처 | URL | 핵심 수치 | 신뢰도 |
|---|---|---|---|---|---|
| **Shen et al. (2026)** | **Mem2ActBench: A Benchmark for Evaluating Long-Term Memory Utilization in Task-Oriented Autonomous Agents** | arXiv:2601.19935 | https://arxiv.org/abs/2601.19935 | **§5.4 Table 5 직접 확인.** 후보 도구 수 1→2→5일 때 선택 정확도 — **hard negative(정답과 의미적으로 가장 유사): 94.50% → 78.00% → 69.75%. random negative: 94.50% → 95.50% → 93.50% (무변화)** | arXiv-only |
| Yeon et al. (2025/2026) | Quantitative Certification of Agentic Tool Selection | arXiv:2510.03992 | https://arxiv.org/abs/2510.03992 | BFCL·OpenAPI 도구 풀에서 Distractor Selection / Top-N Saturation 스펙 하에 **인증된 정확도 상한이 약 20%까지 하락** | arXiv-only |
| Lee et al. (2026) | Lost in the Noise: How Reasoning Models Fail with Contextual Distractors (NoisyBench) | arXiv:2601.07226 | https://arxiv.org/abs/2601.07226 | RAG·추론·정렬·tool-use 4영역 11개 데이터셋. hard negative 디스트랙터 하에서 **SOTA 모델 최대 80% 성능 하락** | arXiv-only |
| Zhang et al. (2026) | Are Tools All We Need? Unveiling the Tool-Use Tax in LLM Agents | arXiv:2605.00136 | https://arxiv.org/abs/2605.00136 | 의미적 디스트랙터 하에서 **도구 증강이 native CoT를 못 이긴다**는 반직관 결과. "tool-use tax" (수치 미확인) | arXiv-only |
| Kwak et al. (2025) | ToolHaystack: Stress-Testing Tool-Augmented LMs in Realistic Long-Term Interactions | arXiv:2505.23662 | https://arxiv.org/abs/2505.23662 | 14개 SOTA LLM — 표준 멀티턴은 양호하나 노이즈 섞인 장기 상호작용에서 크게 고전 (수치 미확인) | arXiv-only |

## 5.3 일반 선택지 개수 → 판단 정확도 저하 (도구 외)

| 저자(연도) | 제목 | 발표처 | URL | 핵심 수치 | 신뢰도 |
|---|---|---|---|---|---|
| Repantis et al. (2026) | The 99% Success Paradox: When Near-Perfect Retrieval Equals Random Selection | arXiv:2605.18857 | https://arxiv.org/abs/2605.18857 | 20 Newsgroups에서 **BM25·SPLADE 모두 K=100에서 성공률 >99%인데 Bits-over-Random ≈ 0**(랜덤 수준 선택성). 기대 커버리지 비율이 3~5를 넘으면 선택성 붕괴 | **ICLR Blog Track 2026** |
| Lee & Son (2026) | Pushing the Boundaries of Multiple Choice Evaluation to One Hundred Options | arXiv:2604.14634 | https://arxiv.org/abs/2604.14634 | 후보를 100개까지 확대. padding-controlled 통제 실험 결과 **병목은 컨텍스트 길이가 아니라 후보 랭킹 자체**. 실패 모드 2종: semantic confusion, 앞쪽 편향 (정확한 % 미확인) | arXiv-only |
| Amiraz et al. (2025) | The Distracting Effect: Understanding Irrelevant Passages in RAG | arXiv:2505.06914 | https://arxiv.org/abs/2505.06914 | 무관 패시지의 distracting effect 정량화 프레임워크. hard distractor 파인튜닝으로 정답률 최대 7.5% 향상 (저하폭 미확인) | **ACL 2025 Long** |
| Valkanova & Yordanov (2024) | Irrelevant Alternatives Bias Large Language Model Hiring Decisions | arXiv:2409.15299 | https://arxiv.org/abs/2409.15299 | **무관한 열등 선택지(decoy) 추가만으로** GPT-3.5·GPT-4의 선택이 유의하게 이동. 프롬프트 경고로도 견고하게 유지 (수치 미확인) | **Findings of EMNLP 2024** |

## 5.4 도구 설명 길이·토큰 → 성능

| 저자(연도) | 제목 | 발표처 | URL | 핵심 수치 | 신뢰도 |
|---|---|---|---|---|---|
| Hasan et al. (2026) | MCP Tool Descriptions Are Smelly! Towards Improving AI Agent Efficiency with Augmented MCP Tool Descriptions | arXiv:2602.14878 | https://arxiv.org/abs/2602.14878 | 103 MCP 서버·856 도구 실측. **97.1%가 최소 1개 smell, 56%는 목적 불명확.** 설명 전면 보강 시 성공률 중위 +5.85%p이지만 **실행 스텝 +67.46%, 16.67% 케이스는 퇴행.** compact 조합이 신뢰성 유지하며 토큰 절감 | arXiv-only |
| Kutschka & Geiger (2026) | Notation Matters: A Benchmark Study of Token-Optimized Formats in Agentic AI Systems | arXiv:2605.29676 | https://arxiv.org/abs/2605.29676 | 벤치마크 4종·open-weight LLM 5종. **TRON 토큰 27% 절감 대가로 정확도 JSON 대비 14%p 이내 하락, TOON 18% 절감에 9%p 하락** — 스키마 토큰 압축은 공짜가 아니다 | arXiv-only |
| Krikorian et al. (2026) | NTILC: Neural Tool Invocation via Learned Compression | arXiv:2606.06566 | https://arxiv.org/abs/2606.06566 | 전체 스펙 투입 시 비용이 레지스트리 크기에 선형 증가하고 "degrades selection accuracy, particularly due to interference from irrelevant tools". 컨텍스트 95%+ 절감 (저하폭 미확인) | arXiv-only |
| Zeng et al. (2026) | LOCA-bench: Benchmarking Language Agents Under Controllable and Extreme Context Growth | arXiv:2602.07962 | https://arxiv.org/abs/2602.07962 | 태스크 의미를 고정한 채 컨텍스트만 통제 확장하는 "context rot" 벤치마크 (수치 미확인) | arXiv-only |

## 5.5 반증 문헌 — 인용 전에 반드시 알아야 할 것

| 저자(연도) | 제목 | 발표처 | URL | 왜 중요한가 | 신뢰도 |
|---|---|---|---|---|---|
| **Chen (2026)** | **Looking Is Not Picking: An Attention-Segment Account of Tool-Selection Failures in LLM Agents** | arXiv:2606.16364 | https://arxiv.org/abs/2606.16364 | **"정보 과부하 때문"이라는 통설을 정면 반박.** 모델은 정답 도구에 80%(우연 21%) 어텐션을 주면서도 오선택한다. **프롬프트 측 개선은 실패의 ≤23%만 복구, readout 측 개입은 59~91% 복구** — 병목은 어텐션 배분이 아니라 결정 메커니즘 | arXiv-only |
| Lei et al. (2025) — MCPVerse 내 단서 | (5.1과 동일) | arXiv:2508.16260 | https://arxiv.org/abs/2508.16260 | Claude-4-Sonnet은 **Oracle(최소 도구)보다 Standard(220+ 도구)에서 더 높은 정확도**를 냈다. 넓은 도구 공간이 새 해법 경로를 여는 케이스가 있으므로 "도구는 적을수록 항상 좋다"는 무조건적 주장에는 반례가 있다 | arXiv-only |
| Bhat et al. (2026) | Benchmarking the Benchmarks: A Validity Audit of Tool-Calling Evaluation | arXiv:2607.02577 | https://arxiv.org/abs/2607.02577 | BFCL v4·τ2-Bench·LiveMCPBench·MCP-Atlas 감사 — 496 태스크 중 **18.5% 평가자-인간 불일치**, LiveMCPBench 동일 설정 23회 반복에서 **57.9%~76.8%(18.9%p 분산)**. 위 벤치마크 기반 수치 인용 시 오차범위에 주의 | arXiv-only |

## 5.6 인용 금지 — 널리 퍼졌으나 원논문에서 확인 실패

조사 에이전트가 원논문까지 확인했으나 존재하지 않았던 수치다. 웹에서 자주 인용되지만 **쓰지 않는다.**

| 떠도는 수치 | 확인 결과 |
|---|---|
| "도구 49→741개에서 성능 7~85% 하락" | 출처가 블로그(nexla, jenova, tianpan)뿐이고 학술 인용 없음 |
| "MCP-Universe에서 무관 서버 추가 시 Claude-4.0-Sonnet 22.22%→11.11%" | arXiv:2508.14704 PDF 전문(1.8MB)까지 확인했으나 **해당 분석이 논문에 존재하지 않음** |

## 5.7 우리 설계와의 연결

우리 논거는 **"에이전트에게 도구 선택을 요구하지 않는다"** 하나다. "도구를 적게 유지하면 정확도가 높다"(개수 프레임)나 "노출 도구는 서로 겹치지 않게 설계한다"(비중첩 프레임)는 쓰지 않는다.

근거는 Mem2ActBench Table 5다. 후보 도구를 1→5개로 늘릴 때 **hard negative 조건에서만** 94.50%→69.75%로 붕괴하고, **random negative 조건에서는 무변화**(93.5~95.5%)였다 — 원인은 개수 자체가 아니라 **의미적으로 겹치는 후보의 존재**다. 그리고 우리 도구 3종은 실측상 이미 겹쳐 있다 — 지식 그래프는 정형 테이블에서 100% 도출되고, 문서 40건은 전부 그래프 개체를 언급하며, `support_tickets` title 28종 중 18종이 문서와 주제가 겹친다 ([dataset-analysis.md](../dataset-analysis.md)). 이 데이터셋에서 자산을 겹치지 않게 설계하는 선택지는 없다.

**성립 조건.** 이 논거는 라우터 배치가 **A안**(에이전트가 `ask`만 호출) 또는 **B2**(코드가 `route` 결과를 집행)일 때만 성립한다. **B1**(LLM이 `route` 결과를 읽고 도구를 고름)이면 후보 4개 hard negative 조건 그대로다 — B1 비권장 근거다 ([routing-topology.md](../routing-topology.md) 3.6). 그리고 이 조건을 강제하는 것은 MCP 프로토콜이 아니라 **에이전트 코드**다 — 도구 4개를 등록하면 `tools/list`에 4개가 다 보이고 서버는 클라이언트 호출을 막을 수 없다 ([design.md](../design.md) D2).

이 논거가 우리 설계에 주는 함의:

| 함의 | 내용 |
|---|---|
| **D2와 정합적이다** | 에이전트는 도구 선택 문제를 겪지 않는다 — **A안이면 후보 1개(`ask`만 호출), B2면 LLM이 선택을 아예 하지 않는다.** B1은 해당 없음(위 "성립 조건"). 도구 3종을 함께 등록하되 에이전트에게 선택을 맡기지 않는 조합이 이 구간을 유지시킨다 |
| **후보 1개 수치를 겹쳐 쓰지 않는다** | Repantis et al. K=1 **100.0%**와 Mem2ActBench N=1 **94.50%**는 벤치마크·모델·지표가 달라 **같은 지점의 두 측정이 아니다.** 하나로 묶어 "우리가 있는 지점"이라고 쓰면 안 되고, "가장 유리한 구간"의 범위로만 인용한다. 애초에 B2에서는 LLM이 선택을 하지 않으므로 두 수치 어느 쪽도 우리 상한이 아니다 |
| **그래서 경계는 자산이 아니라 "요구 출력 형태"로 긋는다** | 도구 설명(description)도 이 축으로 쓴다 — `vector_search`=서술, `nl2sql`=정형 속성·수치, `knowledge_graph`=개체 식별·연결 ([design.md](../design.md) D9). 자산으로 설명을 쓰면 설명끼리 겹쳐 hard negative가 심해진다. 겹치는 구간 자체는 규칙에 중복 유형으로 명시해 처리한다(D3) |
| **프레이밍 리스크** | Chen (2026)이 "정보 과부하" 인과를 반박한다. 발표·보고서에서 "도구가 많으면 과부하로 성능이 떨어진다"고 쓰면 반박 가능한 주장이 된다. **"near-miss 혼동 최소화"로 쓰는 것이 안전하며, 이는 이미 확보한 MetaTool(ICLR 2024, near-miss 디스트랙터) 논지와도 일관된다** |
| 도구 설명 작성 지침 | Hasan et al. (2026) — 856개 도구 중 97.1%가 설명 smell을 갖고, 설명을 과하게 보강하면 실행 스텝이 +67% 늘고 일부는 퇴행한다. **compact하고 목적이 분명한 설명**을 목표로 한다 |
| 수치 인용 시 오차 | Bhat et al. (2026) — 이 절의 벤치마크 기반 수치들은 반복 실행 분산이 최대 18.9%p다. 단정적으로 인용하지 않는다 |
