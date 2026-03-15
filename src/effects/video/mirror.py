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
            frame[:, mid_w : mid_w + frame[:, :mid_w].shape[1]] = np.fliplr(
                frame[:, :mid_w]
            )
        if mode in ["vert", "quad"]:
            frame[mid_h : mid_h + frame[:mid_h, :].shape[0], :] = np.flipud(
                frame[:mid_h, :]
            )
        return frame

    return clip.fl(mirror_filter)
