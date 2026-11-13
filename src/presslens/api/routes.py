"""Versioned, read-only analytics and export endpoints."""

import csv
import io
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from presslens.analytics import AnalyticsRepository
from presslens.api.dependencies import filters, repository
from presslens.api.schemas import Dashboard, FilterOptions
from presslens.analytics.repository import SnapshotSchemaError

router = APIRouter(prefix="/api/v1", tags=["analytics"])
health = APIRouter(tags=["health"])
Repo = Annotated[AnalyticsRepository, Depends(repository)]
FilterParams = Annotated[dict, Depends(filters)]


@health.get("/health/live")
def live() -> dict:
    return {"status": "ok", "service": "presslens"}


@health.get("/health/ready")
def ready(request: Request, repo: Repo) -> dict:
    try:
        repo.filters()
    except (sqlite3.Error, OSError, SnapshotSchemaError):
        raise HTTPException(503, "Analytics snapshot is not ready") from None
    if not (request.app.state.settings.web_dist / "index.html").is_file():
        raise HTTPException(503, "Dashboard build is unavailable")
    return {"status": "ready", "data": "simulated"}


@router.get("/filters", response_model=FilterOptions)
def available_filters(repo: Repo) -> dict:
    return repo.filters()


@router.get("/dashboard", response_model=Dashboard)
def dashboard(repo: Repo, selection: FilterParams) -> dict:
    return repo.dashboard(**selection)


def safe_cell(value):
    """Prevent formula execution when text columns are opened in spreadsheets."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


@router.get("/export.csv")
def export_csv(repo: Repo, selection: FilterParams):
    # Materialize before streaming so database failures have a proper HTTP status.
    rows = list(repo.export_sessions(**selection))
    fields = ["session_id", "date", "article_id", "channel", "device", "engaged_seconds",
              "scroll_depth", "engaged", "newsletter_signup", "subscribed", "title", "category"]

    def generate():
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        yield output.getvalue()
        for row in rows:
            output.seek(0)
            output.truncate(0)
            writer.writerow({key: safe_cell(value) for key, value in row.items()})
            yield output.getvalue()

    return StreamingResponse(
        generate(), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="presslens-simulated-sessions.csv"'},
    )
