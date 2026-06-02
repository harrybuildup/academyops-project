# AcademyOps — Lead-to-Enrollment Management System

## 1. Program Overview & Context
**Client:** EasySkill Career Academy (ECA)  
**Product Context:** AcademyOps is an internal sales pipeline and lead-to-enrollment management tool built to capture prospects, monitor sales funnel efficiency, and optimize counselor follow-ups.

This iteration represents the completion of **WP-01: Lead Data Model & Persistence Layer**. It establishes the core "system of record" database schema, typed domain rules, a decoupled repository tracking layer, centralized logging observability, and an operations terminal interface that downstream application modules will depend on.

---

## 2. Shared Domain: Sales Pipeline Definition
Leads progress sequentially through a strictly validated sales funnel. The state transitions are globally enforced across the source code and database constraints via explicit enumerations:
* `New` (Default status for all freshly registered prospects)
* `Contacted`
* `Qualified`
* `Demo`
* `Enrolled` (Terminal success state)
* `Lost` (Terminal fallback state accessible from any active step)

---

## 3. Architecture & Project Directory Tree
This repository enforces strict Separation of Concerns (SoC). Application execution routines, data access interfaces, data definition patterns, and background automations are decoupled into independent layers:

```text
academyops-project/
│
├── data/                           # Local database storage directory (Git ignored)
│   └── academyops.db               # Live SQLite system of record file
│
├── src/                            # Central core application package
│   ├── __init__.py                 # Package initialization mapping
│   ├── cli.py                      # User-facing command line interface console
│   │
│   ├── database/                   # Data Definition Layer (DDL)
│   │   ├── __init__.py
│   │   ├── connections.py          # SQLite engine connection lifecycle managers
│   │   ├── schema.sql              # Clean DDL structures and optimization indexes
│   │   └── schemas.py              # Schema loader executing external SQL templates
│   │
│   ├── models/                     # Enterprise Core Domain Models
│   │   ├── __init__.py
│   │   ├── errors.py               # Explicit domain exception entities
│   │   └── lead.py                 # Core Lead structural class and Stage enum
│   │
│   ├── repository/                 # Data Access Layer (DAL)
│   │   ├── __init__.py
│   │   └── lead_repository.py      # Encapsulated Repository pattern engine
│   │
│   └── utils/                      # Core System Utilities & Observability
│       ├── __init__.py
│       └── logger.py               # Unified streaming file & console logger
│
├── init_db.py                  # Absolute-path table orchestration script
├── .gitignore                      # Excludes local caches, logs, and databases
├── academyops.log                  # Centralized file-based application logs
├── README.md                       # Comprehensive onboarding & operations guide
└── requirements.txt                # Pinned dependencies manifest