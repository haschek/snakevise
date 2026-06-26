import logging
import random
import re
import shutil
from pathlib import Path
from typing import List, Optional

import numpy as np
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
)
from PIL import Image, ImageOps

from .effects import EffectEngine
from .models import RenderConfig, Snippet
from .reframing import reframe
from .utils import hex_to_rgb, parse_sub_settings

logger = logging.getLogger("snakevise")


class Renderer:
    """Handles the rendering of snippets and final video assembly."""

    def __init__(self, config: RenderConfig):
        """Initializes the renderer.

        Args:
            config: Rendering configuration.
        """
        self.cfg = config

    def _process_snippet(self, snippet: Snippet) -> Optional[Path]:
        """Processes a single snippet (cropping, resizing, effects).

        Args:
            snippet: Snippet object.

        Returns:
            Path to the temporary rendered file, or None on error.
        """
        clips_to_close = []
        try:
            if not self.cfg.temp_dir.exists():
                self.cfg.temp_dir.mkdir(parents=True, exist_ok=True)

            target_res = self.cfg.resolution

            if not snippet.source_path.exists():
                logger.error(
                    f"Source file not found for snippet {snippet.index}: {snippet.source_path}"
                )
                return None

            if snippet.is_image:
                try:
                    with Image.open(snippet.source_path) as pil_img:
                        pil_img = ImageOps.exif_transpose(pil_img)
                        if pil_img.mode not in ("RGB", "RGBA"):
                            pil_img = pil_img.convert("RGB")
                        img_array = np.array(pil_img)
                    source_clip = ImageClip(img_array)
                except Exception as img_err:
                    logger.warning(
                        f"Failed to read/transpose image {snippet.source_path} using PIL, "
                        f"falling back to MoviePy default: {img_err}"
                    )
                    source_clip = ImageClip(str(snippet.source_path))
                clips_to_close.append(source_clip)
                clip = source_clip.set_duration(snippet.duration)
                clips_to_close.append(clip)
            else:
                source_clip = VideoFileClip(str(snippet.source_path))
                clips_to_close.append(source_clip)
                clip = source_clip.subclip(
                    snippet.start_time, snippet.start_time + snippet.duration
                )
                clips_to_close.append(clip)

            # Reframe to target resolution
            clip = reframe(clip, target_res, method=snippet.crop)
            clips_to_close.append(clip)

            clip = EffectEngine.apply(
                clip, snippet.vfx, self.cfg.bpm, self.cfg.fade_color, self.cfg.fps
            )
            clips_to_close.append(clip)
            temp_file = self.cfg.temp_dir / f"~snip_{snippet.index:05d}.tmp.mp4"
            temp_audio_file = (
                self.cfg.temp_dir / f"~snip_{snippet.index:05d}TEMP_MPY_wvf_snd.tmp.mp4"
            )

            clip.write_videofile(
                str(temp_file),
                fps=self.cfg.fps,
                codec="libx264",
                preset="ultrafast",
                audio_codec="aac",
                temp_audiofile=str(temp_audio_file),
                logger=None,
                verbose=False,
            )
            return temp_file
        except Exception as e:
            logger.error(
                f"Error processing snippet {snippet.index} ({snippet.source_path.name}): {e}"
            )
            return None
        finally:
            for c in reversed(clips_to_close):
                try:
                    c.close()
                except Exception:
                    pass
            import gc

            gc.collect()

    def render_snippets(self, edl: List[Snippet]) -> List[Path]:
        """Renders all snippets in the EDL to temporary files.

        Args:
            edl: List of Snippets.

        Returns:
            List of paths to temporary files.
        """
        if self.cfg.temp_dir.exists():
            shutil.rmtree(self.cfg.temp_dir)
        self.cfg.temp_dir.mkdir(parents=True, exist_ok=True)

        valid_files = []
        total = len(edl)

        logger.info(
            f"Starting physical rendering of {total} snippets to {self.cfg.temp_dir}..."
        )
        for i, snippet in enumerate(edl):
            print(f"\rProgress: {i + 1}/{total}", end="", flush=True)
            path = self._process_snippet(snippet)
            if path:
                valid_files.append(path)
        print("")
        return valid_files

    def plan_subtitles(self) -> None:
        """Parses and logs the subtitle plan without rendering.

        Useful for dry runs.
        """
        if not self.cfg.subtitles_path or not self.cfg.subtitles_path.exists():
            return

        logger.info(f"Planning subtitles from {self.cfg.subtitles_path}...")
        try:
            with open(self.cfg.subtitles_path, "r", encoding="utf-8") as f:
                content = f.read().replace("\r\n", "\n")

            cue_pattern = re.compile(
                r"([\d:.]+)\s*-->\s*([\d:.]+)\s*(.*?)\n(.*?)(?=\n\n|\n*$)", re.DOTALL
            )
            matches = cue_pattern.findall(content)

            vid_w, vid_h = self.cfg.resolution

            for start_str, end_str, settings_str, cue_text in matches:
                try:
                    # 1. Parsing
                    raw_text = cue_text.strip()
                    raw_lower = raw_text.lower()
                    is_bold = "<b>" in raw_lower or "<strong>" in raw_lower
                    is_italic = "<i>" in raw_lower or "<em>" in raw_lower
                    is_underline = "<u>" in raw_lower
                    clean_text = re.sub(r"<[^>]+>", "", raw_text)
                    if not clean_text:
                        continue

                    h_align, v_align = parse_sub_settings(settings_str)

                    # 2. Position Simulation (using config resolution)
                    # Support size property (width percentage)
                    size_val = 0.9
                    size_match = re.search(r"size:(\d+)%", settings_str.lower())
                    if size_match:
                        size_val = int(size_match.group(1)) / 100.0

                    sim_txt_w = vid_w * size_val
                    sim_txt_h = 60

                    pos_x = "center"
                    pos_y = "center"

                    if h_align == "left":
                        pos_x = int(vid_w * 0.05)
                    elif h_align == "right":
                        pos_x = int(vid_w - sim_txt_w - (vid_w * 0.05))

                    if v_align == "top":
                        pos_y = int(vid_h * 0.05)
                    elif v_align == "bottom":
                        pos_y = int(vid_h - sim_txt_h - (vid_h * 0.05))

                    style_info = (
                        "/".join(
                            filter(
                                None,
                                [
                                    is_bold and "Bold",
                                    is_italic and "Italic",
                                    is_underline and "Underline",
                                ],
                            )
                        )
                        or "Normal"
                    )

                    logger.info(
                        f'Subtitle Plan: "{clean_text[:30]}..." | Style: {style_info} | '
                        f"Align: {h_align} | Line: {v_align} | Target Pos: {pos_x},{pos_y}"
                    )
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Error planning subtitles: {e}")

    def _apply_subtitles(
        self, video: VideoFileClip, clips_to_close: List
    ) -> VideoFileClip:
        """Manually parses WebVTT and overlays subtitles on the video.

        This bypasses library limitations by using regex to extract cues and settings.
        """
        if not self.cfg.subtitles_path or not self.cfg.subtitles_path.exists():
            return video

        from .utils import check_font_renderable, get_compatible_fonts
        from .effects.subtitles import fadein, fadeout, slidein, slideout

        requested_fonts = self.cfg.subtitle_fonts
        if not requested_fonts:
            requested_fonts = [None]

        working_fonts = []
        logger.info(f"Validating {len(requested_fonts)} subtitle fonts...")

        for f in requested_fonts:
            if check_font_renderable(f):
                working_fonts.append(f)
            else:
                logger.warning(f"Font '{f}' is not renderable. Skipping.")

        if not working_fonts:
            logger.warning(
                "No requested fonts are renderable. Searching for alternatives..."
            )
            alternatives = get_compatible_fonts()
            for alt in alternatives:
                if check_font_renderable(alt):
                    logger.info(f"Found alternative working font: {alt}")
                    working_fonts.append(alt)
                    break  # Just need one as a baseline

            if not working_fonts:
                # Try system default as last resort
                if check_font_renderable(None):
                    working_fonts.append(None)
                else:
                    logger.error(
                        "Absolutely no working fonts found. Subtitles may fail."
                    )

        # Update config with actually working fonts for reference
        self.cfg.subtitle_fonts = working_fonts
        logger.info(
            f"Working subtitle fonts: {', '.join([str(f) for f in working_fonts])}"
        )

        logger.info(f"Applying subtitles from {self.cfg.subtitles_path}...")
        try:
            with open(self.cfg.subtitles_path, "r", encoding="utf-8") as f:
                content = f.read().replace("\r\n", "\n")

            # Regex for WebVTT Cues:
            # 1. Start Timestamp
            # 2. End Timestamp
            # 3. Settings (the rest of the timestamp line)
            # 4. Text (until next empty line or end of file)
            cue_pattern = re.compile(
                r"([\d:.]+)\s*-->\s*([\d:.]+)\s*(.*?)\n(.*?)(?=\n\n|\n*$)", re.DOTALL
            )

            matches = cue_pattern.findall(content)
            if not matches:
                logger.warning("No valid WebVTT cues found in the file.")
                return video

            subtitle_clips = []

            def time_to_seconds(t_str):
                parts = t_str.split(":")
                if len(parts) == 3:  # HH:MM:SS.mmm
                    return (
                        float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    )
                if len(parts) == 2:  # MM:SS.mmm
                    return float(parts[0]) * 60 + float(parts[1])
                return float(t_str)

            for start_str, end_str, settings_str, cue_text in matches:
                try:
                    # 1. Timing
                    start = time_to_seconds(start_str.strip())
                    end = time_to_seconds(end_str.strip())

                    if start >= video.duration:
                        continue
                    duration = min(end - start, video.duration - start)
                    if duration <= 0:
                        continue

                    # 2. Styling tags (case-insensitive)
                    raw_text = cue_text.strip()
                    raw_lower = raw_text.lower()
                    is_bold = "<b>" in raw_lower or "<strong>" in raw_lower
                    is_italic = "<i>" in raw_lower or "<em>" in raw_lower
                    is_underline = "<u>" in raw_lower

                    # Strip all tags for rendering
                    clean_text = re.sub(r"<[^>]+>", "", raw_text)
                    if not clean_text:
                        continue

                    # 3. Parse Settings
                    h_align, v_align = parse_sub_settings(settings_str)

                    size_val = 0.9
                    size_match = re.search(r"size:(\d+)%", settings_str.lower())
                    if size_match:
                        size_val = int(size_match.group(1)) / 100.0

                    # 4. Create TextClip with Font Variants
                    # ImageMagick gravity names for 'align' parameter
                    gravity_map = {"left": "West", "right": "East", "center": "Center"}

                    # Randomly select one of our working base fonts for this cue
                    base_font = random.choice(working_fonts)

                    # Randomly select font size and stroke width
                    base_size = random.choice(self.cfg.subtitle_fontsizes)
                    base_stroke = random.choice(self.cfg.subtitle_strokewidths)

                    # Randomly select colors
                    base_color = random.choice(self.cfg.subtitle_colors)
                    base_scolor = random.choice(self.cfg.subtitle_stroke_colors)

                    font_args_fill = {
                        "fontsize": base_size,
                        "color": base_color,
                        "method": "caption",
                        "align": gravity_map.get(h_align, "Center"),
                        "size": (video.w * size_val, None),
                    }

                    if base_stroke > 0:
                        font_args_stroke = {
                            "fontsize": base_size,
                            "color": base_scolor,
                            "stroke_color": base_scolor,
                            "stroke_width": 2 * base_stroke,
                            "method": "caption",
                            "align": gravity_map.get(h_align, "Center"),
                            "size": (video.w * size_val, None),
                        }

                    if is_underline:
                        # MoviePy's TextClip doesn't natively support 'decorate' in all versions.
                        # We skip it to avoid crashes, focusing on bold/italic/positioning.
                        pass

                    fonts_to_try = []
                    if base_font:
                        if is_bold and is_italic:
                            fonts_to_try = [
                                f"{base_font}-BoldItalic",
                                f"{base_font} Bold Italic",
                                f"{base_font}-Bold-Italic",
                                f"{base_font}BoldItalic",
                            ]
                        elif is_bold:
                            fonts_to_try = [
                                f"{base_font}-Bold",
                                f"{base_font} Bold",
                                f"{base_font}Bold",
                            ]
                        elif is_italic:
                            fonts_to_try = [
                                f"{base_font}-Italic",
                                f"{base_font} Italic",
                                f"{base_font}Italic",
                            ]
                        fonts_to_try.append(base_font)

                    txt_stroke = None
                    txt_fill = None
                    used_font = "default"
                    if fonts_to_try:
                        for font_variant in fonts_to_try:
                            try:
                                t_stroke = None
                                if base_stroke > 0:
                                    t_stroke = TextClip(
                                        clean_text,
                                        font=font_variant,
                                        **font_args_stroke,
                                    )
                                t_fill = TextClip(
                                    clean_text, font=font_variant, **font_args_fill
                                )

                                if t_stroke:
                                    txt_stroke = t_stroke
                                    clips_to_close.append(txt_stroke)
                                txt_fill = t_fill
                                clips_to_close.append(txt_fill)
                                used_font = font_variant
                                break
                            except Exception:
                                if t_stroke:
                                    try:
                                        t_stroke.close()
                                    except Exception:
                                        pass
                                continue

                    if not txt_fill:
                        # Final attempt: use what MoviePy considers default (no font arg)
                        try:
                            if base_stroke > 0:
                                txt_stroke = TextClip(clean_text, **font_args_stroke)
                                clips_to_close.append(txt_stroke)
                            txt_fill = TextClip(clean_text, **font_args_fill)
                            clips_to_close.append(txt_fill)
                            used_font = "system-default"
                        except Exception:
                            if txt_stroke:
                                try:
                                    txt_stroke.close()
                                except Exception:
                                    pass
                            raise RuntimeError(
                                "Could not create TextClip with any font variant."
                            )

                    # 5. Parse VFX / Animations
                    cue_vfx = []

                    # Check for inline WebVTT vfx overrides
                    fadein_match = re.search(
                        r"vfx:fadein:([\d.]+)", settings_str.lower()
                    )
                    if fadein_match:
                        cue_vfx.append(
                            {"name": "fadein", "strength": float(fadein_match.group(1))}
                        )

                    fadeout_match = re.search(
                        r"vfx:fadeout:([\d.]+)", settings_str.lower()
                    )
                    if fadeout_match:
                        cue_vfx.append(
                            {
                                "name": "fadeout",
                                "strength": float(fadeout_match.group(1)),
                            }
                        )

                    slidein_match = re.search(
                        r"vfx:slidein:([a-zA-Z]+)(?::([\d.]+))?", settings_str.lower()
                    )
                    if slidein_match:
                        direction = slidein_match.group(1)
                        dur = (
                            float(slidein_match.group(2))
                            if slidein_match.group(2)
                            else 0.2
                        )
                        cue_vfx.append(
                            {
                                "name": "slidein",
                                "strength": 0.0,
                                "_direct": (direction, dur),
                            }
                        )

                    slideout_match = re.search(
                        r"vfx:slideout:([a-zA-Z]+)(?::([\d.]+))?", settings_str.lower()
                    )
                    if slideout_match:
                        direction = slideout_match.group(1)
                        dur = (
                            float(slideout_match.group(2))
                            if slideout_match.group(2)
                            else 0.2
                        )
                        cue_vfx.append(
                            {
                                "name": "slideout",
                                "strength": 0.0,
                                "_direct": (direction, dur),
                            }
                        )

                    # Select global probabilistic subtitle effects for this cue
                    global_cue_vfx = EffectEngine.select_effects(
                        configs=self.cfg.subtitle_vfx,
                        max_limit=self.cfg.subtitle_vfx_maximum,
                        order=self.cfg.subtitle_vfx_order,
                    )

                    # WebVTT direct cue effects override global effects of the same name
                    final_cue_vfx = list(cue_vfx)
                    cue_vfx_names = {fx["name"] for fx in cue_vfx}
                    for fx in global_cue_vfx:
                        if fx["name"] not in cue_vfx_names:
                            final_cue_vfx.append(fx)

                    # Calculate target absolute numeric coordinates (relative to txt_fill dimensions)
                    if h_align == "left":
                        target_x = int(video.w * 0.05)
                    elif h_align == "right":
                        target_x = video.w - txt_fill.w - int(video.w * 0.05)
                    else:
                        target_x = int((video.w - txt_fill.w) / 2)

                    if v_align == "top":
                        target_y = int(video.h * 0.05)
                    elif v_align == "bottom":
                        target_y = video.h - txt_fill.h - int(video.h * 0.05)
                    else:
                        target_y = int((video.h - txt_fill.h) / 2)

                    # Initial timing/positioning of clips
                    if txt_stroke:
                        txt_stroke_final = txt_stroke.set_start(start).set_duration(
                            duration
                        )
                    else:
                        txt_stroke_final = None

                    txt_fill_final = (
                        txt_fill.set_start(start)
                        .set_duration(duration)
                        .set_position((target_x, target_y))
                    )

                    # Apply visual effects sequentially via plugins
                    for fx in final_cue_vfx:
                        name = fx["name"]
                        strength_val = (
                            fx["_direct"] if "_direct" in fx else fx["strength"]
                        )

                        if name == "slidein":
                            txt_fill_final, txt_stroke_final = slidein.apply(
                                txt_fill_final,
                                txt_stroke_final,
                                strength_val,
                                duration,
                                video.w,
                                video.h,
                                target_x,
                                target_y,
                            )
                        elif name == "slideout":
                            txt_fill_final, txt_stroke_final = slideout.apply(
                                txt_fill_final,
                                txt_stroke_final,
                                strength_val,
                                duration,
                                video.w,
                                video.h,
                                target_x,
                                target_y,
                            )
                        elif name == "fadein":
                            txt_fill_final, txt_stroke_final = fadein.apply(
                                txt_fill_final,
                                txt_stroke_final,
                                strength_val,
                                duration,
                                video.w,
                                video.h,
                                target_x,
                                target_y,
                            )
                        elif name == "fadeout":
                            txt_fill_final, txt_stroke_final = fadeout.apply(
                                txt_fill_final,
                                txt_stroke_final,
                                strength_val,
                                duration,
                                video.w,
                                video.h,
                                target_x,
                                target_y,
                            )

                    # Append to final lists
                    if txt_stroke_final:
                        clips_to_close.append(txt_stroke_final)
                        subtitle_clips.append(txt_stroke_final)

                    clips_to_close.append(txt_fill_final)
                    subtitle_clips.append(txt_fill_final)

                    logger.info(
                        f'Subtitle Cue: "{clean_text[:30]}..." | Style: {"/".join(filter(None, [is_bold and "Bold", is_italic and "Italic", is_underline and "Underline"])) or "Normal"} | '
                        f"Font: {used_font} | Size: {base_size} | Stroke: {base_stroke} | Color: {base_color} | SColor: {base_scolor} | Align: {h_align} | Line: {v_align} | Pos: {target_x},{target_y} | VFX: {[fx['name'] for fx in final_cue_vfx]}"
                    )
                except Exception as cue_err:
                    logger.warning(f"Skipping subtitle cue at {start_str}: {cue_err}")
                    continue

            if not subtitle_clips:
                logger.warning("No valid subtitle clips could be generated.")
                return video

            logger.info(f"Overlaying {len(subtitle_clips)} subtitle clips...")
            composite = CompositeVideoClip([video] + subtitle_clips, size=video.size)
            clips_to_close.append(composite)
            return composite

        except Exception as e:
            logger.error(f"Failed to apply subtitles: {e}")
            logger.error("Troubleshooting Subtitles:")
            logger.error(
                "1. Ensure ImageMagick is installed and in your PATH (use 'magick' for IMv7)."
            )
            logger.error(
                "2. If on Linux, try installing 'ttf-mscorefonts-installer' or 'fonts-liberation'."
            )
            logger.error(
                "3. Try a different font with --stfont (e.g., --stfont Liberation-Sans or --stfont DejaVu-Sans)."
            )
            logger.error(
                "4. Check if MoviePy can find fonts by running: python -c 'from moviepy.config import change_settings; from moviepy.editor import TextClip; print(TextClip.list(\"font\"))'"
            )
            return video

    def finalize(self, clip_paths: List[Path]) -> None:
        """Concatenates all snippet files and adds audio/fades.

        Args:
            clip_paths: List of rendered snippet file paths.
        """
        if not clip_paths:
            logger.error("No valid clips to concatenate.")
            return

        joined_video_path = self.cfg.temp_dir / "~joined_snippets.tmp.mp4"
        clips_to_close = []
        try:
            # 1. Memory-efficient concatenation using ffmpeg concat demuxer
            logger.info(f"Joining {len(clip_paths)} snippets using ffmpeg...")
            concat_file = self.cfg.temp_dir / "~concat_list.tmp.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                for p in clip_paths:
                    # ffmpeg concat needs absolute paths or relative to the txt file
                    f.write(f"file '{p.absolute()}'\n")

            import subprocess

            # We use -c copy because all snippets were rendered with identical settings in _process_snippet
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                "-loglevel",
                "error",
                str(joined_video_path),
            ]
            subprocess.run(cmd, check=True)

            # 2. Load the single joined file for master effects (fades, audio, subtitles)
            logger.info("Applying master effects (audio, fades, subtitles)...")
            joined_clip = VideoFileClip(str(joined_video_path))
            clips_to_close.append(joined_clip)
            final_video = joined_clip

            if self.cfg.audio_path:
                audio_clip = AudioFileClip(str(self.cfg.audio_path))
                clips_to_close.append(audio_clip)
                final_video = final_video.set_audio(audio_clip)
                clips_to_close.append(final_video)
                if self.cfg.target_duration:
                    final_video = final_video.set_duration(self.cfg.target_duration)
                    clips_to_close.append(final_video)

            fade_rgb = hex_to_rgb(self.cfg.fade_color)
            if self.cfg.fade_in > 0:
                final_video = final_video.fadein(
                    self.cfg.fade_in, initial_color=fade_rgb
                )
                clips_to_close.append(final_video)
            if self.cfg.fade_out > 0:
                final_video = final_video.fadeout(
                    self.cfg.fade_out, final_color=fade_rgb
                )
                clips_to_close.append(final_video)

            # --- Apply Subtitles ---
            final_video = self._apply_subtitles(final_video, clips_to_close)
            # -----------------------

            temp_audio_file = (
                self.cfg.temp_dir
                / f"~{self.cfg.output_path.stem}TEMP_MPY_wvf_snd.tmp.mp4"
            )
            params = {
                "fps": self.cfg.fps,
                "codec": self.cfg.codec,
                "audio_codec": "aac",
                "preset": "slower" if self.cfg.optimize else "medium",
                "threads": 4,
                "temp_audiofile": str(temp_audio_file),
            }
            if self.cfg.optimize:
                params["ffmpeg_params"] = ["-crf", "26"]

            logger.info(f"Rendering final file: {self.cfg.output_path}")
            final_video.write_videofile(str(self.cfg.output_path), **params)

        except Exception as e:
            logger.critical(f"Critical error during finalization: {e}", exc_info=True)
            raise e
        finally:
            logger.info("Cleaning up resources...")
            for clip in reversed(clips_to_close):
                try:
                    clip.close()
                except Exception:
                    pass
            import gc

            gc.collect()

            if self.cfg.temp_dir.exists():
                shutil.rmtree(self.cfg.temp_dir)
            logger.info("Done.")
