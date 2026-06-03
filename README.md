# WP-02: Data Ingestion & Cleansing Pipeline

## What It Does
Loads messy CSV lead data, validates & cleans it, and imports only good records into the database. Bad rows get quarantined with reasons.

## Usage

```bash
python -m src.repository.lead_importer \
  --input data/messy_leads.csv \
  --db academyops.db \
  --quarantine data/quarantine.csv
```

## Features

✅ **Cleaning** — Normalizes phone numbers, source names, whitespace  
✅ **Validation** — Requires name & phone, validates phone format (7-15 digits)  
✅ **De-duplication** — Checks within batch AND against database  
✅ **Safe Loading** — Uses transactions, parameterized queries via WP-01 repo  
✅ **Quarantine** — Rejects go to separate CSV with rejection reasons  
✅ **Reconciliation** — Prints summary report (total = imported + skipped + deduplicated)  

## Files

- `src/utils/cleansing.py` — Normalization functions
- `src/repository/lead_importer.py` — Main importer logic
- `data/messy_leads.csv` — Test data with intentional defects

## Testing

Run importer on test data:
```bash
python -m src.repository.lead_importer --input data/messy_leads.csv
```

Verify results:
```bash
sqlite3 academyops.db "SELECT COUNT(*) FROM leads;"
wc -l data/quarantine.csv
```
