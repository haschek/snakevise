from typing import Tuple
import numpy as np
from moviepy.editor import VideoClip, clips_array


def apply(clip: VideoClip, target_res: Tuple[int, int]) -> VideoClip:
    """Tiles/duplicates the clip side-by-side or stacked to fill the target resolution without stretching.

    Args:
        clip: The source clip.
        target_res: The (width, height) tuple of the target resolution.

    Returns:
        The tiled and cropped clip.
    """
    w_s, h_s = clip.size
    w_t, h_t = target_res
    target_ar, source_ar = w_t / h_t, w_s / h_s

    if source_ar > target_ar:
        # Source is wider/shorter than target: stack vertically
        clip_scaled = clip.resize(width=w_t)
        h_scaled = clip_scaled.size[1]
        rows = int(np.ceil(h_t / h_scaled))
        if rows % 2 == 0:
            rows += 1
        # Create a grid with 1 column and 'rows' rows
        grid = [[clip_scaled] for _ in range(rows)]
        composite = clips_array(grid)
    else:
        # Source is taller/narrower than target: place horizontally side-by-side
        clip_scaled = clip.resize(height=h_t)
        w_scaled = clip_scaled.size[0]
        cols = int(np.ceil(w_t / w_scaled))
        if cols % 2 == 0:
            cols += 1
        # Create a single row with 'cols' columns
        row = [clip_scaled] * cols
        composite = clips_array([row])

    # Crop excess area to fit target_res centered
    comp_w, comp_h = composite.size
    x1 = (comp_w - w_t) / 2
    y1 = (comp_h - h_t) / 2

    return composite.crop(x1=x1, y1=y1, width=w_t, height=h_t)
