import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from moviepy.editor import VideoFileClip

from .effects import EffectEngine
from .models import Segment, Snippet
from .utils import parse_int_range_string

logger = logging.getLogger("vidseq")


class MediaSource:
    """Represents a media file that can be sliced into snippets."""

    def __init__(
        self,
        path: Path,
        start: float,
        end: float,
        bpm: float,
        min_b: int,
        max_b: int,
        index: int,
    ):
        """Initializes the media source.

        Args:
            path: Path to the media file.
            start: Start limit in seconds.
            end: End limit in seconds (0 for full duration).
            bpm: BPM for rhythmic calculations.
            min_b: Minimum beats per snippet.
            max_b: Maximum beats per snippet.
            index: Source index.
        """
        self.path = path
        self.index = index
        self.start_limit = start
        self.end_limit = end
        self.bpm = bpm
        self.min_beats = min_b
        self.max_beats = max_b

        if not self.path.exists():
            logger.error(f"Media source path does not exist: {self.path}")
            self.exhausted = True
            return

        self.is_image = path.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
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
        """Pre-calculates all possible segments from this source.

        Returns:
            List of Segment objects.
        """
        if self.is_image or self.exhausted:
            return []
        segments = []
        cursor = self.start_limit
        while True:
            beats = random.randint(self.min_beats, self.max_beats)
            duration = beats * self.beat_duration
            if cursor + duration > self.end_limit:
                break
            segments.append(Segment(self.index, cursor, duration))
            cursor += duration
        return segments

    def get_next_linear(
        self, requested_duration: float, global_offset: float
    ) -> Tuple[float, float]:
        """Gets the next linear slice from the source.

        Args:
            requested_duration: Target duration.
            global_offset: Current progress offset.

        Returns:
            A tuple (start_time, actual_duration).
        """
        if self.exhausted:
            return 0.0, 0.0
        if self.is_image:
            return 0.0, requested_duration
        current_pos = self.start_limit + global_offset
        remaining = self.end_limit - current_pos
        min_seconds = self.min_beats * self.beat_duration
        if remaining < min_seconds:
            self.exhausted = True
            return 0.0, 0.0
        actual_dur = min(requested_duration, remaining)
        return current_pos, actual_dur

    def get_snippet_duration(self) -> float:
        """Calculates a random rhythmic duration based on beat constraints.

        Returns:
            Duration in seconds.
        """
        beats = random.randint(self.min_beats, self.max_beats)
        return beats * self.beat_duration


class TimelinePlanner:
    """Plans the sequence of snippets (EDL) based on selected modes."""

    def __init__(
        self,
        sources: List[MediaSource],
        mode: str,
        vfx_configs: List[Dict[str, Any]],
        vfx_maximum: Optional[int],
        vfx_order: str,
    ):
        """Initializes the planner.

        Args:
            sources: Available media sources.
            mode: Sequencing mode (e.g., 'linear', 'random').
            vfx_configs: Configurations for effects.
            vfx_maximum: Max effects per snippet.
            vfx_order: 'linear' or 'random' effect application order.
        """
        self.sources = sources
        self.mode = mode
        self.vfx_configs = vfx_configs
        self.global_time = 0.0
        self.vfx_maximum = vfx_maximum
        self.vfx_order = vfx_order
        self.edl: List[Snippet] = []
        if "-" in mode:
            self.source_mode, self.snippet_mode = mode.split("-")
        else:
            self.source_mode = mode
            self.snippet_mode = mode

    def _is_sequential(self, segment: Segment) -> bool:
        if not self.edl:
            return False
        last_snip = self.edl[-1]
        if last_snip.source_path != self.sources[segment.source_index].path:
            return False
        return abs((last_snip.start_time + last_snip.duration) - segment.start) < 0.1

    def create_edl(self, target_duration: Optional[float]) -> List[Snippet]:
        """Creates the Edit Decision List (EDL).

        Args:
            target_duration: Target total duration in seconds.

        Returns:
            List of Snippets.
        """
        # --- PREPARE POOLS ---
        global_pool: List[Segment] = []
        source_pools: Dict[int, List[Segment]] = {}

        if self.source_mode == "random" and self.snippet_mode == "random":
            for s in self.sources:
                global_pool.extend(s.pre_slice())
            random.shuffle(global_pool)

        elif self.source_mode == "linear" and self.snippet_mode == "random":
            for s in self.sources:
                pool = s.pre_slice()
                random.shuffle(pool)
                source_pools[s.index] = pool

        pool_cursor = 0
        rr_source_index = 0
        source_offsets = {s.index: 0.0 for s in self.sources}

        while True:
            if target_duration and self.global_time >= target_duration:
                break
            segment = None
            source_obj = None

            if self.source_mode == "random" and self.snippet_mode == "random":
                if pool_cursor >= len(global_pool):
                    logger.warning("All video material exhausted (Random Pool empty). Stopping.")
                    break

                candidate = global_pool[pool_cursor]

                if self._is_sequential(candidate):
                    for swap_idx in range(pool_cursor + 1, len(global_pool)):
                        if not self._is_sequential(global_pool[swap_idx]):
                            global_pool[pool_cursor], global_pool[swap_idx] = (
                                global_pool[swap_idx],
                                global_pool[pool_cursor],
                            )
                            break

                segment = global_pool[pool_cursor]
                pool_cursor += 1
                source_obj = next(s for s in self.sources if s.index == segment.source_index)

            elif self.source_mode == "linear" and self.snippet_mode == "random":
                found_src = False
                for _ in range(len(self.sources)):
                    potential_idx = rr_source_index % len(self.sources)
                    s_idx = self.sources[potential_idx].index

                    if source_pools[s_idx]:
                        source_obj = self.sources[potential_idx]
                        candidate = source_pools[s_idx][0]
                        if self._is_sequential(candidate):
                            for swap_idx in range(1, len(source_pools[s_idx])):
                                if not self._is_sequential(source_pools[s_idx][swap_idx]):
                                    source_pools[s_idx][0], source_pools[s_idx][swap_idx] = (
                                        source_pools[s_idx][swap_idx],
                                        source_pools[s_idx][0],
                                    )
                                    break

                        segment = source_pools[s_idx].pop(0)
                        found_src = True
                        rr_source_index = (potential_idx + 1) % len(self.sources)
                        break
                    rr_source_index = (rr_source_index + 1) % len(self.sources)

                if not found_src:
                    break

            else:
                if self.source_mode == "random":
                    valid_sources = [s for s in self.sources if not s.exhausted]
                    if not valid_sources:
                        break
                    source_obj = random.choice(valid_sources)
                else:
                    found_src = False
                    for _ in range(len(self.sources)):
                        potential_idx = rr_source_index % len(self.sources)
                        if not self.sources[potential_idx].exhausted:
                            source_obj = self.sources[potential_idx]
                            found_src = True
                            rr_source_index = (potential_idx + 1) % len(self.sources)
                            break
                        rr_source_index = (rr_source_index + 1) % len(self.sources)

                    if not found_src:
                        break

                dur = source_obj.get_snippet_duration()
                start, real_dur = source_obj.get_next_linear(
                    dur, source_offsets[source_obj.index]
                )

                if real_dur > 0:
                    segment = Segment(source_obj.index, start, real_dur)
                    source_offsets[source_obj.index] += real_dur
                else:
                    source_obj.exhausted = True
                    continue

            if segment:
                vfx_plan = EffectEngine.select_effects(
                    self.vfx_configs, self.vfx_maximum, self.vfx_order
                )
                snippet = Snippet(
                    index=len(self.edl) + 1,
                    source_path=source_obj.path,
                    start_time=segment.start,
                    duration=segment.duration,
                    is_image=source_obj.is_image,
                    vfx=vfx_plan,
                )
                self.edl.append(snippet)
                self.global_time += segment.duration

        return self.edl
