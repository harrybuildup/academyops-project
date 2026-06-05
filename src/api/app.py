# src/api/app.py
#
# FastAPI application factory.
# Usage:  uvicorn src.api.app:app --reload --port 8000

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.models.errors import DuplicatePhoneError, LeadNotFoundError
from src.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AcademyOps API",
        description="Lead-to-Enrollment management REST API for EasySkill Career Academy.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.exception_handler(LeadNotFoundError)
    async def handle_not_found(request: Request, exc: LeadNotFoundError):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": str(exc)})

    @app.exception_handler(DuplicatePhoneError)
    async def handle_duplicate(request: Request, exc: DuplicatePhoneError):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(exc)})

    @app.exception_handler(Exception)
    async def handle_generic(request: Request, exc: Exception):
        from src.utils.logger import logger
        logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "An internal server error occurred."})

    app.include_router(router)
    return app


app = create_app()
