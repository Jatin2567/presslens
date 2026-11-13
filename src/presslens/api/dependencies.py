"""Request validation and repository construction."""

from datetime import date
from typing import Annotated

from fastapi import HTTPException, Query, Request
from presslens.analytics import AnalyticsRepository


def repository(request: Request) -> AnalyticsRepository:
    path = request.app.state.settings.database_path
    if not path.is_file():
        raise HTTPException(503, "Analytics snapshot unavailable. Run the data pipeline.")
    return AnalyticsRepository(path)


def filters(
    start_date: date | None = None,
    end_date: date | None = None,
    category: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
    channel: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
    device: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
) -> dict:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, "start_date must be on or before end_date")
    return {
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "category": category,
        "channel": channel,
        "device": device,
    }
