import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

from .constants import DEFAULTS
from .presets import PRESETS
from .utils import get_compatible_fonts, parse_int_range_string

logger = logging.getLogger("snakevise")


class ConfigResolver:
    """Handles parsing and merging of configuration from various sources."""

    @staticmethod
    def parse_input_arg(
        input_str: str, defaults: Dict[str, Any]
    ) -> Tuple[str, float, float, float, int, int]:
        """Parses a single input source string.

        Args:
            input_str: Source string (FILE:START:END:BPM:BEATS).
            defaults: Current configuration defaults.

        Returns:
            Tuple (filename, start, end, bpm, min_beats, max_beats).
        """
        parts = input_str.split(":")

        def get(i, d):
            return parts[i] if len(parts) > i and parts[i] else d

        fname = parts[0].strip()
        start = float(get(1, 0))
        end = float(get(2, 0))
        bpm = float(get(3, defaults["bpm"]))

        beat_range_str = get(4, defaults["snippetbeats"])
        min_b, max_b = parse_int_range_string(beat_range_str)

        return fname, start, end, bpm, min_b, max_b

    @staticmethod
    def resolve(args: argparse.Namespace) -> Dict[str, Any]:
        """Merges CLI args, presets, and defaults.

        Args:
            args: Parsed command line arguments.

        Returns:
            A unified configuration dictionary.
        """
        active_conf = DEFAULTS.copy()

        # 1. Presets
        if args.preset:
            if args.preset in PRESETS:
                logger.info(f"Applying internal preset: {args.preset}")
                active_conf.update(PRESETS[args.preset])
            else:
                p_path = Path(args.preset)
                if p_path.is_file():
                    try:
                        with open(p_path, "r", encoding="utf-8") as f:
                            active_conf.update(json.load(f))
                    except Exception as e:
                        logger.error(f"Failed to load custom preset: {e}")

        # 2. Project File
        if args.loadproject:
            lp_path = Path(args.loadproject)
            if lp_path.is_file():
                try:
                    with open(lp_path, "r", encoding="utf-8") as f:
                        project_data = json.load(f)
                        active_conf.update(project_data)
                        active_conf["_project_root"] = lp_path.parent
                except Exception as e:
                    logger.error(f"Failed to load project file: {e}")

        # 3. CLI Overrides
        direct_mappings = [
            "bpm",
            "snippetbeats",
            "modus",
            "vfx_chance",
            "vfx_intensity",
            "vfx_maximum",
            "vfx_order",
            "fadein",
            "fadeout",
        ]
        for attr in direct_mappings:
            val = getattr(args, attr, None)
            if val is not None:
                active_conf[attr] = val

        if args.vfx:
            active_conf["vfx"] = args.vfx

        if args.input:
            active_conf["inputs"] = args.input

        if args.res:
            active_conf["resolution"] = f"{args.res[0][0]}x{args.res[0][1]}"
            active_conf["fps"] = args.res[1]

        if args.codec is not None:
            active_conf["codec"] = args.codec

        if args.optimize is not None:
            active_conf["optimize"] = args.optimize

        if args.output is not None:
            active_conf["output"] = str(args.output)

        if args.temp is not None:
            active_conf["temp"] = str(args.temp)

        if args.fadecolor is not None:
            active_conf["fadecolor"] = args.fadecolor

        if args.audio:
            active_conf["audio_path"] = str(args.audio)
        if args.subtitles:
            active_conf["subtitles_path"] = str(args.subtitles)

        # 4. Collect Raw Font Settings (Multiple, Comma-Separated)
        if args.stfont:
            fonts = []
            for f in args.stfont:
                fonts.extend([s.strip() for s in f.split(",") if s.strip()])
            active_conf["subtitle_fonts"] = fonts

        if args.stfontsize:
            fsizes = []
            for fs in args.stfontsize:
                fsizes.extend([s.strip() for s in fs.split(",") if s.strip()])
            active_conf["subtitle_fontsizes"] = fsizes

        if args.ststrokewidth:
            swidths = []
            for sw in args.ststrokewidth:
                swidths.extend([s.strip() for s in sw.split(",") if s.strip()])
            active_conf["subtitle_strokewidths"] = swidths

        if args.stcolor:
            scolors = []
            for sc in args.stcolor:
                scolors.extend([s.strip() for s in sc.split(",") if s.strip()])
            active_conf["subtitle_colors"] = scolors

        if args.stscolor:
            sscolors = []
            for ssc in args.stscolor:
                sscolors.extend([s.strip() for s in ssc.split(",") if s.strip()])
            active_conf["subtitle_stroke_colors"] = sscolors

        if args.duration:
            active_conf["duration"] = args.duration
        if args.length:
            active_conf["length_beats"] = args.length

        return active_conf

    @staticmethod
    def expand_dynamic_vars(conf: Dict[str, Any]) -> Dict[str, Any]:
        """Expands dynamic values (RANDOM:...) into concrete lists.

        Args:
            conf: The configuration dictionary to expand.

        Returns:
            A new dictionary with expanded values.
        """

        from .utils import (
            expand_random_colors,
            expand_random_fonts,
            expand_random_numeric_range,
        )

        expanded = conf.copy()

        # 1. Expand subtitle_fonts
        raw_fonts = expanded.get("subtitle_fonts", [])
        if not isinstance(raw_fonts, list):
            raw_fonts = [raw_fonts]

        final_fonts = []
        for f in raw_fonts:
            parts = [p.strip() for p in str(f).split(",") if p.strip()]
            for p in parts:
                final_fonts.extend(expand_random_fonts(p))

        if not final_fonts:
            compatible = get_compatible_fonts()
            final_fonts = [compatible[0]] if compatible else ["Arial"]

        expanded["subtitle_fonts"] = final_fonts

        # 2. Expand subtitle_fontsizes
        raw_sizes = expanded.get("subtitle_fontsizes", [48.0])
        if not isinstance(raw_sizes, list):
            raw_sizes = [raw_sizes]

        final_sizes = []
        for s in raw_sizes:
            # Check for multiple values inside one string (e.g. from JSON or comma-separated)
            parts = [p.strip() for p in str(s).split(",") if p.strip()]
            for p in parts:
                final_sizes.extend(expand_random_numeric_range(p, precision=1))

        expanded["subtitle_fontsizes"] = final_sizes or [48.0]

        # 3. Expand subtitle_strokewidths
        raw_widths = expanded.get("subtitle_strokewidths", [1.5])
        if not isinstance(raw_widths, list):
            raw_widths = [raw_widths]

        final_widths = []
        for w in raw_widths:
            parts = [p.strip() for p in str(w).split(",") if p.strip()]
            for p in parts:
                final_widths.extend(expand_random_numeric_range(p, precision=2))

        expanded["subtitle_strokewidths"] = final_widths or [1.5]

        # 4. Expand subtitle_colors
        raw_colors = expanded.get("subtitle_colors", ["white"])
        if not isinstance(raw_colors, list):
            raw_colors = [raw_colors]

        final_colors = []
        for c in raw_colors:
            parts = [p.strip() for p in str(c).split(",") if p.strip()]
            for p in parts:
                final_colors.extend(expand_random_colors(p))
        expanded["subtitle_colors"] = final_colors or ["white"]

        # 5. Expand subtitle_stroke_colors
        raw_scolors = expanded.get("subtitle_stroke_colors", ["black"])
        if not isinstance(raw_scolors, list):
            raw_scolors = [raw_scolors]

        final_scolors = []
        for sc in raw_scolors:
            parts = [p.strip() for p in str(sc).split(",") if p.strip()]
            for p in parts:
                final_scolors.extend(expand_random_colors(p))
        expanded["subtitle_stroke_colors"] = final_scolors or ["black"]

        return expanded
