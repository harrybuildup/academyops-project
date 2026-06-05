"""scripts/import_leads.py — WP-02 CSV ingestion pipeline.

Loads a messy external CSV of leads into the database, cleaning, validating,
and de-duplicating rows, quarantining bad rows, and printing a reconciliation
report.

Usage
-----
    python scripts/import_leads.py --input data/messy_leads.csv
    python scripts/import_leads.py --input data/messy_leads.csv \\
        --quarantine data/quarantine.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

from src.database.connections import get_session_factory
from src.database.schemas import create_tables
from src.models.lead import LeadORM, LeadStage
from src.utils.cleansing import (
    clean_and_validate_phone,
    normalize_source,
    normalize_string,
)


REQUIRED_COLUMNS = {"name", "phone"}


class LeadImporter:
    def __init__(
        self,
        quarantine_path: str = "data/quarantine.csv",
    ):
        self.quarantine_path = quarantine_path
        self.stats = {"total": 0, "imported": 0, "skipped": 0, "deduplicated": 0}

    def run_import(self, csv_input_path: str) -> None:
        create_tables()
        db = get_session_factory()()

        # Load all existing phones from the DB for dedup check
        existing_phones: set[str] = {
            r[0] for r in db.query(LeadORM.phone).all()
        }

        quarantine_rows: list[dict] = []
        seen_phones: set[str] = set()  # dedup within the batch

        try:
            with open(csv_input_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Normalise column names
                if reader.fieldnames is None:
                    print("ERROR: CSV has no headers.")
                    return

                fieldnames_lower = [c.strip().lower() for c in reader.fieldnames]
                missing = REQUIRED_COLUMNS - set(fieldnames_lower)
                if missing:
                    print(f"ERROR: CSV is missing required columns: {missing}")
                    return

                for raw_row in reader:
                    row = {k.strip().lower(): v for k, v in raw_row.items()}
                    self.stats["total"] += 1
                    rejection_reason = None

                    # --- Validate name ---
                    name = normalize_string(row.get("name", ""))
                    if not name:
                        rejection_reason = "Missing name"

                    # --- Validate & normalise phone ---
                    phone = None
                    if not rejection_reason:
                        try:
                            phone = clean_and_validate_phone(row.get("phone", ""))
                        except ValueError as e:
                            rejection_reason = str(e)

                    # --- Dedup within batch ---
                    if not rejection_reason and phone in seen_phones:
                        rejection_reason = "Duplicate phone in batch"

                    # --- Dedup against DB ---
                    if not rejection_reason and phone in existing_phones:
                        rejection_reason = "Phone already exists in database"

                    if rejection_reason:
                        quarantine_rows.append({**row, "rejection_reason": rejection_reason})
                        self.stats["skipped"] += 1
                        continue

                    # --- Normalise optional fields ---
                    source = normalize_source(row.get("source", "Website"))
                    notes = normalize_string(row.get("notes", ""))

                    lead = LeadORM(
                        name=name,
                        phone=phone,
                        source=source,
                        stage=LeadStage.NEW.value,
                        notes=notes,
                    )
                    db.add(lead)
                    seen_phones.add(phone)
                    existing_phones.add(phone)
                    self.stats["imported"] += 1

            db.commit()

        except FileNotFoundError:
            print(f"ERROR: Input file not found: {csv_input_path}")
            return
        except Exception as e:
            db.rollback()
            print(f"ERROR during import: {e}")
            return
        finally:
            db.close()

        # Write quarantine file
        if quarantine_rows:
            os.makedirs(os.path.dirname(self.quarantine_path) or ".", exist_ok=True)
            all_keys = list(quarantine_rows[0].keys())
            with open(self.quarantine_path, "w", newline="", encoding="utf-8") as qf:
                writer = csv.DictWriter(qf, fieldnames=all_keys)
                writer.writeheader()
                writer.writerows(quarantine_rows)

        self._print_report(csv_input_path)

    def _print_report(self, input_path: str) -> None:
        s = self.stats
        print("\n── Import Reconciliation Report ──────────────────────")
        print(f"  Input file  : {input_path}")
        print(f"  Total rows  : {s['total']}")
        print(f"  Imported    : {s['imported']}")
        print(f"  Skipped     : {s['skipped']}")
        print(f"  Quarantine  : {self.quarantine_path}")
        print("──────────────────────────────────────────────────────")
        assert s["imported"] + s["skipped"] == s["total"], "Counts do not reconcile!"
        print("✅  Counts reconcile.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import leads from a CSV file.")
    parser.add_argument("--input",      default="data/messy_leads.csv")
    parser.add_argument("--quarantine", default="data/quarantine.csv")
    args = parser.parse_args()

    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)

    importer = LeadImporter(quarantine_path=args.quarantine)
    importer.run_import(args.input)


if __name__ == "__main__":
    main()
