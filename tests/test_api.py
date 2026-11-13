import csv
import io
import sqlite3

import pytest
from fastapi.testclient import TestClient

from presslens.api.main import create_app
from presslens.api.settings import Settings
from presslens.pipeline.build import build_demo


@pytest.fixture
def environment(tmp_path):
    build_demo(tmp_path / "data", count=300)
    web = tmp_path / "web"
    web.mkdir()
    (web / "index.html").write_text("<html>PressLens</html>", encoding="utf-8")
    return Settings(database_path=tmp_path / "data" / "presslens.sqlite", web_dist=web)


@pytest.fixture
def client(environment):
    with TestClient(create_app(environment)) as instance:
        yield instance


def test_dashboard_contract_and_export_reconcile(client):
    options = client.get("/api/v1/filters").json()
    params = {"channel": options["channels"][0], "device": options["devices"][0]}
    response = client.get("/api/v1/dashboard", params=params)
    assert response.status_code == 200
    data = response.json()
    exported = client.get("/api/v1/export.csv", params=params)
    assert exported.headers["content-type"].startswith("text/csv")
    rows = list(csv.DictReader(io.StringIO(exported.text)))
    assert 0 < data["summary"]["sessions"] == len(rows) < 300
    assert data["summary"]["subscriptions"] == sum(int(row["subscribed"]) for row in rows)
    assert data["summary"]["engaged_sessions"] == sum(int(row["engaged"]) for row in rows)
    assert sum(row["sessions"] for row in data["daily"]) == len(rows)
    assert all(row["channel"] == params["channel"] for row in rows)
    assert data["quality"]["accepted_rows"] == 300
    assert data["meta"]["simulated"] is True


@pytest.mark.parametrize("params", [
    {"start_date": "yesterday"},
    {"start_date": "2026-02-30"},
    {"start_date": "2026-10-01", "end_date": "2026-08-01"},
    {"channel": "x" * 81},
])
def test_bad_queries_fail_explicitly(client, params):
    for endpoint in ("dashboard", "export.csv"):
        assert client.get("/api/v1/" + endpoint, params=params).status_code == 422


def test_inclusive_single_day_and_empty_filter(client):
    first_day = client.get("/api/v1/filters").json()["date_min"]
    single = client.get("/api/v1/dashboard", params={"start_date": first_day, "end_date": first_day}).json()
    assert single["summary"]["sessions"] > 0
    assert [row["date"] for row in single["daily"]] == [first_day]
    empty = client.get("/api/v1/dashboard", params={"channel": "' OR 1=1 --"}).json()
    assert empty["summary"]["sessions"] == empty["summary"]["conversion_rate"] == 0
    assert empty["articles"] == empty["daily"] == empty["channels"] == []
    full_header = client.get("/api/v1/export.csv").text.splitlines()[0]
    empty_export = client.get("/api/v1/export.csv", params={"category": "unknown"}).text
    assert empty_export.splitlines() == [full_header]


def test_health_headers_and_unknown_routes(client):
    assert client.get("/health/ready").json()["status"] == "ready"
    response = client.get("/api/v1/dashboard")
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "no-store"
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert client.get("/api/v1/not-a-route").status_code == 404
    assert client.post("/api/v1/dashboard").status_code == 405
    schema = client.get("/openapi.json").json()
    assert "Dashboard" in schema["components"]["schemas"]


def test_missing_database_does_not_get_created(tmp_path):
    settings = Settings(database_path=tmp_path / "missing.sqlite", web_dist=tmp_path)
    with TestClient(create_app(settings)) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
        assert client.get("/api/v1/dashboard").status_code == 503
    assert not settings.database_path.exists()


def test_schema_mismatch_is_unavailable(environment):
    with sqlite3.connect(environment.database_path) as db:
        db.execute("PRAGMA user_version=999")
    with TestClient(create_app(environment)) as client:
        assert client.get("/health/ready").status_code == 503
        assert client.get("/api/v1/dashboard").status_code == 503


def test_missing_frontend_fails_readiness(environment):
    settings = Settings(database_path=environment.database_path, web_dist=environment.web_dist / "missing")
    with TestClient(create_app(settings)) as client:
        assert client.get("/health/ready").status_code == 503


def test_export_neutralizes_formula_text(environment):
    with sqlite3.connect(environment.database_path) as db:
        db.execute("UPDATE dim_article SET title = ?", ('=HYPERLINK("https://example.invalid")',))
    with TestClient(create_app(environment)) as client:
        rows = list(csv.DictReader(io.StringIO(client.get("/api/v1/export.csv").text)))
        assert rows
        assert all(row["title"].startswith("'=") for row in rows)
