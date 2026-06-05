# src/database/schemas.py

from src.database.connections import Base, get_engine


def create_tables() -> None:
    """Issue CREATE TABLE IF NOT EXISTS for every SQLAlchemy-mapped model."""
    import src.models.lead  # noqa: F401 — registers LeadORM on Base.metadata
    Base.metadata.create_all(bind=get_engine())
