import random
import numpy as np
from moviepy.editor import VideoClip
from ...utils import hex_to_rgb

def apply(clip: VideoClip, strength: float, fade_color_hex: str) -> VideoClip:
    w, h = clip.size
    fade_rgb = hex_to_rgb(fade_color_hex)
    x, y = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))
    mask = (
        1.0
        - (
            np.clip(
                (np.sqrt(x**2 + y**2) - (1.1 - (strength - 1.0) * (0.4 / 9.0))) / 0.4,
                0,
                1,
            )
            * (0.2 + (strength - 1.0) * (0.6 / 9.0))
        )
    )[:, :, np.newaxis]

    def om_filter(get_frame, t):
        f = get_frame(t).astype(np.float32) * (
            1.0
            + random.uniform(
                -(0.05 + (strength - 1.0) * (0.25 / 9.0)),
                0.05 + (strength - 1.0) * (0.25 / 9.0),
            )
        )
        return np.clip(f * mask + np.array(fade_rgb) * (1.0 - mask), 0, 255).astype(
            np.uint8
        )

    return clip.fl(om_filter)
