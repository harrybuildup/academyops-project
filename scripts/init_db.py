"""scripts/init_db.py

Create the database schema.

Usage
-----
    python scripts/init_db.py

Reads DATABASE_URL from the environment (or .env).
Safe to run multiple times — uses CREATE TABLE IF NOT EXISTS.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

from src.database.schemas import create_tables

if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL is not set. Copy .env.example to .env and fill in the values.")
        sys.exit(1)

    # Hide credentials in the printed output
    safe_url = db_url.split("@")[-1] if "@" in db_url else db_url
    print(f"-> Connecting to: {safe_url}")
    create_tables()
    print("[SUCCESS] Schema created (or already up-to-date).")
