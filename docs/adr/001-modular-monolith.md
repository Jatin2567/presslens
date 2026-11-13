# ADR 001: Deploy a modular monolith

- Status: Accepted
- Date: 2026-11-13

## Context

PressLens needs to make a small analytics workflow easy to inspect, run, and deploy. The portfolio should show a coherent path from source records to SQL metrics and browser-visible results. Independent services would introduce network contracts, authentication between services, deployment coordination, and operational cost without a demonstrated need.

## Decision

Keep data preparation, analytical calculations, and the HTTP interface in one Python package with separate responsibilities. Build the React application independently and serve its static output from the same FastAPI container as the API.

Data preparation remains an explicit command. The serving process reads the prepared dataset and does not run ingestion in response to user traffic.

## Consequences

- A single container and health contract simplify local setup, CI, deployment, and rollback.
- Python and SQL code can be tested without the frontend; frontend behavior can be tested against a stable API contract.
- Same-origin delivery avoids an unnecessary cross-origin configuration for the normal deployment.
- The API and frontend are released together. Their independent build steps are not independent production services.
- A slow query competes with other work inside the same service. Dataset size and query latency must be measured before introducing scale mechanisms.

## Revisit when

Separate components only when measured needs justify them: independently scheduled ingestion, different access controls, sustained resource contention, or teams that need independent release cycles. A more complex architecture is not itself evidence of project maturity.
