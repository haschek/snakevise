import logging
import shutil
from pathlib import Path
from typing import List, Optional

from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx,
)

from .effects import EffectEngine
from .models import RenderConfig, Snippet
from .reframing import reframe
from .utils import hex_to_rgb

logger = logging.getLogger("vidseq")


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
        try:
            if not self.cfg.temp_dir.exists():
                self.cfg.temp_dir.mkdir(parents=True, exist_ok=True)

            target_res = self.cfg.resolution

            if not snippet.source_path.exists():
                logger.error(f"Source file not found for snippet {snippet.index}: {snippet.source_path}")
                return None

            if snippet.is_image:
                clip = ImageClip(str(snippet.source_path)).set_duration(snippet.duration)
            else:
                clip = VideoFileClip(str(snippet.source_path)).subclip(
                    snippet.start_time, snippet.start_time + snippet.duration
                )

            # Reframe to target resolution
            clip = reframe(clip, target_res, method="fill")

            clip = EffectEngine.apply(
                clip, snippet.vfx, self.cfg.bpm, self.cfg.fade_color, self.cfg.fps
            )
            temp_file = self.cfg.temp_dir / f"snip_{snippet.index:05d}.mp4"

            clip.write_videofile(
                str(temp_file),
                fps=self.cfg.fps,
                codec="libx264",
                preset="ultrafast",
                audio_codec="aac",
                logger=None,
                verbose=False,
            )
            clip.close()
            return temp_file
        except Exception as e:
            logger.error(
                f"Error processing snippet {snippet.index} ({snippet.source_path.name}): {e}"
            )
            return None

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
            print(f"\rProgress: {i+1}/{total}", end="", flush=True)
            path = self._process_snippet(snippet)
            if path:
                valid_files.append(path)
        print("")
        return valid_files

    def finalize(self, clip_paths: List[Path]) -> None:
        """Concatenates all snippet files and adds audio/fades.

        Args:
            clip_paths: List of rendered snippet file paths.
        """
        if not clip_paths:
            logger.error("No valid clips to concatenate.")
            return

        clips = []
        audio = None
        try:
            logger.info("Concatenating snippets (Chain Mode)...")
            clips = [VideoFileClip(str(p)) for p in clip_paths]
            
            if not clips:
                logger.error("Failed to load any clips for finalization.")
                return

            final_video = concatenate_videoclips(clips, method="chain")

            if self.cfg.audio_path:
                audio = AudioFileClip(str(self.cfg.audio_path))
                final_video = final_video.set_audio(audio)
                if self.cfg.target_duration:
                    final_video = final_video.set_duration(self.cfg.target_duration)

            fade_rgb = hex_to_rgb(self.cfg.fade_color)
            if self.cfg.fade_in > 0:
                final_video = final_video.fadein(self.cfg.fade_in, initial_color=fade_rgb)
            if self.cfg.fade_out > 0:
                final_video = final_video.fadeout(self.cfg.fade_out, final_color=fade_rgb)

            params = {
                "fps": self.cfg.fps,
                "codec": self.cfg.codec,
                "audio_codec": "aac",
                "preset": "slower" if self.cfg.optimize else "medium",
                "threads": 4,
            }
            if self.cfg.optimize:
                params["ffmpeg_params"] = ["-crf", "26"]

            logger.info(f"Rendering final file: {self.cfg.output_path}")
            final_video.write_videofile(str(self.cfg.output_path), **params)

            logger.info("Cleaning up resources...")
            final_video.close()
            if audio:
                audio.close()
            for c in clips:
                try:
                    c.close()
                except Exception:
                    pass

            if self.cfg.temp_dir.exists():
                shutil.rmtree(self.cfg.temp_dir)
            logger.info("Done.")

        except Exception as e:
            logger.critical(f"Critical error during finalization: {e}", exc_info=True)
            # Cleanup even on error
            if audio:
                try: audio.close()
                except: pass
            for c in clips:
                try: c.close()
                except: pass
