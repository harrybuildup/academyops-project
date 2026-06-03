# WP-03: Lead Management REST API (Flask)

REST API for lead management built with Flask. Depends on WP-01 (Lead Repository).

## Setup

```bash
source venv/bin/activate
pip install -r requirements.txt
python src/api.py
```

API runs on `http://localhost:5000/api/v1`

## Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/leads` | List leads (filters: `stage`, `source`; pagination: `page`, `limit`) |
| GET | `/leads/{id}` | Get a lead |
| POST | `/leads` | Create lead (required: `name`, `phone`) |
| PATCH | `/leads/{id}/stage` | Update stage |
| DELETE | `/leads/{id}` | Delete lead |

## Quick Examples

**List leads:**
```bash
curl "http://localhost:5000/api/v1/leads?stage=New&page=1&limit=10"
```

**Create lead:**
```bash
curl -X POST http://localhost:5000/api/v1/leads \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "phone": "+1-555-0100", "source": "google_ads"}'
```

**Update stage:**
```bash
curl -X PATCH http://localhost:5000/api/v1/leads/1/stage \
  -H "Content-Type: application/json" \
  -d '{"stage": "Contacted"}'
```

## Status Codes

- **200** — OK
- **201** — Created
- **204** — Deleted
- **400** — Bad request (validation error)
- **404** — Not found

## Error Response

```json
{
  "error": "Human-readable message",
  "details": "Optional context"
}
```

## Testing

```bash
pytest tests/test_api.py -v
```

## Troubleshooting

**Port 5000 in use?**
```bash
python src/api.py --port 8080
```

**Database not found?**
```bash
python src/cli.py list  # Initialize from WP-01
```

**422 error?**
Check JSON body—missing required fields (`name`, `phone`).

## Valid Pipeline Stages

`New` → `Contacted` → `Qualified` → `Demo` → `Enrolled` / `Lost`

---
