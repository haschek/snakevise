from typing import Any, Dict

CONFIG: Dict[str, Any] = {
    "bpm": 110.0,
    "snippetbeats": "2..4",
    "modus": "random",
    "vfx": [
        "dataglitch:40:5..9",
        "glitchchroma:50:5..8",
        "glitchmotion:40:4..8",
    ],
    "vfx_chance": 50,
    "vfx_intensity": "5..9",
    "vfx_maximum": 3,
    "fadein": 0,
    "fadeout": 1,
    "vfx_order": "random",
    "subtitle_fonts": [
        "RANDOM:3"
    ],  # Favor bold/heavy if possible, but RANDOM:3 gives variety
    "subtitle_fontsizes": [72.0, 84.0, 96.0, 110.0],
    "subtitle_strokewidths": [3.0, 4.5, 6.0],
    "subtitle_colors": ["white", "#FFFF00"],  # White, Yellow
    "subtitle_stroke_colors": ["black"],
}
