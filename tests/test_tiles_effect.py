import numpy as np
from unittest.mock import MagicMock
from src.effects.video.tiles import apply, crop_to_fit_frame


def test_crop_to_fit_frame():
    # Landscape frame 800x600, target landscape tile 200x100 (AR = 2)
    frame = np.zeros((600, 800, 3), dtype=np.uint8)
    res = crop_to_fit_frame(frame, 200, 100)
    assert res.shape == (100, 200, 3)

    # Portrait frame 600x800, target portrait tile 100x200 (AR = 0.5)
    frame2 = np.zeros((800, 600, 3), dtype=np.uint8)
    res2 = crop_to_fit_frame(frame2, 100, 200)
    assert res2.shape == (200, 100, 3)

    # Test safe dtype conversion for int64 arrays (<i8)
    frame_i8 = np.zeros((600, 800, 3), dtype=np.int64)
    res_i8 = crop_to_fit_frame(frame_i8, 200, 100)
    assert res_i8.dtype == np.uint8
    assert res_i8.shape == (100, 200, 3)

    # Test safe boundary handling for zero target dimensions
    res_zero = crop_to_fit_frame(frame, 0, 0)
    assert res_zero.shape == (1, 1, 3)


def test_tiles_apply_landscape():
    # Mock clip of size 800x600 (Landscape)
    clip = MagicMock()
    clip.duration = 4.0
    dummy_frame = np.zeros((600, 800, 3), dtype=np.uint8)
    clip.get_frame = MagicMock(return_value=dummy_frame)
    clip.fl = MagicMock(return_value=clip)

    # Test strength = 1 -> Should be 2 columns, 1 row (2x1)
    apply(clip, 1.0)
    clip.fl.assert_called_once()

    # Extract the filter function passed to fl
    filter_func = clip.fl.call_args[0][0]

    # Mock get_frame function that is passed to the filter at run time
    get_frame = MagicMock(return_value=dummy_frame)
    res_frame = filter_func(get_frame, 0.0)
    assert res_frame.shape == (600, 800, 3)


def test_tiles_apply_portrait():
    # Mock clip of size 600x800 (Portrait)
    clip = MagicMock()
    clip.duration = 4.0
    dummy_frame = np.zeros((800, 600, 3), dtype=np.uint8)
    clip.get_frame = MagicMock(return_value=dummy_frame)
    clip.fl = MagicMock(return_value=clip)

    # Test strength = 2 -> Should be 2 columns, 2 rows (2x2)
    # base for portrait is 1 col, 2 rows. strength=2 increment 1 adds 1 col -> 2x2.
    apply(clip, 2.0)
    clip.fl.assert_called_once()

    filter_func = clip.fl.call_args[0][0]
    get_frame = MagicMock(return_value=dummy_frame)
    res_frame = filter_func(get_frame, 0.0)
    assert res_frame.shape == (800, 600, 3)
