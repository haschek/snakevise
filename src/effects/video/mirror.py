import random
import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    mode = "quad" if strength >= 7 else random.choice(["horiz", "vert"])

    def mirror_filter(get_frame, t):
        frame = get_frame(t).copy()
        h, w, _ = frame.shape
        mid_h, mid_w = h // 2, w // 2
        if mode in ["horiz", "quad"]:
            left_part = frame[:, :mid_w]
            frame[:, mid_w : mid_w + left_part.shape[1]] = np.fliplr(left_part)
        if mode in ["vert", "quad"]:
            top_part = frame[:mid_h, :]
            frame[mid_h : mid_h + top_part.shape[0], :] = np.flipud(top_part)
        return frame

    return clip.fl(mirror_filter)
