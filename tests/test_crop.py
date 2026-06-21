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
