# src/database/connections.py
#
# SQLAlchemy engine, session factory, and declarative Base.
# Configuration is read from the environment — no hard-coded values.
#
# The engine is created lazily on first access so that importing this module
# (e.g. during testing) does not immediately attempt a DB connection.

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

Base = declarative_base()

_engine: Engine | None = None
_SessionLocal = None


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and fill in the value."
        )
    return url


def get_engine() -> Engine:
    """Return the SQLAlchemy engine, creating it on first call."""
    global _engine
    if _engine is None:
        url = _get_database_url()
        _engine = create_engine(
            url,
            echo=os.getenv("DEBUG", "False").lower() in ("true", "1", "yes"),
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> sessionmaker:
    """Return the session factory, creating it on first call."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session and always closes it."""
    factory = get_session_factory()
    db: Session = factory()
    try:
        yield db
    finally:
        db.close()
