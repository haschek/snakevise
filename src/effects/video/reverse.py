from moviepy.editor import VideoClip, concatenate_videoclips, vfx


def apply(clip: VideoClip, strength: float, bpm: float) -> VideoClip:
    if strength <= 0.1 or clip.duration is None or clip.duration <= 0.05:
        return clip

    rev_dur = clip.duration * (strength / 10.0)
    # Quantize to 1/4 beat for rhythm
    beat_unit = (60.0 / bpm) / 4.0
    rev_dur = max(0, round(rev_dur / beat_unit) * beat_unit)

    # If reverse duration is effectively the whole clip
    if rev_dur >= clip.duration - 0.05:
        return clip.fx(vfx.time_mirror)

    # If reverse duration is too small to notice
    if rev_dur <= 0.05:
        return clip

    try:
        # Split and reverse the end
        split_point = clip.duration - rev_dur
        part1 = clip.subclip(0, split_point)
        part2 = clip.subclip(split_point, clip.duration).fx(vfx.time_mirror)
        return concatenate_videoclips([part1, part2])
    except Exception:
        # Fallback if moviepy fails to concatenate (e.g. audio issues)
        return clip
