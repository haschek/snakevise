# SnakeVISE - Generative VIdeo SEquencer, written in Python

**SnakeVISE** (speak: Snake vice) is a CLI-based rhythmic video editor that creates dynamic montages synced to a specific BPM. It uses procedural algorithms to slice input media into beat-accurate snippets and applies a variety of visual effects.

---

## 🌊 Vibe Coding

SnakeVISE was built using **Vibe Coding** principles—leveraging advanced AI orchestration (like Gemini CLI) to rapidly prototype and modularize complex video processing logic. Instead of manual boilerplate, the focus was on defining the "vibe" (rhythmic, glitchy, procedural) and allowing AI to handle the surgical implementation of effects and architecture.

---

## ✨ Features

- **Rhythmic Sequencing**: Slices video and images based on BPM and beat counts.
- **20+ Visual Effects**: Including glitch, zoom, old movie, ASCII art, dataglitch, and more.
- **Intelligent Modes**:
  - `linear`: Sequential processing of sources.
  - `random`: Full chaotic shuffle.
  - `linear-random` & `random-linear`: Hybrid sequencing strategies.
- **Presets**: Quick-start configurations (`lofi`, `vintage`, `urban`, `chaos`).
- **Project Management**: Save and load complex render configurations as JSON.
- **Audio Sync**: Automatically matches video duration to a master audio file.

---

## 🚀 Installation

1. **Clone and Setup**:

   ```bash
   git clone https://github.com/haschek/snakevise.git
   cd snakevise
   python -m venv .venv
   source .venv/bin/activate
   pip install .
   ```

2. **System Dependencies**:
   Ensure you have `ffmpeg` installed on your system as it is required by `moviepy`.

---

## 🛠 Usage

### Basic Example

Create a video from a single source using the `vintage` preset:

```bash
python snakevise.py --input my_video.mp4 --preset vintage --output rhythmic_montage.mp4
```

### Advanced Input Strings

You can define specific ranges and BPMs per input:
`FILE:START_SEC:END_SEC:BPM:BEAT_RANGE`

```bash
python snakevise.py --input "vacation.mp4:10:60:120:4..8" --audio music.mp3 --modus random
```

---

## 📂 Project Persistence

You can save your current configuration (including all inputs, vfx settings, and timing) to a JSON file for later use.

- **Save a project**:

  ```bash
  python snakevise.py --input video.mp4 --vfx glitchchroma:100:5 --saveproject my_cool_edit.json
  ```

- **Load a project**:

  ```bash
  python snakevise.py --loadproject my_cool_edit.json --output second_version.mp4
  ```

---

## 📖 CLI Arguments Reference

### Input Sources

- `--input`: Path to media. Format: `FILE:START:END:BPM:BEATS`. Supports globs.
- `--preset`: Load a built-in style or path to a JSON preset file.
- `--saveproject`: Path to save the current configuration as JSON.
- `--loadproject`: Path to load a configuration from a JSON file.
- `--modus`: Sequencing algorithm. Options: `random`, `linear`, `random-linear`, `linear-random`.
- `--bpm`: Global BPM for the project.
- `--snippetbeats`: Default beat range for snippets (e.g., `4..8`).

### Output Settings

- `--output`: Final filename (default: `output.mp4`).
- `--res`: Output resolution and FPS. Format: `WIDTHxHEIGHT:FPS` (default: `1920x1080:24`).
- `--codec`: Video codec (default: `libx264`).
- `--optimize`: Enable CRF encoding for smaller file sizes.
- `--temp`: Directory for temporary snippet storage.
- `--log`: Path to a log file.
- `--dry-run`: Simulation mode. Prints the timeline without rendering.
- `--seed`: Random seed for reproducibility.

### Timing & Audio

- `--audio`: Path to a master audio file. Sets target duration to audio length.
- `--duration`: Target total duration in seconds.
- `--length`: Target total duration in Beats.

### VFX & Transitions

- `--vfx`: Add an effect. Format: `NAME:CHANCE:STRENGTH`.
- `--vfx-chance`: Global probability (0-100) for all effects.
- `--vfx-intensity`: Global strength range (e.g., `1..5`).
- `--vfx-maximum`: Max number of effects to apply per snippet.
- `--vfx-order`: Order of effects (`linear` or `random`).
- `--fadein`: Fade-in duration in Beats.
- `--fadeout`: Fade-out duration in Beats.
- `--fadecolor`: Hex color for fades (default: `#000000`).

---

## 🎨 Effects Encyclopedia

| Effect | Description |
| :--- | :--- |
| `zoomin` | Smooth procedural zoom into the center of the frame. |
| `zoomout` | Smooth procedural zoom out from the center. |
| `glitchchroma` | Random RGB channel shifting for a chromatic aberration look. |
| `glitchmotion` | Slices the snippet into tiny chunks and shuffles them temporally. |
| `mirror` | Horizontal, vertical, or quad mirroring. |
| `grain` | Adds procedural film grain/noise. |
| `speed` | Procedural speed ramping within the snippet. |
| `blackwhite` | High-contrast black and white filter. |
| `posterize` | Reduces the number of colors for a retro/artistic look. |
| `reverse` | Plays a portion or the entirety of the snippet backwards. |
| `stopmotion` | Lowers the effective framerate for a jerky, rhythmic feel. |
| `pixelize` | Low-res pixel art effect with dynamic scaling. |
| `oldmovie` | Adds vignette, tinting, and flicker for a vintage look. |
| `colorshift` | Dynamic HSV hue rotation. |
| `shutterecho` | Ghosting effect by blending current frames with previous ones. |
| `tvscreen` | Simulated CRT scanlines, static, and signal interference. |
| `newspaper` | Halftone dot pattern reminiscent of print media. |
| `terminal` | Green-on-black monochromatic CRT terminal look. |
| `dataglitch` | Random block-based compression artifacts and inversions. |
| `asciiart` | Real-time conversion of video frames to colored ASCII text. |

---

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0.
