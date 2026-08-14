# 페르소나 카드 — 문면 생성 입력

> 자체 엣지 세트의 **문면(`q`)을 생성할 때 쓰는 입력**이다. 카드는 스키마 어휘(테이블·컬럼·관계명)와 문서 유형만 참조해 썼고, `questions.json`을 보지 않는다. 골격(어떤 케이스를 만들 것인가)은 카드가 아니라 [README.md](./README.md)의 케이스 매트릭스가 정한다.
>
> **카드를 4장·3줄로 제한한 근거**: Kambhatla, Shaib & Govindarajan, *Measuring Lexical Diversity of Synthetic Data Generated through Fine-Grained Persona Prompting* (Findings of EMNLP 2025) — 페르소나 **유무**는 어휘 다양성을 올리지만 **세분화의 추가 이득은 미미**하다. 카드를 정교하게 만드는 데 시간을 쓸 근거가 없다 ([related-work.md](../docs/references/related-work.md) 6.3).

## P1. 영업 관리자

- **역할**: 고객사 계약과 매출을 관리한다. 분기 실적 회의를 준비한다.
- **관심 데이터**: `clients` · `contracts` · `sales` · `MANAGES_ACCOUNT`
- **말투**: 격식 있는 존댓말. 한 문장에 조건을 하나만 담는다.

## P2. 기술지원 엔지니어

- **역할**: 장애 티켓을 받아 원인을 찾고 조치한다. 제품 기술문서를 자주 뒤진다.
- **관심 데이터**: `support_tickets` · `products` · 장애 보고서 · 제품 기술문서 · `REPORTED_ISSUE` · `USES`
- **말투**: 구어체 반말 섞인 실무 말투. 사건과 원인을 한 번에 묻는 습관이 있다.

## P3. 경영지원 담당자

- **역할**: 부서 인원과 인건비, 프로젝트 예산을 정리해 보고한다.
- **관심 데이터**: `departments` · `employees` · `salary` · `budget` · `BELONGS_TO` · `HEAD_IS`
- **말투**: 간결한 존댓말. 수치를 직접 묻는다.

## P4. 신임 팀장

- **역할**: 부임한 지 얼마 안 돼 조직과 담당 관계를 파악하는 중이다.
- **관심 데이터**: `projects` · `employees` · `LEADS` · `BELONGS_TO` · `HAS_PROJECT` · 회의록
- **말투**: 탐색적인 존댓말. "누가", "어디"를 자주 쓴다.
