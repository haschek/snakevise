import PIL.Image
import PIL.ImageEnhance
import PIL.ImageOps
import numpy as np
from moviepy.editor import VideoClip


def apply(clip: VideoClip, strength: float) -> VideoClip:
    """Applies a stable automatic color and light correction.

    Uses Luminance-based Gamma correction, dampened Gray World white balance,
    and conservative histogram stretching.

    Args:
        clip: The video clip to process.
        strength: Intensity of the correction (1 to 10).

    Returns:
        The auto-corrected clip.
    """
    # 1. Analyze segment (Start, Mid, End)
    sample_times = [0, clip.duration / 2, max(0, clip.duration - 0.1)]
    rgb_means = []
    luminance_values = []

    for t in sample_times:
        frame = clip.get_frame(t)
        # RGB Means for White Balance
        m = np.mean(frame, axis=(0, 1))
        rgb_means.append(m)
        # Perceived Luminance: 0.299*R + 0.587*G + 0.114*B
        lum = 0.299 * m[0] + 0.587 * m[1] + 0.114 * m[2]
        luminance_values.append(lum)

    avg_rgb = np.mean(rgb_means, axis=0)
    avg_lum = np.mean(luminance_values)
    global_avg = np.mean(avg_rgb)

    alpha = strength / 10.0

    # 2. White Balance (Gray World)
    # We cap the correction to 0.8 - 1.2 to avoid extreme color shifts
    wb_factors = global_avg / np.maximum(10.0, avg_rgb)
    wb_factors = np.clip(wb_factors, 0.8, 1.2)
    # Apply strength
    wb_factors = 1.0 + (wb_factors - 1.0) * alpha

    # 3. Gamma Correction (Exposure)
    # Target perceived luminance ~115 (conservative to avoid overexposure)
    target_lum = 115.0
    # gamma = log(target) / log(actual)
    # This formula: if actual < target, gamma < 1 (brightens). If actual > target, gamma > 1 (darkens).
    gamma = math_log_safe(target_lum / 255.0) / math_log_safe(max(5.0, avg_lum) / 255.0)
    # Clamp gamma to a reasonable range (0.5 to 2.0) and dampen by strength
    gamma = np.clip(gamma, 0.5, 2.0)
    gamma = 1.0 + (gamma - 1.0) * (alpha * 0.8)

    def autofix_filter(get_frame, t):
        orig = get_frame(t)
        img_arr = orig.astype(np.float32)

        # A. Apply White Balance
        for i in range(3):
            img_arr[:, :, i] *= wb_factors[i]

        # B. Apply Gamma Correction
        # If gamma < 1, this lifts shadows/midtones significantly
        img_arr = 255.0 * (np.clip(img_arr / 255.0, 0, 1) ** gamma)

        # C. Final Polish with PIL
        fixed = PIL.Image.fromarray(np.clip(img_arr, 0, 255).astype(np.uint8))

        # Conservative Auto-Contrast
        # Ignore 1% of extreme pixels to find a better range
        fixed = PIL.ImageOps.autocontrast(fixed, cutoff=1.0)

        # Subtle Saturation
        if alpha > 0.3:
            # Very slight color lift to compensate for gamma flattening
            boost = 1.0 + (alpha * 0.15)
            fixed = PIL.ImageEnhance.Color(fixed).enhance(boost)

        return np.array(fixed)

    return clip.fl(autofix_filter)


def math_log_safe(val: float) -> float:
    """Safe log for gamma calculation."""
    import math

    return math.log(max(0.001, val))
