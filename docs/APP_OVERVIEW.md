# YTGrid v3.1 App Overview

YTGrid v3.1 is a local-first YouTube automation control plane. It combines a
FastAPI backend, Selenium browser automation, a CLI, an optional Celery worker
stack, SQLite persistence, and a basic browser dashboard.

This document describes the app as it ships in v3.1. Future v4 ideas remain in
the roadmap docs and should not be treated as shipped behavior.

## What Ships in v3.1

- CLI commands for starting, stopping, listing, batching, and profile workflows.
- REST API task control at `/tasks/`.
- API-key auth for protected API and stream endpoints.
- Open health/root/static endpoints: `/health`, `/`, and `/static/*`.
- SQLite-backed execution profiles.
- Video, playlist, and channel task types.
- Multiprocessing execution for local development.
- Celery + Redis execution for Docker Compose.
- Basic dashboard at `/static/index.html`.
- Dashboard SSE at `/dashboard/stream`.
- Resource optimizer for tmp cleanup, orphan Chrome cleanup, and load throttling.
- Optional proxy pool primitives and health checks.

## What Does Not Ship Yet

- A packaged desktop app.
- Full proxy analytics/history panels in the dashboard.
- Full v4 microservice separation.
- Production-grade user accounts, roles, or multi-tenant auth.
- A polished installer for Windows, macOS, or Linux.

## Run Locally

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Put the generated value in `.env` as `YTGRID_API_KEY`.

```bash
.venv/bin/python -m pytest -q
.venv/bin/uvicorn ytgrid.backend.main:app --host 127.0.0.1 --port 8000
```

Open the dashboard:

```text
http://127.0.0.1:8000/static/index.html
```

## Run With Docker Compose

```bash
export YTGRID_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up -d
```

Verify:

```bash
curl http://127.0.0.1:8000/health
curl -H "X-API-Key: $YTGRID_API_KEY" http://127.0.0.1:8000/tasks/
```

## API Notes

The REST API uses `loop_count`:

```json
{
  "url": "https://www.youtube.com/watch?v=OaOK76hiW8I",
  "speed": 1.0,
  "loop_count": 3,
  "task_type": "video"
}
```

The CLI batch CSV uses `loops` and converts it to `loop_count` before calling
the API:

```csv
session_id,url,speed,loops,task_type
batch_1,https://www.youtube.com/watch?v=OaOK76hiW8I,1.0,3,video
```

## Release Evidence

The v3.1 stabilization pass verified:

- `62 passed` from the full pytest suite.
- Docker Compose API, worker, and Redis startup.
- API-key enforcement on protected endpoints.
- Dashboard SSE connectivity.
- Real Celery worker playback against five CSV videos, three loops each, at 1x speed.
- Active session cleanup after completion.

See `docs/ACTION_PLAN.md` for the detailed checklist and validation notes.
