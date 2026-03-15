from typing import Tuple
from moviepy.editor import VideoClip, vfx


def apply(clip: VideoClip, target_res: Tuple[int, int]) -> VideoClip:
    """Crops the clip to fill the target resolution, maintaining aspect ratio.

    Args:
        clip: The source clip.
        target_res: The (width, height) tuple of the target resolution.

    Returns:
        The reframed and resized clip.
    """
    w_s, h_s = clip.size
    w_t, h_t = target_res
    target_ar, source_ar = w_t / h_t, w_s / h_s

    if source_ar > target_ar:
        # Source is wider than target
        new_h, new_w = h_s, h_s * target_ar
    else:
        # Source is taller than target
        new_w, new_h = w_s, w_s / target_ar

    clip = clip.fx(
        vfx.crop, x_center=w_s / 2, y_center=h_s / 2, width=new_w, height=new_h
    )
    clip = clip.resize(newsize=target_res)

    return clip
