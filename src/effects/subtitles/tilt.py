import math
import random
from typing import Optional, Tuple
from moviepy.editor import VideoClip
from PIL import Image
import numpy as np


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
    """Applies a tilt (rotation) effect to the subtitle text and optional stroke outline.

    The subtitles tilt smoothly between random angles, alternating signs to
    cross the original upright position. The tilt angle and frequency are
    coupled to strength.
    """
    strength_clamped = max(1.0, min(10.0, strength))

    # Minimum hold duration per position to ensure readability
    min_hold_duration = 0.15

    # Determine maximum number of tilts allowed within cue_duration
    max_intervals = max(1, int(cue_duration / min_hold_duration))
    max_tilts = max_intervals - 1

    # Number of tilts is coupled to strength
    rate = strength_clamped
    min_tilts = strength_clamped
    expected_tilts = cue_duration * rate
    num_tilts = int(round(max(min_tilts, expected_tilts)))
    num_tilts = min(num_tilts, max_tilts)
    num_tilts = max(0, num_tilts)

    if num_tilts == 0:
        return text_clip, stroke_clip

    # Determine safe padded size D (diagonal of bounding boxes)
    w = getattr(text_clip, "w", 100)
    h = getattr(text_clip, "h", 20)
    if stroke_clip:
        stroke_w = getattr(stroke_clip, "w", w)
        stroke_h = getattr(stroke_clip, "h", h)
        w = max(w, stroke_w)
        h = max(h, stroke_h)

    D = int(math.ceil(math.sqrt(w**2 + h**2)))
    if D % 2 != 0:
        D += 1

    # Tilt angle ranges: strength 1 -> 4.2 deg max, strength 10 -> 15 deg max
    max_angle = 3.0 + strength_clamped * 1.2
    min_angle = max_angle / 3.0

    # Pre-generate tilt angles (Interval 0 starts at 0.0 deg)
    sgn = random.choice([-1, 1])
    angles = []
    angles.append(0.0)

    for _ in range(num_tilts):
        angle_val = random.uniform(min_angle, max_angle)
        angles.append(sgn * angle_val)
        sgn = -sgn

    interval_len = cue_duration / (num_tilts + 1)
    transition_dur = interval_len

    # Time-varying angle function
    def angle_fn(t):
        interval_idx = min(int(t / interval_len), len(angles) - 1)
        start_t = interval_idx * interval_len

        angle_curr = angles[interval_idx]
        if interval_idx > 0:
            angle_prev = angles[interval_idx - 1]
        else:
            angle_prev = 0.0

        time_in_interval = t - start_t
        if time_in_interval < transition_dur and transition_dur > 0:
            progress = time_in_interval / transition_dur
            ease_progress = progress * progress * (3.0 - 2.0 * progress)
            return angle_prev + (angle_curr - angle_prev) * ease_progress
        return angle_curr

    # Frame rotation function using PIL with padding to prevent clipping
    def apply_rotation(clip: VideoClip, is_mask: bool = False) -> VideoClip:
        orig_w = getattr(clip, "w", 100)
        orig_h = getattr(clip, "h", 20)
        paste_x = (D - orig_w) // 2
        paste_y = (D - orig_h) // 2

        def filter_fn(get_frame, t):
            frame = get_frame(t)
            angle = angle_fn(t)

            if is_mask:
                # Grayscale mask frame [0.0, 1.0] -> [0, 255] uint8
                mask_uint8 = (frame * 255.0).astype(np.uint8)
                img = Image.fromarray(mask_uint8, mode="L")

                padded_img = Image.new("L", (D, D), color=0)
                padded_img.paste(img, (paste_x, paste_y))

                if angle != 0.0:
                    rotated_img = padded_img.rotate(angle, resample=Image.BICUBIC)
                else:
                    rotated_img = padded_img

                return np.array(rotated_img).astype(frame.dtype) / 255.0
            else:
                img = Image.fromarray(frame)
                if img.mode == "RGBA":
                    color = (0, 0, 0, 0)
                elif img.mode == "RGB":
                    color = (0, 0, 0)
                else:
                    color = 0

                padded_img = Image.new(img.mode, (D, D), color=color)
                padded_img.paste(img, (paste_x, paste_y))

                if angle != 0.0:
                    rotated_img = padded_img.rotate(angle, resample=Image.BICUBIC)
                else:
                    rotated_img = padded_img

                return np.array(rotated_img)

        rotated_clip = clip.fl(filter_fn)

        if not is_mask:
            original_pos = getattr(clip, "pos", None)

            def new_pos(t):
                if callable(original_pos):
                    res = original_pos(t)
                    if isinstance(res, (tuple, list)) and len(res) == 2:
                        x, y = res
                    else:
                        x, y = target_x, target_y
                elif isinstance(original_pos, (tuple, list)) and len(original_pos) == 2:
                    x, y = original_pos
                else:
                    x, y = target_x, target_y

                # Support string coordinates (like 'center') by falling back to target coordinates
                if not isinstance(x, (int, float)):
                    x = target_x
                if not isinstance(y, (int, float)):
                    y = target_y

                return (
                    int(round(x - (D - orig_w) / 2)),
                    int(round(y - (D - orig_h) / 2)),
                )

            if hasattr(clip, "set_position"):
                rotated_clip = rotated_clip.set_position(new_pos)
            else:
                rotated_clip.pos = new_pos

            if clip.mask:
                rotated_clip = rotated_clip.set_mask(
                    apply_rotation(clip.mask, is_mask=True)
                )

        rotated_clip.size = (D, D)
        try:
            rotated_clip.w = D
            rotated_clip.h = D
        except AttributeError:
            pass
        return rotated_clip

    text_clip = apply_rotation(text_clip)
    if stroke_clip:
        stroke_clip = apply_rotation(stroke_clip)

    return text_clip, stroke_clip
