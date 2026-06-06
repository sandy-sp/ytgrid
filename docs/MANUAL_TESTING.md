# YTGrid v3.1 — Manual Testing Guide

> **Audience:** maintainer verifying a release build end-to-end on a fresh checkout.
> **Estimated time:** ~30 min (skip the proxy and Celery sections if not needed).
> **Platform assumed:** Linux with Chrome installed.

This walkthrough touches every feature shipped in v3.1: API-key auth, execution profiles, the dashboard, the resource optimizer, process-group cleanup, validation, and the optional proxy / Celery paths.

Tick each `[ ]` as you confirm the expected behaviour.

---

## 0. Prerequisites

- Python ≥ 3.10
- Google Chrome installed (`google-chrome --version`)
- `git`, `curl`, `sqlite3`
- (Optional) Docker + docker-compose for the Celery / split-image path
- A YouTube URL you don't mind looping — examples below use a 30-second clip

---

## 1. Repo setup

```bash
git clone https://github.com/sandy-sp/ytgrid.git
cd ytgrid
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install pytest pytest-asyncio
```

Generate an API key and write `.env`:

```bash
cp .env.example .env
KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i "s|^YTGRID_API_KEY=.*|YTGRID_API_KEY=$KEY|" .env
echo "API key: $KEY"
export YTGRID_API_KEY=$KEY
```

- [ ] `.env` contains a non-placeholder `YTGRID_API_KEY`
- [ ] `$YTGRID_API_KEY` exported in your shell

---

## 2. Sanity check

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -c "import ytgrid.backend.main; print('import ok')"
```

- [ ] All tests pass (62+ green)
- [ ] `import ok` printed

---

## 3. Start the API

In **terminal A**:

```bash
.venv/bin/python -m ytgrid.backend.main
# OR (auto-reload off, recommended for testing)
.venv/bin/uvicorn ytgrid.backend.main:app --host 127.0.0.1 --port 8000
```

You should see log lines:
```
YTGrid API is starting up.
Initializing database at .../ytgrid/ytgrid.db
Database schema initialized successfully.
ResourceOptimizer started with background tasks.
```

- [ ] No traceback at startup
- [ ] `ytgrid.db` created at the configured path
- [ ] `ResourceOptimizer started` appears

Open **terminal B** for the rest of the steps.

---

## 4. Authentication checks

```bash
# /health is always open
curl -s http://127.0.0.1:8000/health
# → {"status":"healthy"}

# /tasks/ requires auth — should be 401
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/tasks/
# → 401

# With the key — should be 200
curl -s -H "X-API-Key: $YTGRID_API_KEY" http://127.0.0.1:8000/tasks/
# → {"active_sessions":[]}

# Bad key — should be 401
curl -s -o /dev/null -w "%{http_code}\n" -H "X-API-Key: wrong" http://127.0.0.1:8000/tasks/
# → 401
```

- [ ] `/health` returns 200 without auth
- [ ] `/tasks/` returns **401** without the key
- [ ] `/tasks/` returns **200** with the correct key
- [ ] Bad key returns **401**

---

## 5. Input validation

```bash
# Non-YouTube URL → 422
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/tasks/ \
  -H "X-API-Key: $YTGRID_API_KEY" -H "Content-Type: application/json" \
  -d '{"url":"https://evil.com/x","speed":1.0,"loop_count":1}'
# → 422

# Out-of-bounds speed → 422
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/tasks/ \
  -H "X-API-Key: $YTGRID_API_KEY" -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=UXFBUZEpnrc","speed":-1,"loop_count":1}'
# → 422

# Out-of-bounds loop_count → 422
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/tasks/ \
  -H "X-API-Key: $YTGRID_API_KEY" -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=UXFBUZEpnrc","speed":1.0,"loop_count":0}'
# → 422
```

- [ ] All three return **422**

---

## 6. CLI smoke test

Same terminal (B). The CLI reads `YTGRID_API_KEY` from your environment / `.env`.

```bash
.venv/bin/ytgrid status
# → ✅ No active sessions running.

# Start a video task (session_id auto-generated)
.venv/bin/ytgrid start --url "https://www.youtube.com/watch?v=UXFBUZEpnrc" --speed 2.0 --loops 1
# → ✅ Session '<8-char-id>' started successfully.

# Watch it appear
.venv/bin/ytgrid status
# → table with one running session

# Stop it (replace <id> with the printed session id)
.venv/bin/ytgrid stop --session-id <id>
# → ✅ Session '<id>' stopped successfully.
```

- [ ] Auto-generated session id appears in `status`
- [ ] Chrome window/process launches (visible in `pgrep -a chrome`)
- [ ] `stop` removes the session from `status`
- [ ] No leftover Chrome processes after stop: `pgrep -a chrome` shows none from your session

---

## 7. Process-group cleanup (regression guard)

This is the v3.1 fix that replaced the `pkill` hack. While a session is running:

```bash
.venv/bin/ytgrid start --url "https://www.youtube.com/watch?v=UXFBUZEpnrc" --speed 1.0 --loops 5
# note the printed session id
ps -eo pid,ppid,cmd | grep -E '(chrome|chromedriver)' | grep -v grep
# Confirm there are chrome processes whose ancestor is the python worker
```

Then stop and confirm cleanup:

```bash
.venv/bin/ytgrid stop --session-id <id>
sleep 2
pgrep -af 'chrome.*--user-data-dir=/tmp/ytgrid_' || echo "no leftover ytgrid chromes"
```

- [ ] `no leftover ytgrid chromes` after stop
- [ ] `/tmp/ytgrid_*` directory for that session also gone (see Optimizer section)

---

## 8. Profiles end-to-end (v3.1 feature)

```bash
.venv/bin/ytgrid profile create morning-mix --description "demo"
# → ✅ Profile 'morning-mix' created successfully with ID 1.

.venv/bin/ytgrid profile add morning-mix --url "https://www.youtube.com/watch?v=UXFBUZEpnrc" --loops 1
.venv/bin/ytgrid profile add morning-mix --url "https://www.youtube.com/watch?v=OaOK76hiW8I" --loops 1 --speed 2.0
.venv/bin/ytgrid profile list
# → table with 1 profile

# Detail view via REST
curl -s -H "X-API-Key: $YTGRID_API_KEY" http://127.0.0.1:8000/profiles/morning-mix | python3 -m json.tool
# → JSON with two entries, sequence_order 1 and 2

# Run it — spawns one session per entry
.venv/bin/ytgrid profile run morning-mix
# → ✅ Profile 'morning-mix' triggered successfully. Spawned sessions: <id1>, <id2>

.venv/bin/ytgrid status
# → two running sessions
```

Stop them when ready:

```bash
for s in $(curl -s -H "X-API-Key: $YTGRID_API_KEY" http://127.0.0.1:8000/tasks/ | python3 -c "import json,sys;[print(x['id']) for x in json.load(sys.stdin)['active_sessions']]"); do
  .venv/bin/ytgrid stop --session-id "$s"
done
```

- [ ] Profile creation, add, list all succeed
- [ ] `profile run` spawns one session per entry (NOT a TypeError — that was the v3.0.x bug)
- [ ] Bulk stop clears the active list

---

## 9. Database inspection

```bash
sqlite3 ytgrid/ytgrid.db "SELECT * FROM profiles;"
sqlite3 ytgrid/ytgrid.db "SELECT * FROM profile_entries;"
sqlite3 ytgrid/ytgrid.db "SELECT * FROM execution_history;"
```

- [ ] `profiles` row exists for `morning-mix`
- [ ] `profile_entries` rows with monotonically increasing `sequence_order`
- [ ] `execution_history` rows recorded with `status` transitioning from `playing` → `completed`/`failed`

Cascade delete check:

```bash
curl -s -X DELETE -H "X-API-Key: $YTGRID_API_KEY" http://127.0.0.1:8000/profiles/1
sqlite3 ytgrid/ytgrid.db "SELECT COUNT(*) FROM profile_entries WHERE profile_id=1;"
# → 0
```

- [ ] Entries cascade-deleted (proves `PRAGMA foreign_keys = ON` is active per connection)

---

## 10. Dashboard (browser)

Visit `http://127.0.0.1:8000/static/index.html`.

On first load the page prompts: `Enter YTGrid API key…` — paste `$YTGRID_API_KEY`.

Then:

1. Active sessions table populates live (start one in terminal B and watch it appear within ~2 s).
2. Click **Launch Task**, paste a YouTube URL, submit. A new session appears.
3. Click **Stop** on a running session — confirm the prompt; row vanishes.

- [ ] Dashboard loads, prompts for key, stores it (next reload no prompt)
- [ ] EventSource shows live updates (network tab: `dashboard/stream?api_key=...` open, status 200)
- [ ] Launch form starts a session
- [ ] Stop button cleans up the session

Clear the stored key for re-testing:
```js
// in browser devtools console
localStorage.removeItem('ytgrid_api_key')
```

---

## 11. SSE endpoints (curl)

```bash
# /tasks/stream — emits every 5s, max 1h, max 10 concurrent
curl -sN -H "X-API-Key: $YTGRID_API_KEY" http://127.0.0.1:8000/tasks/stream | head -n 3

# /dashboard/stream — same protections, key may be in query string
curl -sN "http://127.0.0.1:8000/dashboard/stream?api_key=$YTGRID_API_KEY" | head -n 3
```

- [ ] Both return `data: {...}` lines and close cleanly when you `Ctrl-C`
- [ ] Without auth: `curl -i http://127.0.0.1:8000/tasks/stream` → `401`

---

## 12. Resource Optimizer behaviour

Start a session, then immediately stop it, then check `/tmp`:

```bash
.venv/bin/ytgrid start --url "https://www.youtube.com/watch?v=UXFBUZEpnrc" --speed 1.0 --loops 1
.venv/bin/ytgrid stop --session-id <id>
ls -d /tmp/ytgrid_* 2>/dev/null
```

After the next TmpCleaner sweep (≤ 5 min by default; you can force a quicker check by setting `YTGRID_TMP_MAX_AGE=0` and restarting the API), the stale dirs disappear.

ZombieReaper proof: with no orphaned Chromes (`ppid==1` chrome >10 min old) you should see no `Reaped orphaned browser process` log lines. If you have real crashed Chromes on the box, you'll see them reaped — that's correct behaviour.

- [ ] TmpCleaner removes stale `/tmp/ytgrid_*` after the configured age
- [ ] ZombieReaper does NOT touch your active session Chromes (their parent is alive → `ppid != 1`)

---

## 13. (Optional) Proxy rotation

Create `proxies.txt`:

```
1.2.3.4:8080
5.6.7.8:3128:user:pass
```

Edit `.env`:
```
YTGRID_PROXY_ENABLED=True
YTGRID_PROXY_SOURCE=file
YTGRID_PROXY_FILE=./proxies.txt
```

Restart the API. Log lines should include:
```
Loaded 2 proxies into pool.
ProxyHealthChecker started.
```

Start a session and grep the log for `Proxy: <host>:<port>` — confirms the per-loop proxy selection.

- [ ] Proxies loaded count matches the file
- [ ] HealthChecker thread running
- [ ] Per-loop log mentions the chosen proxy

---

## 14. (Optional) Celery + Redis path via Docker

```bash
docker-compose up --build
```

Wait for `ytgrid_api`, `ytgrid_worker`, and `redis` to be `Up`. Then from the host:

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "X-API-Key: $YTGRID_API_KEY" -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=UXFBUZEpnrc","speed":1.0,"loop_count":1}'
```

Tail the worker:

```bash
docker logs -f ytgrid_worker
```

You should see Celery picking up `ytgrid.tasks.run_automation`.

- [ ] Both containers stay up
- [ ] Task lands in the worker, runs to completion
- [ ] `/tasks/` on the API reflects the running session

Tear down:
```bash
docker-compose down -v
```

---

## 15. Teardown

```bash
# stop the API (Ctrl-C in terminal A)
deactivate 2>/dev/null
rm -f ytgrid/ytgrid.db ytgrid.log /tmp/ytgrid_*
```

- [ ] No leftover Chrome processes (`pgrep -a chrome`)
- [ ] No leftover `/tmp/ytgrid_*` dirs
- [ ] `ytgrid.db` removed if you want a clean slate

---

## Optional appendix: Desktop controller preview

This is the v3.2-alpha desktop controller path. It does not replace the v3.1
browser dashboard yet; it verifies that the React/Vite frontend can connect to
the local API and that the Tauri shell is ready for native builds on machines
with Rust installed.

Start the API as in section 3, then in a new terminal:

```bash
cd frontend
npm ci
npm run build
npm audit --audit-level=moderate
npm run dev
```

Visit `http://127.0.0.1:1420`, set the API URL to
`http://127.0.0.1:8000`, and paste `$YTGRID_API_KEY`.

- [ ] Desktop web preview loads
- [ ] Health status shows connected
- [ ] Active task list populates
- [ ] Starting/stopping a task works through the desktop UI
- [ ] CSV batch import parses `tests/test.csv`

Native Tauri smoke, if Rust/Cargo is installed:

```bash
cd frontend
npm run tauri -- --version
npm run tauri -- build
```

- [ ] Tauri CLI reports a version
- [ ] Native desktop bundle builds for the host platform

---

## Release sign-off

All boxes ticked → safe to tag and push.

| Section | Status |
|---------|--------|
| 1 – 2  Setup + sanity | ☐ |
| 3 – 5  API up + auth + validation | ☐ |
| 6 – 7  CLI + process cleanup | ☐ |
| 8 – 9  Profiles + DB | ☐ |
| 10 – 11  Dashboard + SSE | ☐ |
| 12  Optimizer | ☐ |
| 13  Proxy (optional) | ☐ |
| 14  Celery (optional) | ☐ |
| 15  Teardown | ☐ |
