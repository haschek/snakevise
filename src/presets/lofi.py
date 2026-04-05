from typing import Any, Dict

CONFIG: Dict[str, Any] = {
    "bpm": 80.0,
    "snippetbeats": "4..12",
    "modus": "linear-random",
    "vfx": ["tvscreen:80:3..6", "asciiart:30:4..7", "stopmotion:60:2..4"],
    "vfx_chance": 40,
    "vfx_intensity": "2..5",
    "vfx_maximum": 2,
    "fadein": 4,
    "fadeout": 4,
    "vfx_order": "random",
    "subtitle_fonts": ["RANDOM:5"],
    "subtitle_fontsizes": [56.0, 64.0, 72.0],
    "subtitle_strokewidths": [2.5, 3.5],
    "subtitle_colors": [
        "#00FFFF",
        "#FF00FF",
        "#00FF00",
        "#FFFF00",
    ],  # Cyan, Magenta, Green, Yellow
    "subtitle_stroke_colors": ["black"],
}
