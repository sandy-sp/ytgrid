
# 🎥 YTGrid — Hybrid CLI + API for Scalable YT Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-3.1.0-green)](https://github.com/sandy-sp/ytgrid/releases)
[![PyPI Downloads](https://img.shields.io/pypi/dm/ytgrid)](https://pypi.org/project/ytgrid/)
[![Docker Pulls](https://img.shields.io/docker/pulls/sandy1sp/ytgrid)](https://hub.docker.com/r/sandy1sp/ytgrid)

YTGrid is a **powerful, scalable, and flexible** YouTube automation tool that enables **looped playback, remote control, and real-time tracking** through a **hybrid CLI + API architecture**.

It combines **FastAPI** for REST control, **Selenium** for browser automation, **Python multiprocessing or Celery** for concurrent execution, and a **SQLite-backed persistence layer** for reusable execution profiles.

---

## ✨ Features

### Core
- **Hybrid Interface** – manage automation via CLI, REST API, or web dashboard.
- **Scalable Execution** – run multiple browser instances in parallel via multiprocessing or Celery.
- **Configurable Automation** – playback speed, loop count, task type.
- **Real-time Updates** – live session status via Server-Sent Events.

### v3.1 additions
- **🔐 API key authentication** – every endpoint protected by `X-API-Key` header (or `api_key` query param for browser EventSource).
- **🗂️ Execution profiles** – save named playlists of URLs + parameters in SQLite; rerun on demand from the CLI or API.
- **🎛️ Web dashboard** – live session table and task launcher at `/static/index.html`; advanced analytics remain on the roadmap.
- **🌐 Optional proxy rotation** – file/env proxy sources, weighted selection, and background health checks; dashboard proxy panels remain on the roadmap.
- **🧹 Resource optimizer** – background tmp-dir cleaner, orphan-only zombie reaper (`ppid==1` Chrome processes), system-load throttling of new sessions.
- **📺 Playlist & channel automation** – new `task_type=playlist` / `channel`; URLs resolved via `yt-dlp`.
- **🐳 Split Docker images** – `Dockerfile.api` (FastAPI only) and `Dockerfile.worker` (Chrome + Celery worker) for microservice deployment.
- **🛡️ Hardened defaults** – input validation, process-group cleanup, isolated browser profiles (0o700), WAL journaling, lifespan-managed startup/shutdown.

---

## 📦 Installation

### 1️⃣ PyPI

```bash
pip install ytgrid
```

### 2️⃣ Docker

```bash
docker pull sandy1sp/ytgrid:latest
docker run -p 8000:8000 -e YTGRID_API_KEY=$(openssl rand -hex 32) sandy1sp/ytgrid:latest
```

### 3️⃣ From source (development)

```bash
git clone https://github.com/sandy-sp/ytgrid.git
cd ytgrid
poetry install
cp .env.example .env
# generate an API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# paste it into .env as YTGRID_API_KEY=...
```

**Requirements**
- **Python 3.10+**
- **Google Chrome** – required for the PyPI install; bundled in the Docker image.
- **ChromeDriver** – managed automatically by `webdriver-manager`.
- **Redis** – only needed if Celery is enabled.

---

## 🔐 Authentication

When `YTGRID_API_KEY` is set, every endpoint (except `/`, `/health`, and static assets) requires the key:

```bash
curl -H "X-API-Key: $YTGRID_API_KEY" http://127.0.0.1:8000/tasks/
```

The CLI reads the key from the same `.env` and forwards it automatically.
Browser dashboard EventSource connections may pass the key as `?api_key=<key>` since browsers cannot set custom headers on `EventSource`.

When `YTGRID_API_KEY` is **unset**, auth is disabled (useful for local development).

---

## 🚀 CLI Usage

### Start a session

```bash
ytgrid start --url "https://www.youtube.com/watch?v=UXFBUZEpnrc" --speed 1.5 --loops 3
```

`--session-id` is now optional — a short id is auto-generated when omitted.

### Status

```bash
ytgrid status
```

### Stop a session

```bash
ytgrid stop --session-id abc12345
```

### Batch (CSV)

```bash
ytgrid batch tasks.csv --delimiter ","
```

CSV header: `session_id, url, speed, loops, task_type`.

### Profiles (new in v3.1)

```bash
ytgrid profile create "morning-mix" --description "Daily wake-up playlist"
ytgrid profile add   "morning-mix" --url "https://www.youtube.com/watch?v=UXFBUZEpnrc" --loops 2
ytgrid profile add   "morning-mix" --url "https://www.youtube.com/watch?v=OaOK76hiW8I" --speed 1.5
ytgrid profile list
ytgrid profile run   "morning-mix"
```

### Dashboard server

```bash
ytgrid server
# → http://127.0.0.1:8000/static/index.html
```

### Toggle Celery

```bash
ytgrid toggle-celery
```

---

## 🖥️ REST API

All examples assume `YTGRID_API_KEY` is set; substitute your own key.

### Start a task

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
     -H "X-API-Key: $YTGRID_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=OaOK76hiW8I", "speed": 1.5, "loop_count": 3}'
```

### List active tasks

```bash
curl -H "X-API-Key: $YTGRID_API_KEY" http://127.0.0.1:8000/tasks/
```

### Stop a task

```bash
curl -X POST http://127.0.0.1:8000/tasks/stop \
     -H "X-API-Key: $YTGRID_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "abc12345"}'
```

### Profiles

```bash
# create
curl -X POST http://127.0.0.1:8000/profiles/ \
     -H "X-API-Key: $YTGRID_API_KEY" -H "Content-Type: application/json" \
     -d '{"name": "morning-mix", "description": "wake up"}'

# add entry
curl -X POST http://127.0.0.1:8000/profiles/1/entries \
     -H "X-API-Key: $YTGRID_API_KEY" -H "Content-Type: application/json" \
     -d '{"video_url": "https://www.youtube.com/watch?v=OaOK76hiW8I", "speed": 1.0, "loop_count": 2}'

# run all entries
curl -X POST http://127.0.0.1:8000/profiles/morning-mix/run \
     -H "X-API-Key: $YTGRID_API_KEY"
```

### Streaming endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /tasks/stream`     | SSE — active session updates every 5 s (auth required) |
| `GET /dashboard/stream` | SSE — dashboard payload every 2 s (auth required; supports `?api_key=`) |

Both cap at 10 concurrent connections and 1 h max duration.

---

## 🎛️ Web Dashboard

Open `http://127.0.0.1:8000/static/index.html` after starting the server. The dashboard shows live sessions, system health, and a "Launch Task" form. On first load it prompts for the API key (stored in `localStorage`).

For the full shipped-app summary, current limitations, and release evidence, see [`docs/APP_OVERVIEW.md`](docs/APP_OVERVIEW.md).

---

## 🌐 Proxy Rotation (optional)

Enable in `.env`:

```ini
YTGRID_PROXY_ENABLED=True
YTGRID_PROXY_SOURCE=file
YTGRID_PROXY_FILE=./proxies.txt
```

`proxies.txt` format (one per line):

```
host:port
host:port:user:pass
```

The pool selects proxies by a weighted score (latency × reliability × idle-time), runs a background health checker, and reports per-session success/failure.

---

## 🧹 Resource Optimizer

Runs three background threads when the API is up:

| Job | Interval | Action |
|-----|----------|--------|
| TmpCleaner   | 5 min  | Deletes `/tmp/ytgrid_*` dirs older than `YTGRID_TMP_MAX_AGE` |
| ZombieReaper | 1 min  | SIGTERMs **orphaned** Chrome processes (`ppid==1`, current UID, >10 min old) |
| SystemMonitor | 30 s  | Samples CPU/mem/disk; throttles new sessions when load is high |

Disable with `YTGRID_OPTIMIZER_ENABLED=False`.

---

## 🐳 Docker

### Single container

```bash
docker build -t ytgrid .
docker run -p 8000:8000 -e YTGRID_API_KEY=$(openssl rand -hex 32) ytgrid
```

### Split API + worker (recommended)

```bash
docker-compose up --build
```

This brings up:
- `ytgrid_api` — FastAPI gateway ([Dockerfile.api](Dockerfile.api))
- `ytgrid_worker` — Celery worker with Chrome ([Dockerfile.worker](Dockerfile.worker))
- `redis` — broker / result backend

Docker Compose requires an API key because it publishes the API port:

```bash
export YTGRID_API_KEY=$(openssl rand -hex 32)
docker-compose up --build
```

---

## 🛠️ Configuration (`.env`)

See [.env.example](.env.example) for the full template.

| Variable | Default | Purpose |
|----------|---------|---------|
| `YTGRID_API_KEY` | *(empty = auth disabled)* | API authentication key |
| `YTGRID_HEADLESS_MODE` | `True` | Chrome headless toggle |
| `YTGRID_DEFAULT_SPEED` / `YTGRID_DEFAULT_LOOP_COUNT` | `1.0` / `1` | CLI defaults |
| `YTGRID_MAX_SESSIONS` | `5` | Concurrency cap |
| `YTGRID_BROWSER_TIMEOUT` | `20` | Selenium implicit wait (s) |
| `YTGRID_DB_PATH` | `ytgrid/ytgrid.db` | SQLite path for profiles + history |
| `YTGRID_USE_CELERY` | `False` | Use Celery instead of multiprocessing |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Celery transport |
| `YTGRID_OPTIMIZER_ENABLED` | `True` | Enable background optimizer |
| `YTGRID_TMP_MAX_AGE` | `1800` | Stale tmp-dir age threshold (s) |
| `YTGRID_PROXY_ENABLED` | `False` | Route Chrome through rotating proxies |
| `YTGRID_PROXY_SOURCE` | `file` | `file` / `env` / `api` |
| `YTGRID_PROXY_FILE` | `./proxies.txt` | Proxy list path |
| `YTGRID_PROXY_COOLDOWN_SECONDS` | `300` | Per-proxy cooldown after selection |
| `YTGRID_PROXY_HEALTH_CHECK_INTERVAL` | `60` | Health-check loop interval (s) |
| `YTGRID_PROXY_MAX_FAILURE_RATE` | `0.3` | Health threshold |

---

## 🧪 Testing

```bash
poetry install --with dev
poetry run pytest
```

For step-by-step manual end-to-end checks see [docs/MANUAL_TESTING.md](docs/MANUAL_TESTING.md).

Architectural docs:
- [docs/VULNERABILITY_FIXES.md](docs/VULNERABILITY_FIXES.md)
- [docs/FEATURE_SPECIFICATIONS.md](docs/FEATURE_SPECIFICATIONS.md)
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- [docs/ROADMAP_SPECIFICATIONS.md](docs/ROADMAP_SPECIFICATIONS.md)

---

## 🔮 Roadmap

- Execution-history UI for `GET /profiles/{id}/history`
- Proxy stats endpoint and dashboard panel
- Profile import/export (JSON)
- Kubernetes manifests for the split-microservice deployment
- Optional PostgreSQL backend for multi-node profile sharing

---

## 📜 License

[MIT](LICENSE)

---

## 🌍 Contributing

1. Fork the repo
2. `git checkout -b feature/my-feature`
3. Add tests for your change (`pytest` must pass)
4. Open a PR

---

## 📖 Resources

- [PyPI](https://pypi.org/project/ytgrid/)
- [Docker Hub](https://hub.docker.com/r/sandy1sp/ytgrid)
- [GitHub](https://github.com/sandy-sp/ytgrid/)
