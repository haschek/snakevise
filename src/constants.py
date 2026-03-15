from typing import Any, Dict

from .presets import PRESETS

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
    "resolution": "1920x1080",
    "fps": 24,
    "codec": "libx264",
    "optimize": False,
    "audio_path": None,
    "duration": None,
    "length_beats": None,
    "seed": None,
}
