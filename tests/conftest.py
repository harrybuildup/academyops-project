import sqlite3
import pytest
from src.repository.lead_repository import LeadRepository
from src.web.app import create_app
from src.database.schemas import create_table

@pytest.fixture()
def isolated_db(tmp_path):
    """Creates a temporary SQLite database for testing."""
    db_path = tmp_path / "test_academyops.db"
    conn = sqlite3.connect(db_path)
    create_table(conn)
    
    return str(db_path)

@pytest.fixture()
def repo(isolated_db):
    """Provides a LeadRepository instance connected to the isolated test database."""
    return LeadRepository(isolated_db)

@pytest.fixture()
def client(repo):
    """Provides a Flask test client with the app configured to use the isolated database."""
    app = create_app(repo.db_path)
    app.config['REPOSITORY'] = repo
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client
