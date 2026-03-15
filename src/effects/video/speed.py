import random
from moviepy.editor import VideoClip, concatenate_videoclips, vfx

def apply(clip: VideoClip, strength: float) -> VideoClip:
    total_dur = clip.duration
    src_split = total_dur / 2.0
    shift = (src_split * 0.85) * (strength / 10.0)
    if random.choice([True, False]):
        target_dur_a, target_dur_b = src_split - shift, (total_dur - src_split) + shift
    else:
        target_dur_a, target_dur_b = src_split + shift, (total_dur - src_split) - shift
    return concatenate_videoclips(
        [
            clip.subclip(0, src_split).fx(vfx.speedx, src_split / target_dur_a),
            clip.subclip(src_split, total_dur).fx(
                vfx.speedx, (total_dur - src_split) / target_dur_b
            ),
        ]
    )
