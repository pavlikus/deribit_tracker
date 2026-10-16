# Deribit Price Tracker
**Crypto Index Price Tracker** is an enterprise-grade backend service built to orchestrate the automated tracking, storage, and analysis of crypto assets index prices (**BTC** and **ETH**) in real time using the Deribit Exchange API infrastructure.

The system encapsulates high-performance asynchronous HTTP data streaming, a robust distributed background task scheduler, atomic database indexing, and a clean REST API interface.

## Features Included:
* **Asynchronous High-Speed Scraping:** Leverages parallel non-blocking `aiohttp` streams to concurrently poll metrics from crypto nodes.
* **Resilient Worker Schemas:** Distributes automated monitoring schedules across isolated `Celery Beat` cron-loops.
* **Optimized Search API:** Exposes flexible HTTP analytical tools including specific timestamp bounds filters and automated live-record lookups.
* **Total Code Quality Automation:** Fully backed by `Ruff` linters, unified `Pre-commit` code quality gate hooks, and multi-stage Docker layers.

## Quick Start (Deployment Guide)

### 1. Requirements Setup
Ensure you have Docker and Docker Compose installed onto your local environment.

### 2. Environment
Create `.env` file
```bash
ENV_MODE=development
DB_NAME=deribit_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
BROKER_URL=redis://redis:6379
BACKEND_URL=redis://redis:6379
TICKERS='["btc_usd", "eth_usd", "ton_usdc"]'
```

### 3. Initialization and Environment Boot
To launch the entire cluster (API, Database, Redis, Celery Workers, and Beat Scheduler) with an isolated context in one command, simply run from the repository root:
```bash
docker-compose up --build
```
*Note: Docker will intelligently verify network readiness using standard PostgreSQL healthchecks, preventing any boot phase crash cascades.*

### 4. Executing Automated Tests
To assert the complete behavioral validity of the REST API layers, trigger the test framework directly within the isolated environment container:
```bash
pytest -v
```

---

## REST API Endpoint Layout & Verification

All client queries require an explicit query-string parameter named `ticker` (case-insensitive, e.g., `btc_usd`).

* **All Prices:**
  `GET http://127.0.0/prices`
* **The Latest price:**
  `GET http://127.0.0/prices/latest`
* **Filter prices by date:**
  `GET http://127.0.0/prices/filter`
* **Docs:**
  `GET http://127.0.0/docs`

## Tech Stack
* **Runtime Language:** Python 3.14
* **Application Framework:** FastAPI (Asynchronous operations, native Pydantic validation)
* **Distributed Task Framework:** Celery & Celery Beat Scheduler
* **Data Transit Layer (Broker):** Redis (In-memory storage)
* **Target Database:** PostgreSQL 16
* **Database Driver/ORM:** SQLModel & SQLAlchemy 2.0 (Unified schema orchestration)
* **Package Manager:** uv (Astral-sh Rust package compiler engine)
* **Testing Engines:** pytest, pytest-asyncio, HTTPX


## Design Decisions (Architectural Rationale)

1. **Unified Schema Lifecycle via SQLModel**

   Instead of splitting development entities into independent database tables (SQLAlchemy) and web schemas (Pydantic), the system deploys `SQLModel` structures. This eliminates code duplication (DRY principle) and guarantees complete type safety across all service boundaries.


2. **Dynamically Isolated Environments (12-Factor App principles)**
   
   System parameters are isolated into explicit `DevelopmentConfig` and `ProductionConfig` inheritance trees powered by `pydantic-settings`. App contexts adapt dynamically based on single system variables (`ENV_MODE`), ensuring strict production secret enforcement.


3. **Compound Relational Indexing Strategy**

   The core schema enforces a strict composite database index: `"ticker", "timestamp"`. This eliminates costly `Sequential Scan` table operations on growing timelines, reducing filtering overhead to optimal \(O(\log N)\) algorithmic metrics.


4. **Robust Application-Level Isolation from Docker Volumes**
   
   Dependencies are installed using `uv`. The setup completely immunizes the runtime framework from being accidentally overwritten or deleted during active development container mounts.


5. **Atomic Testing Isolation via In-Memory Engines** 

   The testing pipelines completely mock and swap active live PostgreSQL configurations with virtual `aiosqlite:///:memory:` contexts during `pytest` operations. This ensures zero disk pollution, eliminates the necessity of mocking data manually, and decreases whole system verification times down to a fraction of a second.
   

6. **Automated Code Quality Governance via Pre-Commit & Ruff**
   
   The development workflow enforces an automated quality gate that prevents poorly formatted or non-compliant code from entering the version control system.
   
   **Rationale:** Instead of traditional, slow pipelines that chain multiple disjointed linters and formatters (`black`, `autoflake`, `pyupgrade`, `isort`), the repository leverages **Ruff** (a lightning-fast static analysis tool written in Rust) embedded into a native `pre-commit` hook pipeline. Combined with `yesqa`, the hooks automatically enforce PEP 8 styles, clean up stale `# noqa` suppressions, sort import groups chronologically, and prune dead or unused variables prior to every single code commit. This ensures absolute consistency across the GitHub repository and dramatically minimizes CI/CD feedback loop overhead.