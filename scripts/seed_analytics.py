"""
Seed the AcademyOps database with realistic lead distribution across pipeline stages.

This script:
1. CLEARS all existing leads from the database
2. Inserts leads distributed across New → Contacted → Qualified → Demo → Enrolled stages
3. Uses REALISTIC timestamps (created_at varies, updated_at increases with stage progression)
4. Uses INDIAN phone numbers (91 format)
5. Distributes leads across actual sources from your CSV

Usage:
  python seed_wp05_analytics.py

The script assumes:
- Database location: data/academyops.db
- Leads table exists (from WP-01)
"""

import sqlite3
from datetime import datetime, timedelta
import random

# Configuration
DB_PATH = "data/academyops.db"

# Actual sources from your CSV
SOURCES = ["Google", "LinkedIn", "Facebook", "Website", "Referral"]

# Stage distribution: how many leads at each stage
STAGE_DISTRIBUTION = {
    "New": 60,           # Most leads are still new
    "Contacted": 28,     # ~47% converted from New
    "Qualified": 14,     # ~50% converted from Contacted
    "Demo": 8,           # ~57% converted from Qualified
    "Enrolled": 5,       # ~63% converted from Demo
}

# Sample names for lead generation
FIRST_NAMES = [
    "Rajesh", "Priya", "Arjun", "Neha", "Vikram", "Anjali", "Anil", "Deepika",
    "Sanjay", "Meera", "Rohan", "Zara", "Karan", "Isha", "Harsh", "Pooja",
    "Nikhil", "Diya", "Aditya", "Shreya", "Varun", "Ritika", "Pawan", "Nisha",
    "Gaurav", "Sneha", "Rohit", "Tanvi", "Akshay", "Swati", "Ashok", "Kavya",
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Reddy", "Verma", "Gupta", "Rao",
    "Nair", "Iyer", "Desai", "Chopra", "Bhat", "Bose", "Sengupta", "Sinha",
    "Menon", "Pillai", "Trivedi", "Joshi", "Bhatt", "Kulkarni", "Naik", "Shah",
]

SAMPLE_NOTES = [
    "Interested in full-stack development",
    "Looking for career transition support",
    "Wants to learn data science",
    "Flexible schedule needed",
    "Interested in placement assistance",
    "Already has some programming background",
    "Needs scholarship information",
    "Wants remote learning option",
    "Working professional",
    "Recent graduate looking to upskill",
    "Self-taught, wants formal certification",
    "Wants to specialize in cloud computing",
]


def generate_phone():
    """Generate an Indian phone number."""
    return f"+91{random.randint(6000000000, 9999999999)}"


def generate_lead_name():
    """Generate a realistic Indian name."""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def generate_lead(stage):
    """
    Generate a realistic lead record with timestamps.
    
    Key insight: 
    - created_at: varies across 60 days in the past
    - updated_at: increases based on stage (later stages took longer to reach)
    """
    # Lead was created sometime in the past 60 days
    days_ago = random.randint(1, 60)
    created_at = datetime.now() - timedelta(days=days_ago)
    
    # Stage progression takes time
    # New → Contacted: 1-3 days
    # Contacted → Qualified: 7-14 days
    # Qualified → Demo: 14-21 days
    # Demo → Enrolled: 7-14 days
    stage_delays = {
        "New": 0,                              # Just created
        "Contacted": random.randint(1, 3),
        "Qualified": random.randint(8, 17),
        "Demo": random.randint(22, 42),
        "Enrolled": random.randint(35, 63),
    }
    
    updated_at = created_at + timedelta(days=stage_delays[stage])
    
    name = generate_lead_name()
    phone = generate_phone()
    source = random.choice(SOURCES)
    notes = random.choice(SAMPLE_NOTES)
    
    return (
        name,
        phone,
        source,
        stage,
        notes,
        created_at.isoformat(),
        updated_at.isoformat(),
    )


def seed_database():
    """
    1. Clear all existing leads
    2. Insert new distribution across stages with realistic timestamps
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # CLEAR existing leads
        print("Clearing existing leads...")
        cursor.execute("DELETE FROM leads")
        conn.commit()
        
        # Generate and insert leads for each stage
        all_leads = []
        for stage, count in STAGE_DISTRIBUTION.items():
            print(f"Generating {count} leads in stage: {stage}")
            for _ in range(count):
                lead = generate_lead(stage)
                all_leads.append(lead)
        
        print(f"\nInserting {len(all_leads)} leads into database...")
        cursor.executemany(
            """
            INSERT INTO leads (name, phone, source, stage, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            all_leads,
        )
        conn.commit()
        conn.close()
        
        # Summary
        print(f"\nSUCCESS! Database seeded with {len(all_leads)} leads")
        print(f"\nStage distribution:")
        for stage, count in STAGE_DISTRIBUTION.items():
            print(f"   {stage:12} → {count:3} leads")
        
        total_enrolled = STAGE_DISTRIBUTION["Enrolled"]
        total_leads = sum(STAGE_DISTRIBUTION.values())
        print(f"\nOverall conversion rate: {total_enrolled}/{total_leads} = {(total_enrolled/total_leads)*100:.1f}%")
        
        print(f"\nDatabase: {DB_PATH}")
        print("✨ You can now run WP-05 analytics with meaningful results!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        print(f"Make sure the database exists at: {DB_PATH}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    seed_database()