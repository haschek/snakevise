import sys
from unittest.mock import MagicMock, patch

# Mock moviepy before importing anything that might use it
mock_moviepy = MagicMock()
sys.modules["moviepy"] = mock_moviepy
sys.modules["moviepy.editor"] = mock_moviepy

from src.utils import (  # noqa: E402
    expand_random_colors,
    expand_random_fonts,
    expand_random_numeric_range,
    get_compatible_fonts,
    check_font_renderable,
    parse_sub_settings,
)


def test_expand_random_colors_static():
    assert expand_random_colors("white") == ["white"]
    assert expand_random_colors("#FF0000") == ["#FF0000"]


def test_expand_random_colors_random():
    colors = expand_random_colors("RANDOM:5")
    assert len(colors) == 5
    for c in colors:
        assert c.startswith("#")
        assert len(c) == 7


def test_expand_random_numeric_range_static():
    assert expand_random_numeric_range("48") == [48.0]
    assert expand_random_numeric_range("1.5") == [1.5]


def test_expand_random_numeric_range_random_single():
    # RANDOM:min..max:count
    res = expand_random_numeric_range("RANDOM:10..20:1")
    assert len(res) == 1
    assert 10 <= res[0] <= 20


def test_expand_random_numeric_range_distribution():
    # Testing the micro-range distribution logic
    res = expand_random_numeric_range("RANDOM:10..50:4")
    assert len(res) == 4
    # Each value should be in one of the segments: [10-20, 20-30, 30-40, 40-50]
    # Since they are shuffled, we sort them to check
    res.sort()
    assert 10 <= res[0] <= 20
    assert 20 <= res[1] <= 30
    assert 30 <= res[2] <= 40
    assert 40 <= res[3] <= 50


def test_get_compatible_fonts():
    # Mock some fonts
    mock_moviepy.TextClip.list.return_value = [
        "Arial",
        "Arial-Bold",
        "Arial-Italic",
        "Arial-BoldItalic",
        "Courier",
        "Courier-Bold",  # No italic
        "Liberation-Sans",
        "Liberation-Sans-Bold",
        "Liberation-Sans-Italic",
        "Liberation-Sans-BoldItalic",
    ]

    fonts = get_compatible_fonts()
    # Arial and Liberation should be in there (split by -)
    assert "Arial" in fonts
    assert "Liberation" in fonts
    # Courier should NOT be there (no italic)
    assert "Courier" not in fonts
    # Check prioritization (Arial should be first)
    assert fonts[0] == "Arial"


@patch("src.utils.get_compatible_fonts")
def test_expand_random_fonts(mock_comp):
    mock_comp.return_value = ["Arial", "Liberation-Sans", "DejaVu-Sans"]

    # Static
    assert expand_random_fonts("Arial") == ["Arial"]

    # Random
    res = expand_random_fonts("RANDOM:2")
    assert len(res) == 2
    for f in res:
        assert f in ["Arial", "Liberation-Sans", "DejaVu-Sans"]


def test_check_font_renderable_success():
    mock_moviepy.TextClip.return_value = MagicMock()
    # Should return True if no exception
    assert check_font_renderable("Arial") is True


def test_check_font_renderable_failure():
    mock_moviepy.TextClip.side_effect = Exception("Magic error")
    assert check_font_renderable("BrokenFont") is False
    # Reset side effect
    mock_moviepy.TextClip.side_effect = None


def test_parse_sub_settings_extended():
    # Test some more edge cases for settings parsing
    h, v = parse_sub_settings("align:start line:0")
    assert h == "left"
    assert v == "top"

    h, v = parse_sub_settings("align:end line:middle")
    assert h == "right"
    assert v == "center"

    h, v = parse_sub_settings("align:middle line:bottom")
    assert h == "center"
    assert v == "bottom"
