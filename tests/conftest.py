"""tests/conftest.py — shared pytest fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database.connections import Base, get_db
from src.api.app import create_app

import src.models.lead  # noqa: F401 — registers LeadORM on Base.metadata


@pytest.fixture()
def db_engine(tmp_path):
    """Per-test isolated SQLite engine with the full schema."""
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(db_engine):
    """Raw SQLAlchemy session for CRUD unit tests."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def client(db_engine):
    """FastAPI TestClient with DB dependency overridden to the isolated engine."""
    TestingSession = sessionmaker(bind=db_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
