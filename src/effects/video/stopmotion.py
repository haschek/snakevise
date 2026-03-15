from moviepy.editor import VideoClip

def apply(clip: VideoClip, strength: float, bpm: float, target_fps: int) -> VideoClip:
    base_fps = int(target_fps * 0.5)
    fps_low_strength = (base_fps // 4) * 4
    if fps_low_strength < 1:
        fps_low_strength = 1
    fps_high_strength = bpm / 60.0
    current_fps = (
        fps_low_strength
        + (strength - 1.0) * (fps_high_strength - fps_low_strength) / 9.0
    )
    if current_fps <= 0.1:
        current_fps = 0.1
    freeze_dur = 1.0 / current_fps

    def stopmotion_filter(get_frame, t):
        t_quantized = int(t / freeze_dur) * freeze_dur
        return get_frame(t_quantized)

    return clip.fl(stopmotion_filter)
