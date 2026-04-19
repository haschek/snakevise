import PIL.Image
import PIL.ImageEnhance
import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    """Applies a contrast enhancement effect.

    10% increase per weight step.
    Weight 10: 100% (extreme) contrast, results in black/white monotone.
    """
    # Map strength 0-10 to a contrast factor.
    # We use a reciprocal mapping so that 10 (100%) approaches extreme contrast.
    # strength 1 -> factor ~1.11
    # strength 5 -> factor 2.0
    # strength 9 -> factor 10.0
    # strength 10 -> factor 100.0 (extreme monotone)
    factor = 1.0 / max(0.01, 1.0 - (strength * 0.1))

    enhancer_func = PIL.ImageEnhance.Contrast

    def contrast_filter(get_frame, t):
        orig = get_frame(t)
        img = PIL.Image.fromarray(orig)
        enhanced = enhancer_func(img).enhance(factor)
        return np.array(enhanced)

    return clip.fl(contrast_filter)
