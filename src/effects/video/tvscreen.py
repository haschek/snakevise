import random
import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    w, h = clip.size
    scanlines = np.repeat(
        (
            1.0
            - (
                (0.1 + (strength - 1.0) * (0.8 / 9.0))
                * (0.5 * (1.0 + np.sin(np.arange(h).reshape(-1, 1) * np.pi * 0.8)))
            )
        ),
        w,
        axis=1,
    )[:, :, np.newaxis]
    shift = int(strength * 3)
    noise = int((strength - 3) * 5) if strength > 3 else 0

    def tv(gf, t):
        f = gf(t).astype(np.float32) * scanlines
        if noise:
            f += np.random.randint(-noise, noise, (h, w, 3))
        if shift:
            f = np.stack(
                (
                    np.roll(f[:, :, 0], -shift, axis=1),
                    f[:, :, 1],
                    np.roll(f[:, :, 2], shift, axis=1),
                ),
                axis=-1,
            )
        if strength > 7 and random.random() < 0.3:
            y = random.randint(0, max(0, h - 50))
            hh = random.randint(10, 50)
            f[y : y + hh, :] = np.roll(
                f[y : y + hh, :], random.randint(-50, 50), axis=1
            )
        return np.clip(f, 0, 255).astype(np.uint8)

    return clip.fl(tv)
