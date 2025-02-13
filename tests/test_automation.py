import pytest
from unittest.mock import patch
from ytgrid.automation.player import VideoPlayer

@pytest.fixture
def sample_video():
    """Mock video input for testing."""
    return {
        "url": "https://www.youtube.com/watch?v=UXFBUZEpnrc",
        "speed": 1.0,
        "loop_count": 1
    }

@patch.object(VideoPlayer, "play_video", return_value=True)
def test_play_video(mock_play_video, sample_video):
    """
    Test if VideoPlayer can play a video successfully (mocked).
    
    - This prevents Selenium from launching a browser during tests.
    """
    player = VideoPlayer()
    success = player.play_video(
        sample_video["url"],
        sample_video["speed"],
        sample_video["loop_count"]
    )
    assert success is True
    mock_play_video.assert_called_once_with(
        sample_video["url"],
        sample_video["speed"],
        sample_video["loop_count"]
    )
