import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import numpy as np
from moviepy.editor import VideoClip
from ...utils import hex_to_rgb


def apply(clip: VideoClip, strength: float, fade_color_hex: str) -> VideoClip:
    w, h = clip.size
    bg = tuple(hex_to_rgb(fade_color_hex))
    try:
        font = PIL.ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15
        )
    except Exception:
        font = PIL.ImageFont.load_default()
    cols = max(20, int(150 - (strength - 1.0) * (130.0 / 9.0)))
    bbox = font.getbbox("@")
    cw, ch = bbox[2] - bbox[0], bbox[3] - bbox[1]
    rows = max(1, int((h / w) * cols * (cw / ch)))
    chars = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    lch = len(chars)
    cont = 1.0 + (strength - 1.0) * (1.5 / 9.0)
    qdiv = 255.0 / max(1, int(64 - (strength - 1.0) * (62.0 / 9.0)) - 1)

    def asc(gf, t):
        f = np.clip(
            np.round(
                np.clip((gf(t).astype(np.float32) - 127.5) * cont + 127.5, 0, 255)
                / qdiv
            )
            * qdiv,
            0,
            255,
        ).astype(np.uint8)
        s_im = PIL.Image.fromarray(f).resize((cols, rows), PIL.Image.BILINEAR)
        sg, sr = np.array(s_im.convert("L")), np.array(s_im)
        # Use actual shape of the resized array to avoid indexing errors
        actual_rows, actual_cols = sg.shape
        aim = PIL.Image.new("RGB", (actual_cols * cw, actual_rows * ch), color=bg)
        dr = PIL.ImageDraw.Draw(aim)
        for r in range(actual_rows):
            yp = r * ch
            for c in range(actual_cols):
                dr.text(
                    (c * cw, yp),
                    chars[int((sg[r, c] / 255.0) * (lch - 1))],
                    font=font,
                    fill=tuple(sr[r, c]),
                )
        return np.array(aim.resize((w, h), PIL.Image.NEAREST))

    return clip.fl(asc)
