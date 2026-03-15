#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
"""
SnakeVISE - Generative Video Sequencer.

Creates rhythmic video montages based on BPM and algorithms.
"""

# --- COMPATIBILITY PATCH FOR PILLOW 10+ ---
# Some older versions of moviepy (like 1.0.3) still use PIL.Image.ANTIALIAS
# which was removed in Pillow 10.0.0 in favor of PIL.Image.LANCZOS.
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
# ------------------------------------------

from src.main import main

if __name__ == "__main__":
    main()
