from ytgrid.automation.url_resolver import URLResolver


def test_get_type_video():
    assert URLResolver.get_type("https://www.youtube.com/watch?v=abc123") == "video"


def test_get_type_playlist():
    assert URLResolver.get_type(
        "https://www.youtube.com/playlist?list=PL123"
    ) == "playlist"
    assert URLResolver.get_type(
        "https://www.youtube.com/watch?v=abc&list=PL123"
    ) == "playlist"


def test_get_type_channel():
    assert URLResolver.get_type("https://www.youtube.com/@SomeChannel") == "channel"
    assert URLResolver.get_type("https://www.youtube.com/channel/UC123") == "channel"
    assert URLResolver.get_type("https://www.youtube.com/c/SomeName") == "channel"
    assert URLResolver.get_type("https://www.youtube.com/user/Legacy") == "channel"


def test_normalize_video_url_from_flat_id():
    entry = {"id": "dQw4w9WgXcQ", "title": "Video"}
    assert URLResolver.normalize_video_url(entry) == (
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )


def test_normalize_video_url_from_flat_url():
    entry = {"url": "dQw4w9WgXcQ", "title": "Video"}
    assert URLResolver.normalize_video_url(entry) == (
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )


def test_normalize_video_url_keeps_watch_url():
    entry = {"webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    assert URLResolver.normalize_video_url(entry) == (
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )


def test_resolve_normalizes_playlist_entries(monkeypatch):
    class FakeYDL:
        def __init__(self, options):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            return {
                "entries": [
                    {"id": "dQw4w9WgXcQ", "title": "One"},
                    {"url": "OaOK76hiW8I", "title": "Two"},
                ]
            }

    monkeypatch.setattr("ytgrid.automation.url_resolver.yt_dlp.YoutubeDL", FakeYDL)
    resolved = URLResolver.resolve("https://www.youtube.com/playlist?list=PL123")
    assert [item["url"] for item in resolved] == [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=OaOK76hiW8I",
    ]
