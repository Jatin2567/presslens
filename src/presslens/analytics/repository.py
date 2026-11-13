"""A small read-only SQL boundary shared by the HTTP API and offline checks."""

from contextlib import contextmanager
from datetime import date
import json
from pathlib import Path
import sqlite3


class SnapshotSchemaError(ValueError):
    """The deployed data contract does not match this application version."""


class AnalyticsRepository:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path).resolve()

    @contextmanager
    def _connect(self):
        if not self.db_path.is_file():
            raise FileNotFoundError("Analytics snapshot is missing. Run python -m presslens.pipeline.")
        connection = sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA query_only = ON")
            if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
                raise SnapshotSchemaError("Unsupported analytics snapshot schema version.")
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _where(start_date=None, end_date=None, category=None, channel=None, device=None):
        for value in (start_date, end_date):
            if value is not None:
                if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                    raise ValueError("Dates must use YYYY-MM-DD.")
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError("Start date must be on or before end date.")
        clauses, parameters = [], []
        for expression, value in (("s.date >= ?", start_date), ("s.date <= ?", end_date),
                                  ("a.category = ?", category), ("s.channel = ?", channel), ("s.device = ?", device)):
            if value is not None:
                if not isinstance(value, str) or len(value) > 100:
                    raise ValueError("Filters must be strings of at most 100 characters.")
                clauses.append(expression)
                parameters.append(value)
        return (" WHERE " + " AND ".join(clauses) if clauses else ""), parameters

    def filters(self) -> dict:
        with self._connect() as db:
            bounds = dict(db.execute("SELECT MIN(date) date_min, MAX(date) date_max FROM fact_session").fetchone())
            return {
                **bounds,
                "categories": [r[0] for r in db.execute("SELECT DISTINCT category FROM dim_article ORDER BY category")],
                "channels": [r[0] for r in db.execute("SELECT DISTINCT channel FROM fact_session ORDER BY channel")],
                "devices": [r[0] for r in db.execute("SELECT DISTINCT device FROM fact_session ORDER BY device")],
            }

    def dashboard(self, start_date=None, end_date=None, category=None, channel=None, device=None) -> dict:
        where, parameters = self._where(start_date, end_date, category, channel, device)
        source = " FROM fact_session s JOIN dim_article a USING (article_id)" + where
        with self._connect() as db:
            # Keep all sections in one read transaction when a snapshot is replaced.
            db.execute("BEGIN")
            summary = dict(db.execute(
                "SELECT COUNT(*) sessions, COALESCE(SUM(s.engaged),0) engaged_sessions, "
                "COALESCE(1.0*SUM(s.engaged)/NULLIF(COUNT(*),0),0.0) engagement_rate, "
                "COALESCE(SUM(s.subscribed),0) subscriptions, "
                "COALESCE(1.0*SUM(s.subscribed)/NULLIF(COUNT(*),0),0.0) conversion_rate, "
                "COALESCE(AVG(s.engaged_seconds),0.0) avg_engaged_seconds" + source, parameters
            ).fetchone())
            daily = [dict(r) for r in db.execute(
                "SELECT s.date date, COUNT(*) sessions, SUM(s.subscribed) subscriptions" + source + " GROUP BY s.date ORDER BY s.date", parameters)]
            channels = [dict(r) for r in db.execute(
                "SELECT s.channel channel, COUNT(*) sessions, 1.0*SUM(s.engaged)/COUNT(*) engagement_rate, "
                "SUM(s.subscribed) subscriptions, 1.0*SUM(s.subscribed)/COUNT(*) conversion_rate" + source +
                " GROUP BY s.channel ORDER BY sessions DESC, s.channel", parameters)]
            article_rows = [dict(r) for r in db.execute(
                "SELECT a.article_id, a.title, a.category, COUNT(*) sessions, "
                "1.0*SUM(s.engaged)/COUNT(*) engagement_rate, SUM(s.subscribed) subscriptions" + source +
                " GROUP BY a.article_id, a.title, a.category ORDER BY sessions DESC, a.article_id", parameters)]
            metadata = {r[0]: json.loads(r[1]) for r in db.execute("SELECT key,value FROM snapshot_metadata")}
            return {"summary": summary, "daily": daily, "channels": channels, "articles": article_rows,
                    "quality": metadata["quality"], "meta": metadata["meta"]}

    def export_sessions(self, start_date=None, end_date=None, category=None, channel=None, device=None):
        where, parameters = self._where(start_date, end_date, category, channel, device)
        with self._connect() as db:
            for row in db.execute(
                "SELECT s.*, a.title, a.category FROM fact_session s JOIN dim_article a USING (article_id)" + where +
                " ORDER BY s.date, s.session_id", parameters
            ):
                yield dict(row)
