import random
import numpy as np
from typing import Optional, Tuple
from moviepy.editor import VideoClip, ColorClip


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
    """Applies a flickering effect to the subtitle text and optional stroke outline.

    The text disappears completely for a few milliseconds at random times.
    The number of flickers is determined by the strength (1 to 10).
    """
    # Clamp strength to the supported range (1 to 10)
    strength_clamped = max(1.0, min(10.0, strength))

    # Calculate number of flickers based on the requirements:
    # - strength 1 = 1/s, min 1 per cue
    # - strength 10 = 10/s, min 10 per cue
    rate = strength_clamped
    min_flickers = strength_clamped
    flickers_by_rate = cue_duration * rate
    num_flickers = int(round(max(min_flickers, flickers_by_rate)))

    # Determine flicker duration (typically between 15ms and 45ms for a brief flicker)
    min_dur = 0.015
    max_dur = 0.045

    # Generate non-overlapping flicker intervals using segment partitioning
    flicker_intervals = []
    segment_len = cue_duration / num_flickers
    for i in range(num_flickers):
        dur = random.uniform(min_dur, max_dur)
        if dur >= segment_len:
            dur = segment_len * 0.6  # Ensure flicker doesn't consume the entire segment

        seg_start = i * segment_len
        max_offset = segment_len - dur
        offset = random.uniform(0.0, max_offset)
        flicker_intervals.append((seg_start + offset, seg_start + offset + dur))

    # Helper function to apply flicker to a clip's mask
    def apply_flicker(clip: VideoClip) -> VideoClip:
        if not clip.mask:
            # Create a default solid mask
            clip = clip.set_mask(ColorClip(size=clip.size, color=1.0, ismask=True))

        def filter_fn(get_frame, t):
            for start, end in flicker_intervals:
                if start <= t <= end:
                    frame = get_frame(t)
                    return np.zeros_like(frame)
            return get_frame(t)

        return clip.set_mask(clip.mask.fl(filter_fn))

    text_clip = apply_flicker(text_clip)
    if stroke_clip:
        stroke_clip = apply_flicker(stroke_clip)

    return text_clip, stroke_clip
