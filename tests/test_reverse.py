from unittest.mock import MagicMock
from moviepy.editor import VideoClip
from src.effects.video.reverse import apply, safe_time_mirror


import numpy as np


def test_safe_time_mirror():
    # Mock clip
    clip = MagicMock(spec=VideoClip)
    clip.duration = 4.0

    # Call safe_time_mirror
    _ = safe_time_mirror(clip)

    # Verify fl_time was called on the mock clip
    clip.fl_time.assert_called_once()
    func = clip.fl_time.call_args[0][0]

    # Test the lambda function bounds with scalar input
    assert func(0.0) == 4.0 - 1e-6
    assert func(2.0) == 2.0 - 1e-6
    assert func(4.0) == 0.0

    # Test the lambda function bounds with numpy array input (used in audio/some clipping pipelines)
    t_arr = np.array([0.0, 2.0, 4.0])
    res_arr = func(t_arr)
    assert np.allclose(res_arr, np.array([4.0 - 1e-6, 2.0 - 1e-6, 0.0]))


def test_apply_no_effect_duration():
    # If duration is None or too small, it should return the original clip
    clip = MagicMock(spec=VideoClip)
    clip.duration = None
    res = apply(clip, 5.0, 120.0)
    assert res == clip

    clip2 = MagicMock(spec=VideoClip)
    clip2.duration = 0.02
    res2 = apply(clip2, 5.0, 120.0)
    assert res2 == clip2


def test_apply_zero_strength():
    clip = MagicMock(spec=VideoClip)
    clip.duration = 4.0
    res = apply(clip, 0.0, 120.0)
    assert res == clip
