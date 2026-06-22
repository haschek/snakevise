import random
import numpy as np
from PIL import Image
from moviepy.editor import VideoClip


def crop_to_fit_frame(frame: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    # Ensure target dimensions are at least 1 pixel
    target_w = max(1, target_w)
    target_h = max(1, target_h)

    h_orig, w_orig, _ = frame.shape

    target_ar = target_w / target_h
    orig_ar = w_orig / h_orig

    # Ensure frame is uint8 to prevent Pillow type errors (e.g. with <i8/int64)
    if frame.dtype != np.uint8:
        frame = np.clip(frame, 0, 255).astype(np.uint8)

    pil_img = Image.fromarray(frame)

    if orig_ar > target_ar:
        # Original is wider than tile: crop horizontally
        new_w = int(h_orig * target_ar)
        x1 = (w_orig - new_w) // 2
        y1 = 0
        cropped = pil_img.crop((x1, y1, x1 + new_w, h_orig))
    else:
        # Original is taller than tile: crop vertically
        new_h = int(w_orig / target_ar)
        x1 = 0
        y1 = (h_orig - new_h) // 2
        cropped = pil_img.crop((x1, y1, w_orig, y1 + new_h))

    resized = cropped.resize(
        (target_w, target_h),
        Image.Resampling.BILINEAR if hasattr(Image, "Resampling") else Image.BILINEAR,
    )
    return np.array(resized)


def apply(clip: VideoClip, strength: float) -> VideoClip:
    """Applies a 'tiles' effect to a clip, tiling it into a grid.

    Args:
        clip: The source clip.
        strength: The strength parameter controlling grid size.

    Returns:
        The tiled clip.
    """
    duration = (
        clip.duration
        if (hasattr(clip, "duration") and isinstance(clip.duration, (int, float)))
        else 1.0
    )
    fps = (
        clip.fps
        if (hasattr(clip, "fps") and isinstance(clip.fps, (int, float)))
        else 24.0
    )
    frame_duration = 1.0 / fps

    # Determine layout based on first frame dimensions
    first_frame = clip.get_frame(0.0)
    h, w, _ = first_frame.shape

    # 1. Base layout
    if w > h:
        # Landscape
        c, r = 2, 1
        is_landscape = True
    elif w < h:
        # Portrait
        c, r = 1, 2
        is_landscape = False
    else:
        # Square: choose randomly
        if random.choice([True, False]):
            c, r = 2, 1
            is_landscape = True
        else:
            c, r = 1, 2
            is_landscape = False

    # 2. Apply increments abwechselnd for strength > 1
    for i in range(1, int(strength)):
        if is_landscape:
            if i % 2 == 1:
                # Add row
                r += 1
            else:
                # Add col
                c += 1
        else:
            if i % 2 == 1:
                # Add col
                c += 1
            else:
                # Add row
                r += 1

    # 3. Choose directions for each tile (once at initialization)
    directions = []
    for _ in range(r):
        row_dirs = []
        for _ in range(c):
            row_dirs.append(random.choice(["forward", "backward"]))
        directions.append(row_dirs)

    def tiles_filter(get_frame, t):
        final_frame = np.zeros((h, w, 3), dtype=np.uint8)

        for i in range(r):
            y_start = (i * h) // r
            y_end = ((i + 1) * h) // r
            tile_h = y_end - y_start

            for j in range(c):
                x_start = (j * w) // c
                x_end = ((j + 1) * w) // c
                tile_w = x_end - x_start

                # Fetch frame for this tile
                if directions[i][j] == "backward":
                    # Offset by frame_duration to avoid querying exactly at EOF/duration
                    # which returns a black frame in MoviePy's VideoFileClip readers.
                    play_time = max(0.0, duration - t - frame_duration)
                else:
                    play_time = t

                raw_tile_frame = get_frame(play_time)
                tile_frame = crop_to_fit_frame(raw_tile_frame, tile_w, tile_h)

                final_frame[y_start:y_end, x_start:x_end] = tile_frame

        return final_frame

    return clip.fl(tiles_filter)
