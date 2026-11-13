# ADR 002: Serve an immutable SQLite snapshot

- Status: Accepted
- Date: 2026-11-13

## Context

The initial release serves a small demonstration dataset. There are no accounts, operational writes, live ingestion jobs, or multi-tenant records. We need reproducible metrics, portable setup, inspectable SQL, and a deployment that works without database credentials.

## Decision

Generate a SQLite analytical snapshot with the Python pipeline, package it with the release, and read it through parameterized queries. The serving application opens the snapshot read-only. The database path is configured with `PRESSLENS_DATABASE_PATH`.

CSV files provide a portable inspection and spreadsheet workflow. SQLite remains the application's query engine; CSV downloads are not a second live datastore.

## Versioning and rollback

The application commit, pinned dependencies, deterministic generation configuration, and built container together identify a release. Pipeline outputs should include the dataset version and quality evidence so reviewers can identify the data behind a metric. Store a release's image digest or deployment identifier alongside the commit when publishing it.

Regenerate data during a new build and replace the whole deployment. Do not modify a running snapshot in place. Roll back to a previously verified image or commit if the new data or query logic fails checks.

## Consequences

- Local development and deployment need no hosted database or database secrets.
- SQL queries and downloadable data can be checked against the same source records.
- Read-only serving avoids write locks and partial pipeline updates during requests.
- Every replica carries its own snapshot; this is appropriate only while the snapshot remains small and immutable.
- The release does not have PostgreSQL, a warehouse, replication, or an incremental ingestion system. Documentation and diagrams must not imply otherwise.

## Revisit when

Use a managed operational database or warehouse only after requirements call for concurrent ingestion, substantial data volume, fine-grained access controls, retention policies, or joins with additional governed sources. Define those requirements and migration tests before selecting a replacement.
