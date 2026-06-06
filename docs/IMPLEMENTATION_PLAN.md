# YTGrid Master Implementation Plan

> **Version:** 3.1.0 → 4.0.0
> **Date:** 2026-04-17
> **Author:** Senior Staff Architect
> **Status:** Approved for Execution

---

## Overview

This document is the chronological, step-by-step master plan that synthesizes the findings from:
- [`VULNERABILITY_FIXES.md`](./VULNERABILITY_FIXES.md) — 14 security vulnerabilities
- [`FEATURE_SPECIFICATIONS.md`](./FEATURE_SPECIFICATIONS.md) — Proxy Rotation, Resource Optimizer, Persistence
- [`ROADMAP_SPECIFICATIONS.md`](./ROADMAP_SPECIFICATIONS.md) — Playlist/Channel, Microservices, Dashboard

The plan is organized into 6 phases across 3 releases, with each phase containing prioritized, dependency-ordered tasks.

---

## Release Timeline

```
v3.1.0 (Security + Stability)     ──── Weeks 1-3
v3.2.0 (Core Features)            ──── Weeks 4-8
v4.0.0 (Future Platform)          ──── Weeks 9-16
```

---

## Phase 1: Critical Security Hardening (Week 1)

> **Goal:** Eliminate all CRITICAL and HIGH severity vulnerabilities.

### 1.1 API Authentication Layer

| Task | File | Priority |
|------|------|----------|
| Create `ytgrid/backend/auth.py` with API key verification | NEW | P0 |
| Add `YTGRID_API_KEY` to `.env.example` | MODIFIED | P0 |
| Apply `Depends(verify_api_key)` to all route handlers in `task.py` | MODIFIED | P0 |
| Apply `Depends(verify_api_key)` to all route handlers in `session.py` | MODIFIED | P0 |
| Update CLI to send `X-API-Key` header with all requests | MODIFIED | P0 |
| Add `YTGRID_API_KEY` to `Config` class in `config.py` | MODIFIED | P0 |

**Acceptance Criteria:**
- [ ] All API endpoints return 401 without a valid key.
- [ ] CLI passes API key from environment.
- [ ] Health endpoint (`/health`) remains unauthenticated.

### 1.2 Fix OS Command Injection (`pkill`)

| Task | File | Priority |
|------|------|----------|
| Create `ProcessRegistry` class in `ytgrid/backend/process_registry.py` | NEW | P0 |
| Remove `kill_browser_processes()` function from `task_manager.py` | MODIFIED | P0 |
| Register Chrome PIDs via `process_registry.register(pid)` in `browser.py` | MODIFIED | P0 |
| Replace `kill_browser_processes()` call in `stop_session()` with `process_registry.kill_all()` | MODIFIED | P0 |

**Acceptance Criteria:**
- [ ] No `os.system("pkill")` calls exist in the codebase.
- [ ] Only YTGrid-owned PIDs are terminated.
- [ ] Grep for `os.system` returns zero results.

### 1.3 Input Validation

| Task | File | Priority |
|------|------|----------|
| Add YouTube URL regex validator to `TaskStartRequest` in `task.py` | MODIFIED | P0 |
| Add field bounds to `speed` (0.25–16.0), `loop_count` (1–1000) | MODIFIED | P0 |
| Add `session_id` format validation (alphanumeric + `_-`, max 64 chars) | MODIFIED | P0 |
| Add same validation to `SessionStartRequest` in `session.py` | MODIFIED | P0 |
| Add URL validation to `get_video_title()` in `player.py` (SSRF prevention) | MODIFIED | P1 |

**Acceptance Criteria:**
- [ ] `file://`, `ftp://`, `javascript:` URLs are rejected with 422.
- [ ] `speed: -1` returns 422.
- [ ] `loop_count: 0` returns 422.

### 1.4 Environment & Configuration Hardening

| Task | File | Priority |
|------|------|----------|
| Add `.env` to `.gitignore` | MODIFIED | P0 |
| Create `.env.example` with placeholder values | NEW | P0 |
| Change CLI default bind from `0.0.0.0` to `127.0.0.1` in `cli.py` | MODIFIED | P1 |
| Redirect CLI-spawned Uvicorn output to log file instead of DEVNULL | MODIFIED | P1 |

---

## Phase 2: Stability & Resource Management (Week 2)

> **Goal:** Fix resource leaks, process management bugs, and the broken session store.

### 2.1 Fix Singleton Session Store

| Task | File | Priority |
|------|------|----------|
| Implement singleton pattern in `get_session_store()` in `dependencies.py` | MODIFIED | P0 |
| Add integration test verifying session persistence across requests | NEW | P1 |

### 2.2 Browser Session Cleanup

| Task | File | Priority |
|------|------|----------|
| Replace `tempfile.mkdtemp()` with `tempfile.TemporaryDirectory()` in `browser.py` | MODIFIED | P1 |
| Add `os.chmod(user_data_dir, 0o700)` after temp dir creation | MODIFIED | P1 |
| Add Chrome hardening flags (see VF-004 remediation) to `browser.py` | MODIFIED | P1 |
| Update `browser_session()` context manager in `player.py` to use TemporaryDirectory | MODIFIED | P1 |

### 2.3 Process Management Fix

| Task | File | Priority |
|------|------|----------|
| Refactor `_start_process()` to not reference global `task_manager` | MODIFIED | P1 |
| Add `atexit` handler to terminate child processes on shutdown | MODIFIED | P1 |
| Implement `join(timeout=10)` with SIGKILL fallback in `stop_session()` | MODIFIED | P1 |

### 2.4 SSE Security

| Task | File | Priority |
|------|------|----------|
| Add auth requirement to `/tasks/stream` endpoint | MODIFIED | P1 |
| Add connection counter with max limit (10) | MODIFIED | P1 |
| Add 1-hour timeout to SSE generator | MODIFIED | P1 |

### 2.5 Modernize FastAPI Lifecycle

| Task | File | Priority |
|------|------|----------|
| Replace `@app.on_event("startup/shutdown")` with `lifespan` context manager | MODIFIED | P2 |

---

## Phase 3: Resource Optimizer (Week 3)

> **Goal:** Deploy the background resource optimization system.

### 3.1 Implement Optimizer Components

| Task | File | Priority |
|------|------|----------|
| Create `ytgrid/optimizer/__init__.py` | NEW | P1 |
| Create `ytgrid/optimizer/tmp_cleaner.py` | NEW | P1 |
| Create `ytgrid/optimizer/zombie_reaper.py` | NEW | P1 |
| Create `ytgrid/optimizer/system_monitor.py` | NEW | P1 |
| Create `ytgrid/optimizer/orchestrator.py` | NEW | P1 |

### 3.2 Integrate with TaskManager

| Task | File | Priority |
|------|------|----------|
| Start `ResourceOptimizer` in FastAPI `lifespan` startup | MODIFIED | P1 |
| Stop `ResourceOptimizer` in FastAPI `lifespan` shutdown | MODIFIED | P1 |
| Add throttle check in `TaskManager.start_session()` | MODIFIED | P1 |
| Add config vars: `YTGRID_OPTIMIZER_ENABLED`, `YTGRID_TMP_MAX_AGE` | MODIFIED | P2 |

### 3.3 Testing

| Task | File | Priority |
|------|------|----------|
| Unit tests for `TmpCleaner` (create fake dirs, verify cleanup) | NEW | P1 |
| Unit tests for `SystemMonitor` (mock `/proc` reads) | NEW | P2 |
| Integration test: start session → stop session → verify tmp cleaned | NEW | P2 |

---

## Phase 4: Auto-Proxy Rotation (Weeks 4-5)

> **Goal:** Integrate proxy rotation into the Selenium pipeline.

### 4.1 Proxy Infrastructure

| Task | File | Priority |
|------|------|----------|
| Create `ytgrid/proxy/__init__.py` | NEW | P1 |
| Create `ytgrid/proxy/models.py` (Proxy, ProxyProtocol, ProxyHealth) | NEW | P1 |
| Create `ytgrid/proxy/pool.py` (ProxyPool with weighted selection) | NEW | P1 |
| Create `ytgrid/proxy/health.py` (ProxyHealthChecker background thread) | NEW | P1 |
| Create `ytgrid/proxy/sources.py` (FileProxySource, EnvProxySource, APIProxySource) | NEW | P1 |

### 4.2 Browser Integration

| Task | File | Priority |
|------|------|----------|
| Add `proxy` parameter to `get_browser()` in `browser.py` | MODIFIED | P1 |
| Add proxy selection logic in `browser_session()` context manager in `player.py` | MODIFIED | P1 |
| Report proxy success/failure after each video play | MODIFIED | P1 |

### 4.3 Configuration & API

| Task | File | Priority |
|------|------|----------|
| Add proxy config vars to `Config` class | MODIFIED | P1 |
| Add `/proxy/stats` API endpoint (proxy pool health) | NEW | P2 |
| Start `ProxyHealthChecker` in FastAPI lifespan | MODIFIED | P2 |

### 4.4 Testing

| Task | File | Priority |
|------|------|----------|
| Unit tests for `ProxyPool` (selection, failure tracking, cooldown) | NEW | P1 |
| Unit tests for `ProxyHealthChecker` (mock HTTP responses) | NEW | P2 |
| Integration test: verify Chrome uses proxy (check external IP) | NEW | P2 |

---

## Phase 5: User Profiles & Persistence (Weeks 6-8)

> **Goal:** Implement persistent profile storage and execution history.

### 5.1 Database Layer

| Task | File | Priority |
|------|------|----------|
| Create `ytgrid/database/__init__.py` | NEW | P1 |
| Create `ytgrid/database/schema.sql` | NEW | P1 |
| Create `ytgrid/database/repository.py` (ProfileRepository) | NEW | P1 |
| Add `aiosqlite` to `pyproject.toml` dependencies | MODIFIED | P1 |
| Initialize database in FastAPI lifespan startup | MODIFIED | P1 |

### 5.2 API Endpoints

| Task | File | Priority |
|------|------|----------|
| Create `ytgrid/backend/routes/profiles.py` | NEW | P1 |
| Register profile router in `routes/__init__.py` | MODIFIED | P1 |
| Implement `POST /profiles/` (create) | NEW | P1 |
| Implement `GET /profiles/` (list) | NEW | P1 |
| Implement `GET /profiles/{name}` (detail with entries) | NEW | P1 |
| Implement `POST /profiles/{id}/entries` (add entry) | NEW | P1 |
| Implement `POST /profiles/{name}/run` (execute profile) | NEW | P1 |
| Implement `DELETE /profiles/{id}` (soft delete) | NEW | P2 |

### 5.3 CLI Integration

| Task | File | Priority |
|------|------|----------|
| Add `profile create` command to CLI | MODIFIED | P1 |
| Add `profile list` command | MODIFIED | P1 |
| Add `profile add` command (add entry to profile) | MODIFIED | P1 |
| Add `profile run` command (execute a profile) | MODIFIED | P1 |
| Add `profile export` command (JSON export) | MODIFIED | P2 |
| Add `profile import` command (JSON import) | MODIFIED | P2 |

### 5.4 Execution History

| Task | File | Priority |
|------|------|----------|
| Record execution start in `task_manager.start_session()` | MODIFIED | P2 |
| Record execution completion/failure in `run_automation()` | MODIFIED | P2 |
| Add `GET /profiles/{id}/history` endpoint | NEW | P2 |
| Add `profile history` CLI command | MODIFIED | P2 |

---

## Phase 6: Playlist/Channel & Dashboard (Weeks 9-16)

> **Goal:** Deliver v4.0 with multi-URL-type support and real-time dashboard.

### 6.1 URL Resolver & New Players

| Task | File | Priority |
|------|------|----------|
| Create `ytgrid/automation/url_resolver.py` (URLResolver) | NEW | P1 |
| Create `ytgrid/automation/playlist_player.py` (PlaylistPlayer) | NEW | P1 |
| Create `ytgrid/automation/channel_player.py` (ChannelPlayer) | NEW | P1 |
| Register `PlaylistPlayer` and `ChannelPlayer` in `AUTOMATION_PLAYERS` dict | MODIFIED | P1 |
| Add `yt-dlp` as optional dependency in `pyproject.toml` | MODIFIED | P1 |
| Update URL validation regex to accept playlist and channel URLs | MODIFIED | P1 |

### 6.2 Dashboard Backend

| Task | File | Priority |
|------|------|----------|
| Create `ytgrid/backend/routes/dashboard.py` (SSE endpoints) | NEW | P2 |
| Register dashboard router in `routes/__init__.py` | MODIFIED | P2 |
| Add static file serving to `main.py` | MODIFIED | P2 |

### 6.3 Dashboard Frontend

| Task | File | Priority |
|------|------|----------|
| Create `ytgrid/backend/static/index.html` | NEW | P2 |
| Create `ytgrid/backend/static/css/dashboard.css` | NEW | P2 |
| Create `ytgrid/backend/static/js/dashboard.js` | NEW | P2 |
| Implement session table with real-time updates via SSE | NEW | P2 |
| Implement system health gauges (CPU, RAM, Disk) | NEW | P2 |
| Implement proxy pool status display | NEW | P2 |

### 6.4 Microservices Preparation

| Task | File | Priority |
|------|------|----------|
| Create `Dockerfile.worker` (Chrome + Celery worker only) | NEW | P2 |
| Create `Dockerfile.api` (FastAPI without Chrome) | NEW | P2 |
| Update `docker-compose.yml` with separate API and worker services | MODIFIED | P2 |
| Add `requirements-worker.txt` (minimal deps for worker) | NEW | P3 |
| Add `requirements-api.txt` (minimal deps for API) | NEW | P3 |

---

## Testing Strategy

### Automated Tests

```bash
# Run after each phase:
poetry run pytest tests/ --disable-warnings -v

# Security-specific checks:
grep -rn "os.system" ytgrid/                    # Should return 0 results
grep -rn "pkill" ytgrid/                        # Should return 0 results
grep -rn "subprocess.call" ytgrid/              # Audit each occurrence
```

### Manual Verification

| Phase | Verification |
|-------|-------------|
| Phase 1 | `curl -X POST /tasks/ -d '...'` returns 401 without key |
| Phase 2 | Start 5 sessions → stop all → `ls /tmp/ytgrid_*` returns nothing |
| Phase 3 | Create 100 temp dirs → wait 30 min → check optimizer cleaned them |
| Phase 4 | Start session with proxy → verify external IP differs from host |
| Phase 5 | `ytgrid profile create` → restart server → `ytgrid profile list` returns it |
| Phase 6 | `ytgrid start --url "youtube.com/playlist?list=..."` plays all videos |

---

## File Manifest

### New Files (25)

```
ytgrid/backend/auth.py
ytgrid/backend/process_registry.py
ytgrid/backend/routes/profiles.py
ytgrid/backend/routes/dashboard.py
ytgrid/backend/static/index.html
ytgrid/backend/static/css/dashboard.css
ytgrid/backend/static/js/dashboard.js
ytgrid/optimizer/__init__.py
ytgrid/optimizer/tmp_cleaner.py
ytgrid/optimizer/zombie_reaper.py
ytgrid/optimizer/system_monitor.py
ytgrid/optimizer/orchestrator.py
ytgrid/proxy/__init__.py
ytgrid/proxy/models.py
ytgrid/proxy/pool.py
ytgrid/proxy/health.py
ytgrid/proxy/sources.py
ytgrid/database/__init__.py
ytgrid/database/schema.sql
ytgrid/database/repository.py
ytgrid/automation/url_resolver.py
ytgrid/automation/playlist_player.py
ytgrid/automation/channel_player.py
.env.example
Dockerfile.worker
```

### Modified Files (14)

```
ytgrid/backend/task_manager.py
ytgrid/backend/task.py
ytgrid/backend/main.py
ytgrid/backend/dependencies.py
ytgrid/backend/routes/__init__.py
ytgrid/backend/routes/session.py
ytgrid/backend/celery_app.py
ytgrid/automation/browser.py
ytgrid/automation/player.py
ytgrid/automation/__init__.py
ytgrid/utils/config.py
ytgrid/cli.py
pyproject.toml
.gitignore
```

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| `yt-dlp` rate limiting by YouTube | High | Medium | Cache resolved playlists; implement backoff |
| SQLite write contention under load | Medium | Medium | Use WAL mode; migrate to PostgreSQL in v4.1 |
| Proxy pool exhaustion (all proxies dead) | Medium | High | Implement no-proxy fallback with user warning |
| Chrome version mismatch after system update | Low | High | Pin chromedriver version; use `webdriver-manager` auto-detect |
| Breaking changes in YouTube DOM structure | High | High | Abstract DOM selectors; use yt-dlp where possible |

---

## Definition of Done

Each phase is considered **done** when:

1. All tasks in the phase checklist are completed.
2. All automated tests pass (`pytest`, `grep` audits).
3. Manual verification scenarios listed above succeed.
4. No CRITICAL or HIGH severity vulnerabilities remain (per updated audit).
5. Documentation in `/docs/` is updated to reflect changes.
