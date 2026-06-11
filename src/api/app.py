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

    # Enable CORS for external frontend clients
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # No-cache middleware: strips ETag/Last-Modified from requests and adds
    # Cache-Control: no-store to all responses so browsers never serve stale JS/CSS.
    from starlette.types import ASGIApp, Receive, Send, Scope
    from starlette.datastructures import MutableHeaders

    class NoCacheMiddleware:
        def __init__(self, app: ASGIApp) -> None:
            self.app = app

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            if scope["type"] == "http":
                # Strip conditional request headers so server never returns 304
                headers = dict(scope.get("headers", []))
                headers.pop(b"if-none-match", None)
                headers.pop(b"if-modified-since", None)
                scope["headers"] = list(headers.items())

                async def send_with_no_cache(message):
                    if message["type"] == "http.response.start":
                        headers = MutableHeaders(scope=message)
                        headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                        headers["Pragma"] = "no-cache"
                        headers["Expires"] = "0"
                    await send(message)

                await self.app(scope, receive, send_with_no_cache)
            else:
                await self.app(scope, receive, send)

    app.add_middleware(NoCacheMiddleware)

    # Serve static frontend files
    from fastapi.staticfiles import StaticFiles
    from pathlib import Path
    import os

    frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
    os.makedirs(frontend_path, exist_ok=True)
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")

    return app


app = create_app()
