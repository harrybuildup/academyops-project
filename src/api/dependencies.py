# src/api/dependencies.py

from src.database.connections import get_db  # re-export for FastAPI Depends()

__all__ = ["get_db"]
