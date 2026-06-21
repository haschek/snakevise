from unittest.mock import MagicMock, patch
import numpy as np
from moviepy.editor import VideoClip
from src.config import ConfigResolver
from src.reframing import reframe


def test_crop_argument_resolution():
    args = MagicMock()
    args.loadproject = None
    args.preset = None
    args.bpm = None
    args.snippetbeats = None
    args.modus = None
    args.vfx = []
    args.input = []
    args.res = ((1920, 1080), 24)
    args.codec = "libx264"
    args.optimize = False
    args.audio = None
    args.duration = None
    args.length = None

    # Test default
    args.crop = None
    config_default = ConfigResolver.resolve(args)
    assert config_default["crop"] == "crop-to-fit"

    # Test explicit override
    args.crop = "stretch"
    config_override = ConfigResolver.resolve(args)
    assert config_override["crop"] == "stretch"


def test_reframe_methods():
    clip = MagicMock(spec=VideoClip)
    clip.size = (800, 600)
    clip.resize = MagicMock(return_value=clip)
    clip.fx = MagicMock(return_value=clip)

    # Test reframe with stretch (fallback to clip.resize)
    reframe(clip, (1920, 1080), method="stretch")
    clip.resize.assert_called_with(newsize=(1920, 1080))


def test_reframe_slideover():
    clip = MagicMock(spec=VideoClip)
    clip.size = (800, 600)
    clip.duration = 4.0
    clip.fl = MagicMock(return_value=clip)
    clip.resize = MagicMock(return_value=clip)

    # Test reframe with slideover
    reframe(clip, (1920, 1080), method="slideover")
    clip.fl.assert_called_once()
    clip.resize.assert_called_with(newsize=(1920, 1080))


def test_reframe_slideover_directions():
    clip = MagicMock(spec=VideoClip)
    clip.size = (800, 600)  # w_s = 800, h_s = 600 (ar = 1.33)
    clip.duration = 4.0
    clip.fl = MagicMock(return_value=clip)
    clip.resize = MagicMock(return_value=clip)

    dummy_frame = np.zeros((600, 800, 3), dtype=np.uint8)
    get_frame = MagicMock(return_value=dummy_frame)

    # We use a target resolution of 800x300 (ar = 2.66 > 1.33)
    # Source is taller than target -> vertical slide (top to bottom or bottom to top)
    # Target height = 800 / 2.66 = 300. Slide range on y is 600 - 300 = 300.

    # Test forward direction (top to bottom)
    with patch("random.choice", return_value="forward"):
        reframe(clip, (800, 300), method="slideover")
        make_frame = clip.fl.call_args[0][0]

        # at t=0, y1 should be 0 (top)
        res_t0 = make_frame(get_frame, 0.0)
        assert res_t0.shape == (300, 800, 3)

        # at t=4, y1 should be 300 (bottom)
        res_t4 = make_frame(get_frame, 4.0)
        assert res_t4.shape == (300, 800, 3)

    # Test reverse direction (bottom to top)
    clip.fl.reset_mock()
    with patch("random.choice", return_value="reverse"):
        reframe(clip, (800, 300), method="slideover")
        make_frame = clip.fl.call_args[0][0]

        # at t=0, y1 should be 300 (bottom)
        res_t0 = make_frame(get_frame, 0.0)
        assert res_t0.shape == (300, 800, 3)

        # at t=4, y1 should be 0 (top)
        res_t4 = make_frame(get_frame, 4.0)
        assert res_t4.shape == (300, 800, 3)


@patch("src.reframing.duplicate.clips_array")
def test_reframe_duplicate(mock_clips_array):
    # Scenario 1: calculated cols = 3 (already odd)
    clip = MagicMock(spec=VideoClip)
    clip.size = (400, 600)  # taller/narrower (ar = 0.66)

    # Mock scaled clip returned by resize
    clip_scaled = MagicMock(spec=VideoClip)
    clip_scaled.size = (720, 1080)
    clip.resize = MagicMock(return_value=clip_scaled)

    # Mock composite clip returned by clips_array
    composite = MagicMock(spec=VideoClip)
    composite.size = (2160, 1080)
    mock_clips_array.return_value = composite

    # Mock cropped clip
    final_clip = MagicMock(spec=VideoClip)
    composite.crop = MagicMock(return_value=final_clip)

    res = reframe(clip, (1920, 1080), method="duplicate")

    # Resize should be called with height=1080 (matching target height)
    clip.resize.assert_called_with(height=1080)

    # clips_array should be called with one row containing 3 copies (since 1920/720 = 2.66 -> 3)
    mock_clips_array.assert_called_with([[clip_scaled, clip_scaled, clip_scaled]])

    # crop should be called centered: x1 = (2160 - 1920) / 2 = 120
    composite.crop.assert_called_with(x1=120.0, y1=0.0, width=1920, height=1080)

    assert res == final_clip

    # Scenario 2: calculated cols = 2 (even) -> bumped to 3 (odd)
    clip2 = MagicMock(spec=VideoClip)
    clip2.size = (400, 450)  # taller/narrower (ar = 0.88)

    clip_scaled2 = MagicMock(spec=VideoClip)
    clip_scaled2.size = (960, 1080)
    clip2.resize = MagicMock(return_value=clip_scaled2)

    composite2 = MagicMock(spec=VideoClip)
    composite2.size = (2880, 1080)
    mock_clips_array.return_value = composite2

    final_clip2 = MagicMock(spec=VideoClip)
    composite2.crop = MagicMock(return_value=final_clip2)

    res2 = reframe(clip2, (1920, 1080), method="duplicate")

    clip2.resize.assert_called_with(height=1080)
    # columns calculated = 1920 / 960 = 2 -> bumped to 3
    mock_clips_array.assert_called_with([[clip_scaled2, clip_scaled2, clip_scaled2]])
    composite2.crop.assert_called_with(x1=480.0, y1=0.0, width=1920, height=1080)
    assert res2 == final_clip2
