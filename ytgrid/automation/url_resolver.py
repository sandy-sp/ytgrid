import yt_dlp
import re
from typing import List, Dict, Any
from ytgrid.utils.logger import log_info, log_error

class URLResolver:
    """Resolves YouTube URLs into a list of constituent videos using yt-dlp."""

    @staticmethod
    def get_type(url: str) -> str:
        if "playlist?list=" in url or "&list=" in url:
            return "playlist"
        if "/user/" in url or "/c/" in url or "/channel/" in url or "/@" in url:
            return "channel"
        return "video"

    @staticmethod
    def normalize_video_url(entry: Dict[str, Any]) -> str | None:
        """Return a full YouTube watch URL from a yt-dlp flat entry."""
        webpage_url = entry.get("webpage_url")
        if webpage_url and re.search(r"(youtube\.com/watch\?v=|youtu\.be/)", webpage_url):
            return webpage_url

        raw_url = entry.get("url") or entry.get("id")
        if not raw_url:
            return None
        raw_url = str(raw_url)

        if raw_url.startswith("http"):
            if re.search(r"(youtube\.com/watch\?v=|youtu\.be/)", raw_url):
                return raw_url
            return None

        video_id = raw_url
        if ":" in video_id:
            video_id = video_id.rsplit(":", 1)[-1]
        if re.fullmatch(r"[\w-]{6,}", video_id):
            return f"https://www.youtube.com/watch?v={video_id}"
        return None

    @staticmethod
    def resolve(url: str) -> List[Dict[str, Any]]:
        url_type = URLResolver.get_type(url)
        log_info(f"Resolving {url_type} URL: {url}")

        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True
        }

        results = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and 'entries' in info:
                    for entry in info['entries']:
                        video_url = URLResolver.normalize_video_url(entry or {})
                        if video_url:
                            results.append({
                                'url': video_url,
                                'title': entry.get('title', 'Unknown Title')
                            })
                elif info:
                    video_url = URLResolver.normalize_video_url(info) or info.get('webpage_url', url)
                    results.append({
                        'url': video_url,
                        'title': info.get('title', 'Unknown Title')
                    })
        except Exception as e:
            log_error(f"Failed to resolve URL {url}: {e}")

        return results
