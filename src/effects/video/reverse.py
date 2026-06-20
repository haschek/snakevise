import numpy as np
from moviepy.editor import VideoClip, concatenate_videoclips
from moviepy.decorators import apply_to_audio, apply_to_mask, requires_duration


@requires_duration
@apply_to_mask
@apply_to_audio
def safe_time_mirror(clip: VideoClip) -> VideoClip:
    """A safer implementation of moviepy's vfx.time_mirror that avoids list index out of range."""
    return clip.fl_time(
        lambda t: np.maximum(0.0, clip.duration - t - 1e-6), keep_duration=True
    )


def apply(clip: VideoClip, strength: float, bpm: float) -> VideoClip:
    if strength <= 0.1 or clip.duration is None or clip.duration <= 0.05:
        return clip

    rev_dur = clip.duration * (strength / 10.0)
    # Quantize to 1/4 beat for rhythm
    beat_unit = (60.0 / bpm) / 4.0
    rev_dur = max(0, round(rev_dur / beat_unit) * beat_unit)

    # If reverse duration is effectively the whole clip
    if rev_dur >= clip.duration - 0.05:
        return safe_time_mirror(clip)

    # If reverse duration is too small to notice
    if rev_dur <= 0.05:
        return clip

    try:
        # Split and reverse the end
        split_point = clip.duration - rev_dur
        part1 = clip.subclip(0, split_point)
        part2 = safe_time_mirror(clip.subclip(split_point, clip.duration))
        return concatenate_videoclips([part1, part2])
    except Exception:
        # Fallback if moviepy fails to concatenate (e.g. audio issues)
        return clip
