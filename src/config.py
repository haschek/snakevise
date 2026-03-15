import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

from .constants import DEFAULTS, PRESETS
from .utils import parse_int_range_string

logger = logging.getLogger("vidseq")


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
                        active_conf.update(json.load(f))
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
            active_conf["vfx"].extend(args.vfx)

        if args.input:
            if "inputs" not in active_conf:
                active_conf["inputs"] = []
            active_conf["inputs"].extend(args.input)

        active_conf["resolution"] = f"{args.res[0][0]}x{args.res[0][1]}"
        active_conf["fps"] = args.res[1]
        active_conf["codec"] = args.codec
        active_conf["optimize"] = args.optimize
        if args.audio:
            active_conf["audio_path"] = str(args.audio)
        if args.duration:
            active_conf["duration"] = args.duration
        if args.length:
            active_conf["length_beats"] = args.length

        return active_conf
