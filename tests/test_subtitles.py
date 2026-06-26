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


@patch("src.renderer.TextClip")
def test_subtitle_blur_effect(mock_text_clip):
    mock_clip = MagicMock()
    mock_clip.w = 100
    mock_clip.h = 20
    mock_clip.set_start.return_value = mock_clip
    mock_clip.set_duration.return_value = mock_clip
    mock_clip.set_position.return_value = mock_clip
    mock_clip.fl_image.return_value = mock_clip
    mock_clip.mask = MagicMock()
    mock_clip.mask.fl_image.return_value = mock_clip.mask
    mock_clip.duration = 2.0
    mock_text_clip.return_value = mock_clip

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
        subtitle_strokewidths=[0.0],
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        subtitle_vfx=[
            {"name": "blur", "chance": 100.0, "strength_range": (5.0, 5.0)},
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

    vtt_content = (
        "WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:center\nHello World\n\n"
    )
    clips_to_close = []

    # Configure mock_clip to not return new mocks on set_duration or set_position
    mock_clip.set_duration.return_value = mock_clip
    mock_clip.set_position.return_value = mock_clip
    mock_clip.mask.set_duration.return_value = mock_clip.mask
    mock_clip.mask.fl_image.return_value = mock_clip.mask

    with patch("builtins.open", mock_open(read_data=vtt_content)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer._apply_subtitles(mock_video, clips_to_close)

    # Verify fl_image was called to apply the blur
    assert mock_clip.fl_image.called
    assert mock_clip.mask.fl_image.called


@patch("src.renderer.TextClip")
def test_subtitle_static_stroke_alignment(mock_text_clip):
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

    mock_stroke_clip.duration = 2.0
    mock_fill_clip.duration = 2.0

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
        subtitle_strokewidths=[2.0],  # stroke enabled
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        subtitle_vfx=[],  # NO slide effects, no other effects
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

    # For align:center line:bottom
    # target_x = (1920 - 100) / 2 = 910
    # target_y = 1080 - 20 - 1080 * 0.05 = 1006
    assert mock_fill_clip.pos == (910, 1006)

    # stroke_offset_x = (100 - 110) / 2 = -5
    # stroke_offset_y = (20 - 25) / 2 = -2.5
    # So stroke pos should be int(1006 - 2.5) = 1003
    # Resulting in (905, 1003)
    assert mock_stroke_clip.pos == (905, 1003)


@patch("src.renderer.TextClip")
def test_subtitle_flickering_effect(mock_text_clip):
    mock_clip = MagicMock()
    mock_clip.w = 100
    mock_clip.h = 20
    mock_clip.set_start.return_value = mock_clip
    mock_clip.set_duration.return_value = mock_clip
    mock_clip.set_position.return_value = mock_clip
    mock_clip.mask = MagicMock()
    mock_clip.mask.fl.return_value = mock_clip.mask
    mock_clip.mask.set_duration.return_value = mock_clip.mask
    mock_clip.duration = 2.0
    mock_text_clip.return_value = mock_clip

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
        subtitle_strokewidths=[0.0],
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        subtitle_vfx=[
            {"name": "flickering", "chance": 100.0, "strength_range": (3.0, 3.0)},
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

    vtt_content = (
        "WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:center\nHello World\n\n"
    )
    clips_to_close = []
    with patch("builtins.open", mock_open(read_data=vtt_content)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer._apply_subtitles(mock_video, clips_to_close)

    # Verify that the filter fn was applied to the mask
    assert mock_clip.mask.fl.called


def test_flicker_count_calculation():
    import random
    import numpy as np
    from src.effects.subtitles import flickering

    # A simple mock clip class to bypass moviepy global mock pollution
    class FakeClip:
        def __init__(self, duration):
            self.duration = duration
            self.mask = self
            self.fl_fn = None

        def fl(self, filter_fn):
            self.fl_fn = filter_fn
            return self

        def set_mask(self, mask):
            self.mask = mask
            return self

        def get_frame(self, t):
            if self.fl_fn:

                def base_get_frame(time):
                    return np.array([1.0])

                return self.fl_fn(base_get_frame, t)
            return np.array([1.0])

    # Test cases: (strength, cue_duration, expected_flickers)
    # 1. strength = 1.0, cue_duration = 0.5s -> max(1.0, 0.5 * 1.0) = 1.0 -> 1 flicker
    # 2. strength = 1.0, cue_duration = 2.0s -> max(1.0, 2.0 * 1.0) = 2.0 -> 2 flickers
    # 3. strength = 10.0, cue_duration = 0.5s -> max(10.0, 0.5 * 10.0) = 10.0 -> 10 flickers
    # 4. strength = 10.0, cue_duration = 2.0s -> max(10.0, 2.0 * 10.0) = 20.0 -> 20 flickers
    test_cases = [
        (1.0, 0.5, 1),
        (1.0, 2.0, 2),
        (10.0, 0.5, 10),
        (10.0, 2.0, 20),
    ]

    state = random.getstate()
    try:
        for strength, duration, expected in test_cases:
            # Seed random to ensure deterministic flicker interval generation
            random.seed(42)

            clip = FakeClip(duration)
            res_clip, _ = flickering.apply(
                text_clip=clip,
                stroke_clip=None,
                strength=strength,
                cue_duration=duration,
                video_w=1920,
                video_h=1080,
                target_x=0,
                target_y=0,
            )

            # Sample the mask's frame values across the duration
            sampled_frames = []
            steps = 2000
            for i in range(steps + 1):
                t = (i / steps) * duration
                frame = res_clip.mask.get_frame(t)
                sampled_frames.append(frame[0])

            # Count the number of distinct zero intervals in sampled_frames
            zero_intervals = 0
            in_zero = False
            for val in sampled_frames:
                if val == 0.0:
                    if not in_zero:
                        zero_intervals += 1
                        in_zero = True
                else:
                    in_zero = False

            assert zero_intervals == expected, (
                f"Expected {expected} flickers for strength={strength}, dur={duration}, "
                f"but got {zero_intervals}."
            )
    finally:
        random.setstate(state)


@patch("src.renderer.TextClip")
def test_subtitle_jumping_effect(mock_text_clip):
    mock_clip = MagicMock()
    mock_clip.w = 100
    mock_clip.h = 20
    mock_clip.set_start.return_value = mock_clip
    mock_clip.set_duration.return_value = mock_clip
    mock_clip.set_position.return_value = mock_clip
    mock_clip.duration = 2.0
    mock_text_clip.return_value = mock_clip

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
        subtitle_strokewidths=[0.0],
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        subtitle_vfx=[
            {"name": "jumping", "chance": 100.0, "strength_range": (3.0, 3.0)},
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

    vtt_content = (
        "WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:center\nHello World\n\n"
    )
    clips_to_close = []
    with patch("builtins.open", mock_open(read_data=vtt_content)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer._apply_subtitles(mock_video, clips_to_close)

    # Verify that the position was set
    assert mock_clip.set_position.called


def test_jumping_count_and_intervals():
    import numpy as np
    from src.effects.subtitles import jumping

    class FakeClip:
        def __init__(self, duration):
            self.duration = duration
            self.pos = (100, 200)

        def set_position(self, pos_fn):
            self.pos = pos_fn
            return self

    # Test cases for number of jumps capping: (strength, duration, expected_jumps)
    # min_hold_duration = 0.15
    # For S=10.0, dur=0.5: expected = 5 jumps, max_intervals = max(1, 0.5/0.15) = 3 -> max_jumps = 2.
    # So capped num_jumps = 2.
    clip = FakeClip(0.5)
    res_clip, _ = jumping.apply(clip, None, 10.0, 0.5, 1920, 1080, 100, 200)

    # We sampled positions at intervals. Since we have 2 jumps, we have 3 intervals (index 0, 1, 2)
    # interval_len = 0.5 / 3 = 0.1667s.
    pos_0 = res_clip.pos(0.0)
    pos_1 = res_clip.pos(0.2)
    pos_2 = res_clip.pos(0.4)

    # Calculate displacement relative to (100, 200)
    dx_0, dy_0 = pos_0[0] - 100, pos_0[1] - 200
    dx_1, dy_1 = pos_1[0] - 100, pos_1[1] - 200
    dx_2, dy_2 = pos_2[0] - 100, pos_2[1] - 200

    # Interval 0 must be the original position (0, 0)
    assert dx_0 == 0 and dy_0 == 0

    # Jump 1 (dx_1, dy_1) and Jump 2 (dx_2, dy_2) should have opposite signs
    # so they cross/overstep the origin!
    assert np.sign(dx_1) == -np.sign(dx_2)
    assert np.sign(dy_1) == -np.sign(dy_2)

    # Displacement bounds: min_disp = 60.0 / 3.0 = 20.0, max_disp = 60.0
    assert 20.0 <= abs(dx_1) <= 60.0
    assert 20.0 <= abs(dy_1) <= 60.0
    assert 20.0 <= abs(dx_2) <= 60.0
    assert 20.0 <= abs(dy_2) <= 60.0


@patch("src.renderer.TextClip")
def test_subtitle_moving_effect(mock_text_clip):
    mock_clip = MagicMock()
    mock_clip.w = 100
    mock_clip.h = 20
    mock_clip.set_start.return_value = mock_clip
    mock_clip.set_duration.return_value = mock_clip
    mock_clip.set_position.return_value = mock_clip
    mock_clip.duration = 2.0
    mock_text_clip.return_value = mock_clip

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
        subtitle_strokewidths=[0.0],
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        subtitle_vfx=[
            {"name": "moving", "chance": 100.0, "strength_range": (3.0, 3.0)},
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

    vtt_content = (
        "WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:center\nHello World\n\n"
    )
    clips_to_close = []
    with patch("builtins.open", mock_open(read_data=vtt_content)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer._apply_subtitles(mock_video, clips_to_close)

    # Verify that position was set
    assert mock_clip.set_position.called


def test_moving_smooth_interpolation():
    from src.effects.subtitles import moving

    class FakeClip:
        def __init__(self, duration):
            self.duration = duration
            self.pos = (100, 200)

        def set_position(self, pos_fn):
            self.pos = pos_fn
            return self

    # cue_duration = 0.5s, strength = 10.0 -> expected 2 jumps, 3 intervals
    # interval_len = 0.5 / 3 = 0.1667s
    # transition_dur = interval_len = 0.1667s
    clip = FakeClip(0.5)
    res_clip, _ = moving.apply(clip, None, 10.0, 0.5, 1920, 1080, 100, 200)

    # Sample position at start (interval 0)
    pos_start = res_clip.pos(0.0)
    dx_start = pos_start[0] - 100
    assert dx_start == 0

    # Sample position right at the boundary of interval 1 (t = 0.1667)
    pos_boundary = res_clip.pos(0.1667)
    dx_boundary = pos_boundary[0] - 100
    assert dx_boundary == 0

    # Sample position at the end of interval 1 (t = 0.3333)
    pos_end = res_clip.pos(0.3333)
    dx_target = pos_end[0] - 100

    # Sample position mid-transition (t = 0.25)
    pos_mid = res_clip.pos(0.25)
    dx_mid = pos_mid[0] - 100

    # Check that mid-transition displacement is strictly between start (0) and target
    assert abs(dx_mid) > 0
    assert abs(dx_mid) < abs(dx_target)


@patch("src.renderer.TextClip")
def test_subtitle_tilt_effect(mock_text_clip):
    mock_clip = MagicMock()
    mock_clip.w = 100
    mock_clip.h = 20
    mock_clip.set_start.return_value = mock_clip
    mock_clip.set_duration.return_value = mock_clip
    mock_clip.set_position.return_value = mock_clip
    mock_clip.duration = 2.0
    mock_text_clip.return_value = mock_clip

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
        subtitle_strokewidths=[0.0],
        subtitle_colors=["white"],
        subtitle_stroke_colors=["black"],
        subtitle_vfx=[
            {"name": "tilt", "chance": 100.0, "strength_range": (3.0, 3.0)},
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

    vtt_content = (
        "WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:center\nHello World\n\n"
    )
    clips_to_close = []
    with patch("builtins.open", mock_open(read_data=vtt_content)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer._apply_subtitles(mock_video, clips_to_close)

    # Verify that the TextClip was created (which triggers the tilt plugin)
    assert mock_text_clip.called


def test_tilt_logic_and_transitions():
    from src.effects.subtitles import tilt

    class FakeClip:
        def __init__(self, duration):
            self.duration = duration
            self.mask = None
            self.fl_fn = None
            self.w = 100
            self.h = 20
            self.size = (100, 20)

        def fl(self, filter_fn):
            self.fl_fn = filter_fn
            return self

        def set_mask(self, mask):
            self.mask = mask
            return self

    # cue_duration = 0.5s, strength = 10.0 -> expected 2 tilts, 3 intervals
    # interval_len = 0.5 / 3 = 0.1667s
    clip = FakeClip(0.5)

    # We patch random.uniform and random.choice inside tilt to make it deterministic
    # strength 10 -> max_angle = (3 + 10 * 1.2) * 0.5 = 7.5 deg. min_angle = 2.5 deg.
    with patch("random.choice", return_value=1):
        with patch("random.uniform", return_value=12.0):
            res_clip, _ = tilt.apply(clip, None, 10.0, 0.5, 1920, 1080, 100, 200)

    # Verify that the clip properties are padded to D = 102
    assert res_clip.w == 102
    assert res_clip.h == 102
    assert res_clip.size == (102, 102)

    # Verify that the position calculation is correctly shifted:
    # x - (D - orig_w)/2 = 100 - (102 - 100)/2 = 99
    # y - (D - orig_h)/2 = 200 - (102 - 20)/2 = 159
    assert res_clip.pos(0.0) == (99, 159)

    # We patch PIL Image.rotate to capture the angle passed to it
    from PIL import Image

    captured_angles = []
    original_rotate = Image.Image.rotate

    def mock_rotate(self, angle, *args, **kwargs):
        captured_angles.append(angle)
        return original_rotate(self, angle, *args, **kwargs)

    with patch("PIL.Image.Image.rotate", mock_rotate):
        import numpy as np

        # Create dummy frame matching original 100x20 size
        dummy_frame = np.zeros((20, 100, 4), dtype=np.uint8)

        def get_frame_fn(time):
            return dummy_frame

        # Sample at start (t=0.0): angle is 0.0, so rotate is not called
        frame_start = res_clip.fl_fn(get_frame_fn, 0.0)
        assert len(captured_angles) == 0
        assert frame_start.shape == (102, 102, 4)

        # Sample at midpoint (t=0.25): mid transition
        frame_mid = res_clip.fl_fn(get_frame_fn, 0.25)
        assert frame_mid.shape == (102, 102, 4)

        # Sample at end of interval 1 (t=1/3): reaches target angle
        frame_end = res_clip.fl_fn(get_frame_fn, 1.0 / 3.0)
        assert frame_end.shape == (102, 102, 4)

    assert len(captured_angles) == 2
    angle_mid = captured_angles[0]
    angle_end = captured_angles[1]

    # Target angle should be exactly 12.0 degrees (the mocked random.uniform value)
    assert abs(angle_end - 12.0) < 1e-4
    # Mid-transition angle should be strictly between 0 and 12.0
    assert 0.0 < abs(angle_mid) < 12.0


@patch("src.renderer.TextClip")
def test_subtitle_wrapping(mock_text_clip):
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
        subtitle_fontsizes=[40.0],
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

    renderer = Renderer(config)
    long_text = (
        "This is an extremely long subtitle line that will definitely exceed "
        "the maximum estimated character limit and trigger pre-wrapping."
    )
    vtt_content = (
        f"WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:center\n{long_text}\n\n"
    )

    mock_video = MagicMock()
    mock_video.w = 1920
    mock_video.h = 1080
    mock_video.duration = 10.0

    clips_to_close = []
    with patch("builtins.open", mock_open(read_data=vtt_content)):
        with patch("src.utils.check_font_renderable", return_value=True):
            with patch.object(Path, "exists", return_value=True):
                renderer._apply_subtitles(mock_video, clips_to_close)

    # Verify TextClip was called for stroke and fill
    assert mock_text_clip.call_count == 2

    # Extract the text string passed to the first TextClip instantiation
    passed_text = mock_text_clip.call_args_list[0][0][0]

    # Assert that the text contains newlines (\n) due to textwrap.fill
    assert "\n" in passed_text
    # Check that it starts and ends with parts of our original text
    assert passed_text.replace("\n", " ") == long_text
