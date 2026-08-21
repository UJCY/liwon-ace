-- ============================================================
-- Company-X 데이터베이스 스키마
-- 오픈소스 개발자대회 지정과제 데이터셋
-- PostgreSQL 15+ / pgvector 확장 필요
-- ============================================================

-- 1. 부서
CREATE TABLE departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,   -- 값: 경영지원팀 | 기술지원팀 | 데이터플랫폼팀 | 보안솔루션팀 | 영업팀 | 클라우드사업부
    head_id     INTEGER,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 2. 직원
CREATE TABLE employees (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    position    VARCHAR(50) NOT NULL,   -- 값: 과장 | 대리 | 부장 | 사원 | 이사 | 차장
    dept_id     INTEGER NOT NULL REFERENCES departments(id),
    hire_date   DATE NOT NULL,
    salary      INTEGER NOT NULL,   -- 단위: 만원 (1억원=10000, 5천만원=5000, 100만원=100)
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 3. 고객사
CREATE TABLE clients (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    industry        VARCHAR(50) NOT NULL,   -- 값: IT/SW | 건설 | 공공기관 | 교육 | 금융 | 미디어 | 에너지 | 유통/물류 | 의료/바이오 | 제조업
    region          VARCHAR(30) NOT NULL,   -- 값: 경기 | 광주 | 대구 | 대전 | 부산 | 서울 | 인천 | 제주
    company_size    VARCHAR(20) NOT NULL,   -- 값: enterprise | mid | startup
    contact_name    VARCHAR(50),
    contact_email   VARCHAR(100),
    registered_at   DATE NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 4. 제품/솔루션
CREATE TABLE products (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,   -- 값: Product-C1 | Product-C2 | Product-C3 | Product-C4 | Product-D1 | Product-D2 | Product-D3 | Product-S1 | Product-S2 | Product-S3 | Product-T1 | Product-T2
    category        VARCHAR(50) NOT NULL,   -- 값: cloud | consulting | data | security
    description     TEXT,   -- 값: DB 마이그레이션 자동화 도구. | 보안 인증 관리 시스템. | 인프라 모니터링 및 알림 시스템.
    price_monthly   INTEGER NOT NULL,   -- 단위: 만원 (1억원=10000, 5천만원=5000, 100만원=100)
    version         VARCHAR(20),   -- 값: 1.0 | 2.1.0 | 2.3.7 | 2.9.5 | 3.2.1 | 3.7.5 | 4.0.9 | 4.4.1 | 4.6.7 | 4.7.4 | 5.6.3
    release_date    DATE,   -- 값: 2023-03-16 | 2023-06-26 | 2024-02-16 | 2024-08-01 | 2024-10-16 | 2024-11-21 | 2025-03-22 | 2025-04-24 | 2025-05-27 | 2025-06-15 | 2025-09-10
    status          VARCHAR(20) DEFAULT 'active',   -- 값: active | beta
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 5. 계약
CREATE TABLE contracts (
    id              SERIAL PRIMARY KEY,
    client_id       INTEGER NOT NULL REFERENCES clients(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    manager_id      INTEGER NOT NULL REFERENCES employees(id),
    contract_type   VARCHAR(20) NOT NULL,   -- 값: maintenance | project | subscription
    amount          INTEGER NOT NULL,   -- 단위: 만원 (1억원=10000, 5천만원=5000, 100만원=100)
    start_date      DATE NOT NULL,
    end_date        DATE,
    status          VARCHAR(20) DEFAULT 'active',   -- 값: active | cancelled | completed
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 6. 프로젝트
CREATE TABLE projects (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    client_id       INTEGER NOT NULL REFERENCES clients(id),
    manager_id      INTEGER NOT NULL REFERENCES employees(id),
    contract_id     INTEGER REFERENCES contracts(id),
    status          VARCHAR(20) DEFAULT 'in_progress',   -- 값: completed | in_progress | on_hold | planning
    start_date      DATE NOT NULL,
    end_date        DATE,
    budget          INTEGER,   -- 단위: 만원 (1억원=10000, 5천만원=5000, 100만원=100)
    description     TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 7. 매출
CREATE TABLE sales (
    id              SERIAL PRIMARY KEY,
    contract_id     INTEGER NOT NULL REFERENCES contracts(id),
    client_id       INTEGER NOT NULL REFERENCES clients(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    amount          INTEGER NOT NULL,   -- 단위: 만원 (1억원=10000, 5천만원=5000, 100만원=100)
    sale_date       DATE NOT NULL,
    quarter         VARCHAR(10) NOT NULL,   -- 값: 2024-Q1 | 2024-Q2 | 2024-Q3 | 2024-Q4 | 2025-Q1 | 2025-Q2 | 2025-Q3 | 2025-Q4 | 2026-Q1 | 2026-Q2
    category        VARCHAR(50) NOT NULL,   -- 값: cloud | consulting | data | security
    region          VARCHAR(30) NOT NULL,   -- 값: 경기 | 광주 | 대구 | 대전 | 부산 | 서울 | 인천 | 제주
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 8. 기술 지원 티켓
CREATE TABLE support_tickets (
    id              SERIAL PRIMARY KEY,
    client_id       INTEGER NOT NULL REFERENCES clients(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    assignee_id     INTEGER REFERENCES employees(id),
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    priority        VARCHAR(10) NOT NULL,   -- 값: critical | high | low | medium
    status          VARCHAR(20) DEFAULT 'open',   -- 값: closed | in_progress | open | resolved
    created_at      TIMESTAMP NOT NULL,
    resolved_at     TIMESTAMP
);

-- 9. 문서 벡터 저장소 (참가자가 임베딩 후 적재)
CREATE TABLE document_chunks (
    id              SERIAL PRIMARY KEY,
    doc_id          VARCHAR(20) NOT NULL,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    embedding       vector(768),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 인덱스
