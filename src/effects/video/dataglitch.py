import random
import numpy as np
import PIL.Image
from moviepy.editor import VideoClip

def apply(clip: VideoClip, strength: float) -> VideoClip:
    w, h = clip.size
    n_glitch = int(strength * 2.0)
    mw, mh = int(w * (0.05 + strength * 0.025)), int(h * (0.05 + strength * 0.025))
    pxf = int(4 + strength * 1.2)

    def dg(gf, t):
        orig = gf(t)
        gl = orig.copy()
        for _ in range(random.randint(1, max(1, n_glitch + random.randint(-2, 3)))):
            bw, bh = random.randint(32, max(33, mw)), random.randint(32, max(33, mh))
            bx, by = random.randint(0, max(0, w - bw)), random.randint(0, max(0, h - bh))
            reg = orig[by : by + bh, bx : bx + bw].copy()
            typ = random.choice(["px", "px", "sh", "inv"])
            if typ == "px":
                gl[by : by + bh, bx : bx + bw] = np.array(
                    PIL.Image.fromarray(reg)
                    .resize((max(1, bw // pxf), max(1, bh // pxf)), PIL.Image.NEAREST)
                    .resize((bw, bh), PIL.Image.NEAREST)
                )
            elif typ == "sh":
                s = random.randint(5, 20 + int(strength * 2))
                reg[:, :, 0] = np.roll(reg[:, :, 0], s, axis=1)
                reg[:, :, 2] = np.roll(reg[:, :, 2], -s, axis=1)
                gl[by : by + bh, bx : bx + bw] = reg
            elif typ == "inv":
                gl[by : by + bh, bx : bx + bw] = 255 - reg
        return gl

    return clip.fl(dg)
