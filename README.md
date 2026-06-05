# AcademyOps v1.0

Lead-to-Enrollment Management System for EasySkill Career Academy.

Tracks prospective students through a defined sales pipeline:
**New → Contacted → Qualified → Demo → Enrolled / Lost**

---

## Table of Contents

1. [Stack](#stack)
2. [Prerequisites](#prerequisites)
3. [Setup](#setup)
4. [Running the system](#running-the-system)
5. [API reference](#api-reference)
6. [Intent classifier](#intent-classifier)
7. [Tests](#tests)
8. [Scripts](#scripts)
9. [Environment variables](#environment-variables)
10. [Project structure](#project-structure)
11. [Architecture](#architecture)

---

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Pydantic v2 + Uvicorn |
| Database | PostgreSQL + SQLAlchemy 2 |
| Dashboard | Streamlit + Plotly |
| Classifier | Rule-based keyword engine |
| Tests | pytest + httpx2 (SQLite in-memory) |
| CI | GitHub Actions |

---

## Prerequisites

- Python 3.12+
- PostgreSQL 14+ running locally (for the live API)
- Git

---

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd academyops-project

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt
pip install psycopg2-binary==2.9.12   # PostgreSQL driver (runtime only)

# 4. Configure environment
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env

# Edit .env and set DATABASE_URL to your PostgreSQL connection string.
# Example:  DATABASE_URL=postgresql://postgres:password@localhost:5432/academyops

# 5. Create the database schema
python scripts/init_db.py

# 6. (Optional) Seed with realistic sample data
python scripts/seed_db.py
```

---

## Running the system

### Everything together (recommended)

```bash
python main.py
```

| Service | URL |
|---------|-----|
| REST API | http://localhost:8000/api/v1 |
| Swagger docs | http://localhost:8000/docs |
| Dashboard | http://localhost:8501 |

### Docker (recommended for a clean environment)

No Python or PostgreSQL installation needed — Docker handles everything.

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| REST API | http://localhost:8000/api/v1 |
| Swagger docs | http://localhost:8000/docs |
| Dashboard | http://localhost:8501 |

The `init` service creates the schema automatically on first boot.
To also seed sample data:

```bash
docker compose run --rm api python scripts/seed_db.py
```

To stop and remove containers:

```bash
docker compose down          # keep the database volume
docker compose down -v       # also delete all data
```

### Standalone API

```bash
uvicorn src.api.app:app --reload --port 8000
```

### Standalone Dashboard

```bash
streamlit run src/dashboard/app.py
```

---

## API reference

All endpoints are versioned under `/api/v1`. Errors always return `{"error": "<message>"}`.

| Method | Endpoint | Purpose | Status codes |
|--------|----------|---------|--------------|
| GET | `/api/v1/health` | Liveness probe | 200 |
| GET | `/api/v1/leads` | List leads — `stage`, `source`, `page`, `limit` params | 200 |
| GET | `/api/v1/leads/{id}` | Get a single lead | 200 / 404 |
| POST | `/api/v1/leads` | Create a lead | 201 / 400 / 422 |
| PATCH | `/api/v1/leads/{id}/stage` | Advance pipeline stage | 200 / 404 / 422 |
| DELETE | `/api/v1/leads/{id}` | Delete a lead | 204 / 404 |
| POST | `/api/v1/leads/{id}/message` | Classify inbound message, suggest next action | 200 / 400 / 404 |

**List leads query params**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `stage` | string | — | Filter by pipeline stage |
| `source` | string | — | Filter by lead source |
| `page` | int ≥ 1 | 1 | Page number |
| `limit` | int 1–100 | 10 | Results per page |

**Create lead body**

```json
{ "name": "Alice Smith", "phone": "9876543210", "source": "Google", "notes": "" }
```

**Update stage body**

```json
{ "stage": "Qualified" }
```

Valid stages: `New`, `Contacted`, `Qualified`, `Demo`, `Enrolled`, `Lost`

---

## Intent classifier

`POST /api/v1/leads/{id}/message` classifies an inbound message from a lead.

**Request**
```json
{ "message": "How much does the course cost?" }
```

**Response**
```json
{
  "intent": "fees",
  "suggested_stage": "Qualified",
  "reply": "Thanks for asking about our fee structure! ..."
}
```

| Intent | Trigger | Suggested stage |
|--------|---------|----------------|
| `fees` | Cost, payment, scholarship, EMI, discount | Qualified |
| `timing` | Schedule, batch, duration, start date | Qualified |
| `eligibility` | Prerequisites, degree, fresher, criteria | Qualified |
| `not_interested` | Stop contact, unsubscribe, opt out | Lost |
| `other` | Anything else | *(current stage unchanged)* |

To evaluate classifier accuracy against the labelled sample set:

```bash
python scripts/evaluate_classifier.py
```

---

## Tests

```bash
pytest
```

The test suite runs entirely against an isolated in-memory SQLite database — no live PostgreSQL connection is needed.

```
tests/
├── test_api.py         HTTP-level tests for all lead endpoints
├── test_crud.py        CRUD unit tests (data-access layer)
└── test_classifier.py  Classifier engine + message endpoint tests
```

CI runs automatically on every push and pull request to `main` via GitHub Actions.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `python scripts/init_db.py` | Create the PostgreSQL schema (safe to re-run) |
| `python scripts/seed_db.py` | Populate with 115 realistic sample leads |
| `python scripts/evaluate_classifier.py` | Print classifier accuracy report |

---

## Environment variables

Stored in `.env` (never committed). Copy `.env.example` to get started.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL URL — `postgresql://user:pass@host:port/db` |
| `DEBUG` | No | `True` enables SQLAlchemy query logging (default: `False`) |

---

## Project structure

```
academyops-project/
├── src/
│   ├── api/                   FastAPI application
│   │   ├── app.py             Application factory + exception handlers
│   │   ├── routes.py          All API routes (/api/v1/...)
│   │   ├── crud.py            Database operations (leads)
│   │   └── dependencies.py    DB session injection
│   ├── classifier/
│   │   └── engine.py          Keyword-based intent classifier
│   ├── dashboard/
│   │   └── app.py             Streamlit operations dashboard
│   ├── database/
│   │   ├── connections.py     SQLAlchemy engine + Base (lazy init)
│   │   └── schemas.py         create_tables()
│   ├── models/
│   │   ├── lead.py            LeadStage enum + LeadORM (SQLAlchemy)
│   │   └── errors.py          Domain exceptions
│   ├── schemas/
│   │   ├── lead.py            Pydantic request/response schemas
│   │   └── message.py         Message request/response schemas
│   └── utils/
│       ├── logger.py          Structured file + console logger
│       └── cleansing.py       Phone/source normalisation helpers
├── scripts/
│   ├── init_db.py             Create schema
│   ├── seed_db.py             Seed sample data
│   └── evaluate_classifier.py Classifier accuracy report
├── tests/
│   ├── conftest.py            Shared fixtures (isolated SQLite DB)
│   ├── test_api.py            HTTP-level API tests
│   ├── test_crud.py           CRUD unit tests
│   └── test_classifier.py     Classifier + message endpoint tests
├── data/
│   └── messy_leads.csv        Sample import dataset
├── .github/
│   └── workflows/tests.yml    CI pipeline
├── .env.example               Environment variable template
├── .dockerignore
├── Dockerfile                 Multi-stage image (builder + runtime)
├── docker-compose.yml         Orchestrates db, init, api, dashboard
├── requirements.txt           Pinned Python dependencies
├── pyproject.toml             Build + pytest config
└── main.py                    Unified launcher (API + Dashboard)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Clients                          │
│          Browser / Postman / Dashboard                  │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP
┌───────────────────▼─────────────────────────────────────┐
│              FastAPI  (port 8000)                        │
│                                                         │
│  GET/POST/PATCH/DELETE  /api/v1/leads                   │
│  POST                   /api/v1/leads/{id}/message      │
│                                                         │
│  ┌──────────────┐   ┌──────────────────────────────┐   │
│  │  CRUD layer  │   │   Classifier engine           │   │
│  │  (crud.py)   │   │   (classifier/engine.py)      │   │
│  └──────┬───────┘   └──────────────────────────────┘   │
│         │ SQLAlchemy ORM                                │
└─────────┼───────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────┐
│              PostgreSQL  (port 5432)                    │
│              leads table                                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│           Streamlit Dashboard  (port 8501)               │
│           Reads from FastAPI via HTTP                   │
└─────────────────────────────────────────────────────────┘
```

### Component summary

| Component | Role |
|-----------|------|
| **FastAPI** | REST API — validates requests via Pydantic, routes to CRUD or classifier |
| **CRUD layer** | All SQLAlchemy DB operations for leads (create, read, list, update, delete) |
| **Classifier engine** | Stateless keyword scorer — classifies messages into 5 intents, maps to a suggested stage + reply |
| **PostgreSQL** | Persistent store for the `leads` table |
| **Streamlit dashboard** | Read-only ops view — KPI cards, funnel chart, recent leads table, filters |
| **pytest suite** | 53 tests running against an isolated SQLite DB — no live Postgres needed |
