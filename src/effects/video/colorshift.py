import PIL.Image
import numpy as np
from moviepy.editor import VideoClip

def apply(clip: VideoClip, strength: float) -> VideoClip:
    alpha, shift = strength / 10.0, int((strength / 10.0) * 128)

    def cs_filter(get_frame, t):
        orig = get_frame(t)
        h, s, v = PIL.Image.fromarray(orig).convert("HSV").split()
        new_h = PIL.Image.fromarray(
            ((np.array(h, dtype=np.int16) + shift) % 255).astype(np.uint8)
        )
        shifted = np.array(
            PIL.Image.merge("HSV", (new_h, s, v)).convert("RGB")
        )
        return np.clip(orig * (1.0 - alpha) + shifted * alpha, 0, 255).astype(
            np.uint8
        )

    return clip.fl(cs_filter)
