# Verification record

Verified locally on 2026-11-13 with Python 3.12 and Node.js 22.17.0.

The public [GitHub repository](https://github.com/Jatin2567/presslens) and `main` commit [`633d9122d36d5edc84af81e6f6e6059bc1155487`](https://github.com/Jatin2567/presslens/commit/633d9122d36d5edc84af81e6f6e6059bc1155487) were independently verified on 2026-11-14. [CI run 43485320975](https://github.com/Jatin2567/presslens/actions/runs/43485320975) completed successfully: **Python and SQL**, **Web application**, and **Container smoke test** all passed.

| Check | Result |
| --- | --- |
| Python pipeline, SQL and API tests | 22 passed |
| Frontend logic tests | 5 passed |
| TypeScript type checking and Vite production build | Passed |
| Installed Python dependency consistency (`pip check`) | Passed |
| Docker Compose configuration | Valid |
| Running application health endpoint | HTTP 200, ready |
| HTTP smoke test (`scripts/smoke.py`) | Passed: 6,000 total sessions, 435 sessions in the tested combined channel/device selection, CSV row and conversion totals reconcile |
| Browser rendering and interactive controls | Unverified |
| Docker image build and container runtime | Passed in GitHub CI: image build, read-only container, readiness/liveness, frontend response, and unprivileged user checks. Local Docker Engine remained stopped. |
| GitHub Actions | All three jobs passed for commit `633d912`; see the linked run above |
| Render deployment and public HTTP access | Live at [presslens-y426.onrender.com](https://presslens-y426.onrender.com); unauthenticated health, HTML, JavaScript and CSS requests returned HTTP 200 |
| Public HTTP acceptance check | `scripts/smoke.py` passed against the Render URL: 6,000 sessions; 435 filtered CSV rows; subscription totals reconcile; empty results and invalid date ranges behave as expected |
| Deployment settings | Free plan, Singapore, Docker, `/health/ready`, `autoDeployTrigger: checksPass`; confirmed through Render's API |
| DuckDNS custom domain | Not configured; exact hostname and supported DNS configuration remain pending |

The local network smoke check and in-process HTTP tests required execution outside the Windows sandbox, whose socket restrictions prevented them from running normally. The API suite emitted one upstream deprecation warning about Starlette's current `httpx` test transport. Tests passed with the pinned development dependencies; review that transport during the next dependency update.

Render deployment `dep-dbrm1rrl550s73cs5ucg` reached `live` at 2026-11-13 19:12:47 UTC (2026-11-14 in India), running commit `633d9122d36d5edc84af81e6f6e6059bc1155487`. Service: [`srv-dbrm1rjl550s73cs5t2g`](https://dashboard.render.com/web/srv-dbrm1rjl550s73cs5t2g), free plan, Singapore. Verification used public requests without Render authentication.

This report describes code and runtime checks, not proof of production readiness. Browser rendering and interactive controls remain unverified. Data is simulated. The existing ChatGPT Site's sharing policy was not changed.
