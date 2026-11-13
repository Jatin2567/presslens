# Verification record

Verified locally on 2026-11-13 with Python 3.12 and Node.js 22.17.0.

| Check | Result |
| --- | --- |
| Python pipeline, SQL and API tests | 22 passed |
| Frontend logic tests | 5 passed |
| TypeScript type checking and Vite production build | Passed |
| Installed Python dependency consistency (`pip check`) | Passed |
| Docker Compose configuration | Valid |
| Running application health endpoint | HTTP 200, ready |
| HTTP smoke test (`scripts/smoke.py`) | Passed: 6,000 total sessions, 435 sessions in the tested combined channel/device selection, CSV row and conversion totals reconcile |
| Browser rendering and interactive controls | Unverified; no supported browser session was connected |
| Docker image build and container runtime | Unverified; Docker Engine was stopped |
| GitHub Actions | Configured, not run remotely |
| Render deployment and public access | Not performed; repository/account destination remains pending |
| DuckDNS custom domain | Not configured; exact hostname and supported DNS configuration remain pending |

The local network smoke check and in-process HTTP tests required execution outside the Windows sandbox, whose socket restrictions prevented them from running normally. The API suite emitted one upstream deprecation warning about Starlette's current `httpx` test transport. Tests passed with the pinned development dependencies; review that transport during the next dependency update.

This report describes code and runtime checks, not proof of production readiness or recruiter access. Data is simulated. The existing ChatGPT Site's sharing policy was not changed.
