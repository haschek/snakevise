import PIL.Image
import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    """Applies a color boost effect.

    Weights 1-5: Increases vibrance (boosts less saturated colors).
    Weights 6-10: Additionally increases global saturation.

    Args:
        clip: The video clip to process.
        strength: The intensity of the effect (1 to 10).

    Returns:
        The processed clip with enhanced colors.
    """
    # Vibrance boost (applied for all strengths)
    # Factor ranges from 0.08 to 0.8
    v_factor = strength * 0.08

    # Saturation boost (applied for strengths 6-10)
    # Factor ranges from 0.12 to 0.6
    s_factor = max(0.0, strength - 5) * 0.12

    def colorboost_filter(get_frame, t):
        orig = get_frame(t)
        # Convert to HSV to manipulate saturation
        img_hsv = PIL.Image.fromarray(orig).convert("HSV")
        h, s, v = img_hsv.split()

        s_array = np.array(s, dtype=np.float32) / 255.0

        # 1. Apply Vibrance
        # Formula: S = S * (1 + v_factor * (1 - S))
        # This boosts low-saturation pixels more than high-saturation ones.
        s_array = s_array * (1.0 + v_factor * (1.0 - s_array))

        # 2. Apply Saturation (if strength > 5)
        if s_factor > 0:
            s_array = s_array * (1.0 + s_factor)

        # Clip and convert back
        s_array = np.clip(s_array * 255.0, 0, 255).astype(np.uint8)
        new_s = PIL.Image.fromarray(s_array)

        # Merge and convert back to RGB
        boosted_rgb = np.array(PIL.Image.merge("HSV", (h, new_s, v)).convert("RGB"))
        return boosted_rgb

    return clip.fl(colorboost_filter)
