import numpy as np
from moviepy.editor import VideoClip

def apply(clip: VideoClip, strength: float) -> VideoClip:
    w, h = clip.size
    freq = max(0.1, 0.8 - strength * 0.05)
    xv, yv = np.meshgrid(np.arange(w), np.arange(h))
    dots = ((np.sin(xv * freq) * np.sin(yv * freq)) + 1.0)[:, :, np.newaxis]

    def np_flt(gf, t):
        return np.where(
            (gf(t).astype(np.float32) * (2.0 / 255.0)) > dots, gf(t), 0
        ).astype(np.uint8)

    return clip.fl(np_flt)
