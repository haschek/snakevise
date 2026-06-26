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
    """Applies a fade-out effect to the subtitle text and optional stroke outline."""
    ratio = min(max(0.0, strength * 0.04), 0.4)
    fade_duration = cue_duration * ratio

    if fade_duration <= 0:
        return text_clip, stroke_clip

    if text_clip.mask:
        text_clip = text_clip.set_mask(text_clip.mask.fadeout(fade_duration))
    else:
        text_clip = text_clip.fadeout(fade_duration)

    if stroke_clip:
        if stroke_clip.mask:
            stroke_clip = stroke_clip.set_mask(stroke_clip.mask.fadeout(fade_duration))
        else:
            stroke_clip = stroke_clip.fadeout(fade_duration)

    return text_clip, stroke_clip
