import pytest
from ytgrid.automation.player import VideoPlayer

@pytest.fixture
def sample_video():
    return {
        "url": "https://www.youtube.com/watch?v=UXFBUZEpnrc",
        "speed": 1.5,
        "loop_count": 2
    }

def test_play_video(sample_video):
    """Test if VideoPlayer can play a video successfully."""
    player = VideoPlayer()
    success = player.play_video(
        sample_video["url"],
        sample_video["speed"],
        sample_video["loop_count"]
    )
    assert success is True  # Should return True on successful execution
