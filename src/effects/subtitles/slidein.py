import random
from typing import Optional, Tuple, Union
from moviepy.editor import VideoClip


def apply(
    text_clip: VideoClip,
    stroke_clip: Optional[VideoClip],
    strength: Union[float, Tuple[str, float]],
    cue_duration: float,
    video_w: int,
    video_h: int,
    target_x: int,
    target_y: int,
) -> Tuple[VideoClip, Optional[VideoClip]]:
    """Applies a slide-in transition to the subtitle text and optional stroke outline.

    All slide calculations, direction choices, and relative offsets run inside the plugin.
    """
    if isinstance(strength, tuple):
        direction, ratio = strength
    else:
        val = int(round(strength))
        directions = ["bottom", "top", "left", "right"]
        if val <= 1:
            direction, ratio = "bottom", 0.25
        elif val == 2:
            direction, ratio = "bottom", 0.12
        elif val == 3:
            direction, ratio = "top", 0.25
        elif val == 4:
            direction, ratio = "top", 0.12
        elif val == 5:
            direction, ratio = "left", 0.25
        elif val == 6:
            direction, ratio = "left", 0.12
        elif val == 7:
            direction, ratio = "right", 0.25
        elif val == 8:
            direction, ratio = "right", 0.12
        elif val == 9:
            direction, ratio = random.choice(directions), 0.25
        else:  # val >= 10
            direction, ratio = random.choice(directions), 0.12

    ratio = min(max(0.0, ratio), 0.5)
    slide_duration = cue_duration * ratio
    if slide_duration <= 0 or not direction:
        return text_clip, stroke_clip

    # Get fill dimensions
    fill_w, fill_h = text_clip.w, text_clip.h
    original_fill_pos = text_clip.pos

    # Apply slide-in to text_clip pos_fn
    def fill_pos_fn(t):
        if t >= slide_duration:
            if callable(original_fill_pos):
                return original_fill_pos(t)
            return (target_x, target_y)

        progress = t / slide_duration
        ease_progress = 1.0 - (1.0 - progress) ** 2

        if direction == "left":
            x = -fill_w + (target_x + fill_w) * ease_progress
            return (int(x), target_y)
        elif direction == "right":
            x = video_w - (video_w - target_x) * ease_progress
            return (int(x), target_y)
        elif direction == "top":
            y = -fill_h + (target_y + fill_h) * ease_progress
            return (target_x, int(y))
        elif direction == "bottom":
            y = video_h - (video_h - target_y) * ease_progress
            return (target_x, int(y))
        return (target_x, target_y)

    text_clip = text_clip.set_position(fill_pos_fn)

    # Apply stroke alignment if present
    if stroke_clip:
        stroke_w, stroke_h = stroke_clip.w, stroke_clip.h
        stroke_offset_x = (fill_w - stroke_w) / 2
        stroke_offset_y = (fill_h - stroke_h) / 2
        original_fill_pos_capture = text_clip.pos

        def stroke_pos_fn(
            t,
            orig_pos=original_fill_pos_capture,
            off_x=stroke_offset_x,
            off_y=stroke_offset_y,
        ):
            if callable(orig_pos):
                fill_x, fill_y = orig_pos(t)
            else:
                fill_x, fill_y = orig_pos
            return (int(fill_x + off_x), int(fill_y + off_y))

        stroke_clip = stroke_clip.set_position(stroke_pos_fn)

    return text_clip, stroke_clip
