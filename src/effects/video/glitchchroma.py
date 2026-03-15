import random
import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    def gc(gf, t):
        f = gf(t)
        if random.random() > 0.3:
            s_x, s_y = int(strength * 10), int(strength * 3)
            rx, ry = random.randint(-s_x, s_x), random.randint(-s_y, s_y)
            bx, by = random.randint(-s_x, s_x), random.randint(-s_y, s_y)
            g = f.copy()
            g[:, :, 0] = np.roll(f[:, :, 0], shift=(ry, rx), axis=(0, 1))
            g[:, :, 2] = np.roll(f[:, :, 2], shift=(by, bx), axis=(0, 1))
            return g
        return f

    return clip.fl(gc)
