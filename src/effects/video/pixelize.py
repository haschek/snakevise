import PIL.Image
import numpy as np
from moviepy.editor import VideoClip

def apply(clip: VideoClip, strength: float) -> VideoClip:
    w, h = clip.size
    div = 50.0 - (strength - 1.0) * (40.0 / 9.0)
    px_size = w / div

    def px_filter(get_frame, t):
        cur_px = 1.0 + (px_size - 1.0) * (t / clip.duration)
        sw, sh = max(1, int(w / cur_px)), max(1, int(h / cur_px))
        return np.array(
            PIL.Image.fromarray(get_frame(t))
            .resize((sw, sh), PIL.Image.BILINEAR)
            .resize((w, h), PIL.Image.NEAREST)
        )

    return clip.fl(px_filter)
