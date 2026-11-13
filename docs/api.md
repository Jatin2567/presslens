# HTTP API contract

The public API is read-only and versioned under `/api/v1`. Machine-readable OpenAPI schemas are served at `/openapi.json`. Interactive third-party documentation assets are disabled so the app works with a self-only content security policy.

| Route | Purpose |
| --- | --- |
| `GET /health/live` | Process responds. No database access. |
| `GET /health/ready` | Supported database schema can be queried and compiled frontend exists. |
| `GET /api/v1/filters` | Dataset bounds and available category, channel and device values. |
| `GET /api/v1/dashboard` | Summary, daily series, channel comparisons, article performance and dataset provenance. |
| `GET /api/v1/export.csv` | Session rows for the same selected population. |

Dashboard and export support optional `start_date`, `end_date`, `category`, `channel`, and `device`. Dates use `YYYY-MM-DD`, with inclusive bounds. Omit a dimension to include all values. Unknown values produce an empty result, not a fallback to all data. Missing dates are unbounded. Invalid dates or reversed bounds return HTTP 422. Unavailable or incompatible snapshots return HTTP 503. Unknown routes return 404.

```text
/api/v1/dashboard?start_date=2026-08-01&end_date=2026-08-31&channel=Search
```

Counts are integers. Rates are fractions in `[0,1]`, calculated from matching counts, never means of segment percentages. Empty populations return zero summary values and empty series. `quality` and `meta` describe the entire snapshot, even when a filter narrows the visible population. CSV has a stable header even with no matches; text that could execute as spreadsheet formulas is escaped.

The API opens SQLite read-only and uses bound query parameters. No request creates a snapshot or accepts uploads. Application request logs contain a generated request ID, method, route, response status and duration; filter query strings and CSV contents are excluded. The documented start command and container disable Uvicorn's additional access log with `--no-access-log`, since its default format includes query strings. Read-only public access is appropriate only for the included fictional data. Real reader data requires a separate access and retention design before ingestion.
