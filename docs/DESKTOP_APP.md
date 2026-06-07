# YTGrid Desktop Controller

The desktop controller is the v3.2 foundation for a cross-platform YTGrid app.
It is a React + Vite frontend wrapped by Tauri. The backend remains the
existing FastAPI service; the desktop app connects to a local or network API.

## Scope

This is a controller shell, not a bundled backend installer yet.

Included:

- API URL and API key settings stored in browser/Tauri local storage.
- API health detection.
- Dashboard SSE session updates.
- Task launcher for video, playlist, and channel task types.
- CSV batch import using `session_id,url,speed,loops,task_type`.
- Profile creation and profile run controls.
- Tauri v2 configuration for native Windows, macOS, and Linux packaging.

Not included yet:

- Installing or starting Docker/Redis/FastAPI from the desktop app.
- Secure OS keychain storage.
- Native log tailing.
- Signed installers.

## Development

Start the YTGrid API first:

```bash
export YTGRID_API_KEY=dev-key
.venv/bin/uvicorn ytgrid.backend.main:app --host 127.0.0.1 --port 8000
```

Then run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:1420
```

Run the frontend checks:

```bash
cd frontend
npm test
npm run build
npm audit --audit-level=moderate
```

## Native Tauri Builds

Native builds require Rust/Cargo and platform-specific Tauri dependencies.
On Debian/Ubuntu Linux, install the native packages first:

```bash
sudo apt-get update
sudo apt-get install -y pkg-config libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf
```

After installing Rust:

```bash
cd frontend
npm install
npm run tauri dev
npm run tauri build
```

This workspace currently verifies the web frontend with `npm run build`.
Native verification should be run on machines with the full Tauri toolchain.
The GitHub desktop workflow runs the frontend tests before packaging.

## GitHub Desktop Builds

Native cross-platform packaging is handled by
`.github/workflows/desktop-release.yml`.

Run it manually from the GitHub Actions tab to produce workflow artifacts for:

- Windows x64
- macOS arm64
- macOS x64
- Linux x64

To create a draft desktop release with attached bundles:

```bash
git tag desktop-v3.2.0-alpha.0
git push origin refs/tags/desktop-v3.2.0-alpha.0
```

The desktop bundles are currently unsigned preview builds. The YTGrid API is
still started separately; the app connects to it using the API URL and key.

## Backend CORS

The API allows local desktop development origins by default:

```text
http://localhost:1420
http://127.0.0.1:1420
http://localhost:5173
http://127.0.0.1:5173
tauri://localhost
https://tauri.localhost
http://tauri.localhost
```

Override with:

```bash
YTGRID_CORS_ALLOWED_ORIGINS=http://127.0.0.1:1420,https://tauri.localhost
```
