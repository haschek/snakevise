import argparse
import glob
import json
import logging
import random
from collections import Counter
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
    parse_duration_string,
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
    g_out.add_argument(
        "--crop",
        action="append",
        help="Initial crop/resize method for input media (default: crop-to-fit). "
        "Supports multiple values and comma-separated options. "
        "Valid choices: crop-to-fit, stretch, slideover, duplicate",
    )
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
    g_time.add_argument(
        "--stfx",
        action="append",
        help="Add a subtitle visual effect. Format: NAME:CHANCE:STRENGTH (e.g., fadein:50:1..3). Available: fadein, fadeout, slidein, slideout, blur",
    )
    g_time.add_argument(
        "--stfx-chance",
        dest="stfx_chance",
        type=float,
        help="Global probability (0-100) for all subtitle effects.",
    )
    g_time.add_argument(
        "--stfx-intensity",
        dest="stfx_intensity",
        type=str,
        help="Global subtitle effect strength/intensity (e.g. 1..3).",
    )
    g_time.add_argument(
        "--stfx-maximum",
        dest="stfx_maximum",
        type=int,
        help="Maximum number of subtitle effects to apply per cue.",
    )
    g_time.add_argument(
        "--stfx-order",
        dest="stfx_order",
        type=str,
        choices=["linear", "random"],
        help="Execution order for subtitle effects.",
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
    g_vfx.add_argument(
        "--fadein", type=str, help="Fade-in duration in Beats or Seconds (e.g. 4, 2.5s)"
    )
    g_vfx.add_argument(
        "--fadeout",
        type=str,
        help="Fade-out duration in Beats or Seconds (e.g. 4, 2.5s)",
    )
    g_vfx.add_argument("--fadecolor", type=str, help="Hex color for fades")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    setup_logging(args.log)
    logger.info("Initializing SnakeVISE...")

    active_conf = ConfigResolver.resolve(args)

    # Validate crop methods
    valid_crops = {"crop-to-fit", "stretch", "slideover", "duplicate"}
    for crop in active_conf.get("crop", []):
        if crop not in valid_crops:
            logger.error(f"Requested crop method '{crop}' does not exist.")
            logger.error(f"Valid crop methods are: {', '.join(sorted(valid_crops))}")
            return

    # Validate VFX
    available_vfx = set(EffectEngine.AVAILABLE_EFFECTS) | {"all", "none"}
    for vfx_str in active_conf.get("vfx", []):
        vfx_name = vfx_str.split(":")[0]
        if vfx_name not in available_vfx:
            logger.error(f"Requested effect '{vfx_name}' does not exist.")
            logger.error(
                f"Valid effects are: {', '.join(sorted(EffectEngine.AVAILABLE_EFFECTS))}"
            )
            return

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
            save_path = Path(args.saveproject).expanduser().absolute()
            save_dir = save_path.parent
            save_conf = active_conf.copy()
            # Don't save internal helper or temporary directory
            save_conf.pop("_project_root", None)
            save_conf.pop("temp", None)

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

            # Relativize output
            if save_conf.get("output"):
                save_conf["output"] = relativize_path(save_conf["output"], save_dir)

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

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(save_conf, f, indent=4)
            logger.info(f"Project configuration saved to: {save_path}")
        except Exception as e:
            logger.error(f"Failed to save project: {e}")

    # Expand dynamic variables (RANDOM:...) into concrete lists
    active_conf = ConfigResolver.expand_dynamic_vars(active_conf)

    # Parse Subtitle VFX

    global_stfx_range = parse_range_string(active_conf["stfx_intensity"])
    stfx_configs = [
        parse_effect_string(fx_str, active_conf["stfx_chance"], global_stfx_range)
        for fx_str in active_conf["stfx"]
    ] or []

    # Prep Render Config
    w, h = map(int, active_conf["resolution"].lower().split("x"))
    global_beat_dur = 60.0 / active_conf["bpm"]

    # Resolve paths (respecting project root if loaded from JSON)
    project_root = active_conf.get("_project_root")

    # Check if JSON had output/temp overrides
    final_output = Path(active_conf.get("output", args.output))
    final_temp = Path(active_conf.get("temp", args.temp))

    # Enforce cloud-ignore naming convention for the temporary directory name
    temp_name = final_temp.name
    if not temp_name.startswith("~"):
        temp_name = "~" + temp_name
    if not temp_name.endswith(".tmp"):
        temp_name = temp_name + ".tmp"
    final_temp = final_temp.with_name(temp_name)

    render_config = RenderConfig(
        output_path=resolve_path(str(final_output), project_root),
        temp_dir=resolve_path(str(final_temp), project_root),
        crop=active_conf["crop"],
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
        subtitle_vfx=stfx_configs,
        subtitle_vfx_chance=float(active_conf["stfx_chance"]),
        subtitle_vfx_intensity=active_conf["stfx_intensity"],
        subtitle_vfx_maximum=active_conf["stfx_maximum"],
        subtitle_vfx_order=active_conf["stfx_order"],
        target_duration=None,
        fade_in=parse_duration_string(active_conf["fadein"], global_beat_dur),
        fade_out=parse_duration_string(active_conf["fadeout"], global_beat_dur),
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
        active_conf["crop"],
    )
    edl = planner.create_edl(render_config.target_duration)

    logger.info(
        f"Planning complete: {len(edl)} snippets, total: {planner.global_time:.2f}s "
        f"({planner.global_time / global_beat_dur:.1f} beats)"
    )

    # Output detailed information about selected snippets
    logger.info("\n" + "=" * 60)
    logger.info("USED VIDEO SNIPPETS")
    logger.info("=" * 60)
    source_stats = Counter()

    for idx, snippet in enumerate(edl, 1):
        matching_source = next(
            (s for s in sources if s.path == snippet.source_path), None
        )
        beat_dur = matching_source.beat_duration if matching_source else global_beat_dur
        beats = snippet.duration / beat_dur
        source_stats[snippet.source_path.name] += 1

        if snippet.vfx:
            vfx_details = []
            for fx in snippet.vfx:
                name = fx.get("name", "none")
                strength = fx.get("strength")
                if strength is not None:
                    vfx_details.append(f"{name}:{strength:.2f}")
                else:
                    vfx_details.append(name)
            vfx_str = " -> ".join(vfx_details)
        else:
            vfx_str = "None"

        logger.info(
            f"Snippet {idx:02d}: {snippet.source_path.name} | "
            f"Length: {beats:.2f} beats ({snippet.duration:.2f}s) | "
            f"Crop: {snippet.crop} | "
            f"Effects: {vfx_str}"
        )

    logger.info("\n" + "=" * 60)
    logger.info("INPUT FILE STATISTICS")
    logger.info("=" * 60)
    for src_name, count in sorted(source_stats.items()):
        logger.info(f"{src_name}: used {count} time(s)")
    logger.info("=" * 60)

    unused_sources = sorted({s.path.name for s in sources} - set(source_stats.keys()))
    logger.info("\n" + "=" * 60)
    logger.info("UNUSED INPUT FILES")
    logger.info("=" * 60)
    if unused_sources:
        for src_name in unused_sources:
            logger.info(f"{src_name}")
    else:
        logger.info("None (all inputs were used)")
    logger.info("=" * 60 + "\n")

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
