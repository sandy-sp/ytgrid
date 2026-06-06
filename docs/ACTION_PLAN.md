# YTGrid v3.1 Stabilization Action Plan

## Summary

Stabilize the current uncommitted v3.1 work before any push or release. This is not a full v4 roadmap pass; the goal is to make the current v3.1 changes safe, coherent, tested, and accurately documented.

Execution order:

1. Write this action plan.
2. Fix release blockers.
3. Tighten tests so they verify the real app.
4. Re-run validation and update docs to match shipped behavior.
5. Prepare a clean commit/release recommendation.

## Key Changes

- Security and packaging:
  - Keep `.env` deleted from git, keep `.env.example`, and remove `.env` from package manifests.
  - Require `YTGRID_API_KEY` for Docker/public binds; Docker Compose must not expose an unauthenticated API by default.
  - Keep `/health`, `/`, and `/static/*` unauthenticated; protect task/session/profile/dashboard stream endpoints.
- Task lifecycle:
  - Ensure completed multiprocessing sessions are removed from active session state.
  - Ensure Celery and multiprocessing both record profile execution end states: `completed` or `failed`.
  - Validate `task_type` as only `video`, `playlist`, or `channel`; invalid values must fail before starting work.
  - Make `/tasks/` failure details distinguish duplicate session, throttled system, and invalid task type where practical.
- Playlist/channel:
  - Normalize resolver output to full YouTube watch URLs.
  - Add tests proving playlist/channel entries become `https://www.youtube.com/watch?v=...`.
  - Keep playlist/channel support in v3.1 only if resolver tests pass without live browser automation.
- Dashboard and proxy:
  - Keep dashboard as a basic v3.1 UI, but make README clear that proxy stats/history panels are not complete unless implemented.
  - Add `/proxy/stats` only if wiring is small and testable; otherwise move it to roadmap.
- Docker and release docs:
  - Align `README.md`, `pyproject.toml`, Dockerfiles, and Compose around one v3.1 story.
  - Preserve old single-image `Dockerfile` only if it still builds; otherwise document the split image path and update workflows later.

## Test Plan

- Run `./.venv/bin/python -m pytest -q` after each major group.
- Replace the toy `tests/test_api_endpoints.py` app with tests against `ytgrid.backend.main:app`.
- Add or confirm tests for:
  - unauthenticated protected endpoints return 401 when `YTGRID_API_KEY` is set
  - `/health` remains open
  - invalid `task_type`, bad URL, invalid speed, invalid loop count return validation errors
  - completed multiprocessing process no longer appears in `/tasks/`
  - profile execution history transitions out of `playing`
  - Celery task path calls history completion logic
  - `.env` is ignored and excluded from package manifests
  - URL resolver normalizes playlist/channel flat entries into full watch URLs
- Run grep checks:
  - no `os.system("pkill")`
  - no committed `.env`
  - no packaging include for `.env`

## Execution Checklist

- [x] Create `docs/ACTION_PLAN.md` with this stabilization plan.
- [x] Fix `.env`/manifest/package hygiene.
- [x] Lock Docker Compose/API auth defaults.
- [x] Fix task lifecycle cleanup for completed multiprocessing sessions.
- [x] Fix profile execution history for multiprocessing and Celery.
- [x] Validate `task_type` at request model level.
- [x] Normalize playlist/channel resolver output.
- [x] Replace fake API endpoint tests with real app tests.
- [x] Add focused regression tests for release blockers.
- [x] Update README to describe only what v3.1 actually ships.
- [x] Run full test suite and grep audits.
- [x] Produce final review: commit-ready, release-ready, or remaining blockers.

## Validation Results

- `./.venv/bin/python -m pytest -q` passed: 62 tests.
- Code audit passed: no `os.system` or `pkill` references in `ytgrid/` or `tests/`.
- Package hygiene passed: `.env` is ignored and removed from `MANIFEST.in`.
- Import sanity passed: `ytgrid.__version__ == "3.1.0"` and `ytgrid.backend.main` imports.
- E2E smoke uncovered and fixed CLI configurability: `YTGRID_API_BASE_URL` now lets the CLI target a non-default API port.
- Docker smoke uncovered and fixed split-image dependency installation: `Dockerfile.api` and `Dockerfile.worker` install dependencies with `--no-root` before copying source.
- Docker worker smoke uncovered and fixed deprecated/removed `apt-key` usage for Chrome installation.
- `YTGRID_API_KEY=smoke-test-key docker compose config` passed, proving Compose requires the API key and renders valid config.
- `YTGRID_API_KEY=smoke-test-key docker compose build api` passed.
- `YTGRID_API_KEY=smoke-test-key docker compose build worker` passed.
- Manual local API smoke passed on port 8001 because port 8000 was already occupied:
  - `/health`, `/`, and `/static/index.html` returned 200 without auth.
  - `/tasks/` returned 401 without `X-API-Key` and 200 with `X-API-Key`.
  - Bad URL and invalid `task_type` returned validation errors before starting work.
  - Dashboard SSE connected with `api_key`.
  - Direct task start/status/stop launched Chrome, reached YouTube, and cleared active sessions after stop.
  - CLI `status`, `start`, `stop`, and profile commands worked against `YTGRID_API_BASE_URL=http://127.0.0.1:8001`.
  - Profile run/stop history transitioned from `playing` to `stopped` with `completed_at` set.
- Full `docker compose up -d` passed after freeing port 8000:
  - Stopped the previous container using port 8000: `engineering-interview-orders-tutorial-100-backend-1`.
  - `ytgrid_api`, `ytgrid_worker`, and `ytgrid_redis` started successfully.
  - `/health` returned 200 on `http://127.0.0.1:8000`.
  - `/tasks/` returned 401 without `X-API-Key` and 200 with `X-API-Key`.
  - `/`, `/static/index.html`, dashboard SSE, validation errors, and profile creation worked through Compose.
  - Compose Celery mode accepted a video task, the worker received `ytgrid.tasks.run_automation`, created a Chrome session, reached YouTube, and was stopped cleanly.
  - `/tasks/` was empty after stopping the Compose smoke task.
  - Non-blocking warnings observed: Celery running as root, Celery startup retry deprecation warning, and worker WebSocket DNS warning for realtime updates.

## Assumptions

- Scope is `Stabilize v3.1`, not full v4 completion.
- Existing uncommitted work should be repaired where aligned, not wholesale reverted.
- Public release should wait until all release-blocking checklist items pass.
