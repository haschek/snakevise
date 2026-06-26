from unittest.mock import MagicMock, patch
from src.utils import parse_sub_settings


def test_subtitle_parsing_combinations():
    # Format: (input_settings, expected_h_align, expected_v_align)
    test_cases = [
        # Horizontal alignments
        ("align:left", "left", "bottom"),
        ("align:right", "right", "bottom"),
        ("align:center", "center", "bottom"),
        ("align:middle", "center", "bottom"),
        ("align:start", "left", "bottom"),
        ("align:end", "right", "bottom"),
        ("align : left", "left", "bottom"),  # Test spacing
        # Vertical lines (Keywords)
        ("line:top", "center", "top"),
        ("line:0", "center", "top"),
        ("line:middle", "center", "center"),
        ("line:bottom", "center", "bottom"),
        ("line : middle", "center", "center"),  # Test spacing
        # Combinations
        ("align:left line:top", "left", "top"),
        ("align:right line:middle", "right", "center"),
        ("align:center line:bottom", "center", "bottom"),
    ]

    for settings, exp_h, exp_v in test_cases:
        h_align, v_align = parse_sub_settings(settings)
        assert h_align == exp_h, f"Failed H-align for '{settings}'"
        assert v_align == exp_v, f"Failed V-align for '{settings}'"


def test_default_subtitle_parsing():
    # Empty settings should return defaults
    h_align, v_align = parse_sub_settings("")
    assert h_align == "center"
    assert v_align == "bottom"


@patch("src.renderer.TextClip")
def test_subtitle_two_pass_rendering(mock_text_clip):
    # Mock TextClip instance
    mock_clip_instance = MagicMock()
    mock_clip_instance.w = 100
    mock_clip_instance.h = 20
    mock_clip_instance.set_start.return_value = mock_clip_instance
    mock_clip_instance.set_duration.return_value = mock_clip_instance
    mock_clip_instance.set_position.return_value = mock_clip_instance
    mock_text_clip.return_value = mock_clip_instance

    from unittest.mock import mock_open
    from pathlib import Path
    from src.models import RenderConfig
    from src.renderer import Renderer

    # Case 1: base_stroke > 0 -> should create two TextClips (stroke background, fill foreground)
    config_stroke = RenderConfig(
        output_path=Path("output.mp4"),
        temp_dir=Path("temp"),
        crop=[],
        resolution=(1920, 1080),
        fps=24,
        codec="libx264",
        optimize=False,
        audio_path=None,
        subtitles_path=Path("dummy_subs.vtt"),
        subtitle_fonts=["Arial"],
        subtitle_fontsizes=[24.0],
        subtitle_strokewidths=[2.0],
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        target_duration=None,
        fade_in=0.0,
        fade_out=0.0,
        fade_color="black",
        dry_run=False,
        bpm=120.0,
    )

    renderer_stroke = Renderer(config_stroke)
    vtt_content = "WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:center line:bottom\nHello World\n\n"
    mock_video = MagicMock()
    mock_video.w = 1920
    mock_video.h = 1080
    mock_video.duration = 10.0

    clips_to_close = []
    with patch("builtins.open", mock_open(read_data=vtt_content)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer_stroke._apply_subtitles(mock_video, clips_to_close)

    # With base_stroke=2.0 (>0), it should call TextClip twice for the subtitle cue:
    # 1. stroke TextClip
    # 2. fill TextClip
    assert mock_text_clip.call_count == 2

    # Check first call (stroke background) arguments:
    first_call_args = mock_text_clip.call_args_list[0][1]
    assert first_call_args.get("stroke_color") == "black"
    assert first_call_args.get("stroke_width") == 4.0  # 2 * base_stroke

    # Check second call (fill foreground) arguments:
    second_call_args = mock_text_clip.call_args_list[1][1]
    assert "stroke_color" not in second_call_args
    assert "stroke_width" not in second_call_args

    # Reset mock for Case 2
    mock_text_clip.reset_mock()

    # Case 2: base_stroke == 0 -> should only create one TextClip (fill foreground only)
    config_no_stroke = RenderConfig(
        output_path=Path("output.mp4"),
        temp_dir=Path("temp"),
        crop=[],
        resolution=(1920, 1080),
        fps=24,
        codec="libx264",
        optimize=False,
        audio_path=None,
        subtitles_path=Path("dummy_subs.vtt"),
        subtitle_fonts=["Arial"],
        subtitle_fontsizes=[24.0],
        subtitle_strokewidths=[0.0],
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        target_duration=None,
        fade_in=0.0,
        fade_out=0.0,
        fade_color="black",
        dry_run=False,
        bpm=120.0,
    )

    renderer_no_stroke = Renderer(config_no_stroke)
    clips_to_close_no = []
    with patch("builtins.open", mock_open(read_data=vtt_content)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer_no_stroke._apply_subtitles(mock_video, clips_to_close_no)

    # Should only call TextClip once (no stroke background needed)
    assert mock_text_clip.call_count == 1
    call_args = mock_text_clip.call_args[1]
    assert "stroke_color" not in call_args
    assert "stroke_width" not in call_args


@patch("src.renderer.TextClip")
def test_subtitle_effects_and_slide_in(mock_text_clip):
    # Mock TextClip instance
    mock_clip_instance = MagicMock()
    mock_clip_instance.w = 100
    mock_clip_instance.h = 20
    mock_clip_instance.set_start.return_value = mock_clip_instance
    mock_clip_instance.set_duration.return_value = mock_clip_instance
    mock_clip_instance.pos = None
    mock_clip_instance.mask = None

    def set_position_side_effect(pos):
        mock_clip_instance.pos = pos
        return mock_clip_instance

    mock_clip_instance.set_position.side_effect = set_position_side_effect
    mock_clip_instance.fadein.return_value = mock_clip_instance
    mock_clip_instance.fadeout.return_value = mock_clip_instance
    mock_clip_instance.duration = 2.0
    mock_text_clip.return_value = mock_clip_instance

    from unittest.mock import mock_open
    from pathlib import Path
    from src.models import RenderConfig
    from src.renderer import Renderer

    # Config with global defaults
    config = RenderConfig(
        output_path=Path("output.mp4"),
        temp_dir=Path("temp"),
        crop=[],
        resolution=(1920, 1080),
        fps=24,
        codec="libx264",
        optimize=False,
        audio_path=None,
        subtitles_path=Path("dummy_subs.vtt"),
        subtitle_fonts=["Arial"],
        subtitle_fontsizes=[24.0],
        subtitle_strokewidths=[0.0],
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        subtitle_vfx=[
            {"name": "fadein", "chance": 100.0, "strength_range": (0.5, 0.5)},
            {"name": "fadeout", "chance": 100.0, "strength_range": (0.3, 0.3)},
            {
                "name": "slidein",
                "chance": 100.0,
                "strength_range": (5.0, 5.0),
            },  # left, slow (1.0s)
            {
                "name": "slideout",
                "chance": 100.0,
                "strength_range": (8.0, 8.0),
            },  # right, fast (0.3s)
        ],
        subtitle_vfx_chance=100.0,
        subtitle_vfx_intensity="1..3",
        subtitle_vfx_maximum=None,
        subtitle_vfx_order="linear",
        target_duration=None,
        fade_in=0.0,
        fade_out=0.0,
        fade_color="black",
        dry_run=False,
        bpm=120.0,
    )

    renderer = Renderer(config)
    mock_video = MagicMock()
    mock_video.w = 1920
    mock_video.h = 1080
    mock_video.duration = 10.0

    # Case 1: VTT Cue with overridden values: fadein=0.8, fadeout=0.4, slidein=top:0.2, slideout=bottom:0.3
    vtt_content = "WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:center line:bottom vfx:fadein:0.8 vfx:fadeout:0.4 vfx:slidein:top:0.2 vfx:slideout:bottom:0.3\nHello World\n\n"

    clips_to_close = []
    with patch("builtins.open", mock_open(read_data=vtt_content)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer._apply_subtitles(mock_video, clips_to_close)

    # 1. Verify fadein was called with 0.064 (overridden) instead of 0.5 (global)
    import pytest

    assert mock_clip_instance.fadein.call_args[0][0] == pytest.approx(0.064)

    # 2. Verify fadeout was called with 0.032 (overridden) instead of 0.3 (global)
    assert mock_clip_instance.fadeout.call_args[0][0] == pytest.approx(0.032)

    # 3. Verify set_position was called with a callable function
    called_pos = mock_clip_instance.set_position.call_args[0][0]
    assert callable(called_pos)

    # 4. Check coordinates returned by pos_fn at t=0 (should be top-slide start)
    # Starts at -txt_fill.h = -20 (y), and target_x = (1920 - 100)/2 = 910
    assert called_pos(0) == (910, -20)
    # At t=0.4 (ends slide-in) and later, it should be at target_y = 1080 - 20 - 1080*0.05 = 1006
    assert called_pos(0.4) == (910, 1006)
    # At t=2.0 (cue end, slides out to bottom)
    assert called_pos(2.0) == (910, 1080)

    # Case 2: Use global settings (no cue overrides)
    mock_clip_instance.fadein.reset_mock()
    mock_clip_instance.fadeout.reset_mock()
    mock_clip_instance.set_position.reset_mock()

    vtt_content_global = (
        "WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:left line:top\nHello World\n\n"
    )
    clips_to_close_global = []
    with patch("builtins.open", mock_open(read_data=vtt_content_global)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer._apply_subtitles(mock_video, clips_to_close_global)

    # Global fadein strength was 0.5 -> duration = 2.0 * (0.5 * 0.04) = 0.04
    # Global fadeout strength was 0.3 -> duration = 2.0 * (0.3 * 0.04) = 0.024
    assert mock_clip_instance.fadein.call_args[0][0] == pytest.approx(0.04)
    assert mock_clip_instance.fadeout.call_args[0][0] == pytest.approx(0.024)

    called_pos_global = mock_clip_instance.set_position.call_args[0][0]
    assert callable(called_pos_global)
    # Global slide direction is left, duration is 0.5s (25% of 2.0s, from strength 5.0)
    # Target x for align:left is int(video.w * 0.05) = 96
    # Target y for line:top is int(video.h * 0.05) = 54
    # Starts at -txt_fill.w = -100 (x), target_y = 54
    assert called_pos_global(0) == (-100, 54)
    # At t=0.2 (mid slide-in) x should be 25
    assert called_pos_global(0.2) == (25, 54)
    # Ends slide-in at t=0.5
    assert called_pos_global(0.4) == (88, 54)
    # Slides out to right at t=2.0 (duration of cue is 2.0s, slideout is fast: 12% of 2.0s = 0.24s)
    # Ends slide-out at t=2.0 -> target_x + video.w - target_x = 1920
    assert called_pos_global(2.0) == (1920, 54)

    # Case 3: Test random direction selection (strength 9 and 10)
    mock_clip_instance.fadein.reset_mock()
    mock_clip_instance.fadeout.reset_mock()
    mock_clip_instance.set_position.reset_mock()

    config_random = RenderConfig(
        output_path=Path("output.mp4"),
        temp_dir=Path("temp"),
        crop=[],
        resolution=(1920, 1080),
        fps=24,
        codec="libx264",
        optimize=False,
        audio_path=None,
        subtitles_path=Path("dummy_subs.vtt"),
        subtitle_fonts=["Arial"],
        subtitle_fontsizes=[24.0],
        subtitle_strokewidths=[0.0],
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        subtitle_vfx=[
            {
                "name": "slidein",
                "chance": 100.0,
                "strength_range": (9.0, 9.0),
            },  # random, slow (25% -> 0.5s)
            {
                "name": "slideout",
                "chance": 100.0,
                "strength_range": (10.0, 10.0),
            },  # random, fast (12% -> 0.24s)
        ],
        subtitle_vfx_chance=100.0,
        subtitle_vfx_intensity="1..3",
        subtitle_vfx_maximum=None,
        subtitle_vfx_order="linear",
        target_duration=None,
        fade_in=0.0,
        fade_out=0.0,
        fade_color="black",
        dry_run=False,
        bpm=120.0,
    )

    renderer_random = Renderer(config_random)
    clips_to_close_random = []
    with patch("builtins.open", mock_open(read_data=vtt_content_global)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer_random._apply_subtitles(mock_video, clips_to_close_random)

    called_pos_random = mock_clip_instance.set_position.call_args[0][0]
    assert callable(called_pos_random)
    pos_t0 = called_pos_random(0)
    assert len(pos_t0) == 2
    assert isinstance(pos_t0[0], int)
    assert isinstance(pos_t0[1], int)


@patch("src.renderer.TextClip")
def test_stroke_and_fill_slide_directions(mock_text_clip):
    # Mock TextClip instances
    mock_stroke_clip = MagicMock()
    mock_stroke_clip.w = 110
    mock_stroke_clip.h = 25
    mock_stroke_clip.set_start.return_value = mock_stroke_clip
    mock_stroke_clip.set_duration.return_value = mock_stroke_clip
    mock_stroke_clip.pos = None

    def stroke_set_pos(pos):
        mock_stroke_clip.pos = pos
        return mock_stroke_clip

    mock_stroke_clip.set_position.side_effect = stroke_set_pos
    mock_stroke_clip.fadein.return_value = mock_stroke_clip
    mock_stroke_clip.fadeout.return_value = mock_stroke_clip

    mock_fill_clip = MagicMock()
    mock_fill_clip.w = 100
    mock_fill_clip.h = 20
    mock_fill_clip.set_start.return_value = mock_fill_clip
    mock_fill_clip.set_duration.return_value = mock_fill_clip
    mock_fill_clip.pos = None

    def fill_set_pos(pos):
        mock_fill_clip.pos = pos
        return mock_fill_clip

    mock_fill_clip.set_position.side_effect = fill_set_pos
    mock_fill_clip.fadein.return_value = mock_fill_clip
    mock_fill_clip.fadeout.return_value = mock_fill_clip
    mock_stroke_clip.duration = 2.0
    mock_fill_clip.duration = 2.0

    # mock_text_clip side effect: first call is stroke, second call is fill
    mock_text_clip.side_effect = [mock_stroke_clip, mock_fill_clip]

    from unittest.mock import mock_open
    from pathlib import Path
    from src.models import RenderConfig
    from src.renderer import Renderer

    config = RenderConfig(
        output_path=Path("output.mp4"),
        temp_dir=Path("temp"),
        crop=[],
        resolution=(1920, 1080),
        fps=24,
        codec="libx264",
        optimize=False,
        audio_path=None,
        subtitles_path=Path("dummy_subs.vtt"),
        subtitle_fonts=["Arial"],
        subtitle_fontsizes=[24.0],
        subtitle_strokewidths=[2.0],
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        subtitle_vfx=[
            {
                "name": "slidein",
                "chance": 100.0,
                "strength_range": (9.0, 9.0),
            },  # random direction, slow (25% -> 0.5s)
        ],
        subtitle_vfx_chance=100.0,
        subtitle_vfx_intensity="1..3",
        subtitle_vfx_maximum=None,
        subtitle_vfx_order="linear",
        target_duration=None,
        fade_in=0.0,
        fade_out=0.0,
        fade_color="black",
        dry_run=False,
        bpm=120.0,
    )

    renderer = Renderer(config)
    mock_video = MagicMock()
    mock_video.w = 1920
    mock_video.h = 1080
    mock_video.duration = 10.0

    vtt_content = "WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:center line:bottom\nHello World\n\n"
    clips_to_close = []
    with patch("builtins.open", mock_open(read_data=vtt_content)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer._apply_subtitles(mock_video, clips_to_close)

    # Let's inspect the resolved direction
    assert callable(mock_fill_clip.pos)
    assert callable(mock_stroke_clip.pos)

    # Get fill position at t=0 (start of slidein) and t=0.4 (end of slidein)
    fill_p0 = mock_fill_clip.pos(0)
    fill_p4 = mock_fill_clip.pos(0.4)

    # Get stroke position at t=0 and t=0.4
    stroke_p0 = mock_stroke_clip.pos(0)
    stroke_p4 = mock_stroke_clip.pos(0.4)

    # Check that they match the expected offsets at all times
    assert stroke_p0[0] == int(fill_p0[0] - 5.0)
    assert stroke_p0[1] == int(fill_p0[1] - 2.5)
    assert stroke_p4[0] == int(fill_p4[0] - 5.0)
    assert stroke_p4[1] == int(fill_p4[1] - 2.5)
