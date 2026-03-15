import argparse
import logging
import sys
from typing import Any, Dict, List, Optional, Tuple, Union


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
