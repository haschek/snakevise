import PIL.Image
import PIL.ImageFilter
import numpy as np
from typing import Optional, Tuple
from moviepy.editor import VideoClip


def apply(
    text_clip: VideoClip,
    stroke_clip: Optional[VideoClip],
    strength: float,
    cue_duration: float,
    video_w: int,
    video_h: int,
    target_x: int,
    target_y: int,
) -> Tuple[VideoClip, Optional[VideoClip]]:
    """Applies a constant blur effect to the subtitle text and optional stroke outline."""
    sigma = strength * 0.5

    def blur_clip(clip: VideoClip, r: float) -> VideoClip:
        if r < 0.1:
            return clip

        def blur_image(img_arr: np.ndarray) -> np.ndarray:
            img = PIL.Image.fromarray(img_arr)
            blurred = img.filter(PIL.ImageFilter.GaussianBlur(radius=r))
            return np.array(blurred)

        blurred_clip = clip.fl_image(blur_image)

        if clip.mask:

            def blur_mask(mask_arr: np.ndarray) -> np.ndarray:
                mask_uint8 = (mask_arr * 255.0).astype(np.uint8)
                img = PIL.Image.fromarray(mask_uint8, mode="L")
                blurred = img.filter(PIL.ImageFilter.GaussianBlur(radius=r))
                return np.array(blurred).astype(float) / 255.0

            blurred_clip = blurred_clip.set_mask(clip.mask.fl_image(blur_mask))

        return blurred_clip

    text_clip = blur_clip(text_clip, sigma)
    if stroke_clip:
        stroke_clip = blur_clip(stroke_clip, sigma)

    return text_clip, stroke_clip
