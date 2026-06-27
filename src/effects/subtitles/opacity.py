import math
from typing import Optional, Tuple
from moviepy.editor import VideoClip


def apply(
    text_clip: VideoClip,
    stroke_clip: Optional[VideoClip],
    strength: float,
    cue_duration: float,
    video_w: int,
    video_h: int,
    target_x: int,
    target_y: int,
) -> Tuple[VideoClip, Optional[VideoClip]]:
    """Applies an opacity effect to the subtitle text and optional stroke outline.

    The overall combined opacity scales linearly from 87% (0.87) at strength 1 to 39% (0.39) at strength 10.
    """
    strength_clamped = max(1.0, min(10.0, strength))

    # Linear interpolation of combined target opacity: strength 1 -> 0.87, strength 10 -> 0.39
    opacity_final = 0.87 - (strength_clamped - 1.0) / 9.0 * 0.48

    # If both text and stroke layers are present, they are superimposed.
    # We solve: O_final = O_val + O_val * (1 - O_val) = 2*O_val - O_val^2
    # to get: O_val = 1 - sqrt(1 - O_final)
    if stroke_clip:
        opacity_val = 1.0 - math.sqrt(1.0 - opacity_final)
    else:
        opacity_val = opacity_final

    def apply_opacity(clip: VideoClip) -> VideoClip:
        if clip.mask:
            new_mask = clip.mask.fl(lambda get_frame, t: get_frame(t) * opacity_val)
            return clip.set_mask(new_mask)
        return clip

    text_clip = apply_opacity(text_clip)
    if stroke_clip:
        stroke_clip = apply_opacity(stroke_clip)

    return text_clip, stroke_clip
