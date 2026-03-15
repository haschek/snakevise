import numpy as np
from moviepy.editor import VideoClip

def apply(clip: VideoClip, strength: float) -> VideoClip:
    n_levels = int(np.clip(32.0 - (strength - 1.0) * (28.0 / 9.0), 2, 256))
    factor = (n_levels - 1) / 255.0

    def posterize_filter(get_frame, t):
        if n_levels >= 256:
            return get_frame(t)
        return np.clip(
            np.round(get_frame(t).astype(np.float32) * factor) / factor, 0, 255
        ).astype(np.uint8)

    return clip.fl(posterize_filter)
