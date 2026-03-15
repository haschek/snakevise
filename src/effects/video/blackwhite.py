import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    t = np.clip((strength - 1.0) / 9.0, 0.0, 1.0)

    def bw_filter(get_frame, t_time):
        frame = get_frame(t_time).astype(np.float32)
        gray = frame[:, :, 0] * 0.299 + frame[:, :, 1] * 0.587 + frame[:, :, 2] * 0.114
        thresholded = np.where(gray > 127.5, 255.0, 0.0)
        blended = (1.0 - t) * gray + t * thresholded
        return np.clip(np.stack((blended,) * 3, axis=-1), 0, 255).astype(np.uint8)

    return clip.fl(bw_filter)
