# AcademyOps

Lead-to-Enrollment Management System for EasySkill Career Academy.

Tracks prospective students through a defined sales pipeline:
**New → Contacted → Qualified → Demo → Enrolled / Lost**

---

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Pydantic + Uvicorn |
| Database | PostgreSQL + SQLAlchemy |
| Dashboard | Streamlit + Plotly |
| Tests | pytest + httpx2 |

---

## Setup

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd academyops-project

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
# Edit .env — set DATABASE_URL to your PostgreSQL connection string

# 5. Initialise the schema
python scripts/init_db.py

# 6. (Optional) Seed with sample data
python scripts/seed_db.py
```

---

## Running

### API + Dashboard together

```bash
python main.py
```

| Service | URL |
|---------|-----|
| REST API | http://localhost:8000/api/v1 |
| Swagger docs | http://localhost:8000/docs |
| Dashboard | http://localhost:8501 |

### Standalone API

```bash
uvicorn src.api.app:app --reload --port 8000
```

### Standalone Dashboard

```bash
streamlit run src/dashboard/app.py
```

---

## API Reference

| Method | Endpoint | Purpose | Status codes |
|--------|----------|---------|--------------|
| GET | `/api/v1/health` | Liveness probe | 200 |
| GET | `/api/v1/leads` | List leads (`stage`, `source`, `page`, `limit` params) | 200 |
| GET | `/api/v1/leads/{id}` | Get a single lead | 200 / 404 |
| POST | `/api/v1/leads` | Create a lead | 201 / 400 / 422 |
| PATCH | `/api/v1/leads/{id}/stage` | Advance pipeline stage | 200 / 404 / 422 |
| DELETE | `/api/v1/leads/{id}` | Delete a lead | 204 / 404 |
| POST | `/api/v1/leads/{id}/message` | Classify inbound message, suggest next action | 200 / 400 / 404 |

Error shape: `{"error": "<message>"}`

---

## Tests

```bash
pytest
```

Tests use an isolated in-memory SQLite database — no live PostgreSQL needed.

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | e.g. `postgresql://user:pass@localhost:5432/academyops_prod` |
| `DEBUG` | No | `True` enables SQLAlchemy query logging (default: `False`) |

---

## Project structure

```
academyops-project/
├── src/
│   ├── api/               FastAPI application
│   │   ├── app.py         Application factory
│   │   ├── routes.py      API router (/api/v1/leads)
│   │   ├── crud.py        Data-access layer
│   │   └── dependencies.py  DB session injection
│   ├── database/
│   │   ├── connections.py SQLAlchemy engine + Base
│   │   └── schemas.py     create_tables()
│   ├── models/
│   │   ├── lead.py        LeadStage enum + LeadORM
│   │   └── errors.py      Domain exceptions
│   ├── schemas/
│   │   ├── lead.py        Pydantic request/response models
│   │   └── message.py     Message request/response models
│   ├── utils/
│   │   ├── logger.py
│   │   └── cleansing.py
│   ├── classifier/
│   │   └── engine.py      Intent classifier (keyword rules)
│   ├── dashboard/
│   │   └── app.py         Streamlit dashboard
├── scripts/
│   ├── init_db.py              Create schema
│   ├── seed_db.py              Populate with sample data
│   └── evaluate_classifier.py  Classifier accuracy report
├── tests/
│   ├── conftest.py
│   ├── test_api.py        HTTP-level tests
│   └── test_crud.py       CRUD unit tests
├── data/
│   └── messy_leads.csv
├── .env.example
├── requirements.txt
├── pyproject.toml
└── main.py
```
