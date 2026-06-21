"""Reframing package for handling aspect ratio conversions and cropping."""

from typing import Tuple
from moviepy.editor import VideoClip
from . import fill, slideover


def reframe(
    clip: VideoClip, target_res: Tuple[int, int], method: str = "crop-to-fit"
) -> VideoClip:
    """Applies reframing to a clip.

    Args:
        clip: The source clip.
        target_res: Target (width, height).
        method: Reframing method (default is "crop-to-fit").

    Returns:
        The reframed clip.
    """
    if method in ("fill", "crop-to-fit"):
        return fill.apply(clip, target_res)
    elif method == "slideover":
        return slideover.apply(clip, target_res)

    # Default fallback
    return clip.resize(newsize=target_res)
