import pytest
from ytgrid.automation.player import VideoPlayer

@pytest.fixture
def sample_video():
    return {
        "url": "https://www.youtube.com/watch?v=UXFBUZEpnrc",
        "speed": 1.0,
        "loop_count": 1
    }

def test_play_video(sample_video):
    """
    Test if VideoPlayer can play a video successfully.
    
    Note: This test may actually invoke a browser session. In a real CI environment,
    consider mocking Selenium's behavior.
    """
    player = VideoPlayer()
    # Depending on how play_video is implemented, you might want to simulate or mock browser actions.
    success = player.play_video(
        sample_video["url"],
        sample_video["speed"],
        sample_video["loop_count"]
    )
    assert success is True
