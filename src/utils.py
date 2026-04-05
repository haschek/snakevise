import argparse
import logging
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


def get_compatible_fonts() -> List[str]:
    """Returns a list of base font names that have both Bold and Italic variants.
    Prioritizes common, high-quality fonts.
    """
    try:
        from moviepy.editor import TextClip

        fonts = TextClip.list("font")
        if not fonts:
            return []

        grouped = defaultdict(list)
        for font in sorted(fonts):
            # Cleanup common font naming conventions to get the base
            base = font.split("-")[0].split("_")[0].split(" ")[0]
            grouped[base].append(font)

        compatible = []
        for base in grouped.keys():
            variants = grouped[base]
            has_bold = any("bold" in v.lower() for v in variants)
            has_italic = any("italic" in v.lower() for v in variants)
            if has_bold and has_italic:
                compatible.append(base)

        if not compatible:
            return []

        # Prioritization list (descending order of preference)
        preferred = [
            "Arial",
            "Liberation-Sans",
            "DejaVu-Sans",
            "Helvetica",
            "Sans",
            "Verdana",
            "Tahoma",
        ]

        # Sort the compatible list: Preferred first, then alphabetical
        def sort_key(font_name):
            try:
                # Find the index in preferred list, lower is better.
                # If not found, use a high index.
                idx = -1
                for i, p in enumerate(preferred):
                    if p.lower() in font_name.lower():
                        idx = i
                        break

                if idx != -1:
                    return (0, idx, font_name.lower())
                return (1, 0, font_name.lower())
            except Exception:
                return (2, 0, font_name.lower())

        return sorted(compatible, key=sort_key)
    except Exception:
        return []


def check_font_renderable(font_name: str) -> bool:
    """Tests if a font is actually renderable by MoviePy/ImageMagick.

    Args:
        font_name: The name of the font to test.

    Returns:
        True if rendering succeeded, False otherwise.
    """
    try:
        from moviepy.editor import TextClip

        # Attempt to create a tiny temporary clip
        txt = TextClip("test", font=font_name, fontsize=10)
        txt.close()
        return True
    except Exception:
        return False


def expand_random_colors(color_str: str) -> List[str]:
    """Expands a color string or RANDOM:n into a list of hex color strings.

    Args:
        color_str: The color (e.g., "white", "#FF0000") or "RANDOM:n".

    Returns:
        A list of color strings.
    """
    import random

    if not color_str.upper().startswith("RANDOM:"):
        return [color_str]

    try:
        parts = color_str.split(":")
        count = int(parts[1]) if len(parts) > 1 else 1
    except (ValueError, IndexError):
        count = 1

    colors = []
    for _ in range(count):
        # Generate random hex color
        c = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        colors.append(c)
    return colors


def expand_random_fonts(font_str: str) -> List[str]:
    """Expands a font name or RANDOM:n string into a list of font names.

    Args:
        font_str: The font name or "RANDOM:n".

    Returns:
        A list of font names.
    """
    import random

    if not font_str.upper().startswith("RANDOM:"):
        return [font_str]

    try:
        parts = font_str.split(":")
        random_limit = int(parts[1]) if len(parts) > 1 else 1
    except (ValueError, IndexError):
        random_limit = 1

    from .utils import get_compatible_fonts

    compatible = get_compatible_fonts()
    if not compatible:
        return []

    n = min(random_limit, len(compatible))
    return random.sample(compatible, n)


def expand_random_numeric_range(
    val_str: str, default_count: int = 1, precision: int = 1
) -> List[float]:
    """Expands a RANDOM:min..max:count string into a list of random floats.
    Divides the range into 'count' equal sub-ranges and picks one value from each
     to ensure even distribution.

    Args:
        val_str: The string to expand (e.g., "RANDOM:10..20:5").
        default_count: Default number of values if not specified.
        precision: Number of decimal places.

    Returns:
        A list of random floats.
    """
    import random

    if not val_str.upper().startswith("RANDOM:"):
        try:
            return [float(val_str)]
        except ValueError:
            return []

    parts = val_str.split(":")
    if len(parts) < 2:
        return []

    r_range = parts[1]
    r_count = int(parts[2]) if len(parts) > 2 else default_count
    if r_count <= 0:
        return []

    low, high = parse_range_string(r_range)
    if low > high:
        low, high = high, low

    if r_count == 1:
        return [round(random.uniform(low, high), precision)]

    # Divide range into r_count micro-ranges
    results = []
    step = (high - low) / r_count
    for i in range(r_count):
        m_low = low + (i * step)
        m_high = m_low + step
        val = random.uniform(m_low, m_high)
        results.append(round(val, precision))

    # Shuffle results so they are not always ascending
    random.shuffle(results)
    return results


def unescape_path(path_str: str) -> str:
    """Removes common shell escapes from a path string."""
    for char in [" ", "(", ")", "[", "]", "{", "}", "&", "!", "'", '"', "*", "?", "$"]:
        path_str = path_str.replace(f"\\{char}", char)
    return path_str


def resolve_path(path_str: str, base_dir: Optional[Path] = None) -> Path:
    """Resolves a path string.

    Handles:
    1. Home path (~)
    2. Absolute path
    3. Relative path (relative to base_dir if provided, else CWD)

    Args:
        path_str: The path string to resolve.
        base_dir: Optional base directory for relative paths.

    Returns:
        The resolved Path object.
    """
    path = Path(path_str)

    # 1. Home path expansion
    if path_str.startswith("~"):
        return path.expanduser()

    # 2. Absolute path
    if path.is_absolute():
        return path

    # 3. Relative path
    if base_dir:
        return (base_dir / path).resolve()

    return path.resolve()


def parse_sub_settings(settings: str) -> Tuple[str, str]:
    """Parses WebVTT settings into simple keywords.
    Supports spaces and various VTT naming conventions.
    """
    s = str(settings).lower()
    h_align = "center"
    v_align = "bottom"

    # Horizontal Alignment
    if re.search(r"align\s*:\s*(left|start)", s):
        h_align = "left"
    elif re.search(r"align\s*:\s*(right|end)", s):
        h_align = "right"
    elif re.search(r"align\s*:\s*(center|middle)", s):
        h_align = "center"

    # Vertical Position
    if re.search(r"line\s*:\s*(top|0)", s):
        v_align = "top"
    elif re.search(r"line\s*:\s*middle", s):
        v_align = "center"
    elif re.search(r"line\s*:\s*bottom", s):
        v_align = "bottom"

    return h_align, v_align


def relativize_path(path_str: str, base_dir: Path) -> str:
    """Converts a path to be strictly relative to the base_dir.

    Args:
        path_str: The path to convert.
        base_dir: The directory to make it relative to.

    Returns:
        A string representation of the relative path.
    """
    try:
        # 1. Resolve to absolute path (handling escapes and ~)
        path_str = unescape_path(path_str)
        p = Path(path_str)
        if path_str.startswith("~"):
            abs_path = p.expanduser().resolve()
        else:
            abs_path = p.resolve()

        abs_base = base_dir.resolve()

        # 2. Get relative path from base_dir
        return os.path.relpath(abs_path, abs_base)
    except Exception:
        return path_str


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Sets up logging for the script.

    Args:
        log_file: Optional path to a log file.

    Returns:
        The configured logger instance.
    """
    logger_instance = logging.getLogger("snakevise")
    logger_instance.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S"
    )

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger_instance.addHandler(ch)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger_instance.addHandler(fh)

    return logger_instance


def hex_to_rgb(hex_str: str) -> List[int]:
    """Converts a hex color string to an RGB list.

    Args:
        hex_str: Hex color string (e.g., "#FF0000").

    Returns:
        List of three integers [R, G, B].
    """
    hex_str = hex_str.lstrip("#")
    return [int(hex_str[i : i + 2], 16) for i in (0, 2, 4)]


def parse_resolution(res_str: str) -> Tuple[Tuple[int, int], int]:
    """Parses a resolution string in the format WIDTHxHEIGHT:FPS.

    Args:
        res_str: The resolution string.

    Returns:
        A tuple containing ((width, height), fps).

    Raises:
        argparse.ArgumentTypeError: If the format is invalid.
    """
    try:
        size, fps = res_str.split(":")
        w, h = map(int, size.lower().split("x"))
        return (w, h), int(fps)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            "Format must be WIDTHxHEIGHT:FRAMERATE (e.g., 1920x1080:24)"
        ) from e


def parse_range_string(val: Union[str, float, int]) -> Tuple[float, float]:
    """Parses a string representing a numeric range (e.g., "1..5").

    Args:
        val: The value to parse.

    Returns:
        A tuple (min, max).
    """
    s = str(val)
    if ".." in s:
        try:
            parts = s.split("..")
            return float(parts[0]), float(parts[1])
        except ValueError:
            return 5.0, 5.0
    try:
        f = float(s)
        return f, f
    except ValueError:
        return 5.0, 5.0


def parse_int_range_string(val: Union[str, int]) -> Tuple[int, int]:
    """Parses a string representing an integer range (e.g., "1..5").

    Args:
        val: The value to parse.

    Returns:
        A tuple (min, max) as integers.
    """
    s = str(val)
    if ".." in s:
        try:
            parts = s.split("..")
            return int(float(parts[0])), int(float(parts[1]))
        except ValueError:
            return 4, 4
    try:
        i = int(float(s))
        return i, i
    except ValueError:
        return 4, 4


def parse_effect_string(
    fx_str: str, default_chance: float, default_range: Tuple[float, float]
) -> Dict[str, Any]:
    """Parses an effect configuration string.

    Args:
        fx_str: Format NAME:CHANCE:STRENGTH (e.g., "glitch:50:1..5").
        default_chance: Default chance if not specified.
        default_range: Default strength range if not specified.

    Returns:
        A dictionary with effect configuration.
    """
    parts = fx_str.split(":")
    name = parts[0]
    chance = float(parts[1]) if len(parts) > 1 and parts[1] else default_chance

    if len(parts) > 2 and parts[2]:
        str_range = parse_range_string(parts[2])
    else:
        str_range = default_range

    return {"name": name, "chance": chance, "strength_range": str_range}
