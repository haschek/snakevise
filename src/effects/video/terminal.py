import random
import numpy as np
import PIL.Image
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    w, h = clip.size
    sf = 1.0 + (strength - 1.0)
    nw, nh = max(1, int(w / sf)), max(1, int(h / sf))
    gs = max(2, int(sf))
    mask = np.clip(
        (
            np.where(np.arange(w) % gs == 0, 0.0, 1.0).reshape(1, -1)
            * np.where(np.arange(h) % gs == 0, 0.0, 1.0).reshape(-1, 1)
        )
        + 0.2,
        0.0,
        1.0,
    )[:, :, np.newaxis]
    famp = 0.02 + strength * 0.02

    def term(gf, t):
        px = np.array(
            PIL.Image.fromarray(gf(t))
            .resize((nw, nh), PIL.Image.BILINEAR)
            .resize((w, h), PIL.Image.NEAREST)
        ).astype(np.float32)
        g = (px[:, :, 0] * 0.299 + px[:, :, 1] * 0.587 + px[:, :, 2] * 0.114) * 1.3
        out = np.zeros_like(px)
        out[:, :, 1] = g
        return np.clip(
            out
            * mask
            * (1.0 + np.sin(t * 50) * famp)
            * random.uniform(1.0 - famp, 1.0 + famp),
            0,
            255,
        ).astype(np.uint8)

    return clip.fl(term)
