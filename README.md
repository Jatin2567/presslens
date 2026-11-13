# PressLens

Newsroom and audience analytics for a data analyst portfolio. PressLens demonstrates how a simulated publisher can investigate readership, engagement and subscription conversion using reproducible Python, SQL and a filterable dashboard.

This is an independent portfolio project. All reader sessions and article records are simulated, not Economic Times data. No results represent measured business impact.

## Architecture

Python generates and validates source CSVs, publishes a versioned SQLite snapshot, and SQL calculates metrics. A modular FastAPI service exposes read-only endpoints and serves the React/TypeScript dashboard from the same origin. This keeps metric definitions in one place and makes the demonstration reproducible.

See [architecture](docs/architecture.md), [API contracts](docs/api.md), [deployment](docs/deployment.md), and the SQL in `src/presslens/analytics/sql`.

```text
presslens/
├── apps/web/                  React dashboard and frontend tests
├── src/presslens/
│   ├── pipeline/              Generate, validate and publish data
│   ├── analytics/             Parameterized SQL and snapshot reader
│   │   └── sql/               Versioned schema and analytical views
│   └── api/                   Routes, response contracts and settings
├── sql/analysis.sql           Analyst queries and window-function examples
├── tests/                     Pipeline, SQL and HTTP contract checks
├── scripts/smoke.py           Running-service acceptance check
├── docs/                      Architecture, ADRs, model and operations
├── .github/workflows/ci.yml   Automated checks and container smoke test
├── Dockerfile                Multi-stage, non-root release image
├── compose.yaml              Local container setup
└── render.yaml               Render deployment blueprint
```

## Local setup

Requires Python 3.12 and Node.js 22. Run from this directory. On Windows use `.venv\Scripts\python` in place of `.venv/bin/python`.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m presslens.pipeline --output-dir data/demo
npm --prefix apps/web ci
npm --prefix apps/web run build
.venv/bin/python -m uvicorn presslens.api.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Open http://127.0.0.1:8000. For frontend development, run `npm --prefix apps/web run dev` in another terminal; Vite forwards API requests to port 8000.

## Verify

```sh
.venv/bin/python -m pytest
npm --prefix apps/web run typecheck
npm --prefix apps/web test
npm --prefix apps/web run build
```

Against a running service, use `.venv/bin/python scripts/smoke.py --base-url http://127.0.0.1:8000`. Current results and verification limits are recorded in [verification.md](docs/verification.md).

The data pipeline is an explicit offline operation. HTTP startup never creates, downloads or mutates data. The public API has no upload or write endpoint. Set `PRESSLENS_DATABASE_PATH` and `WEB_DIST` explicitly when using other locations; see `.env.example`.

## Scope

This setup includes the cleaning pipeline, SQL analytics, a working dashboard, CSV export, tests, Docker and Render configuration. Native Excel reports, a trained ML experiment, real event ingestion and managed PostgreSQL are subsequent work, not features claimed by this foundation.

Deployment requires a GitHub repository and Render account. The existing ChatGPT Site stays private. A DuckDNS hostname is pending and must be checked against Render's custom-domain requirements before configuring DNS.
