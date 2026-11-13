import csv
import sqlite3

import pytest

from presslens.pipeline.build import build_demo, build_snapshot
from presslens.pipeline.clean import clean_sessions
from presslens.pipeline.generate import articles, generate_sessions


def test_deterministic_build_and_reconciliation(tmp_path):
    result = build_demo(tmp_path)
    quality = result["quality"]
    assert quality["raw_rows"] == 6035
    assert quality["accepted_rows"] == 6000
    assert quality["rejected_rows"] == 35
    assert quality["reconciled"] is True
    assert quality["rejection_reasons"]["duplicate_session_id"] == 30
    assert result["meta"]["date_min"] == "2026-08-01"
    assert result["meta"]["date_max"] == "2026-10-29"
    assert result["meta"]["simulated"] is True
    with (tmp_path / "sessions.csv").open(encoding="utf-8") as handle:
        exported = list(csv.DictReader(handle))
    assert len(exported) == 6000
    first_bytes = (tmp_path / "sessions.csv").read_bytes()
    repeated = build_demo(tmp_path)
    assert repeated["meta"]["source_sha256"] == result["meta"]["source_sha256"]
    assert (tmp_path / "sessions.csv").read_bytes() == first_bytes
    with sqlite3.connect(tmp_path / "presslens.sqlite") as db:
        assert db.execute("SELECT COUNT(*) FROM fact_session").fetchone()[0] == 6000
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_invalid_rows_are_quarantined_and_normalization_is_tracked():
    row = generate_sessions(1, include_defects=False)[0]
    raw = [dict(row, channel="  search "), dict(row), dict(row, session_id="bad-date", date="2026-02-30"),
           dict(row, session_id="bad-number", scroll_depth="nan"),
           dict(row, session_id="bad-funnel", engaged=0, subscribed=1)]
    accepted, rejected, quality = clean_sessions(raw, {a["article_id"] for a in articles()})
    assert len(accepted) == 1
    assert accepted[0]["channel"] == "Search"
    assert quality["normalized_rows"] == 1
    assert len(rejected) == 4
    assert quality["rejection_reasons"] == {"duplicate_session_id": 1, "invalid_date": 1, "invalid_funnel": 1, "invalid_numeric_value": 1}


def test_invalid_first_duplicate_does_not_discard_later_valid_row():
    row = generate_sessions(1, include_defects=False)[0]
    accepted, rejected, _ = clean_sessions([dict(row, date="bad"), row], {a["article_id"] for a in articles()})
    assert len(accepted) == len(rejected) == 1


def test_failure_preserves_previous_database(tmp_path):
    build_demo(tmp_path, count=50)
    before = (tmp_path / "presslens.sqlite").read_bytes()
    bad_catalog = [articles()[0], articles()[0]]
    with pytest.raises(ValueError, match="unique"):
        build_snapshot([], bad_catalog, tmp_path)
    assert (tmp_path / "presslens.sqlite").read_bytes() == before
