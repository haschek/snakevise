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
