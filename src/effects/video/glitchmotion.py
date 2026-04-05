import random
import numpy as np
from moviepy.editor import VideoClip, concatenate_videoclips


def apply(clip: VideoClip, strength: float, bpm: float) -> VideoClip:
    chunk_len = max(
        1.0 / 30.0,
        (60.0 / bpm) * (2 ** (-1.0 + (strength - 1.0) * (-4.0 / 9.0))),
    )
    chunks = [
        clip.subclip(t, min(t + chunk_len, clip.duration))
        for t in np.arange(0, clip.duration, chunk_len)
        if min(t + chunk_len, clip.duration) - t > 0.001
    ]
    if not chunks:
        return clip
    random.shuffle(chunks)
    try:
        return concatenate_videoclips(chunks)
    except Exception:
        return clip
