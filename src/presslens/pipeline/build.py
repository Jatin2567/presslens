"""Build an atomic SQLite snapshot with downloadable, reconciled source artifacts."""

import csv
from contextlib import closing
import hashlib
from importlib.resources import files
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

from .clean import clean_sessions
from .generate import ARTICLE_FIELDS, SESSION_FIELDS, articles, generate_sessions


def write_csv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_snapshot(rows: list[dict], catalog: list[dict], output_dir: Path | str, *, seed: int | None = None) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if len({a["article_id"] for a in catalog}) != len(catalog):
        raise ValueError("Article IDs must be unique.")
    cleaned, rejected, quality = clean_sessions(rows, {a["article_id"] for a in catalog})
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    meta = {
        "dataset_name": "PressLens simulated publisher sessions", "simulated": True,
        "schema_version": 1, "generator_seed": seed, "source_sha256": hashlib.sha256(canonical).hexdigest(),
        "date_min": min((r["date"] for r in cleaned), default=None),
        "date_max": max((r["date"] for r in cleaned), default=None),
        "metric_definitions": {
            "engagement_rate": "Sessions with at least 30 engaged seconds and 50% scroll depth / sessions.",
            "conversion_rate": "Sessions with a subscription conversion / sessions. Not unique-reader conversion.",
            "avg_engaged_seconds": "Sum of engaged seconds / all accepted sessions, including zeros.",
        },
        "limitations": ["Fictional session-level observations; no real publisher or reader data.",
                        "Channel and topic differences are encoded in the generator, not causal findings.",
                        "Sessions are not unique readers; retention and lifetime value cannot be inferred."],
    }
    with TemporaryDirectory(prefix=".presslens-build-", dir=output) as temporary:
        staging = Path(temporary)
        write_csv(staging / "raw_sessions.csv", rows, SESSION_FIELDS)
        write_csv(staging / "sessions.csv", cleaned, SESSION_FIELDS)
        write_csv(staging / "articles.csv", catalog, ARTICLE_FIELDS)
        write_csv(staging / "rejected_sessions.csv", rejected, (*SESSION_FIELDS, "source_line", "rejection_reason"))
        (staging / "quality.json").write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")
        db = staging / "presslens.sqlite"
        with closing(sqlite3.connect(db)) as connection:
            connection.executescript(files("presslens.analytics").joinpath("sql/schema.sql").read_text(encoding="utf-8"))
            with connection:
                connection.executemany("INSERT INTO dim_article VALUES (:article_id, :title, :category)", catalog)
                connection.executemany(
                    "INSERT INTO fact_session VALUES (:session_id,:date,:article_id,:channel,:device,:engaged_seconds,:scroll_depth,:engaged,:newsletter_signup,:subscribed)", cleaned
                )
                connection.executemany("INSERT INTO snapshot_metadata VALUES (?,?)", [("meta", json.dumps(meta)), ("quality", json.dumps(quality))])
                if connection.execute("PRAGMA foreign_key_check").fetchall():
                    raise ValueError("Snapshot failed foreign-key validation.")
                if connection.execute("SELECT COUNT(*) FROM fact_session").fetchone()[0] != len(cleaned):
                    raise ValueError("Snapshot row count did not reconcile.")
            connection.execute("ANALYZE")
        # The API reads the database only. Replacing this last makes publication atomic.
        for name in ("raw_sessions.csv", "sessions.csv", "articles.csv", "rejected_sessions.csv", "quality.json", "presslens.sqlite"):
            (staging / name).replace(output / name)
    return {"database": str(output / "presslens.sqlite"), "quality": quality, "meta": meta}


def build_demo(output_dir: Path | str, count: int = 6000, seed: int = 42) -> dict:
    return build_snapshot(generate_sessions(count=count, seed=seed), articles(), output_dir, seed=seed)
