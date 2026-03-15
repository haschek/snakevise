#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
#
# VidSeq - Generative Video Sequencer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
VidSeq - Generative Video Sequencer.
Creates rhythmic video montages based on BPM and algorithms.
"""

import argparse
import datetime
import logging
import random
import shutil
import sys
import glob
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Generator, Union

# --- COMPATIBILITY PATCH FOR PILLOW 10+ ---
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageEnhance
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
# ------------------------------------------

# 3rd Party Imports
import argcomplete
import numpy as np
from moviepy.editor import (
    VideoFileClip, ImageClip, concatenate_videoclips, AudioFileClip, vfx, VideoClip
)

# --- SYSTEM DEFAULTS ---
DEFAULTS = {
    'inputs': [],
    'bpm': 120.0,
    'snippetbeats': '8..16',
    'modus': 'linear',
    'effects': [],
    'fx_chance': 20,
    'fx_intensity': '1..3',
    'fx_maximum': 1,
    'fx_order': 'linear',
    'fadein': 0,
    'fadeout': 0,
    'fadecolor': '#000000',
    'resolution': '1920x1080',
    'fps': 24,
    'codec': 'libx264',
    'optimize': False,
    'audio_path': None,
    'duration': None,
    'length_beats': None,
    'seed': None
}

# --- PRESET CONFIGURATION ---
PRESETS = {
    'subtle': {
        'bpm': 120.0, 
        'snippetbeats': '8..16', 
        'modus': 'linear',
        'effects': [], 
        'fx_chance': 20, 
        'fx_intensity': '1..3',
        'fx_maximum': 1,
        'fadein': 1, 'fadeout': 1,
        'fx_order': 'linear'
    },
    'vintage': {
        'bpm': 90.0, 
        'snippetbeats': '4..8',
        'modus': 'linear',
        'effects': ['newspaper:100:2..5', 'oldmovie:50:3..6', 'speed:25:2'],
        'fx_chance': 50, 
        'fx_intensity': '4..6',
        'fx_maximum': None,
        'fadein': 2, 'fadeout': 2,
        'fx_order': 'linear'
    },
    'lofi': {
        'bpm': 80.0, 
        'snippetbeats': '4..12',
        'modus': 'linear-random',
        'effects': ['tvscreen:80:3..6', 'asciiart:30:4..7', 'stopmotion:60:2..4'],
        'fx_chance': 40, 
        'fx_intensity': '2..5',
        'fx_maximum': 2,
        'fadein': 4, 'fadeout': 4,
        'fx_order': 'random'
    },
    'urban': {
        'bpm': 110.0, 
        'snippetbeats': '2..4',
        'modus': 'random',
        'effects': ['dataglitch:40:5..9', 'glitchchroma:50:5..8', 'glitchmotion:40:4..8'],
        'fx_chance': 50, 
        'fx_intensity': '5..9',
        'fx_maximum': 3,
        'fadein': 0, 'fadeout': 1,
        'fx_order': 'random'
    },
    'chaos': {
        'bpm': 160.0, 
        'snippetbeats': '1..2',
        'modus': 'random',
        'effects': ['all'], 
        'fx_chance': 90, 
        'fx_intensity': '5..10',
        'fx_maximum': None,
        'fadein': 0, 'fadeout': 0,
        'fx_order': 'random'
    }
}

# --- CONFIGURATION & DATA STRUCTURES ---

@dataclass
class RenderConfig:
    """Holds all configurations for the rendering process."""
    output_path: Path
    temp_dir: Path
    resolution: Tuple[int, int]
    fps: int
    codec: str
    optimize: bool
    audio_path: Optional[Path]
    target_duration: Optional[float]
    fade_in: int  # in Seconds
    fade_out: int # in Seconds
    fade_color: str
    dry_run: bool
    bpm: float

@dataclass
class Snippet:
    index: int
    source_path: Path
    start_time: float
    duration: float
    is_image: bool
    effects: List[Dict[str, float]]
    temp_file: Optional[Path] = None

@dataclass
class Segment:
    """A pre-calculated slice of a media source."""
    source_index: int
    start: float
    duration: float

# --- LOGGING SETUP ---

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("vidseq")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

logger = logging.getLogger("vidseq")

# --- HELPER FUNCTIONS ---

def hex_to_rgb(hex_str: str) -> List[int]:
    hex_str = hex_str.lstrip('#')
    return [int(hex_str[i:i+2], 16) for i in (0, 2, 4)]

def parse_resolution(res_str: str) -> Tuple[Tuple[int, int], int]:
    try:
        size, fps = res_str.split(':')
        w, h = map(int, size.lower().split('x'))
        return (w, h), int(fps)
    except ValueError:
        raise argparse.ArgumentTypeError("Format must be WIDTHxHEIGHT:FRAMERATE (e.g., 1920x1080:24)")

def parse_range_string(val: Union[str, float, int]) -> Tuple[float, float]:
    s = str(val)
    if '..' in s:
        try:
            parts = s.split('..')
            return float(parts[0]), float(parts[1])
        except ValueError:
            return 5.0, 5.0
    try:
        f = float(s)
        return f, f
    except ValueError:
        return 5.0, 5.0

def parse_int_range_string(val: Union[str, int]) -> Tuple[int, int]:
    s = str(val)
    if '..' in s:
        try:
            parts = s.split('..')
            return int(float(parts[0])), int(float(parts[1]))
        except ValueError:
            return 4, 4
    try:
        i = int(float(s))
        return i, i
    except ValueError:
        return 4, 4

def parse_effect_string(fx_str: str, default_chance: float, default_range: Tuple[float, float]) -> Dict[str, Any]:
    parts = fx_str.split(':')
    name = parts[0]
    chance = float(parts[1]) if len(parts) > 1 and parts[1] else default_chance
    
    if len(parts) > 2 and parts[2]:
        str_range = parse_range_string(parts[2])
    else:
        str_range = default_range
        
    return {'name': name, 'chance': chance, 'strength_range': str_range}

# --- CORE LOGIC CLASSES ---

class EffectEngine:
    AVAILABLE_EFFECTS = [
        'zoomin', 'zoomout', 'glitchchroma', 'glitchmotion', 
        'mirror', 'grain', 'speed', 'blackwhite', 'posterize', 
        'reverse', 'stopmotion', 'pixelize', 'oldmovie', 'colorshift',
        'shutterecho', 'tvscreen', 'newspaper', 'terminal', 'dataglitch',
        'asciiart'
    ]

    @staticmethod
    def select_effects(configs: List[Dict[str, Any]], max_limit: Optional[int] = None, order: str = 'linear') -> List[Dict[str, float]]:
        planned = []
        processed_configs = []
        
        for c in configs:
            if c['name'] == 'all':
                for name in EffectEngine.AVAILABLE_EFFECTS:
                    processed_configs.append({
                        'name': name, 
                        'chance': c['chance'], 
                        'strength_range': c['strength_range']
                    })
            else:
                processed_configs.append(c)

        candidates = []
        for fx in processed_configs:
            if fx['name'] != 'none' and random.random() * 100 <= fx['chance']:
                min_s, max_s = fx['strength_range']
                actual_strength = min_s if min_s == max_s else random.uniform(min_s, max_s)
                candidates.append({'name': fx['name'], 'strength': actual_strength})

        if order == 'random':
            random.shuffle(candidates)
        
        if max_limit is not None:
            planned = candidates[:max_limit]
        else:
            planned = candidates

        return planned

    @staticmethod
    def _zoom_vfx(clip: VideoClip, mode: str, strength: float) -> VideoClip:
        w, h = clip.size
        max_zoom = 1 + (strength * 0.05) 
        def effect(get_frame, t):
            img = PIL.Image.fromarray(get_frame(t))
            progress = t / clip.duration
            if mode == 'zoomin': current_zoom = 1 + (max_zoom - 1) * progress
            else: current_zoom = max_zoom - (max_zoom - 1) * progress
            crop_w, crop_h = w / current_zoom, h / current_zoom
            x1, y1 = (w - crop_w) / 2, (h - crop_h) / 2
            return np.array(img.crop((x1, y1, x1 + crop_w, y1 + crop_h)).resize((w, h), PIL.Image.LANCZOS))
        return clip.fl(effect)

    @staticmethod
    def _mirror_vfx(clip: VideoClip, strength: float) -> VideoClip:
        mode = 'quad' if strength >= 7 else random.choice(['horiz', 'vert'])
        def mirror_filter(get_frame, t):
            frame = get_frame(t).copy()
            h, w, c = frame.shape
            mid_h, mid_w = h // 2, w // 2
            if mode in ['horiz', 'quad']:
                frame[:, mid_w:mid_w+frame[:, :mid_w].shape[1]] = np.fliplr(frame[:, :mid_w])
            if mode in ['vert', 'quad']:
                frame[mid_h:mid_h+frame[:mid_h, :].shape[0], :] = np.flipud(frame[:mid_h, :])
            return frame
        return clip.fl(mirror_filter)

    @staticmethod
    def _grain_vfx(clip: VideoClip, strength: float) -> VideoClip:
        w, h = clip.size
        scale_factor = 1.0 + (strength - 1) * (3.0 / 9.0)
        intensity = int(10 + (strength - 1) * (50 / 9.0))
        small_w, small_h = int(w / scale_factor), int(h / scale_factor)
        def grain_filter(get_frame, t):
            frame = get_frame(t).astype(np.float32)
            noise = np.random.randint(-intensity, intensity, (small_h, small_w)).astype(np.float32)
            if scale_factor > 1.0:
                noise = np.array(PIL.Image.fromarray(noise).resize((w, h), resample=PIL.Image.NEAREST))
            frame += noise[:,:,np.newaxis]
            return np.clip(frame, 0, 255).astype(np.uint8)
        return clip.fl(grain_filter)

    @staticmethod
    def _blackwhite_vfx(clip: VideoClip, strength: float) -> VideoClip:
        t = np.clip((strength - 1.0) / 9.0, 0.0, 1.0)
        def bw_filter(get_frame, t_time):
            frame = get_frame(t_time).astype(np.float32)
            gray = frame[:,:,0]*0.299 + frame[:,:,1]*0.587 + frame[:,:,2]*0.114
            thresholded = np.where(gray > 127.5, 255.0, 0.0)
            blended = (1.0 - t) * gray + t * thresholded
            return np.clip(np.stack((blended,)*3, axis=-1), 0, 255).astype(np.uint8)
        return clip.fl(bw_filter)

    @staticmethod
    def _posterize_vfx(clip: VideoClip, strength: float) -> VideoClip:
        n_levels = int(np.clip(32.0 - (strength - 1.0) * (28.0 / 9.0), 2, 256))
        factor = (n_levels - 1) / 255.0
        def posterize_filter(get_frame, t):
            if n_levels >= 256: return get_frame(t)
            return np.clip(np.round(get_frame(t).astype(np.float32) * factor) / factor, 0, 255).astype(np.uint8)
        return clip.fl(posterize_filter)

    @staticmethod
    def _speed_vfx(clip: VideoClip, strength: float) -> VideoClip:
        total_dur = clip.duration
        src_split = total_dur / 2.0 
        shift = (src_split * 0.85) * (strength / 10.0)
        if random.choice([True, False]): target_dur_a, target_dur_b = src_split - shift, (total_dur - src_split) + shift
        else: target_dur_a, target_dur_b = src_split + shift, (total_dur - src_split) - shift
        return concatenate_videoclips([clip.subclip(0, src_split).fx(vfx.speedx, src_split/target_dur_a), clip.subclip(src_split, total_dur).fx(vfx.speedx, (total_dur-src_split)/target_dur_b)])

    @staticmethod
    def _reverse_vfx(clip: VideoClip, strength: float, bpm: float) -> VideoClip:
        rev_dur = clip.duration * (strength / 10.0)
        rev_dur = round(rev_dur / ((60.0/bpm)/4.0)) * ((60.0/bpm)/4.0)
        if rev_dur >= clip.duration: return clip.fx(vfx.time_mirror)
        if clip.duration - rev_dur <= 0.01: return clip.fx(vfx.time_mirror)
        return concatenate_videoclips([clip.subclip(0, clip.duration - rev_dur), clip.subclip(clip.duration - rev_dur, clip.duration).fx(vfx.time_mirror)])

    @staticmethod
    def _stopmotion_vfx(clip: VideoClip, strength: float, bpm: float, target_fps: int) -> VideoClip:
        base_fps = int(target_fps * 0.5)
        fps_low_strength = (base_fps // 4) * 4
        if fps_low_strength < 1: fps_low_strength = 1 
        fps_high_strength = bpm / 60.0
        current_fps = fps_low_strength + (strength - 1.0) * (fps_high_strength - fps_low_strength) / 9.0
        if current_fps <= 0.1: current_fps = 0.1 
        freeze_dur = 1.0 / current_fps
        def stopmotion_filter(get_frame, t):
            t_quantized = int(t / freeze_dur) * freeze_dur
            return get_frame(t_quantized)
        return clip.fl(stopmotion_filter)

    @staticmethod
    def _glitchmotion_vfx(clip: VideoClip, strength: float, bpm: float) -> VideoClip:
        chunk_len = max(1.0/30.0, (60.0/bpm) * (2 ** (-1.0 + (strength - 1.0) * (-4.0 / 9.0))))
        chunks = [clip.subclip(t, min(t+chunk_len, clip.duration)) for t in np.arange(0, clip.duration, chunk_len) if min(t+chunk_len, clip.duration) - t > 0.001]
        random.shuffle(chunks)
        return concatenate_videoclips(chunks)

    @staticmethod
    def _pixelize_vfx(clip: VideoClip, strength: float) -> VideoClip:
        w, h = clip.size
        div = 50.0 - (strength - 1.0) * (40.0 / 9.0)
        px_size = w / div
        def px_filter(get_frame, t):
            cur_px = 1.0 + (px_size - 1.0) * (t/clip.duration)
            sw, sh = max(1, int(w/cur_px)), max(1, int(h/cur_px))
            return np.array(PIL.Image.fromarray(get_frame(t)).resize((sw, sh), PIL.Image.BILINEAR).resize((w, h), PIL.Image.NEAREST))
        return clip.fl(px_filter)

    @staticmethod
    def _oldmovie_vfx(clip: VideoClip, strength: float, fade_color_hex: str) -> VideoClip:
        w, h = clip.size
        fade_rgb = hex_to_rgb(fade_color_hex)
        x, y = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))
        mask = (1.0 - (np.clip((np.sqrt(x**2 + y**2) - (1.1 - (strength-1.0)*(0.4/9.0)))/0.4, 0, 1) * (0.2+(strength-1.0)*(0.6/9.0))))[:,:,np.newaxis]
        def om_filter(get_frame, t):
            f = get_frame(t).astype(np.float32) * (1.0 + random.uniform(-(0.05+(strength-1.0)*(0.25/9.0)), 0.05+(strength-1.0)*(0.25/9.0)))
            return np.clip(f * mask + np.array(fade_rgb) * (1.0 - mask), 0, 255).astype(np.uint8)
        return clip.fl(om_filter)

    @staticmethod
    def _colorshift_vfx(clip: VideoClip, strength: float) -> VideoClip:
        alpha, shift = strength/10.0, int((strength/10.0)*128)
        def cs_filter(get_frame, t):
            orig = get_frame(t)
            h, s, v = PIL.Image.fromarray(orig).convert('HSV').split()
            new_h = PIL.Image.fromarray(((np.array(h, dtype=np.int16)+shift)%255).astype(np.uint8))
            shifted = np.array(PIL.Image.merge('HSV', (new_h, s, v)).convert('RGB'))
            return np.clip(orig*(1.0-alpha) + shifted*alpha, 0, 255).astype(np.uint8)
        return clip.fl(cs_filter)

    @staticmethod
    def _shutterecho_vfx(clip: VideoClip, strength: float) -> VideoClip:
        delay = 0.05 + (strength - 1.0) * (0.45 / 9.0)
        alpha = int((0.15 + (strength - 1.0) * (0.45 / 9.0)) * 256)
        def echo(gf, t):
            c = gf(t).astype(np.uint16)
            p = gf(max(0, t-delay)).astype(np.uint16)
            return np.clip(c + ((p*alpha)>>8), 0, 255).astype(np.uint8)
        return clip.fl(echo)

    @staticmethod
    def _glitchchroma_vfx(clip: VideoClip, strength: float) -> VideoClip:
        def gc(gf, t):
            f = gf(t)
            if random.random() > 0.3:
                s_x, s_y = int(strength*10), int(strength*3)
                rx, ry = random.randint(-s_x, s_x), random.randint(-s_y, s_y)
                bx, by = random.randint(-s_x, s_x), random.randint(-s_y, s_y)
                g = f.copy()
                g[:,:,0] = np.roll(f[:,:,0], shift=(ry, rx), axis=(0,1))
                g[:,:,2] = np.roll(f[:,:,2], shift=(by, bx), axis=(0,1))
                return g
            return f
        return clip.fl(gc)

    @staticmethod
    def _tvscreen_vfx(clip: VideoClip, strength: float) -> VideoClip:
        w, h = clip.size
        scanlines = np.repeat((1.0 - ((0.1+(strength-1.0)*(0.8/9.0)) * (0.5*(1.0+np.sin(np.arange(h).reshape(-1,1)*np.pi*0.8))))), w, axis=1)[:,:,np.newaxis]
        shift = int(strength*3)
        noise = int((strength-3)*5) if strength > 3 else 0
        def tv(gf, t):
            f = gf(t).astype(np.float32) * scanlines
            if noise: f += np.random.randint(-noise, noise, (h, w, 3))
            if shift: 
                f = np.stack((np.roll(f[:,:,0], -shift, axis=1), f[:,:,1], np.roll(f[:,:,2], shift, axis=1)), axis=-1)
            if strength > 7 and random.random() < 0.3:
                y = random.randint(0, max(0, h-50))
                hh = random.randint(10, 50)
                f[y:y+hh, :] = np.roll(f[y:y+hh, :], random.randint(-50, 50), axis=1)
            return np.clip(f, 0, 255).astype(np.uint8)
        return clip.fl(tv)

    @staticmethod
    def _newspaper_vfx(clip: VideoClip, strength: float) -> VideoClip:
        w, h = clip.size
        freq = max(0.1, 0.8 - strength*0.05)
        xv, yv = np.meshgrid(np.arange(w), np.arange(h))
        dots = ((np.sin(xv*freq)*np.sin(yv*freq)) + 1.0)[:,:,np.newaxis]
        def np_flt(gf, t):
            return np.where((gf(t).astype(np.float32)*(2.0/255.0)) > dots, gf(t), 0).astype(np.uint8)
        return clip.fl(np_flt)

    @staticmethod
    def _terminal_vfx(clip: VideoClip, strength: float) -> VideoClip:
        w, h = clip.size
        sf = 1.0 + (strength - 1.0)
        nw, nh = max(1, int(w/sf)), max(1, int(h/sf))
        gs = max(2, int(sf))
        mask = np.clip((np.where(np.arange(w)%gs==0,0.,1.).reshape(1,-1) * np.where(np.arange(h)%gs==0,0.,1.).reshape(-1,1)) + 0.2, 0., 1.)[:,:,np.newaxis]
        famp = 0.02 + strength*0.02
        def term(gf, t):
            px = np.array(PIL.Image.fromarray(gf(t)).resize((nw, nh), PIL.Image.BILINEAR).resize((w, h), PIL.Image.NEAREST)).astype(np.float32)
            g = (px[:,:,0]*0.299 + px[:,:,1]*0.587 + px[:,:,2]*0.114) * 1.3
            out = np.zeros_like(px); out[:,:,1] = g
            return np.clip(out * mask * (1.0+np.sin(t*50)*famp) * random.uniform(1.0-famp, 1.0+famp), 0, 255).astype(np.uint8)
        return clip.fl(term)

    @staticmethod
    def _dataglitch_vfx(clip: VideoClip, strength: float) -> VideoClip:
        w, h = clip.size
        n_glitch = int(strength*2.0)
        mw, mh = int(w*(0.05+strength*0.025)), int(h*(0.05+strength*0.025))
        pxf = int(4 + strength*1.2)
        def dg(gf, t):
            orig = gf(t)
            gl = orig.copy()
            for _ in range(random.randint(1, max(1, n_glitch + random.randint(-2, 3)))):
                bw, bh = random.randint(32, max(33, mw)), random.randint(32, max(33, mh))
                bx, by = random.randint(0, max(0, w-bw)), random.randint(0, max(0, h-bh))
                reg = orig[by:by+bh, bx:bx+bw].copy()
                typ = random.choice(['px','px','sh','inv'])
                if typ == 'px': 
                    gl[by:by+bh, bx:bx+bw] = np.array(PIL.Image.fromarray(reg).resize((max(1,bw//pxf), max(1,bh//pxf)), PIL.Image.NEAREST).resize((bw, bh), PIL.Image.NEAREST))
                elif typ == 'sh':
                    s = random.randint(5, 20+int(strength*2))
                    reg[:,:,0] = np.roll(reg[:,:,0], s, axis=1); reg[:,:,2] = np.roll(reg[:,:,2], -s, axis=1)
                    gl[by:by+bh, bx:bx+bw] = reg
                elif typ == 'inv': gl[by:by+bh, bx:bx+bw] = 255 - reg
            return gl
        return clip.fl(dg)

    @staticmethod
    def _asciiart_vfx(clip: VideoClip, strength: float, fade_color_hex: str) -> VideoClip:
        w, h = clip.size
        bg = tuple(hex_to_rgb(fade_color_hex))
        try: font = PIL.ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
        except: font = PIL.ImageFont.load_default()
        cols = max(20, int(150 - (strength-1.0)*(130.0/9.0)))
        bbox = font.getbbox("@"); cw, ch = bbox[2]-bbox[0], bbox[3]-bbox[1]
        rows = max(1, int((h/w)*cols*(cw/ch)))
        chars = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
        lch = len(chars)
        cont = 1.0 + (strength-1.0)*(1.5/9.0)
        qdiv = 255.0 / max(1, int(64 - (strength-1.0)*(62.0/9.0)) - 1)
        def asc(gf, t):
            f = np.clip(np.round(np.clip((gf(t).astype(np.float32)-127.5)*cont+127.5, 0, 255)/qdiv)*qdiv, 0, 255).astype(np.uint8)
            s_im = PIL.Image.fromarray(f).resize((cols, rows), PIL.Image.BILINEAR)
            sg, sr = np.array(s_im.convert('L')), np.array(s_im)
            aim = PIL.Image.new('RGB', (cols*cw, rows*ch), color=bg)
            dr = PIL.ImageDraw.Draw(aim)
            for r in range(rows):
                yp = r*ch
                for c in range(cols):
                    dr.text((c*cw, yp), chars[int((sg[r,c]/255.0)*(lch-1))], font=font, fill=tuple(sr[r,c]))
            return np.array(aim.resize((w, h), PIL.Image.NEAREST))
        return clip.fl(asc)

    @staticmethod
    def apply(clip: VideoClip, effects: List[Dict[str, float]], bpm: float, fade_color: str, target_fps: int) -> VideoClip:
        for fx in effects:
            s = fx['strength']
            name = fx['name']
            
            if name == 'mirror': clip = EffectEngine._mirror_vfx(clip, s)
            elif name == 'blackwhite': clip = EffectEngine._blackwhite_vfx(clip, s)
            elif name == 'speed': clip = EffectEngine._speed_vfx(clip, s)
            elif name == 'zoomin': clip = EffectEngine._zoom_vfx(clip, 'zoomin', s)
            elif name == 'zoomout': clip = EffectEngine._zoom_vfx(clip, 'zoomout', s)
            elif name == 'grain': clip = EffectEngine._grain_vfx(clip, s)
            elif name == 'posterize': clip = EffectEngine._posterize_vfx(clip, s)
            elif name == 'reverse': clip = EffectEngine._reverse_vfx(clip, s, bpm)
            elif name == 'stopmotion': clip = EffectEngine._stopmotion_vfx(clip, s, bpm, target_fps)
            elif name == 'glitchmotion': clip = EffectEngine._glitchmotion_vfx(clip, s, bpm)
            elif name == 'pixelize': clip = EffectEngine._pixelize_vfx(clip, s)
            elif name == 'oldmovie': clip = EffectEngine._oldmovie_vfx(clip, s, fade_color)
            elif name == 'colorshift': clip = EffectEngine._colorshift_vfx(clip, s)
            elif name == 'shutterecho': clip = EffectEngine._shutterecho_vfx(clip, s)
            elif name == 'glitchchroma': clip = EffectEngine._glitchchroma_vfx(clip, s)
            elif name == 'tvscreen': clip = EffectEngine._tvscreen_vfx(clip, s)
            elif name == 'newspaper': clip = EffectEngine._newspaper_vfx(clip, s)
            elif name == 'terminal': clip = EffectEngine._terminal_vfx(clip, s)
            elif name == 'dataglitch': clip = EffectEngine._dataglitch_vfx(clip, s)
            elif name == 'asciiart': clip = EffectEngine._asciiart_vfx(clip, s, fade_color)

        return clip

class MediaSource:
    def __init__(self, path: Path, start: float, end: float, bpm: float, min_b: int, max_b: int, index: int):
        self.path = path
        self.index = index
        self.start_limit = start
        self.end_limit = end
        self.bpm = bpm
        self.min_beats = min_b
        self.max_beats = max_b
        
        self.is_image = path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        self.beat_duration = 60.0 / bpm
        self.exhausted = False
        
        if not self.is_image and self.end_limit == 0:
            try:
                with VideoFileClip(str(self.path)) as v:
                    self.end_limit = v.duration
            except Exception as e:
                logger.warning(f"Could not read {self.path.name}: {e}")
                self.exhausted = True

    def pre_slice(self) -> List[Segment]:
        if self.is_image or self.exhausted: return []
        segments = []
        cursor = self.start_limit
        while True:
            beats = random.randint(self.min_beats, self.max_beats)
            duration = beats * self.beat_duration
            if cursor + duration > self.end_limit: break
            segments.append(Segment(self.index, cursor, duration))
            cursor += duration
        return segments

    def get_next_linear(self, requested_duration: float, global_offset: float) -> Tuple[float, float]:
        if self.exhausted: return 0.0, 0.0
        if self.is_image: return 0.0, requested_duration
        current_pos = self.start_limit + global_offset
        remaining = self.end_limit - current_pos
        min_seconds = self.min_beats * self.beat_duration
        if remaining < min_seconds:
            self.exhausted = True
            return 0.0, 0.0
        actual_dur = min(requested_duration, remaining)
        return current_pos, actual_dur

    def get_snippet_duration(self) -> float:
        beats = random.randint(self.min_beats, self.max_beats)
        return beats * self.beat_duration

class TimelinePlanner:
    def __init__(self, sources: List[MediaSource], mode: str, effect_configs: List[Dict], fx_maximum: Optional[int], fx_order: str):
        self.sources = sources
        self.mode = mode
        self.effect_configs = effect_configs
        self.global_time = 0.0
        self.fx_maximum = fx_maximum
        self.fx_order = fx_order
        self.edl: List[Snippet] = []
        if '-' in mode: self.source_mode, self.snippet_mode = mode.split('-')
        else: self.source_mode = mode; self.snippet_mode = mode

    def _is_sequential(self, segment: Segment) -> bool:
        if not self.edl: return False
        last_snip = self.edl[-1]
        if last_snip.source_path != self.sources[segment.source_index].path: return False
        return abs((last_snip.start_time + last_snip.duration) - segment.start) < 0.1

    def create_edl(self, target_duration: Optional[float]) -> List[Snippet]:
        # --- PREPARE POOLS ---
        # For 'random' global mode: single large pool
        global_pool: List[Segment] = []
        
        # For 'linear-random' mode: specific pools per source
        source_pools: Dict[int, List[Segment]] = {}
        
        if self.source_mode == 'random' and self.snippet_mode == 'random':
            for s in self.sources: global_pool.extend(s.pre_slice())
            random.shuffle(global_pool)
        
        elif self.source_mode == 'linear' and self.snippet_mode == 'random':
            for s in self.sources:
                pool = s.pre_slice()
                random.shuffle(pool)
                source_pools[s.index] = pool
        
        # Cursors
        pool_cursor = 0
        rr_source_index = 0 # Round-robin source cursor for linear modes
        source_offsets = {s.index: 0.0 for s in self.sources} # Track progress for linear-linear

        while True:
            if target_duration and self.global_time >= target_duration: break
            segment = None
            source_obj = None
            
            # --- STRATEGY 1: GLOBAL RANDOM (Mode: random) ---
            if self.source_mode == 'random' and self.snippet_mode == 'random':
                if pool_cursor >= len(global_pool):
                    logger.warning("All video material exhausted (Random Pool empty). Stopping.")
                    break
                
                candidate = global_pool[pool_cursor]
                
                # Anti-Sequential Logic
                if self._is_sequential(candidate):
                    swapped = False
                    for swap_idx in range(pool_cursor + 1, len(global_pool)):
                        if not self._is_sequential(global_pool[swap_idx]):
                            global_pool[pool_cursor], global_pool[swap_idx] = global_pool[swap_idx], global_pool[pool_cursor]
                            swapped = True
                            break
                
                segment = global_pool[pool_cursor]
                pool_cursor += 1
                source_obj = next(s for s in self.sources if s.index == segment.source_index)

            # --- STRATEGY 2: LINEAR-RANDOM (Round-Robin Sources, Shuffled Segments) ---
            elif self.source_mode == 'linear' and self.snippet_mode == 'random':
                # Try finding a source with segments left, starting from rr_source_index
                start_search_idx = rr_source_index
                found_src = False
                
                for _ in range(len(self.sources)):
                    potential_idx = rr_source_index % len(self.sources)
                    s_idx = self.sources[potential_idx].index
                    
                    if source_pools[s_idx]: # If this source has segments left
                        source_obj = self.sources[potential_idx]
                        
                        # Anti-Sequential Logic (check against last used)
                        candidate = source_pools[s_idx][0]
                        if self._is_sequential(candidate):
                            swapped = False
                            for swap_idx in range(1, len(source_pools[s_idx])):
                                if not self._is_sequential(source_pools[s_idx][swap_idx]):
                                    source_pools[s_idx][0], source_pools[s_idx][swap_idx] = source_pools[s_idx][swap_idx], source_pools[s_idx][0]
                                    swapped = True
                                    break
                        
                        segment = source_pools[s_idx].pop(0)
                        found_src = True
                        
                        # Advance Round Robin
                        rr_source_index = (potential_idx + 1) % len(self.sources)
                        break
                    
                    # Try next source
                    rr_source_index = (rr_source_index + 1) % len(self.sources)
                
                if not found_src:
                    break # All sources exhausted

            # --- STRATEGY 3: LINEAR / RANDOM-LINEAR (Cursor based, Round-Robin if Linear) ---
            else: 
                if self.source_mode == 'random':
                    # Random-Linear: Pick random source, play next linear chunk
                    valid_sources = [s for s in self.sources if not s.exhausted]
                    if not valid_sources: break
                    source_obj = random.choice(valid_sources)
                else:
                    # Linear-Linear: Round Robin behavior
                    # Try to find next non-exhausted source
                    start_search_idx = rr_source_index
                    found_src = False
                    
                    for _ in range(len(self.sources)):
                        potential_idx = rr_source_index % len(self.sources)
                        if not self.sources[potential_idx].exhausted:
                            source_obj = self.sources[potential_idx]
                            found_src = True
                            rr_source_index = (potential_idx + 1) % len(self.sources)
                            break
                        rr_source_index = (rr_source_index + 1) % len(self.sources)
                    
                    if not found_src: break

                # Generate Segment
                dur = source_obj.get_snippet_duration()
                start, real_dur = source_obj.get_next_linear(dur, source_offsets[source_obj.index])
                
                if real_dur > 0:
                    segment = Segment(source_obj.index, start, real_dur)
                    source_offsets[source_obj.index] += real_dur
                else:
                    # Mark exhausted and retry loop to find next source
                    source_obj.exhausted = True
                    continue

            # --- APPEND ---
            if segment:
                fx_plan = EffectEngine.select_effects(self.effect_configs, self.fx_maximum, self.fx_order)
                snippet = Snippet(
                    index=len(self.edl) + 1,
                    source_path=source_obj.path,
                    start_time=segment.start,
                    duration=segment.duration,
                    is_image=source_obj.is_image,
                    effects=fx_plan
                )
                self.edl.append(snippet)
                self.global_time += segment.duration
                
        return self.edl

class Renderer:
    def __init__(self, config: RenderConfig):
        self.cfg = config
        
    def _process_snippet(self, snippet: Snippet) -> Optional[Path]:
        try:
            if not self.cfg.temp_dir.exists():
                self.cfg.temp_dir.mkdir(parents=True, exist_ok=True)

            target_res = self.cfg.resolution
            
            if snippet.is_image:
                clip = ImageClip(str(snippet.source_path)).set_duration(snippet.duration)
            else:
                clip = VideoFileClip(str(snippet.source_path)).subclip(
                    snippet.start_time, snippet.start_time + snippet.duration
                )
            
            # Crop to Fit
            w_s, h_s = clip.size
            w_t, h_t = target_res
            target_ar, source_ar = w_t / h_t, w_s / h_s
            
            if source_ar > target_ar:
                new_h, new_w = h_s, h_s * target_ar
            else:
                new_w, new_h = w_s, w_s / target_ar
                
            clip = clip.fx(vfx.crop, x_center=w_s/2, y_center=h_s/2, width=new_w, height=new_h)
            clip = clip.resize(newsize=target_res)
            
            # Pass global BPM and fade_color to effect engine
            clip = EffectEngine.apply(clip, snippet.effects, self.cfg.bpm, self.cfg.fade_color, self.cfg.fps)
            temp_file = self.cfg.temp_dir / f"snip_{snippet.index:05d}.mp4"
            
            clip.write_videofile(
                str(temp_file), 
                fps=self.cfg.fps, 
                codec="libx264", 
                preset="ultrafast", 
                audio_codec="aac",
                logger=None, 
                verbose=False
            )
            clip.close()
            return temp_file
        except Exception as e:
            logger.error(f"Error processing snippet {snippet.index} ({snippet.source_path.name}): {e}")
            return None

    def render_snippets(self, edl: List[Snippet]) -> List[Path]:
        if self.cfg.temp_dir.exists():
            shutil.rmtree(self.cfg.temp_dir)
        self.cfg.temp_dir.mkdir(parents=True, exist_ok=True)
        
        valid_files = []
        total = len(edl)
        
        logger.info(f"Starting physical rendering of {total} snippets to {self.cfg.temp_dir}...")
        for i, snippet in enumerate(edl):
            print(f"\rProgress: {i+1}/{total}", end="", flush=True)
            path = self._process_snippet(snippet)
            if path:
                valid_files.append(path)
        print("") 
        return valid_files

    def finalize(self, clip_paths: List[Path]):
        if not clip_paths:
            logger.error("No valid clips to concatenate.")
            return

        try:
            logger.info("Concatenating snippets (Chain Mode)...")
            clips = [VideoFileClip(str(p)) for p in clip_paths]
            final_video = concatenate_videoclips(clips, method="chain")
            
            if self.cfg.audio_path:
                audio = AudioFileClip(str(self.cfg.audio_path))
                final_video = final_video.set_audio(audio)
                if self.cfg.target_duration:
                    final_video = final_video.set_duration(self.cfg.target_duration)
            
            fade_rgb = hex_to_rgb(self.cfg.fade_color)
            if self.cfg.fade_in > 0: 
                final_video = final_video.fadein(self.cfg.fade_in, initial_color=fade_rgb)
            if self.cfg.fade_out > 0:
                final_video = final_video.fadeout(self.cfg.fade_out, final_color=fade_rgb)

            params = {
                "fps": self.cfg.fps,
                "codec": self.cfg.codec,
                "audio_codec": "aac",
                "preset": "slower" if self.cfg.optimize else "medium",
                "threads": 4
            }
            if self.cfg.optimize:
                params["ffmpeg_params"] = ["-crf", "26"]

            logger.info(f"Rendering final file: {self.cfg.output_path}")
            final_video.write_videofile(str(self.cfg.output_path), **params)
            
            logger.info("Cleaning up resources...")
            for c in clips: 
                try: c.close() 
                except: pass
            
            if self.cfg.temp_dir.exists():
                shutil.rmtree(self.cfg.temp_dir)
            logger.info("Done.")

        except Exception as e:
            logger.critical(f"Critical error during finalization: {e}", exc_info=True)

# --- MAIN ORCHESTRATION ---

def parse_input_arg(input_str: str, defaults: Dict[str, Any]) -> Tuple[str, float, float, float, int, int]:
    parts = input_str.split(':')
    get = lambda i, d: parts[i] if len(parts) > i and parts[i] else d
    
    fname = parts[0]
    start = float(get(1, 0))
    end = float(get(2, 0))
    bpm = float(get(3, defaults['bpm']))
    
    # Parse beat range from input string (4th param) using unified logic
    beat_range_str = get(4, defaults['snippetbeats'])
    min_b, max_b = parse_int_range_string(beat_range_str)
    
    return fname, start, end, bpm, min_b, max_b

def main():
    parser = argparse.ArgumentParser(description="VidSeq - CLI Video Generator")
    
    preset_list = ", ".join(PRESETS.keys())
    effects_list = ", ".join(EffectEngine.AVAILABLE_EFFECTS)

    g_in = parser.add_argument_group("Input Sources")
    g_in.add_argument('--input', action='append', 
                      help="Format: FILE:START:END:BPM:BEATS (e.g. video.mp4:0:0:120:4..8)")
    g_in.add_argument('--preset', type=str, 
                      help=f"Load a configuration preset. Options: {preset_list} or path to a JSON file.")
    g_in.add_argument('--saveproject', type=Path, help="Save current configuration to JSON")
    g_in.add_argument('--loadproject', type=Path, help="Load configuration from JSON")
    g_in.add_argument('--modus', choices=['random', 'linear', 'random-linear', 'linear-random'], 
                      help="Sequencing algorithm (Source-Snippet)")
    g_in.add_argument('--bpm', type=float, help="Global BPM")
    g_in.add_argument('--snippetbeats', type=str, help="Beats per snippet range (e.g. 4..8)")

    g_out = parser.add_argument_group("Output Settings")
    g_out.add_argument('--output', type=Path, default=Path("output.mp4"), help="Output filename")
    g_out.add_argument('--res', type=parse_resolution, default="1920x1080:24", help="WxH:FPS")
    g_out.add_argument('--codec', type=str, default="libx264", help="Video Codec")
    g_out.add_argument('--optimize', action='store_true', help="Enable CRF Encoding")
    g_out.add_argument('--temp', type=Path, default=Path("tempsnippets"), help="Temp directory")
    g_out.add_argument('--log', type=str, help="Path to log file")
    g_out.add_argument('--dry-run', action='store_true', help="Simulate only")
    g_out.add_argument('--seed', type=int, help="Random seed for reproducibility")

    g_time = parser.add_argument_group("Timing & Audio")
    g_time.add_argument('--audio', type=Path, help="Master Audio File path")
    g_time.add_argument('--duration', type=float, help="Target duration in seconds")
    g_time.add_argument('--length', type=float, help="Target duration in Beats")

    g_fx = parser.add_argument_group("Effects & Transitions")
    g_fx.add_argument('--effects', action='append', 
                      help=f"Format: NAME:CHANCE:STRENGTH (e.g., glitchchroma:50:3..8). Available: {effects_list}")
    g_fx.add_argument('--fx-chance', type=float, help="Global effect probability")
    g_fx.add_argument('--fx-intensity', type=str, help="Global effect intensity (e.g. 5 or 3..8)")
    g_fx.add_argument('--fx-maximum', type=int, help="Maximum number of effects per snippet")
    g_fx.add_argument('--fx-order', choices=['linear', 'random'], help="Apply effects in defined or random order")
    g_fx.add_argument('--fadein', type=int, help="Fade-in duration in Beats")
    g_fx.add_argument('--fadeout', type=int, help="Fade-out duration in Beats")
    g_fx.add_argument('--fadecolor', type=str, default="#000000", help="Hex color for fades")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    
    setup_logging(args.log)
    logger.info("Initializing VidSeq...")

    # --- RESOLVE CONFIGURATION ---
    
    # 1. System Defaults
    active_conf = DEFAULTS.copy()
    
    # 2. Preset Override
    if args.preset:
        if args.preset in PRESETS:
            logger.info(f"Applying internal preset: {args.preset}")
            active_conf.update(PRESETS[args.preset])
        else:
            p_path = Path(args.preset)
            if p_path.is_file():
                try:
                    with open(p_path, 'r', encoding='utf-8') as f:
                        custom_preset = json.load(f)
                        logger.info(f"Applying custom preset from file: {p_path}")
                        active_conf.update(custom_preset)
                except Exception as e:
                    logger.error(f"Failed to load custom preset '{args.preset}': {e}. Using defaults.")
            else:
                logger.warning(f"Preset '{args.preset}' not found. Using defaults.")
    else:
        logger.info("No preset specified. Using system defaults.")

    # 3. Load Project Override (New Layer)
    if args.loadproject:
        lp_path = Path(args.loadproject)
        if lp_path.is_file():
            try:
                with open(lp_path, 'r', encoding='utf-8') as f:
                    project_conf = json.load(f)
                    logger.info(f"Loading project configuration from: {lp_path}")
                    active_conf.update(project_conf)
            except Exception as e:
                logger.error(f"Failed to load project file '{args.loadproject}': {e}")
        else:
            logger.error(f"Project file not found: {args.loadproject}")
        
    # 4. CLI Arguments Override
    if args.bpm is not None: active_conf['bpm'] = args.bpm
    if args.snippetbeats is not None: active_conf['snippetbeats'] = args.snippetbeats
    if args.modus is not None: active_conf['modus'] = args.modus
    if args.fx_chance is not None: active_conf['fx_chance'] = args.fx_chance
    if args.fx_intensity is not None: active_conf['fx_intensity'] = args.fx_intensity
    if args.fx_maximum is not None: active_conf['fx_maximum'] = args.fx_maximum
    if args.fx_order is not None: active_conf['fx_order'] = args.fx_order
    if args.fadein is not None: active_conf['fadein'] = args.fadein
    if args.fadeout is not None: active_conf['fadeout'] = args.fadeout
    
    # Append CLI effects to the config's effects list (if any)
    if args.effects:
        active_conf['effects'].extend(args.effects)
    
    # CLI Inputs: Append to project/preset inputs
    if args.input:
        if 'inputs' not in active_conf: active_conf['inputs'] = []
        active_conf['inputs'].extend(args.input)

    # CLI Output Settings overrides
    active_conf['resolution'] = f"{args.res[0][0]}x{args.res[0][1]}" 
    active_conf['fps'] = args.res[1]
    active_conf['codec'] = args.codec
    active_conf['optimize'] = args.optimize
    if args.audio: active_conf['audio_path'] = str(args.audio)
    if args.duration: active_conf['duration'] = args.duration
    if args.length: active_conf['length_beats'] = args.length

    # --- SEED INITIALIZATION ---
    if args.seed is not None:
        final_seed = args.seed
    elif active_conf.get('seed') is not None:
        final_seed = active_conf['seed']
    else:
        final_seed = random.randint(0, 99999999)

    active_conf['seed'] = final_seed
    random.seed(final_seed)
    np.random.seed(final_seed)
    logger.info(f"Random Seed initialized: {final_seed}")

    # --- PRINT CONFIGURATION SUMMARY ---
    logger.info("\n" + "="*60)
    logger.info("ACTIVE CONFIGURATION SUMMARY")
    logger.info("="*60)
    for key, value in sorted(active_conf.items()):
        val_str = str(value)
        if len(val_str) > 80: val_str = val_str[:77] + "..."
        logger.info(f"{key:<20}: {val_str}")
    logger.info("="*60 + "\n")

    # --- INPUT VALIDATION (Late Check) ---
    if not active_conf['inputs']:
        logger.error("No input sources defined. Use --input or load a project with inputs.")
        return

    # --- SAVE PROJECT ---
    if args.saveproject:
        try:
            with open(args.saveproject, 'w', encoding='utf-8') as f:
                serializable_conf = active_conf.copy()
                if serializable_conf.get('audio_path'): 
                    serializable_conf['audio_path'] = str(serializable_conf['audio_path'])
                json.dump(serializable_conf, f, indent=4)
            logger.info(f"Project configuration successfully saved to: {args.saveproject}")
        except Exception as e:
            logger.error(f"Failed to save project: {e}")

    final_effects_strings = active_conf['effects']
    
    if isinstance(active_conf['resolution'], str):
        w, h = map(int, active_conf['resolution'].lower().split('x'))
        res_size = (w, h)
    else:
        res_size = active_conf['resolution'] 
    
    res_fps = active_conf['fps']
    global_beat_dur = 60.0 / active_conf['bpm']

    # Timing Conflict Check
    target_dur = active_conf.get('duration')
    target_len_beats = active_conf.get('length_beats')
    
    if target_dur is not None and target_len_beats is not None:
        calc_len_sec = target_len_beats * global_beat_dur
        if abs(calc_len_sec - target_dur) > 0.1:
            logger.error(f"Timing conflict: duration {target_dur}s != length {target_len_beats} beats.")
            return

    # Final Render Config
    render_config = RenderConfig(
        output_path=args.output,
        temp_dir=args.temp,
        resolution=res_size,
        fps=res_fps,
        codec=active_conf['codec'],
        optimize=active_conf['optimize'],
        audio_path=Path(active_conf['audio_path']) if active_conf.get('audio_path') else None,
        target_duration=None,
        fade_in=active_conf['fadein'] * global_beat_dur,
        fade_out=active_conf['fadeout'] * global_beat_dur,
        fade_color=active_conf['fadecolor'],
        dry_run=args.dry_run,
        bpm=active_conf['bpm']
    )

    if render_config.audio_path:
        try:
            with AudioFileClip(str(render_config.audio_path)) as a:
                render_config.target_duration = a.duration
        except Exception as e:
            logger.error(f"Error reading audio file: {e}")
            return
    elif target_dur:
        render_config.target_duration = target_dur
    elif target_len_beats:
        render_config.target_duration = target_len_beats * global_beat_dur

    global_fx_range = parse_range_string(active_conf['fx_intensity'])
    
    effect_configs = []
    if final_effects_strings:
        for fx_str in final_effects_strings:
            effect_configs.append(parse_effect_string(
                fx_str, active_conf['fx_chance'], global_fx_range
            ))
    else:
        effect_configs.append({'name': 'none', 'chance': 0, 'strength_range': (0.0, 0.0)})

    defaults = {'bpm': active_conf['bpm'], 'snippetbeats': active_conf['snippetbeats']}
    sources = []
    
    for idx, inp_str in enumerate(active_conf['inputs']):
        fname, start, end, bpm, min_b, max_b = parse_input_arg(inp_str, defaults)
        
        potential_path = Path(fname)
        if potential_path.is_file():
            files = [str(potential_path)]
        elif Path(fname.replace(r'\ ', ' ').replace(r'\(', '(').replace(r'\)', ')').replace(r'\[', '[').replace(r'\]', ']')).is_file():
             files = [str(Path(fname.replace(r'\ ', ' ').replace(r'\(', '(').replace(r'\)', ')').replace(r'\[', '[').replace(r'\]', ']')))]
        else:
            files = list(glob.glob(fname))

        if not files:
            logger.warning(f"No files found for pattern: {fname}")
            continue
        for f in files:
            source = MediaSource(Path(f), start, end, bpm, min_b, max_b, index=len(sources))
            if not source.exhausted:
                sources.append(source)

    if not sources:
        logger.error("No valid media sources available. Aborting.")
        return

    planner = TimelinePlanner(sources, active_conf['modus'], effect_configs, active_conf['fx_maximum'], active_conf['fx_order'])
    edl = planner.create_edl(render_config.target_duration)

    total_beats = planner.global_time / global_beat_dur
    logger.info(f"Planning complete: {len(edl)} snippets, total: {planner.global_time:.2f}s ({total_beats:.1f} beats)")

    # --- TABLE OUTPUT ---
    header = f"{'TIME (s)':<10} | {'BEATS':<8} | {'FROM':<10} | {'SOURCE':<30} | {'EFFECTS'}"
    logger.info("\n" + header)
    logger.info("-" * len(header))
    
    curr = 0.0
    for s in edl:
        curr_beats = curr / global_beat_dur
        fx_list = []
        for e in s.effects:
            fx_list.append(f"{e['name']}({e['strength']:.1f})")
        fx_str = ",".join(fx_list) or "-"
        
        from_ts = f"{s.start_time:.2f}s"
        line = f"{curr:<10.2f} | {curr_beats:<8.1f} | {from_ts:<10} | {s.source_path.name:<30} | {fx_str}"
        logger.info(line)
        curr += s.duration

    if args.dry_run:
        logger.info("Dry run finished. Exiting.")
        return

    renderer = Renderer(render_config)
    temp_files = renderer.render_snippets(edl)
    
    if temp_files:
        renderer.finalize(temp_files)
    else:
        logger.warning("No snippets were generated. Rendering aborted.")

if __name__ == "__main__":
    main()