# src/database/schemas.py

import os
from pathlib import Path
from alembic.config import Config
from alembic import command

from src.database.connections import get_session_factory


def create_tables() -> None:
    """Issue Alembic upgrade to generate and keep DB tables up to date."""
    project_root = Path(__file__).resolve().parent.parent.parent
    ini_path = project_root / "alembic.ini"
    
    # Setup configuration matching local path structures
    alembic_cfg = Config(str(ini_path))
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
    
    # Programmatically run migrations
    print("-> Running database migrations via Alembic...")
    command.upgrade(alembic_cfg, "head")
    
    # Auto-seed a default admin user if none exist in the DB
    from src.models.user import UserORM
    from src.utils.auth import hash_password
    
    Session = get_session_factory()
    db = Session()
    try:
        admin_user = db.query(UserORM).filter(UserORM.username == "admin").first()
        if not admin_user:
            default_admin = UserORM(
                username="admin",
                email="admin@easyskill.com",
                hashed_password=hash_password("admin123"),
                role="Admin"
            )
            db.add(default_admin)
            db.commit()
            print("Auto-seeded default admin user (username: admin, password: admin123)")
        elif admin_user.role != "Admin":
            admin_user.role = "Admin"
            db.commit()
            print("Updated existing admin user role to Admin")
    except Exception as e:
        print(f"Warning: Failed to auto-seed default admin user: {e}")
        db.rollback()
    finally:
        db.close()
