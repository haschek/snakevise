import PIL.Image
import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    """Applies a grayscale effect by desaturating the video.

    Strength 1: 10% desaturation.
    Strength 10: 100% desaturation (full grayscale).
    """
    # strength 1 -> 0.1 desaturation, strength 10 -> 1.0 desaturation
    desat_factor = strength / 10.0

    def grayscale_filter(get_frame, t):
        orig = get_frame(t)
        # Convert to HSV to manipulate saturation
        img_hsv = PIL.Image.fromarray(orig).convert("HSV")
        h, s, v = img_hsv.split()

        # Desaturate
        s_array = np.array(s, dtype=np.float32)
        s_array = s_array * (1.0 - desat_factor)
        new_s = PIL.Image.fromarray(s_array.astype(np.uint8))

        # Merge back and convert to RGB
        gray_rgb = np.array(PIL.Image.merge("HSV", (h, new_s, v)).convert("RGB"))
        return gray_rgb

    return clip.fl(grayscale_filter)
