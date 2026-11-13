# Working on PressLens

Use a feature branch and keep changes focused on one business question or operational concern. Follow the setup in README.md; generated data, dependencies and credentials are ignored.

## Change boundaries

- Pipeline code owns generation, validation, exclusion rules and snapshot publication.
- Analytics code owns SQL and metric definitions. Every dashboard section and CSV uses the same filter population.
- API code owns HTTP validation, response schemas and delivery. Keep SQL out of route functions.
- React code owns presentation and user selections. It must not invent business metrics or reinterpret denominators.

For a data contract change, update the SQL schema, `PRAGMA user_version`, pipeline metadata, API schemas, frontend types, tests and data-model documentation together. Rebuild the immutable demonstration snapshot; do not modify a running release in place. A new schema version needs an explicit compatibility decision in the repository reader.

## Before a pull request

Run Python tests, frontend tests and the production build using the README commands. Run the container smoke check when Docker is available. Explain the user-visible change, data/metric impact and validation performed. Record browser checks accurately; an HTTP 200 does not verify browser interaction.

Update requirements locks and package-lock.json deliberately when changing dependencies. Commit the app source and lockfiles, not `.venv`, `node_modules`, generated data, private datasets or `.env` files. Never label synthetic results as real publisher evidence. Do not introduce personal data into the public demo.
