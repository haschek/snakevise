# SnakeVISE - Generative VIdeo SEquencer, written in Python

**SnakeVISE** (speak: Snake vice) is a CLI-based rhythmic video editor that creates dynamic montages synced to a specific BPM.
It uses procedural algorithms to slice input media into beat-accurate snippets and applies a variety of visual effects.

---

## 🌊 Vibe Coding

SnakeVISE was built using **Vibe Coding** principles—leveraging advanced AI orchestration (like Gemini CLI) to rapidly prototype and modularize complex video processing logic.
Instead of manual boilerplate, the focus was on defining the "vibe" (rhythmic, glitchy, procedural), allowing AI to handle the surgical implementation of effects and architecture.

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

   # For developers:
   pip install -e ".[dev]"
   pre-commit install
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
- `--audio`: Path to a master audio file. Sets target duration to audio length.
- `--preset`: Load a built-in style or path to a JSON preset file.
- `--loadproject`: Path to load a configuration from a JSON file.
- `--modus`: Sequencing algorithm. Options: `random`, `linear`, `random-linear`, `linear-random`.

### Output Settings

- `--output`: Final filename (default: `output.mp4`).
- `--res`: Output resolution and FPS. Format: `WIDTHxHEIGHT:FPS` (default: `1920x1080:24`).
- `--codec`: Video codec (default: `libx264`).
- `--optimize`: Enable CRF encoding for smaller file sizes.
- `--temp`: Directory for temporary snippet storage.
- `--log`: Path to a log file.
- `--dry-run`: Simulation mode. Prints the timeline without rendering.
- `--seed`: Random seed for reproducibility.
- `--saveproject`: Path to save the current configuration as JSON.

### Timing & Audio

- `--duration`: Target total duration in seconds.
- `--length`: Target total duration in Beats.
- `--bpm`: Global BPM for the project.
- `--snippetbeats`: Default beat range for snippets (e.g., `4..8`).

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

## 💬 Subtitle Rendering (WebVTT)

SnakeVISE supports overlaying text onto the final video using the WebVTT format.
This is ideal for lyrics, titles, or commentary that needs to be perfectly synced with the rhythmic montage.

- `--subtitles`: Path to a WebVTT file for overlaying text onto the final video.
- `--stfont`: Name of the font(s) to use for subtitles (default: `Arial`).
  - Supports multiple values: `--stfont Arial --stfont Courier`.
  - Supports comma-separated: `--stfont "Arial, Verdana, Courier"`.
  - Supports random selection: `--stfont RANDOM:5` picks 5 random compatible fonts from your system.
  - If multiple fonts are provided, a random one is chosen for each subtitle line.
  - Use `make list-fonts` to see available options.
- `--stfontsize`: Font size(s) for subtitles (default: `48`).
  - Supports multiple values: `--stfontsize 40 --stfontsize 60`.
  - Supports comma-separated: `--stfontsize "40, 50, 60"`.
  - Supports random range: `--stfontsize RANDOM:40..80:5` (picks 5 random sizes between 40 and 80).
  - If multiple values are provided, a random one is chosen for each line.
- `--ststrokewidth`: Stroke width(s) for subtitles (default: `1.5`).
  - Supports multiple values: `--ststrokewidth 1 --ststrokewidth 3`.
  - Supports comma-separated: `--ststrokewidth "1, 1.5, 2"`.
  - Supports random range: `--ststrokewidth RANDOM:1..4:3` (picks 3 random widths between 1 and 4).
  - If multiple values are provided, a random one is chosen for each line.
- `--stcolor`: Text color(s) for subtitles (default: `white`).
  - Supports multiple values: `--stcolor white --stcolor yellow`.
  - Supports comma-separated: `--stcolor "white, #FFFF00"`.
  - Supports random selection: `--stcolor RANDOM:5` picks 5 random colors.
- `--stscolor`: Stroke color(s) for subtitles (default: `black`).
  - Same format as `--stcolor`.

### Supported Features

- **Standard Timing**: Cues are rendered at their specified `START --> END` times. Supports both `MM:SS.mmm` and `HH:MM:SS.mmm`.
- **Positioning**: Use the `align` and `line` settings in the cue header.
  - `align:left`, `align:right`, `align:center` (horizontal).
  - `line:top`, `line:middle`, `line:bottom` (vertical).
- **Sizing**: Use the `size` setting to define the width of the subtitle area as a percentage of the video width (e.g., `size:50%`). Default is 90%.
- **Formatting**: Supports standard HTML-like tags (case-insensitive):
  - `<b>...</b>` or `<strong>...</strong>` for **Bold** text.
  - `<i>...</i>` or `<em>...</em>` for *Italic* text.
- **Dry Run Support**: Use `--dry-run` to see the calculated subtitle plan and positions in the log without rendering the video.
- **Dynamic Sizing**: Subtitles are automatically wrapped and sized to fit within 90% of the video width.
- **Advanced Font Support**:
  - Use `--stfont` to specify one or multiple system fonts.
  - Mix fonts: `--stfont Arial --stfont Courier` (randomly chosen per line).
  - Use comma lists: `--stfont "Arial, Verdana, Courier"`.
  - Chaos Mode: Use `--stfont RANDOM:3` to select 3 random fonts from the available inventory.
  - **Automatic Validation**: SnakeVISE proactively tests each font for compatibility. If a chosen font is broken or missing, it automatically falls back to other working alternatives.
  - Use `make list-fonts` to see compatible fonts on your system.

### Example WebVTT File

Save this as `lyrics.vtt`:

```vtt
WEBVTT

00:00.500 --> 00:02.000 align:left line:top
<b>SNAKEVISE</b> - THE VIBE

00:02.500 --> 00:05.000 align:center line:middle
<i>Procedural Video Generator</i>

00:06.000 --> 00:08.000 align:right line:bottom
Created with <u>Gemini CLI</u>
```

To render with these subtitles:

```bash
python snakevise.py --input my_video.mp4 --subtitles lyrics.vtt
```

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
