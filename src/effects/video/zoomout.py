import numpy as np
import PIL.Image
from moviepy.editor import VideoClip

def apply(clip: VideoClip, strength: float) -> VideoClip:
    w, h = clip.size
    max_zoom = 1 + (strength * 0.05)

    def effect(get_frame, t):
        img = PIL.Image.fromarray(get_frame(t))
        progress = t / clip.duration
        current_zoom = max_zoom - (max_zoom - 1) * progress
        crop_w, crop_h = w / current_zoom, h / current_zoom
        x1, y1 = (w - crop_w) / 2, (h - crop_h) / 2
        return np.array(
            img.crop((x1, y1, x1 + crop_w, y1 + crop_h)).resize(
                (w, h), PIL.Image.Resampling.LANCZOS
            )
        )

    return clip.fl(effect)
