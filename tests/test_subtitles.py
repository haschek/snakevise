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
