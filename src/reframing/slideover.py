import random
from typing import Tuple
from moviepy.editor import VideoClip


def apply(clip: VideoClip, target_res: Tuple[int, int]) -> VideoClip:
    """Crops the clip to target resolution while panning/sliding over the extra width/height.

    Args:
        clip: The source clip.
        target_res: The (width, height) tuple of the target resolution.

    Returns:
        The reframed and resized clip.
    """
    w_s, h_s = clip.size
    w_t, h_t = target_res
    target_ar, source_ar = w_t / h_t, w_s / h_s

    if source_ar > target_ar:
        # Source is wider than target: slide horizontally
        new_h = h_s
        new_w = h_s * target_ar
    else:
        # Source is taller than target: slide vertically
        new_w = w_s
        new_h = w_s / target_ar

    duration = clip.duration if clip.duration else 1.0
    direction = random.choice(["forward", "reverse"])

    def make_frame(get_frame, t):
        frame = get_frame(t)
        progress = min(1.0, max(0.0, t / duration))
        if direction == "reverse":
            progress = 1.0 - progress

        if source_ar > target_ar:
            x1 = int(progress * (w_s - new_w))
            y1 = 0
        else:
            x1 = 0
            y1 = int(progress * (h_s - new_h))

        x2 = x1 + int(new_w)
        y2 = y1 + int(new_h)

        # Ensure we stay within frame boundaries
        h_frame, w_frame = frame.shape[:2]
        x1 = min(w_frame - 1, max(0, x1))
        y1 = min(h_frame - 1, max(0, y1))
        x2 = min(w_frame, max(x1 + 1, x2))
        y2 = min(h_frame, max(y1 + 1, y2))

        return frame[y1:y2, x1:x2]

    # fl maps a function (get_frame, t) -> frame
    # We must also apply it to the mask if it exists
    clip = clip.fl(make_frame, apply_to=["mask"])
    clip = clip.resize(newsize=target_res)

    return clip
