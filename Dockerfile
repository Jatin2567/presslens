# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS web-build
WORKDIR /build/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PRESSLENS_DATABASE_PATH=/app/data/demo/presslens.sqlite \
    WEB_DIST=/app/apps/web/dist
WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install -r requirements.txt
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN python -m pip install --no-deps . \
    && python -m presslens.pipeline --output-dir /app/data/demo \
    && chmod -R a-w /app/data/demo
COPY --from=web-build /build/web/dist/ ./apps/web/dist/

RUN groupadd --gid 10001 presslens \
    && useradd --uid 10001 --gid presslens --no-create-home --shell /usr/sbin/nologin presslens
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8000') + '/health/ready', timeout=3)" || exit 1
CMD ["sh", "-c", "exec uvicorn presslens.api.main:app --host 0.0.0.0 --port \"${PORT:-8000}\" --no-access-log"]
