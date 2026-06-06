# YTGrid Roadmap Specifications — Future Releases

> **Version Target:** 4.0.0
> **Date:** 2026-04-17
> **Author:** Senior Staff Architect

---

## Table of Contents

1. [Playlist & Channel Support](#1-playlist--channel-support)
2. [Microservices Architecture Migration](#2-microservices-architecture-migration)
3. [Real-Time Dashboard (Web UI)](#3-real-time-dashboard-web-ui)

---

## 1. Playlist & Channel Support

### 1.1 Problem Statement

YTGrid v3 only handles single video URLs. Users need to automate:
- **Playlists:** Play all videos in a YouTube playlist in order.
- **Channels:** Play the N most recent uploads from a channel.
- **Mixed profiles:** A profile that contains a mix of videos, playlists, and channels.

### 1.2 Architecture: Fan-Out Pattern

```
                    ┌─────────────────────┐
                    │   User Request      │
                    │   (playlist URL)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   URLResolver       │
                    │   • Detect type     │
                    │   • Extract videos  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ Video 1  │    │ Video 2  │    │ Video N  │
        │ Session  │    │ Session  │    │ Session  │
        └──────────┘    └──────────┘    └──────────┘
```

### 1.3 URL Resolver

The URL Resolver detects the input type and extracts individual video URLs.

```python
# ytgrid/automation/url_resolver.py
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class URLType(Enum):
    VIDEO = "video"
    PLAYLIST = "playlist"
    CHANNEL = "channel"
    UNKNOWN = "unknown"

@dataclass
class ResolvedTarget:
    """Result of resolving a YouTube URL into individual targets."""
    original_url: str
    url_type: URLType
    video_urls: List[str]
    title: Optional[str] = None
    total_count: int = 0

class URLResolver:
    """
    Resolves YouTube URLs into individual video targets.

    Supports:
    - youtube.com/watch?v=xxx
    - youtube.com/playlist?list=PLxxx
    - youtube.com/@channel or youtube.com/channel/UCxxx
    """

    # Patterns
    VIDEO_PATTERN = re.compile(
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
    )
    PLAYLIST_PATTERN = re.compile(
        r'youtube\.com/playlist\?list=(PL[a-zA-Z0-9_-]+)'
    )
    CHANNEL_PATTERNS = [
        re.compile(r'youtube\.com/@([a-zA-Z0-9_-]+)'),
        re.compile(r'youtube\.com/channel/(UC[a-zA-Z0-9_-]+)'),
        re.compile(r'youtube\.com/c/([a-zA-Z0-9_-]+)'),
    ]

    def detect_type(self, url: str) -> URLType:
        if self.PLAYLIST_PATTERN.search(url):
            return URLType.PLAYLIST
        if any(p.search(url) for p in self.CHANNEL_PATTERNS):
            return URLType.CHANNEL
        if self.VIDEO_PATTERN.search(url):
            return URLType.VIDEO
        return URLType.UNKNOWN

    async def resolve(self, url: str, max_videos: int = 50) -> ResolvedTarget:
        """
        Resolve a URL into individual video targets.

        For playlists: extract all video URLs (up to max_videos).
        For channels: extract the N most recent uploads.
        For videos: return the single URL.
        """
        url_type = self.detect_type(url)

        if url_type == URLType.VIDEO:
            return ResolvedTarget(
                original_url=url,
                url_type=url_type,
                video_urls=[url],
                total_count=1,
            )
        elif url_type == URLType.PLAYLIST:
            videos = await self._resolve_playlist(url, max_videos)
            return ResolvedTarget(
                original_url=url,
                url_type=url_type,
                video_urls=videos,
                total_count=len(videos),
            )
        elif url_type == URLType.CHANNEL:
            videos = await self._resolve_channel(url, max_videos)
            return ResolvedTarget(
                original_url=url,
                url_type=url_type,
                video_urls=videos,
                total_count=len(videos),
            )
        else:
            raise ValueError(f"Unrecognized YouTube URL format: {url}")

    async def _resolve_playlist(self, url: str, max_videos: int) -> List[str]:
        """
        Extract video URLs from a YouTube playlist.

        Strategy: Use Selenium to load the playlist page and scrape video links.
        Alternative: Use yt-dlp --flat-playlist for faster extraction.
        """
        # Primary: Use yt-dlp for reliable extraction
        import asyncio
        import json

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--flat-playlist", "--dump-json",
            "--playlist-items", f"1:{max_videos}",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        videos = []
        for line in stdout.decode().strip().split("\n"):
            if line:
                data = json.loads(line)
                video_id = data.get("id") or data.get("url")
                if video_id:
                    videos.append(f"https://www.youtube.com/watch?v={video_id}")

        return videos[:max_videos]

    async def _resolve_channel(self, url: str, max_videos: int) -> List[str]:
        """
        Extract the most recent video URLs from a YouTube channel.

        Uses yt-dlp to get the channel's uploads playlist.
        """
        import asyncio
        import json

        # yt-dlp automatically resolves channel URLs to their uploads
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--flat-playlist", "--dump-json",
            "--playlist-items", f"1:{max_videos}",
            f"{url}/videos",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        videos = []
        for line in stdout.decode().strip().split("\n"):
            if line:
                data = json.loads(line)
                video_id = data.get("id") or data.get("url")
                if video_id:
                    videos.append(f"https://www.youtube.com/watch?v={video_id}")

        return videos[:max_videos]
```

### 1.4 New Automation Players

```python
# ytgrid/automation/playlist_player.py
from ytgrid.automation.base_player import AutomationPlayer
from ytgrid.automation.url_resolver import URLResolver, URLType
from ytgrid.automation.player import VideoPlayer
from ytgrid.utils.logger import log_info, log_error

class PlaylistPlayer(AutomationPlayer):
    """Plays all videos in a YouTube playlist sequentially."""

    def __init__(self):
        self._resolver = URLResolver()
        self._video_player = VideoPlayer()

    def play_video(self, playlist_url: str, speed: float, loop_count: int) -> bool:
        """
        Resolves the playlist URL and plays each video.

        Each video in the playlist is played `loop_count` times before
        moving to the next video.
        """
        import asyncio
        try:
            resolved = asyncio.run(self._resolver.resolve(playlist_url))
        except Exception as e:
            log_error(f"Failed to resolve playlist: {e}")
            return False

        log_info(f"Playlist resolved: {resolved.total_count} videos found.")

        success_count = 0
        for i, video_url in enumerate(resolved.video_urls, 1):
            log_info(f"Playlist video {i}/{resolved.total_count}: {video_url}")
            try:
                result = self._video_player.play_video(video_url, speed, loop_count)
                if result:
                    success_count += 1
            except Exception as e:
                log_error(f"Error playing playlist video {i}: {e}")

        log_info(
            f"Playlist complete: {success_count}/{resolved.total_count} "
            f"videos played successfully."
        )
        return success_count > 0


class ChannelPlayer(AutomationPlayer):
    """Plays the most recent videos from a YouTube channel."""

    def __init__(self, max_videos: int = 10):
        self._resolver = URLResolver()
        self._video_player = VideoPlayer()
        self._max_videos = max_videos

    def play_video(self, channel_url: str, speed: float, loop_count: int) -> bool:
        import asyncio
        try:
            resolved = asyncio.run(
                self._resolver.resolve(channel_url, max_videos=self._max_videos)
            )
        except Exception as e:
            log_error(f"Failed to resolve channel: {e}")
            return False

        log_info(f"Channel resolved: {resolved.total_count} videos found.")

        success_count = 0
        for i, video_url in enumerate(resolved.video_urls, 1):
            log_info(f"Channel video {i}/{resolved.total_count}: {video_url}")
            try:
                result = self._video_player.play_video(video_url, speed, loop_count)
                if result:
                    success_count += 1
            except Exception as e:
                log_error(f"Error playing channel video {i}: {e}")

        return success_count > 0
```

### 1.5 Register New Players

```python
# Updated task_manager.py
from ytgrid.automation.playlist_player import PlaylistPlayer, ChannelPlayer

AUTOMATION_PLAYERS: Dict[str, object] = {
    "video": VideoPlayer,
    "playlist": PlaylistPlayer,
    "channel": ChannelPlayer,
}
```

### 1.6 Dependencies

```bash
# yt-dlp is required for playlist/channel resolution
pip install yt-dlp
# OR add to pyproject.toml:
# "yt-dlp" (optional dependency group)
```

### 1.7 CLI Updates

```bash
# Playlist support:
ytgrid start --session-id pl1 --url "https://youtube.com/playlist?list=PLxxx" --task_type playlist

# Channel support:
ytgrid start --session-id ch1 --url "https://youtube.com/@channelname" --task_type channel --loops 2
```

---

## 2. Microservices Architecture Migration

### 2.1 Current Monolith Architecture

```
┌────────────────────────────────────────┐
│           YTGrid Monolith              │
│                                        │
│  ┌──────────┐  ┌────────────────────┐  │
│  │ FastAPI   │  │ TaskManager +      │  │
│  │ Routes    │──│ multiprocessing    │  │
│  └──────────┘  └────────────────────┘  │
│  ┌──────────┐  ┌────────────────────┐  │
│  │ Selenium  │  │ Celery Workers    │  │
│  │ Browsers  │  │ (optional)        │  │
│  └──────────┘  └────────────────────┘  │
└────────────────────────────────────────┘
```

### 2.2 Target Microservices Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                               │
│                    (Kong / Traefik / Nginx)                       │
│                Auth │ Rate Limit │ Routing                        │
└─────────┬───────────┼─────────────┼──────────┬──────────────────┘
          │           │             │          │
    ┌─────▼─────┐ ┌───▼───┐ ┌──────▼────┐ ┌───▼────────┐
    │ API Svc   │ │ Auth  │ │ Profile   │ │ Dashboard  │
    │ (FastAPI) │ │ Svc   │ │ Svc       │ │ Svc        │
    │           │ │       │ │ (SQLite/  │ │ (SSE/WS)   │
    │ /tasks    │ │ JWT   │ │  Postgres)│ │            │
    │ /sessions │ │ OAuth │ │           │ │            │
    └─────┬─────┘ └───────┘ └───────────┘ └────────────┘
          │
          │ Redis Queue
          ▼
    ┌───────────────────────────────────────────┐
    │          Worker Pool (Celery)              │
    │                                           │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
    │  │ Worker 1 │ │ Worker 2 │ │ Worker N │  │
    │  │ Chrome   │ │ Chrome   │ │ Chrome   │  │
    │  │ Selenium │ │ Selenium │ │ Selenium │  │
    │  └──────────┘ └──────────┘ └──────────┘  │
    └───────────────────────────────────────────┘
```

### 2.3 Service Boundaries

| Service | Responsibility | Protocol | Data Store |
|---------|---------------|----------|------------|
| **API Service** | HTTP endpoints, input validation, task dispatch | REST (JSON) | Stateless (Redis for temp state) |
| **Auth Service** | Authentication, API key management, rate limiting | gRPC or REST | SQLite / Redis |
| **Profile Service** | CRUD profiles, execution history, analytics | REST | SQLite → PostgreSQL |
| **Worker Service** | Execute Selenium automation, proxy management | Celery (AMQP/Redis) | None (ephemeral) |
| **Dashboard Service** | Real-time status, SSE/WebSocket streaming | SSE/WS | Redis PubSub |
| **Optimizer Service** | Resource monitoring, tmp cleanup, zombie reaping | Internal daemon | /proc filesystem |

### 2.4 Migration Strategy: Strangler Fig Pattern

The migration follows a **phased Strangler Fig** approach — each service is extracted one at a time while the monolith continues to serve traffic.

```
Phase 1 (v3.1): Extract Auth → separate middleware (no separate service)
Phase 2 (v3.2): Extract Profiles → separate FastAPI service + DB
Phase 3 (v3.5): Extract Workers → dedicated Celery worker containers
Phase 4 (v4.0): Extract API + Dashboard → full microservices
```

#### Phase 1: Auth Extraction

```yaml
# docker-compose.yml addition
services:
  api:
    # Existing ytgrid service
    environment:
      - AUTH_MODE=api_key   # api_key | jwt | none
```

The auth layer starts as middleware within the monolith (`ytgrid/backend/auth.py`) and is later promoted to a standalone service.

#### Phase 2: Profile Service Extraction

```yaml
  profile-service:
    build:
      context: .
      dockerfile: Dockerfile.profile
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=sqlite:///data/profiles.db
    volumes:
      - profile-data:/data
```

The API service proxies profile requests:
```python
# In API service, profile routes become a forwarding proxy:
@router.post("/profiles/")
async def create_profile(request: CreateProfileRequest):
    async with httpx.AsyncClient() as client:
        resp = await client.post("http://profile-service:8001/profiles/", json=request.dict())
    return resp.json()
```

#### Phase 3: Worker Pool Extraction

```yaml
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    deploy:
      replicas: 3            # Horizontal scaling
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - YTGRID_HEADLESS_MODE=True
    depends_on:
      - redis
```

**Worker Dockerfile** (specialized for Chrome + Selenium):
```dockerfile
FROM python:3.12-slim

# Install Chrome
RUN apt-get update && apt-get install -y google-chrome-stable

# Install only worker dependencies
COPY requirements-worker.txt .
RUN pip install -r requirements-worker.txt

COPY ytgrid/automation /app/ytgrid/automation
COPY ytgrid/utils /app/ytgrid/utils
COPY ytgrid/proxy /app/ytgrid/proxy
COPY ytgrid/backend/celery_app.py /app/ytgrid/backend/celery_app.py
COPY ytgrid/backend/tasks.py /app/ytgrid/backend/tasks.py

WORKDIR /app
CMD ["celery", "-A", "ytgrid.backend.celery_app", "worker", "--loglevel=info", "--concurrency=2"]
```

### 2.5 Inter-Service Communication

```
┌──────────┐   REST    ┌───────────────┐
│ API Svc  │──────────▶│ Profile Svc   │
└────┬─────┘           └───────────────┘
     │
     │ Redis Queue (Celery)
     ▼
┌──────────┐   Redis   ┌───────────────┐
│ Workers  │──PubSub──▶│ Dashboard Svc │
└──────────┘           └───────────────┘
```

- **API → Workers:** Celery task dispatch via Redis broker.
- **Workers → Dashboard:** Redis PubSub for real-time status updates.
- **API → Profile:** REST over internal Docker network.

### 2.6 Scaling Characteristics

| Service | Scaling Model | Bottleneck | Strategy |
|---------|--------------|------------|----------|
| API | Horizontal (stateless) | Request rate | Add replicas behind load balancer |
| Workers | Horizontal (GPU/CPU bound) | Chrome memory (~500MB/instance) | Scale replicas; limit concurrency per worker |
| Profile | Vertical (DB-bound) | SQLite write lock | Migrate to PostgreSQL for multi-writer |
| Dashboard | Horizontal (connection-bound) | WebSocket connections | Use Redis PubSub to decouple from workers |

---

## 3. Real-Time Dashboard (Web UI)

### 3.1 Overview

A browser-based dashboard that provides real-time visibility into running automation sessions, system health, proxy pool status, and execution history.

### 3.2 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | FastAPI + SSE | Already in use; SSE is simpler than WebSocket for unidirectional data |
| Frontend | Vanilla HTML/CSS/JS | No build step; serves directly from FastAPI `StaticFiles` |
| Charts | Chart.js | Lightweight; no npm required |
| State | SSE EventSource | Native browser API; auto-reconnects |

### 3.3 Dashboard Pages

#### Page 1: Session Overview
```
┌──────────────────────────────────────────────────────┐
│  YTGrid Dashboard                     [■] System OK  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Active Sessions: 3        Completed: 47             │
│  ┌────────────┬──────────┬────────┬─────────┐        │
│  │ Session ID │ URL      │ Loop   │ Status  │        │
│  ├────────────┼──────────┼────────┼─────────┤        │
│  │ session_1  │ ...XYZ   │ 3/10   │ ▶ Play  │        │
│  │ session_2  │ ...ABC   │ 7/7    │ ✓ Done  │        │
│  │ session_3  │ ...DEF   │ 1/5    │ ▶ Play  │        │
│  └────────────┴──────────┴────────┴─────────┘        │
│                                                      │
│  [Start New Session]  [Stop All]  [Export CSV]       │
└──────────────────────────────────────────────────────┘
```

#### Page 2: System Health
```
┌──────────────────────────────────────────────────────┐
│  System Resources                                     │
│                                                      │
│  CPU  ████████░░░░░░░░  52%                          │
│  RAM  ██████████░░░░░░  68%                          │
│  DISK ████░░░░░░░░░░░░  28%                          │
│                                                      │
│  Proxy Pool: 12 healthy / 3 degraded / 1 dead        │
│  Temp Dirs: 4 active / 0 stale                       │
│  Chrome PIDs: 3 registered / 0 zombie                │
└──────────────────────────────────────────────────────┘
```

### 3.4 SSE Endpoints for Dashboard

```python
# ytgrid/backend/routes/dashboard.py (NEW)
import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ytgrid.backend.task_manager import task_manager
from ytgrid.optimizer.system_monitor import get_system_resources

router = APIRouter()

@router.get("/stream/sessions")
async def stream_sessions():
    async def generator():
        while True:
            sessions = task_manager.get_active_sessions()
            yield f"data: {json.dumps({'sessions': sessions})}\n\n"
            await asyncio.sleep(2)
    return StreamingResponse(generator(), media_type="text/event-stream")

@router.get("/stream/health")
async def stream_health():
    async def generator():
        while True:
            resources = get_system_resources()
            yield f"data: {json.dumps(resources.__dict__)}\n\n"
            await asyncio.sleep(5)
    return StreamingResponse(generator(), media_type="text/event-stream")
```

### 3.5 Frontend SSE Client

```javascript
// static/js/dashboard.js
const sessionsSource = new EventSource('/dashboard/stream/sessions');
sessionsSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateSessionTable(data.sessions);
};

const healthSource = new EventSource('/dashboard/stream/health');
healthSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateResourceBars(data);
};
```

### 3.6 Serving Static Files

```python
# In main.py
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="ytgrid/backend/static"), name="static")
```

---

## Dependency Summary

| Feature | New Dependencies | Impact |
|---------|-----------------|--------|
| Playlist/Channel | `yt-dlp` | ~15MB; CLI tool for YouTube URL resolution |
| Persistence | `aiosqlite` | ~50KB; async SQLite driver |
| Dashboard | None | Vanilla HTML/CSS/JS + Chart.js (CDN) |
| Microservices | `httpx` (already present) | Inter-service HTTP calls |
| Proxy | None new (uses `requests`, `threading`) | Built on stdlib + existing deps |
