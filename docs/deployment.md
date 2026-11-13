# Deployment runbook

The project is published at [Jatin2567/presslens](https://github.com/Jatin2567/presslens) and live at [presslens-y426.onrender.com](https://presslens-y426.onrender.com). [Commit `633d912`](https://github.com/Jatin2567/presslens/commit/633d9122d36d5edc84af81e6f6e6059bc1155487) passed [all three CI jobs](https://github.com/Jatin2567/presslens/actions/runs/43485320975), including the Docker build and container smoke test. Public HTTP acceptance checks passed after Render reported the deployment live. Browser interaction testing and a custom domain remain pending. The existing Readership Lab Site remains private.

## Local container

Run these commands from the repository root with Docker Engine available:

```sh
docker compose up --build --detach
docker compose ps
curl --fail http://127.0.0.1:8000/health/ready
```

Open `http://127.0.0.1:8000`. The Compose file binds only to the local machine. It uses a read-only container filesystem and a small writable temporary directory; the generated demonstration database is packaged in the image.

```sh
docker compose logs --tail=100 presslens
docker compose down
```

The multi-stage Docker build installs the locked Python runtime requirements, installs the local package, generates the demonstration dataset, and copies the Vite build into the final Python image. It runs Uvicorn as user `10001`, using `PORT` when supplied by the host.

## GitHub and CI

1. Push future changes to [Jatin2567/presslens](https://github.com/Jatin2567/presslens), with this project at the repository root. Keep credentials and local `.env` files out of Git.
2. Ensure the default deployment branch is `main`, or update the workflow's push branch and the selected Render branch together.
3. Run the `CI` workflow. It checks Python/data/SQL/API tests, frontend types and tests, a production frontend build, and a container smoke test.
4. Resolve failing checks before deployment and record the successful run URL for the exact commit being deployed. The verified baseline is commit `633d912` and the CI run linked above; later changes require their own passing run.

The workflow uses the official [checkout](https://github.com/actions/checkout), [setup-python](https://github.com/actions/setup-python), and [setup-node](https://github.com/actions/setup-node) actions. It does not hold deployment credentials or publish a container to a registry.

## Render

The [Render Blueprint specification](https://render.com/docs/blueprint-spec) supports a Docker web service, `healthCheckPath`, and `autoDeployTrigger: checksPass`. The supplied `render.yaml` uses those settings.

The existing service is [`srv-dbrm1rjl550s73cs5t2g`](https://dashboard.render.com/web/srv-dbrm1rjl550s73cs5t2g), on the free plan in Singapore, connected to `main` in this repository. It was created directly through Render's CLI with the Docker and health settings below; it is not managed by a Blueprint. Do not create another service when updating this deployment. The following setup steps describe creating a new environment. Free services sleep after inactivity; see [Render's free-tier limits](https://render.com/docs/free).

The live service's `autoDeployTrigger` is verified as `checksPass`: future code updates are eligible to deploy after their GitHub checks pass. Deployment-record-only commits use Render's documented `[skip render]` marker to keep the verified application release running. Changes to `render.yaml` must also be applied to this directly managed service; the file is a reproducible specification, not an active Blueprint sync.

1. Connect the selected GitHub repository to Render and create a Blueprint from `render.yaml`. If this project is kept inside a larger repository, configure the appropriate root directory before creating the service; the supplied paths assume this project is the repository root.
2. Review the service name, plan, region, deployment branch, and any pricing shown in Render before creating paid resources. The file requests the `free` plan; availability and platform restrictions must be confirmed in the account.
3. Confirm the build uses `Dockerfile` with this repository as its build context. Do not add a second start command; the container starts the API and serves the compiled frontend.
4. Keep `PRESSLENS_DATABASE_PATH=/app/data/demo/presslens.sqlite` and `WEB_DIST=/app/apps/web/dist`. No database credentials or persistent disk are required for the current simulated snapshot.
5. Confirm `/health/ready` passes and the deployment reaches a healthy state. Render controls `PORT`; the container reads it.
6. Open the actual `*.onrender.com` URL returned by Render and perform the acceptance checks below. Do not infer a URL from the requested service name.

`checksPass` gates automatic deployments on repository checks when Render uses a connected Git provider. A service linked only by public repository URL requires manual deployment. Verify the connection and inspect the first deployment separately; passing GitHub CI does not establish a live Render deployment. See [Render's deployment behavior](https://render.com/docs/deploys).

## Custom domain and DuckDNS

First verify the Render-assigned URL. A custom domain is a separate task and requires the exact desired hostname plus access to both Render's custom-domain settings and its DNS provider.

Render's [DNS instructions](https://render.com/docs/configure-other-dns) recommend a CNAME record for a subdomain. The documented [DuckDNS API](https://www.duckdns.org/spec.jsp) exposes IP and TXT updates, but does not document a way to create a CNAME. Therefore this runbook does **not** promise that a `*.duckdns.org` hostname can be connected using Render's normal subdomain setup.

Before changing DNS:

1. Add the exact hostname in Render and read the current verification and DNS requirements it returns.
2. Confirm with Render's current documentation or support whether the intended DuckDNS hostname has a supported configuration.
3. If a CNAME is required and DuckDNS cannot provide one, use the working Render URL or a domain/DNS provider that supports the required record.
4. Do not assume Render's documented apex A-record fallback (`216.24.57.1` at the time of this runbook) is a supported substitute for a DuckDNS subdomain. Apply an A-record workaround only after Render confirms that exact configuration and supplies its current target.
5. Verify domain ownership, HTTPS certificate issuance, and the final hostname in a fresh browser session after DNS propagation.

Keep DuckDNS tokens in the provider's secret mechanism or a local secret store. Never put a token in this repository, a browser-visible URL, a screenshot, or a deployment log. No DuckDNS updater or token is needed by the application itself.

## Acceptance checks

Record the date, commit, dataset version, deployment URL, and check results for each release:

- `/health/live` and `/health/ready` return successful responses.
- The page renders on desktop and a narrow mobile viewport, with the simulated-data label visible.
- Category, channel, and date filters change the metrics and visualizations consistently; reset returns to the baseline.
- Empty and invalid selections produce an understandable response, with no `NaN`, infinite rates, or stale metrics.
- CSV and other advertised downloads complete, have the expected content type, and match their stated scope.
- A sample SQL aggregate reconciles with the current clean dataset and dashboard.
- Browser navigation and page reload work; inspect browser errors while exercising controls.
- Recruiter access is tested in a signed-out/fresh browser session for a public deployment.

Do not label browser interaction testing or public access as verified until those checks have actually been performed.

## Updates and rollback

Update code and generation rules through a reviewed commit. CI builds and checks the same application structure used by Render. Let the connected Render service deploy the selected passing commit, then repeat the health and browser acceptance checks.

If a release is faulty, use Render's supported rollback/redeploy controls to restore a previously verified deployment or commit, and confirm health plus the displayed dataset version. There is no mutable production database to migrate or restore in the current architecture. Keep the working Render URL available while diagnosing any custom-domain failure.
