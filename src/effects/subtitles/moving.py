import random
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
    """Applies a moving effect to the subtitle text and optional stroke outline.

    The subtitles move smoothly between random positions. The displacement
    distance and the number of movements are coupled to strength.
    """
    strength_clamped = max(1.0, min(10.0, strength))

    # Minimum hold duration per position (e.g., 150ms) to maintain readability
    min_hold_duration = 0.15

    # Determine maximum number of movements/jumps allowed within cue_duration
    max_intervals = max(1, int(cue_duration / min_hold_duration))
    max_jumps = max_intervals - 1

    # Number of movements is coupled to strength
    rate = strength_clamped
    min_jumps = strength_clamped
    expected_jumps = cue_duration * rate
    num_jumps = int(round(max(min_jumps, expected_jumps)))
    num_jumps = min(num_jumps, max_jumps)
    num_jumps = max(0, num_jumps)

    if num_jumps == 0:
        return text_clip, stroke_clip

    # Calculate maximum displacement per axis based on font size:
    # strength 1 -> 15% of font size, strength 10 -> 40% of font size
    font_size = getattr(text_clip, "fontsize", 40.0)
    percent = 0.15 + (strength_clamped - 1.0) / 9.0 * 0.25
    max_disp = font_size * percent
    # Minimum offset is 1/3 of the maximum possible displacement
    min_disp = max_disp / 3.0

    # Pre-generate offsets (Interval 0 starts at 0, 0)
    sgn_x = random.choice([-1, 1])
    sgn_y = random.choice([-1, 1])

    offsets = []
    offsets.append((0.0, 0.0))

    for _ in range(num_jumps):
        mag_x = random.uniform(min_disp, max_disp)
        mag_y = random.uniform(min_disp, max_disp)
        offsets.append((sgn_x * mag_x, sgn_y * mag_y))
        sgn_x = -sgn_x
        sgn_y = -sgn_y

    interval_len = cue_duration / (num_jumps + 1)

    # Continuous movement: transition spans the entire interval length (no stationary pause)
    transition_dur = interval_len

    # Position function for fill clip
    original_fill_pos = text_clip.pos

    def fill_pos_fn(t):
        interval_idx = min(int(t / interval_len), len(offsets) - 1)
        start_t = interval_idx * interval_len

        # Get target displacement for the current interval
        dx_curr, dy_curr = offsets[interval_idx]

        # Get previous displacement (for transition)
        if interval_idx > 0:
            dx_prev, dy_prev = offsets[interval_idx - 1]
        else:
            dx_prev, dy_prev = 0.0, 0.0

        # Calculate smooth interpolation if we are in the transition window
        time_in_interval = t - start_t
        if time_in_interval < transition_dur and transition_dur > 0:
            progress = time_in_interval / transition_dur
            # Smoothstep (cubic ease-in-out)
            ease_progress = progress * progress * (3.0 - 2.0 * progress)
            dx = dx_prev + (dx_curr - dx_prev) * ease_progress
            dy = dy_prev + (dy_curr - dy_prev) * ease_progress
        else:
            dx, dy = dx_curr, dy_curr

        if callable(original_fill_pos):
            orig_x, orig_y = original_fill_pos(t)
        else:
            orig_x, orig_y = target_x, target_y

        return (int(round(orig_x + dx)), int(round(orig_y + dy)))

    text_clip = text_clip.set_position(fill_pos_fn)

    # Apply same offset transitions to stroke clip if present
    if stroke_clip:
        fill_w, fill_h = text_clip.w, text_clip.h
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
                fill_x, fill_y = target_x, target_y
            return (int(round(fill_x + off_x)), int(round(fill_y + off_y)))

        stroke_clip = stroke_clip.set_position(stroke_pos_fn)

    return text_clip, stroke_clip
