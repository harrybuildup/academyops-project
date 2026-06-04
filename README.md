# WP-04 — Automated Test Suite & Quality Gates

## Overview

This module establishes automated testing for the **Lead Management REST API** and underlying **repository layer**. All tests run in isolation against fresh, temporary databases. A GitHub Actions CI workflow runs the full suite automatically on every push and pull request to `main`.

## Running Tests Locally

```bash
# Install test dependencies (if not already done)
pip install pytest

# Run all tests with verbose output
pytest -v

# Run a specific test file
pytest tests/test_api.py -v

# Run with coverage (optional)
pip install pytest-cov
pytest --cov=src tests/
```

## Test Coverage

- **Repository layer**: CRUD operations, constraint enforcement, error handling
- **API endpoints**: Status codes, validation, pagination, filtering, error responses
- **Isolation**: Each test gets a fresh, temporary SQLite database

## CI/CD Workflow

Every push to `main` and every pull request triggers `.github/workflows/ci.yml`:

1. Checks out the code
2. Sets up Python 3.14
3. Installs dependencies
4. Runs `pytest -v`

Tests must pass before merging to `main`.

## Test Structure
tests/
├── conftest.py              # Fixtures (isolated_db, repo, client)
├── test_repository.py       # Unit tests for LeadRepository
└── test_api.py              # API endpoint tests


## Key Test Characteristics

- ✅ **Isolated**: Each test uses a temporary database; no shared state
- ✅ **Independent**: Tests can run in any order
- ✅ **Fast**: In-memory databases where practical
- ✅ **Repeatable**: Same code, same result every time

