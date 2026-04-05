from unittest.mock import MagicMock, patch
from src.config import ConfigResolver


@patch("src.utils.get_compatible_fonts")
def test_resolve_subtitle_params(mock_fonts):
    mock_fonts.return_value = ["Arial"]

    args = MagicMock()
    args.preset = None
    args.loadproject = None
    args.bpm = 120
    args.snippetbeats = "4..8"
    args.modus = "linear"
    args.vfx = []
    args.input = []
    args.res = ((1920, 1080), 24)
    args.codec = "libx264"
    args.optimize = False
    args.audio = None
    args.subtitles = "subs.vtt"
    args.stfont = ["Arial", "Courier"]
    args.stfontsize = ["48", "RANDOM:20..30:2"]
    args.ststrokewidth = ["1.5"]
    args.stcolor = ["white"]
    args.stscolor = ["black"]
    args.duration = None
    args.length = None

    conf = ConfigResolver.resolve(args)

    # Check that they are stored as lists in active_conf (raw)
    assert conf["subtitle_fonts"] == ["Arial", "Courier"]
    assert conf["subtitle_fontsizes"] == ["48", "RANDOM:20..30:2"]
    assert conf["subtitle_strokewidths"] == ["1.5"]
    assert conf["subtitle_colors"] == ["white"]
    assert conf["subtitle_stroke_colors"] == ["black"]


@patch("src.utils.get_compatible_fonts")
@patch("src.utils.check_font_renderable")
def test_expand_dynamic_vars_full(mock_renderable, mock_fonts):
    mock_fonts.return_value = ["Arial", "Liberation-Sans"]
    mock_renderable.return_value = True

    raw_conf = {
        "subtitle_fonts": ["RANDOM:2"],
        "subtitle_fontsizes": ["RANDOM:40..80:2"],
        "subtitle_strokewidths": ["1.0", "RANDOM:2..4:1"],
        "subtitle_colors": ["RANDOM:1"],
        "subtitle_stroke_colors": ["black"],
    }

    expanded = ConfigResolver.expand_dynamic_vars(raw_conf)

    assert len(expanded["subtitle_fonts"]) == 2
    assert len(expanded["subtitle_fontsizes"]) == 2
    assert len(expanded["subtitle_strokewidths"]) == 2
    assert len(expanded["subtitle_colors"]) == 1
    assert expanded["subtitle_stroke_colors"] == ["black"]

    # Check types
    for s in expanded["subtitle_fontsizes"]:
        assert isinstance(s, float)
    for w in expanded["subtitle_strokewidths"]:
        assert isinstance(w, float)
