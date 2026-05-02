import PIL.Image
import PIL.ImageFilter
import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    """Applies a sharpening effect (blur to clear) finishing at the midpoint.

    Args:
        clip: The video clip to process.
        strength: The intensity of the initial blur (typically 1 to 10).

    Returns:
        The processed clip that clears up by the midpoint.
    """
    w, h = clip.size
    short_side = min(w, h)

    # Calculate max sigma (e) based on strength and shorter side.
    # Same logic as blur effect for consistency.
    e = (strength / 10.0) * (short_side * 0.05)

    duration = clip.duration
    midpoint = duration / 2.0

    def filter_frame(get_frame, t):
        frame = get_frame(t)
        if t > midpoint:
            return frame

        # Linear interpolation from start to midpoint (e down to 0)
        factor = (midpoint - t) / midpoint
        current_sigma = factor * e

        if current_sigma < 0.1:
            return frame

        img = PIL.Image.fromarray(frame)
        # PIL GaussianBlur radius is equivalent to sigma
        blurred_img = img.filter(PIL.ImageFilter.GaussianBlur(radius=current_sigma))
        return np.array(blurred_img)

    return clip.fl(filter_frame)
