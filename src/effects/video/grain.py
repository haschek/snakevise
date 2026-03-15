import numpy as np
import PIL.Image
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    w, h = clip.size
    scale_factor = 1.0 + (strength - 1) * (3.0 / 9.0)
    intensity = int(10 + (strength - 1) * (50 / 9.0))
    small_w, small_h = int(w / scale_factor), int(h / scale_factor)

    def grain_filter(get_frame, t):
        frame = get_frame(t).astype(np.float32)
        noise = np.random.randint(-intensity, intensity, (small_h, small_w)).astype(
            np.float32
        )
        if scale_factor > 1.0:
            noise = np.array(
                PIL.Image.fromarray(noise).resize((w, h), resample=PIL.Image.NEAREST)
            )
        frame += noise[:, :, np.newaxis]
        return np.clip(frame, 0, 255).astype(np.uint8)

    return clip.fl(grain_filter)
