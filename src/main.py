import argparse
import glob
import json
import logging
import random
from pathlib import Path

import argcomplete
import numpy as np
import webvtt
from moviepy.editor import AudioFileClip

from .config import ConfigResolver
from .effects import EffectEngine
from .models import RenderConfig
from .planner import MediaSource, TimelinePlanner
from .renderer import Renderer
from .utils import (
    parse_effect_string,
    parse_range_string,
    parse_resolution,
    relativize_path,
    resolve_path,
    setup_logging,
    unescape_path,
)

logger = logging.getLogger("snakevise")


def main() -> None:
    """Main entry point for SnakeVISE CLI."""
    parser = argparse.ArgumentParser(description="SnakeVISE - CLI Video Generator")

    effects_list = ", ".join(EffectEngine.AVAILABLE_EFFECTS)

    g_in = parser.add_argument_group("Input Sources")
    g_in.add_argument(
        "--input",
        action="append",
        help="Format: FILE:START:END:BPM:BEATS (e.g. video.mp4:0:0:120:4..8)",
    )
    g_in.add_argument(
        "--preset",
        type=str,
        help="Load a configuration preset. Options: subtle, vintage, lofi, urban, chaos or path to a JSON file.",
    )
    g_in.add_argument(
        "--saveproject", type=Path, help="Save current configuration to JSON"
    )
    g_in.add_argument("--loadproject", type=Path, help="Load configuration from JSON")
    g_in.add_argument(
        "--modus",
        choices=["random", "linear", "random-linear", "linear-random"],
        help="Sequencing algorithm (Source-Snippet)",
    )
    g_in.add_argument("--bpm", type=float, help="Global BPM")
    g_in.add_argument(
        "--snippetbeats", type=str, help="Beats per snippet range (e.g. 4..8)"
    )

    g_out = parser.add_argument_group("Output Settings")
    g_out.add_argument("--output", type=Path, help="Output filename")
    g_out.add_argument("--res", type=parse_resolution, help="WxH:FPS")
    g_out.add_argument("--codec", type=str, help="Video Codec")
    g_out.add_argument("--optimize", action="store_true", help="Enable CRF Encoding")
    g_out.add_argument(
        "--no-optimize",
        dest="optimize",
        action="store_false",
        help="Disable CRF Encoding",
    )
    g_out.set_defaults(optimize=None)
    g_out.add_argument("--temp", type=Path, help="Temp directory")
    g_out.add_argument("--log", type=str, help="Path to log file")
    g_out.add_argument("--dry-run", action="store_true", help="Simulate only")
    g_out.add_argument("--seed", type=int, help="Random seed for reproducibility")

    g_time = parser.add_argument_group("Timing & Audio")
    g_time.add_argument("--audio", type=Path, help="Master Audio File path")
    g_time.add_argument("--subtitles", type=Path, help="WebVTT Subtitles path")
    g_time.add_argument(
        "--stfont",
        type=str,
        action="append",
        help="Font(s) for subtitles. Can be multiple, comma-separated, or RANDOM:n",
    )
    g_time.add_argument(
        "--stfontsize",
        type=str,
        action="append",
        help="Font size(s) for subtitles. Can be multiple or comma-separated.",
    )
    g_time.add_argument(
        "--ststrokewidth",
        type=str,
        action="append",
        help="Stroke width(s) for subtitles. Can be multiple or comma-separated.",
    )
    g_time.add_argument(
        "--stcolor",
        type=str,
        action="append",
        help="Text color(s) for subtitles. Can be multiple, comma-separated, or RANDOM:n.",
    )
    g_time.add_argument(
        "--stscolor",
        type=str,
        action="append",
        help="Stroke color(s) for subtitles. Can be multiple, comma-separated, or RANDOM:n.",
    )
    g_time.add_argument("--duration", type=float, help="Target duration in seconds")
    g_time.add_argument("--length", type=float, help="Target duration in Beats")

    g_vfx = parser.add_argument_group("VFX & Transitions")
    g_vfx.add_argument(
        "--vfx",
        action="append",
        help=f"Format: NAME:CHANCE:STRENGTH (e.g., glitchchroma:50:3..8). Available: {effects_list}",
    )
    g_vfx.add_argument(
        "--vfx-chance", dest="vfx_chance", type=float, help="Global effect probability"
    )
    g_vfx.add_argument(
        "--vfx-intensity",
        dest="vfx_intensity",
        type=str,
        help="Global effect intensity (e.g. 5 or 3..8)",
    )
    g_vfx.add_argument(
        "--vfx-maximum",
        dest="vfx_maximum",
        type=int,
        help="Maximum number of effects per snippet",
    )
    g_vfx.add_argument(
        "--vfx-order",
        dest="vfx_order",
        choices=["linear", "random"],
        help="Apply effects in defined or random order",
    )
    g_vfx.add_argument("--fadein", type=int, help="Fade-in duration in Beats")
    g_vfx.add_argument("--fadeout", type=int, help="Fade-out duration in Beats")
    g_vfx.add_argument("--fadecolor", type=str, help="Hex color for fades")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    setup_logging(args.log)
    logger.info("Initializing SnakeVISE...")

    active_conf = ConfigResolver.resolve(args)

    # Seed Initialization
    final_seed = args.seed or active_conf.get("seed") or random.randint(0, 99999999)
    active_conf["seed"] = final_seed
    random.seed(final_seed)
    np.random.seed(final_seed)
    logger.info(f"Random Seed initialized: {final_seed}")

    # Configuration Summary
    logger.info("\n" + "=" * 60)
    logger.info("ACTIVE CONFIGURATION SUMMARY")
    logger.info("=" * 60)
    for key, value in sorted(active_conf.items()):
        val_str = str(value)
        if len(val_str) > 80:
            val_str = val_str[:77] + "..."
        logger.info(f"{key:<20}: {val_str}")
    logger.info("=" * 60 + "\n")

    if not active_conf["inputs"]:
        logger.error(
            "No input sources defined. Use --input or load a project with inputs."
        )
        return

    # Save Project
    if args.saveproject:
        try:
            save_dir = args.saveproject.parent.resolve()
            save_conf = active_conf.copy()
            # Don't save internal helper
            save_conf.pop("_project_root", None)

            # Relativize audio_path
            if save_conf.get("audio_path"):
                save_conf["audio_path"] = relativize_path(
                    save_conf["audio_path"], save_dir
                )

            # Relativize subtitles_path
            if save_conf.get("subtitles_path"):
                save_conf["subtitles_path"] = relativize_path(
                    save_conf["subtitles_path"], save_dir
                )

            # Relativize inputs

            if save_conf.get("inputs"):
                rel_inputs = []
                for inp_str in save_conf["inputs"]:
                    # Format: FILE:START:END:BPM:BEATS
                    parts = inp_str.split(":")
                    if parts:
                        parts[0] = relativize_path(parts[0], save_dir)
                    rel_inputs.append(":".join(parts))
                save_conf["inputs"] = rel_inputs

            with open(args.saveproject, "w", encoding="utf-8") as f:
                json.dump(save_conf, f, indent=4)
            logger.info(f"Project configuration saved to: {args.saveproject}")
        except Exception as e:
            logger.error(f"Failed to save project: {e}")

    # Expand dynamic variables (RANDOM:...) into concrete lists
    active_conf = ConfigResolver.expand_dynamic_vars(active_conf)

    # Prep Render Config
    w, h = map(int, active_conf["resolution"].lower().split("x"))
    global_beat_dur = 60.0 / active_conf["bpm"]

    # Resolve paths (respecting project root if loaded from JSON)
    project_root = active_conf.get("_project_root")

    # Check if JSON had output/temp overrides
    final_output = Path(active_conf.get("output", args.output))
    final_temp = Path(active_conf.get("temp", args.temp))

    render_config = RenderConfig(
        output_path=resolve_path(str(final_output), project_root),
        temp_dir=resolve_path(str(final_temp), project_root),
        resolution=(w, h),
        fps=active_conf["fps"],
        codec=active_conf["codec"],
        optimize=active_conf["optimize"],
        audio_path=resolve_path(active_conf["audio_path"], project_root)
        if active_conf.get("audio_path")
        else None,
        subtitles_path=resolve_path(active_conf["subtitles_path"], project_root)
        if active_conf.get("subtitles_path")
        else None,
        subtitle_fonts=active_conf["subtitle_fonts"],
        subtitle_fontsizes=active_conf["subtitle_fontsizes"],
        subtitle_strokewidths=active_conf["subtitle_strokewidths"],
        subtitle_colors=active_conf["subtitle_colors"],
        subtitle_stroke_colors=active_conf["subtitle_stroke_colors"],
        target_duration=None,
        fade_in=active_conf["fadein"] * global_beat_dur,
        fade_out=active_conf["fadeout"] * global_beat_dur,
        fade_color=active_conf["fadecolor"],
        dry_run=args.dry_run,
        bpm=active_conf["bpm"],
    )

    if render_config.subtitles_path:
        if not render_config.subtitles_path.exists():
            logger.error(f"Subtitles file not found: {render_config.subtitles_path}")
            return
        try:
            # Validate basic WebVTT structure
            webvtt.read(str(render_config.subtitles_path))
        except Exception as e:
            logger.error(
                f"Malformed Subtitles file ({render_config.subtitles_path.name}): {e}"
            )
            logger.error(
                "Please ensure the file is a valid WebVTT format (starting with 'WEBVTT')."
            )
            return

    if render_config.audio_path:
        if not render_config.audio_path.exists():
            logger.error(f"Audio file not found: {render_config.audio_path}")
            return
        try:
            with AudioFileClip(str(render_config.audio_path)) as a:
                render_config.target_duration = a.duration
        except Exception as e:
            logger.error(f"Could not read audio file {render_config.audio_path}: {e}")
            return
    elif active_conf.get("duration"):
        render_config.target_duration = active_conf["duration"]
    elif active_conf.get("length_beats"):
        render_config.target_duration = active_conf["length_beats"] * global_beat_dur

    # Parse Effects
    global_vfx_range = parse_range_string(active_conf["vfx_intensity"])
    vfx_configs = [
        parse_effect_string(fx_str, active_conf["vfx_chance"], global_vfx_range)
        for fx_str in active_conf["vfx"]
    ] or [{"name": "none", "chance": 0, "strength_range": (0.0, 0.0)}]

    # Parse Sources
    sources = []
    defaults = {"bpm": active_conf["bpm"], "snippetbeats": active_conf["snippetbeats"]}
    for inp_str in active_conf["inputs"]:
        fname, start, end, bpm, min_b, max_b = ConfigResolver.parse_input_arg(
            inp_str, defaults
        )

        # Resolve the path using the improved utility
        unescaped_fname = unescape_path(fname)
        potential_path = resolve_path(unescaped_fname, project_root)

        if potential_path.exists():
            files = [str(potential_path)]
        else:
            files = glob.glob(str(potential_path))

        if not files:
            logger.warning(f"File or pattern not found: {fname}")
            continue

        for f in files:
            source = MediaSource(Path(f), start, end, bpm, min_b, max_b, len(sources))
            if not source.exhausted:
                sources.append(source)

    if not sources:
        logger.error("No valid media sources available.")
        return

    # Plan Timeline
    planner = TimelinePlanner(
        sources,
        active_conf["modus"],
        vfx_configs,
        active_conf["vfx_maximum"],
        active_conf["vfx_order"],
    )
    edl = planner.create_edl(render_config.target_duration)

    logger.info(
        f"Planning complete: {len(edl)} snippets, total: {planner.global_time:.2f}s "
        f"({planner.global_time / global_beat_dur:.1f} beats)"
    )

    # Render
    if args.dry_run:
        renderer = Renderer(render_config)
        renderer.plan_subtitles()
        logger.info("Dry run finished. Exiting.")
        return

    renderer = Renderer(render_config)
    temp_files = renderer.render_snippets(edl)
    if temp_files:
        renderer.finalize(temp_files)
