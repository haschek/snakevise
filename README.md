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
- **26+ Visual Effects**: Including glitch, zoom, old movie, ASCII art, dataglitch, and more.
- **Intelligent Modes**:
  - `linear`: Sequential processing of sources.
  - `random`: Full chaotic shuffle.
  - `linear-random` & `random-linear`: Hybrid sequencing strategies.
- **Presets**: Quick-start configurations (`subtle`, `lofi`, `vintage`, `urban`, `chaos`).
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
- `--crop`: Initial crop/resize method for input media. Can be specified multiple
  times or as a comma-separated list. If multiple are specified, a random one
  is selected for each snippet. Options:
  - `crop-to-fit` (default)
  - `stretch`
  - `slideover` (pans randomly left-to-right/right-to-left or top-to-bottom/bottom-to-top)
  - `duplicate` (tiles copies of the clip to fill dimensions)
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
- `--fadein`: Fade-in duration. Integer = Beats, Suffix 's' = Seconds (e.g. `4` or `2.5s`).
- `--fadeout`: Fade-out duration. Integer = Beats, Suffix 's' = Seconds (e.g. `4` or `2.5s`).
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
  - Use `make list-fonts ARGS="--test"` to verify which fonts are actually renderable on your system.
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
- --stfx: Subtitle effect. Format: `EFFECT:CHANCE:STRENGTH` (e.g. `fadein:50:1..10`). Effects: `fadein`/`fadeout`, `slidein`/`slideout`, `blur`, `flickering`, `jumping`, `moving`, `tilt`.
- `--stfx-chance`: Global probability (0-100) for all subtitle effects (default: `20`).
- `--stfx-intensity`: Global subtitle effect strength/intensity (default: `1..3`).
- `--stfx-maximum`: Maximum number of subtitle effects to apply per cue (default: `None`).
- `--stfx-order`: Execution order for subtitle effects (`linear` or `random`).

### Supported Features

- **Standard Timing**: Cues are rendered at their specified `START --> END` times. Supports both `MM:SS.mmm` and `HH:MM:SS.mmm`.
- **Positioning & Styling**: Use the settings in the cue header.
  - `align:left`, `align:right`, `align:center` (horizontal positioning).
  - `line:top`, `line:middle`, `line:bottom` (vertical positioning).
  - `color:VALUE` (e.g., `color:yellow` or `color:#ff0000`) overrides text color.
  - `scolor:VALUE` (or `strokecolor:VALUE`) overrides the stroke outline color.
  - `fontsize:NUMBER` (e.g., `fontsize:36`) overrides the font size.
  - `strokewidth:NUMBER` (e.g., `strokewidth:2`) overrides the stroke outline width.
- **Sizing**: Use the `size` setting to define the width of the subtitle area as a percentage of the video width (e.g., `size:50%`). Default is 90%.
- **Formatting**: Supports standard HTML-like tags (case-insensitive):
  - `<b>...</b>` or `<strong>...</strong>` for **Bold** text.
  - `<i>...</i>` or `<em>...</em>` for *Italic* text.
- **Visual Effects & Animations**: Subtitles can fade in/out, slide in/out from off-screen, blur, flicker, jump, move, or tilt smoothly.
  - **Inline Configuration (WebVTT settings block)**: Add tags directly to the cue header using the `stfx:NAME:CHANCE:STRENGTH` format.
    - If `CHANCE` or `STRENGTH` are omitted (e.g., `stfx:fadein`), they automatically fall back to the global defaults.
    - Custom values for `slidein` and `slideout` are passed in the `STRENGTH` segment as `direction-duration` (e.g., `left-0.2` or `top-0.15`).
    - Special control effects: `stfx:none:100:0` disables all effects for the cue; `stfx:onlyvtt:100:0` runs ONLY VTT-specified effects, ignoring global probabilistic effects.
    - Example: `stfx:fadein:100:8` (100% chance, strength 8 fade duration)
    - Example: `stfx:slidein:100:left-0.2` (100% chance, slide-in from left taking 20% of cue duration)
    - Example: `stfx:slideout:100:right-0.15` (100% chance, slide-out to right taking 15% of cue duration)
    - Example: `stfx:blur:50:5` (50% chance, strength 5 constant blur)
    - Example: `stfx:jumping` (runs with default chance and intensity)
  - **Global Configuration (CLI & Presets)**: Use the structured subtitle visual effects engine (analogous to video effects).
    - Example: `python snakevise.py --subtitles lyrics.vtt --stfx fadein:50:1..10 --stfx slideout:50:8`
    - **Fading Strength**: Relative to the cue's active display time: `1 = 4%` to
      `10 = 40%` of the subtitle cue's duration (e.g., strength `8` on a `2.0s`
      cue results in a `0.64s` fade duration).
    - **Slidein / Slideout Strength**: Relative to the cue's active display time
      (slow = `25%` of cue duration, fast = `12%` of cue duration). Decoded into
      direction and speed combinations:
      - `1`: bottom, slow (25% of cue duration)
      - `2`: bottom, fast (12% of cue duration)
      - `3`: top, slow (25% of cue duration)
      - `4`: top, fast (12% of cue duration)
      - `5`: left, slow (25% of cue duration)
      - `6`: left, fast (12% of cue duration)
      - `7`: right, slow (25% of cue duration)
      - `8`: right, fast (12% of cue duration)
      - `9`: random direction, slow (25% of cue duration)
      - `10` or higher: random direction, fast (12% of cue duration)
    - **Blur Strength**: Constant blur intensity over the entire subtitle display
      duration. Strength `1` corresponds to a blur radius of `0.5px` and strength
      `10` corresponds to `5px`, scaled linearly (`sigma = strength * 0.5`).
    - **Flickering Strength**: Determines the frequency and minimum number of times the text and outline disappear. Strength `1` corresponds to 1 flicker per second
      (minimum 1 flicker per cue), and strength `10` corresponds to 10 flickers per second (minimum 10 flickers per cue). The duration of each flicker is 15ms to 45ms.
    - **Jumping Strength**: Dictates displacement distance and jump frequency. Strength `1` corresponds to 1 jump per second (min 1 per cue), and strength `10`
      corresponds to 10 jumps per second (min 10 per cue). The position jumps randomly in all directions, alternating signs to cross the original position on every jump.
      The final displacement is randomly chosen between a minimum offset (1/3 of max
      possible displacement) and maximum (15% of the font size at strength 1, 40% of the font size at strength 10).
      To ensure readability, each position is held for a minimum of 150ms.
    - **Moving Strength**: Similar to jumping, but moves the subtitle continuously between positions without stationary pauses, using smooth cubic ease-in-out transitions. Strength
      `1` corresponds to 1 move per second (min 1 per cue) and `10` corresponds to 10 moves
      per second (min 10 per cue). Alternates signs to cross the origin. Displacement is bound to 15%–40% of font size.
    - **Tilt Strength**: Smoothly rotates/inclines the subtitle back and forth continuously without stationary pauses using cubic ease-in-out transitions. Strength `1`
      corresponds to 1 tilt per second (min 1 per cue) and `10` corresponds to 10 tilts per second (min 10 per cue). The rotation alternates signs to cross the original
      upright position (0 deg). Maximum tilt angle ranges from 4.2 degrees (at strength 1) to 15.0 degrees (at strength 10), with a minimum offset of 1/3 of the max angle.
- **Dry Run Support**: Use `--dry-run` to see the calculated subtitle plan and positions in the log without rendering the video.
- **Dynamic Sizing & Line Spacing**: Subtitles are automatically wrapped to fit within 90% of the
  video width using a dynamic font width check. Multi-line subtitles use a tight default line height (max 125%).
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

00:00.500 --> 00:02.000 align:left line:top stfx:fadein:100:8 stfx:fadeout:100:6
<b>SNAKEVISE</b> - THE VIBE

00:02.500 --> 00:05.000 align:center line:middle stfx:slidein:100:left-0.2 stfx:fadeout:100:5
<i>Procedural Video Generator</i>

00:06.000 --> 00:08.000 align:right line:bottom stfx:slidein:100:top-0.15 stfx:slideout:100:right-0.2
Created with <u>Gemini CLI</u>
```

To render with these subtitles and custom global defaults:

```bash
python snakevise.py --input my_video.mp4 --subtitles lyrics.vtt --stfx fadein:100:8 --stfx slideout:50:8
```

---

## 🎨 Effects Encyclopedia

| Effect | Description |
| :--- | :--- |
| `zoomin` | Smooth procedural zoom into the center of the frame. |
| `zoomout` | Smooth procedural zoom out from the center. |
| `autofix` | Automatically corrects light, contrast, and color balance by analyzing the segment. |
| `blur` | Progressive Gaussian blur that increases from the midpoint to the end of the snippet. |
| `sharpen` | Starts blurry and clears up by the midpoint (the inverse of the blur effect). |
| `colorboost` | Enhances colors; boosts vibrance (low-sat colors) at weights 1-5, adds global saturation at 6-10. |
| `invert` | Gradually inverts the colors (10% at weight 1, 100% at weight 10). |
| `glitchchroma` | Random RGB channel shifting for a chromatic aberration look. |
| `glitchmotion` | Slices the snippet into tiny chunks and shuffles them temporally. |
| `mirror` | Horizontal, vertical, or quad mirroring. |
| `grain` | Adds procedural film grain/noise. |
| `speed` | Procedural speed ramping within the snippet. |
| `posterize` | Reduces the number of colors for a retro/artistic look. |
| `reverse` | Plays a portion or the entirety of the snippet backwards. |
| `stopmotion` | Lowers the effective framerate for a jerky, rhythmic feel. |
| `pixelize` | Low-res pixel art effect with dynamic scaling. |
| `oldmovie` | Adds vignette, tinting, and flicker for a vintage look. |
| `colorshift` | Dynamic HSV hue rotation. |
| `grayscale` | Desaturates the video (10% at strength 1, 100% at strength 10). |
| `contrast` | Increases video contrast (10% increase per weight, monotone at strength 10). |
| `shutterecho` | Ghosting effect by blending current frames with previous ones. |
| `tvscreen` | Simulated CRT scanlines, static, and signal interference. |
| `newspaper` | Halftone dot pattern reminiscent of print media. |
| `terminal` | Green-on-black monochromatic CRT terminal look. |
| `dataglitch` | Random block-based compression artifacts and inversions. |
| `asciiart` | Real-time conversion of video frames to colored ASCII text. |
| `tiles` | Divide video frame into a grid of crop-to-fit tiles with random play directions (forward/backward). |

---

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0.
