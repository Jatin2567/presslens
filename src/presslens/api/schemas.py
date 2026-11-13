"""Public response contracts. Rates are fractions, timestamps are calendar dates."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class FilterOptions(BaseModel):
    date_min: date | None
    date_max: date | None
    categories: list[str]
    channels: list[str]
    devices: list[str]


class Summary(BaseModel):
    sessions: int = Field(ge=0)
    engaged_sessions: int = Field(ge=0)
    engagement_rate: float = Field(ge=0, le=1)
    subscriptions: int = Field(ge=0)
    conversion_rate: float = Field(ge=0, le=1)
    avg_engaged_seconds: float = Field(ge=0)


class Daily(BaseModel):
    date: date
    sessions: int = Field(ge=0)
    subscriptions: int = Field(ge=0)


class Channel(BaseModel):
    channel: str
    sessions: int = Field(ge=0)
    engagement_rate: float = Field(ge=0, le=1)
    subscriptions: int = Field(ge=0)
    conversion_rate: float = Field(ge=0, le=1)


class Article(BaseModel):
    article_id: str
    title: str
    category: str
    sessions: int = Field(ge=0)
    engagement_rate: float = Field(ge=0, le=1)
    subscriptions: int = Field(ge=0)


class Quality(BaseModel):
    raw_rows: int
    accepted_rows: int
    rejected_rows: int
    normalized_rows: int
    rejection_reasons: dict[str, int]
    reconciled: bool
    acceptance_rate: float
    policy: str


class Metadata(BaseModel):
    simulated: Literal[True]
    dataset_name: str
    schema_version: int
    generator_seed: int | None
    source_sha256: str
    date_min: date | None
    date_max: date | None
    metric_definitions: dict[str, str]
    limitations: list[str]


class Dashboard(BaseModel):
    summary: Summary
    daily: list[Daily]
    channels: list[Channel]
    articles: list[Article]
    quality: Quality
    meta: Metadata
