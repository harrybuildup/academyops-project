"""scripts/seed_db.py

Seed the database with a realistic lead distribution for analytics and testing.

Usage
-----
    python scripts/seed_db.py

Reads DATABASE_URL from the environment (or .env).
WARNING: clears all existing leads before inserting.
"""

import os
import random
import sys
from datetime import datetime, timedelta
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

SOURCES = ["Google", "LinkedIn", "Facebook", "Website", "Referral"]

STAGE_DISTRIBUTION = {
    LeadStage.NEW.value: 60,
    LeadStage.CONTACTED.value: 28,
    LeadStage.QUALIFIED.value: 14,
    LeadStage.DEMO.value: 8,
    LeadStage.ENROLLED.value: 5,
}

FIRST_NAMES = [
    "Rajesh", "Priya", "Arjun", "Neha", "Vikram", "Anjali", "Anil", "Deepika",
    "Sanjay", "Meera", "Rohan", "Karan", "Isha", "Harsh", "Pooja", "Nikhil",
    "Diya", "Aditya", "Shreya", "Varun", "Ritika", "Gaurav", "Sneha", "Rohit",
]
LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Reddy", "Verma", "Gupta", "Rao",
    "Nair", "Iyer", "Desai", "Chopra", "Bhat", "Joshi", "Trivedi", "Kulkarni",
]
NOTES = [
    "Interested in full-stack development", "Wants career transition support",
    "Looking to learn data science", "Needs placement assistance",
    "Working professional seeking upskill", "Recent graduate",
]


def _phone() -> str:
    return f"+91{random.randint(7000000000, 9999999999)}"


def _name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _lead(stage: str) -> LeadORM:
    days_ago = random.randint(1, 60)
    created = datetime.now() - timedelta(days=days_ago)
    stage_delay = {
        LeadStage.NEW.value: 0,
        LeadStage.CONTACTED.value: random.randint(1, 3),
        LeadStage.QUALIFIED.value: random.randint(8, 17),
        LeadStage.DEMO.value: random.randint(22, 42),
        LeadStage.ENROLLED.value: random.randint(35, 63),
    }
    updated = created + timedelta(days=stage_delay[stage])
    return LeadORM(
        name=_name(),
        phone=_phone(),
        source=random.choice(SOURCES),
        stage=stage,
        notes=random.choice(NOTES),
        created_at=created,
        updated_at=updated,
    )


def seed() -> None:
    create_tables()
    db = get_session_factory()()
    try:
        deleted = db.query(LeadORM).delete()
        db.commit()
        print(f"Cleared {deleted} existing leads.")

        total = 0
        for stage, count in STAGE_DISTRIBUTION.items():
            for _ in range(count):
                db.add(_lead(stage))
            total += count
            print(f"  {stage:<12} → {count} leads")

        db.commit()
        print(f"\n✅  Seeded {total} leads.")
    finally:
        db.close()


if __name__ == "__main__":
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)
    seed()
