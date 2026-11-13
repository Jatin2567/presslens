import sqlite3

import pytest

from presslens.analytics import AnalyticsRepository
from presslens.pipeline import build_demo


@pytest.fixture
def repository(tmp_path):
    build_demo(tmp_path)
    return AnalyticsRepository(tmp_path / "presslens.sqlite")


def test_dashboard_reconciles_and_rates_use_sessions(repository):
    data = repository.dashboard()
    summary = data["summary"]
    assert summary["sessions"] == 6000
    assert sum(row["sessions"] for row in data["daily"]) == summary["sessions"]
    assert sum(row["sessions"] for row in data["channels"]) == summary["sessions"]
    assert sum(row["subscriptions"] for row in data["articles"]) == summary["subscriptions"]
    assert summary["engagement_rate"] == summary["engaged_sessions"] / summary["sessions"]
    assert summary["conversion_rate"] == summary["subscriptions"] / summary["sessions"]
    exported = list(repository.export_sessions())
    assert summary["avg_engaged_seconds"] == pytest.approx(sum(row["engaged_seconds"] for row in exported) / 6000)


def test_combined_filters_and_export_match(repository):
    filters = dict(start_date="2026-09-01", end_date="2026-09-30", category="Markets", channel="Search", device="Mobile")
    data = repository.dashboard(**filters)
    rows = list(repository.export_sessions(**filters))
    assert data["summary"]["sessions"] == len(rows) > 0
    assert all("2026-09-01" <= row["date"] <= "2026-09-30" and row["category"] == "Markets" and row["channel"] == "Search" and row["device"] == "Mobile" for row in rows)
    assert data["summary"]["subscriptions"] == sum(row["subscribed"] for row in rows)
    assert repository.filters()["date_min"] == "2026-08-01"


def test_empty_result_and_sql_injection_are_safe(repository):
    data = repository.dashboard(channel="Search' OR 1=1 --")
    assert data["summary"]["sessions"] == 0
    assert data["summary"]["conversion_rate"] == 0
    assert data["daily"] == data["channels"] == data["articles"] == []
    assert list(repository.export_sessions(start_date="2030-01-01")) == []
    assert repository.dashboard()["summary"]["sessions"] == 6000


@pytest.mark.parametrize("filters", [{"start_date": "2026-02-30"}, {"start_date": "2026-10-01", "end_date": "2026-09-01"}, {"channel": "x" * 101}])
def test_invalid_filters_fail_early(repository, filters):
    with pytest.raises(ValueError):
        repository.dashboard(**filters)


def test_connection_cannot_write(repository):
    with repository._connect() as db:
        with pytest.raises(sqlite3.OperationalError):
            db.execute("DELETE FROM fact_session")
