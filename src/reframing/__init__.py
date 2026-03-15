"""Reframing package for handling aspect ratio conversions and cropping."""

from typing import Tuple
from moviepy.editor import VideoClip
from . import fill

def reframe(clip: VideoClip, target_res: Tuple[int, int], method: str = "fill") -> VideoClip:
    """Applies reframing to a clip.

    Args:
        clip: The source clip.
        target_res: Target (width, height).
        method: Reframing method (default is "fill").

    Returns:
        The reframed clip.
    """
    if method == "fill":
        return fill.apply(clip, target_res)
    
    # Default fallback
    return clip.resize(newsize=target_res)
