import random
from typing import Any, Dict, List, Optional

from moviepy.editor import VideoClip

from .video import (
    asciiart,
    blackwhite,
    colorshift,
    dataglitch,
    glitchchroma,
    glitchmotion,
    grain,
    mirror,
    newspaper,
    oldmovie,
    pixelize,
    posterize,
    reverse,
    shutterecho,
    speed,
    stopmotion,
    terminal,
    tvscreen,
    zoomin,
    zoomout,
)


class EffectEngine:
    """Engine for selecting and applying visual effects to video clips."""

    AVAILABLE_EFFECTS = [
        "zoomin",
        "zoomout",
        "glitchchroma",
        "glitchmotion",
        "mirror",
        "grain",
        "speed",
        "blackwhite",
        "posterize",
        "reverse",
        "stopmotion",
        "pixelize",
        "oldmovie",
        "colorshift",
        "shutterecho",
        "tvscreen",
        "newspaper",
        "terminal",
        "dataglitch",
        "asciiart",
    ]

    @staticmethod
    def select_effects(
        configs: List[Dict[str, Any]], max_limit: Optional[int] = None, order: str = "linear"
    ) -> List[Dict[str, Any]]:
        """Selects effects based on probability configurations.

        Args:
            configs: List of effect configurations.
            max_limit: Maximum number of effects to select.
            order: 'linear' or 'random' order of selection.

        Returns:
            List of selected effects with specific strengths.
        """
        processed_configs = []

        for c in configs:
            if c["name"] == "all":
                for name in EffectEngine.AVAILABLE_EFFECTS:
                    processed_configs.append(
                        {
                            "name": name,
                            "chance": c["chance"],
                            "strength_range": c["strength_range"],
                        }
                    )
            else:
                processed_configs.append(c)

        candidates = []
        for fx in processed_configs:
            if fx["name"] != "none" and random.random() * 100 <= fx["chance"]:
                min_s, max_s = fx["strength_range"]
                actual_strength = (
                    min_s if min_s == max_s else random.uniform(min_s, max_s)
                )
                candidates.append({"name": fx["name"], "strength": actual_strength})

        if order == "random":
            random.shuffle(candidates)

        if max_limit is not None:
            planned = candidates[:max_limit]
        else:
            planned = candidates

        return planned

    @staticmethod
    def apply(
        clip: VideoClip,
        vfx: List[Dict[str, Any]],
        bpm: float,
        fade_color: str,
        target_fps: int,
    ) -> VideoClip:
        """Applies a list of effects to a clip.

        Args:
            clip: The clip to process.
            vfx: List of effect definitions.
            bpm: Current BPM.
            fade_color: Fade color for background.
            target_fps: Target frames per second.

        Returns:
            The processed clip.
        """
        # Dispatch table for effects mapping to their modular apply functions
        dispatch = {
            "mirror": lambda c, s: mirror.apply(c, s),
            "blackwhite": lambda c, s: blackwhite.apply(c, s),
            "speed": lambda c, s: speed.apply(c, s),
            "zoomin": lambda c, s: zoomin.apply(c, s),
            "zoomout": lambda c, s: zoomout.apply(c, s),
            "grain": lambda c, s: grain.apply(c, s),
            "posterize": lambda c, s: posterize.apply(c, s),
            "reverse": lambda c, s: reverse.apply(c, s, bpm),
            "stopmotion": lambda c, s: stopmotion.apply(c, s, bpm, target_fps),
            "glitchmotion": lambda c, s: glitchmotion.apply(c, s, bpm),
            "pixelize": lambda c, s: pixelize.apply(c, s),
            "oldmovie": lambda c, s: oldmovie.apply(c, s, fade_color),
            "colorshift": lambda c, s: colorshift.apply(c, s),
            "shutterecho": lambda c, s: shutterecho.apply(c, s),
            "glitchchroma": lambda c, s: glitchchroma.apply(c, s),
            "tvscreen": lambda c, s: tvscreen.apply(c, s),
            "newspaper": lambda c, s: newspaper.apply(c, s),
            "terminal": lambda c, s: terminal.apply(c, s),
            "dataglitch": lambda c, s: dataglitch.apply(c, s),
            "asciiart": lambda c, s: asciiart.apply(c, s, fade_color),
        }

        for fx in vfx:
            s = fx["strength"]
            name = fx["name"]
            if name in dispatch:
                clip = dispatch[name](clip, s)

        return clip
