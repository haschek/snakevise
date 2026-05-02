import math

import PIL.Image
import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    """Applies a vibrant inversion effect using Difference Blend Mode.

    Instead of a linear blend (which goes grey at the midpoint), this uses
    a "Difference" blend against a target color that transitions from
    Black -> Saturated Color -> White.

    Args:
        clip: The video clip to process.
        strength: The intensity of the effect (1 to 10).

    Returns:
        The processed clip with vibrant inversion.
    """
    factor = strength / 10.0

    # Create a "Target Color" for the Difference Blend.
    # Target Value goes 0 -> 255
    t_v = int(factor * 255)
    # Target Saturation peaks at midpoint (sin curve) to avoid grey-out
    t_s = int(math.sin(factor * math.pi) * 255)
    # Target Hue rotates as we transition
    t_h = int(factor * 128)

    # Convert Target HSV color to RGB to use in Difference blend
    target_img = PIL.Image.new("HSV", (1, 1), (t_h, t_s, t_v)).convert("RGB")
    t_rgb = np.array(target_img)[0, 0].astype(np.int16)

    def invert_filter(get_frame, t):
        orig = get_frame(t).astype(np.int16)

        # Difference Blend Mode: |Image - TargetColor|
        # This stays high-contrast because TargetColor is vibrant at the midpoint.
        diff = np.abs(orig - t_rgb).astype(np.uint8)

        # Apply a final saturation boost during the transition to keep it "vibe"
        # We boost more as we approach the midpoint
        if 0.1 < factor < 0.9:
            res_img = PIL.Image.fromarray(diff).convert("HSV")
            rh, rs, rv = res_img.split()
            # Boost saturation by up to 50%
            boost = 1.0 + (math.sin(factor * math.pi) * 0.5)
            rs_arr = np.clip(np.array(rs, dtype=np.float32) * boost, 0, 255)
            diff = np.array(
                PIL.Image.merge(
                    "HSV", (rh, PIL.Image.fromarray(rs_arr.astype(np.uint8)), rv)
                ).convert("RGB")
            )

        return diff

    return clip.fl(invert_filter)
