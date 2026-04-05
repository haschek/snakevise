from typing import Any, Dict


# --- SYSTEM DEFAULTS ---
DEFAULTS: Dict[str, Any] = {
    "inputs": [],
    "bpm": 120.0,
    "snippetbeats": "8..16",
    "modus": "linear",
    "vfx": [],
    "vfx_chance": 20,
    "vfx_intensity": "1..3",
    "vfx_maximum": 1,
    "vfx_order": "linear",
    "fadein": 0,
    "fadeout": 0,
    "fadecolor": "#000000",
    "output": "output.mp4",
    "temp": "tempsnippets",
    "resolution": "1920x1080",
    "fps": 24,
    "codec": "libx264",
    "optimize": False,
    "audio_path": None,
    "subtitles_path": None,
    "subtitle_fonts": [],
    "subtitle_fontsizes": [48.0],
    "subtitle_strokewidths": [1.5],
    "subtitle_colors": ["white"],
    "subtitle_stroke_colors": ["black"],
    "duration": None,
    "length_beats": None,
    "seed": None,
}
