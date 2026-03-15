from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RenderConfig:
    """Holds all configurations for the rendering process.

    Attributes:
        output_path: Final output file path.
        temp_dir: Directory for temporary snippets.
        resolution: Output video dimensions (width, height).
        fps: Frames per second.
        codec: Video codec to use.
        optimize: Whether to use optimized encoding (CRF).
        audio_path: Optional path to master audio file.
        target_duration: Final duration in seconds.
        fade_in: Fade-in duration in seconds.
        fade_out: Fade-out duration in seconds.
        fade_color: Hex color for fades.
        dry_run: If True, only plan the timeline without rendering.
        bpm: Beats per minute.
    """

    output_path: Path
    temp_dir: Path
    resolution: Tuple[int, int]
    fps: int
    codec: str
    optimize: bool
    audio_path: Optional[Path]
    target_duration: Optional[float]
    fade_in: float  # in Seconds
    fade_out: float  # in Seconds
    fade_color: str
    dry_run: bool
    bpm: float


@dataclass
class Snippet:
    """Represents a processed video/image snippet.

    Attributes:
        index: Sequential index.
        source_path: Path to the source media.
        start_time: Start timestamp in source.
        duration: Duration of the snippet.
        is_image: Whether the source is an image.
        effects: List of planned effects.
        temp_file: Path to the rendered temporary file.
    """

    index: int
    source_path: Path
    start_time: float
    duration: float
    is_image: bool
    vfx: List[Dict[str, Any]]
    temp_file: Optional[Path] = None


@dataclass
class Segment:
    """A pre-calculated slice of a media source.

    Attributes:
        source_index: Index of the source in the planner's list.
        start: Start timestamp.
        duration: Duration of the slice.
    """

    source_index: int
    start: float
    duration: float
