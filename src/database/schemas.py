# src/database/schemas.py

from src.database.connections import Base, get_engine, get_session_factory


def create_tables() -> None:
    """Issue CREATE TABLE IF NOT EXISTS for every SQLAlchemy-mapped model."""
    import src.models.lead  # noqa: F401
    import src.models.user  # noqa: F401
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed a default admin user if none exist in the DB
    from src.models.user import UserORM
    from src.utils.auth import hash_password
    
    Session = get_session_factory()
    db = Session()
    try:
        if db.query(UserORM).count() == 0:
            default_admin = UserORM(
                username="admin",
                email="admin@easyskill.com",
                hashed_password=hash_password("admin123")
            )
            db.add(default_admin)
            db.commit()
            print("Auto-seeded default admin user (username: admin, password: admin123)")
    except Exception as e:
        print(f"Warning: Failed to auto-seed default admin user: {e}")
        db.rollback()
    finally:
        db.close()
