from typing import Any, Dict

CONFIG: Dict[str, Any] = {
    "bpm": 90.0,
    "snippetbeats": "4..8",
    "modus": "linear",
    "vfx": ["newspaper:100:2..5", "oldmovie:50:3..6", "speed:25:2"],
    "vfx_chance": 50,
    "vfx_intensity": "4..6",
    "vfx_maximum": None,
    "fadein": 2,
    "fadeout": 2,
    "vfx_order": "linear",
    "subtitle_fonts": ["RANDOM:10"],
    "subtitle_fontsizes": [48.0, 52.0, 60.0],
    "subtitle_strokewidths": [1.5, 2.0],
    "subtitle_colors": ["#FFFFE0", "#FDF5E6", "#FAF0E6"],  # Ivory, OldLace, Linen
    "subtitle_stroke_colors": ["#2e2e2e"],
}
