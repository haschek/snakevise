import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    delay = 0.05 + (strength - 1.0) * (0.45 / 9.0)
    alpha = int((0.15 + (strength - 1.0) * (0.45 / 9.0)) * 256)

    def echo(gf, t):
        c = gf(t).astype(np.uint16)
        p = gf(max(0, t - delay)).astype(np.uint16)
        return np.clip(c + ((p * alpha) >> 8), 0, 255).astype(np.uint8)

    return clip.fl(echo)
