import pytest
from ytgrid.automation.player import play_video

@pytest.mark.parametrize("url, speed, loops", [
    ("https://www.youtube.com/watch?v=tCDvOQI3pco", 1.0, 1),
    ("https://www.youtube.com/watch?v=zU9y354XAgM", 1.5, 2)
])
def test_play_video(url, speed, loops):
    """Test if video automation runs without errors."""
    try:
        play_video(url, speed, loops)
        assert True  # If execution reaches here, test passed
    except Exception as e:
        pytest.fail(f"Automation failed: {e}")
