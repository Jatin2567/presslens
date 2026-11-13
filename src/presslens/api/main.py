"""Compose the application, middleware, versioned routes and static dashboard."""

import json
import logging
import sqlite3
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from presslens import __version__
from presslens.api.routes import health, router
from presslens.api.settings import Settings
from presslens.analytics.repository import SnapshotSchemaError

logger = logging.getLogger("uvicorn.error")


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(
        title="PressLens Analytics API", version=__version__, docs_url=None, redoc_url=None,
        description="Read-only analytics from a labelled, reproducible simulated news dataset.",
    )
    app.state.settings = settings or Settings.from_env()

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = str(uuid4())
        started = perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        logger.info(json.dumps({
            "event": "http_request", "request_id": request_id,
            "method": request.method, "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
        }))
        return response

    @app.exception_handler(sqlite3.Error)
    @app.exception_handler(SnapshotSchemaError)
    async def unavailable_database(request: Request, exc: sqlite3.Error):
        logger.error("Analytics snapshot query failed: %s", type(exc).__name__)
        return JSONResponse(status_code=503, content={"detail": "Analytics temporarily unavailable"})

    app.include_router(health)
    app.include_router(router)
    # The frontend is same-origin in production. Vite proxies /api during development.
    if app.state.settings.web_dist.is_dir():
        app.mount("/", StaticFiles(directory=app.state.settings.web_dist, html=True), name="dashboard")
    return app


app = create_app()
