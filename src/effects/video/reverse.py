from moviepy.editor import VideoClip, concatenate_videoclips, vfx

def apply(clip: VideoClip, strength: float, bpm: float) -> VideoClip:
    rev_dur = clip.duration * (strength / 10.0)
    rev_dur = round(rev_dur / ((60.0 / bpm) / 4.0)) * ((60.0 / bpm) / 4.0)
    if rev_dur >= clip.duration:
        return clip.fx(vfx.time_mirror)
    if clip.duration - rev_dur <= 0.01:
        return clip.fx(vfx.time_mirror)
    return concatenate_videoclips(
        [
            clip.subclip(0, clip.duration - rev_dur),
            clip.subclip(clip.duration - rev_dur, clip.duration).fx(vfx.time_mirror),
        ]
    )
