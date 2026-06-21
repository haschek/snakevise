from pathlib import Path
from unittest.mock import patch, MagicMock
from src.planner import MediaSource


@patch("src.planner.VideoFileClip")
def test_media_source_pre_slice_video(mock_video):
    # Mock video duration
    mock_clip = MagicMock()
    mock_clip.duration = 10.0
    mock_video.return_value.__enter__.return_value = mock_clip

    # 120 BPM -> 0.5s beat duration
    # min_beats=4 (2s), max_beats=8 (4s)
    with patch.object(Path, "exists", return_value=True):
        source = MediaSource(
            path=Path("video.mp4"),
            start=0.0,
            end=10.0,
            bpm=120.0,
            min_b=4,
            max_b=8,
            index=0,
        )

        with patch("random.randint", return_value=4):
            # We enforce exactly 4 beats per segment (2.0s)
            # Video duration is 10s. Pre-slice should yield 5 segments of 2s.
            segments = source.pre_slice()
            assert len(segments) == 5
            for idx, seg in enumerate(segments):
                assert seg.source_index == 0
                assert seg.start == idx * 2.0
                assert seg.duration == 2.0


def test_media_source_pre_slice_image():
    # 120 BPM -> 0.5s beat duration
    # min_beats=4 (2s), max_beats=8 (4s)
    # Virtual length = max_beats * beat_duration = 8 * 0.5 = 4.0s
    with patch.object(Path, "exists", return_value=True):
        source = MediaSource(
            path=Path("image.jpg"),
            start=0.0,
            end=0.0,
            bpm=120.0,
            min_b=4,
            max_b=8,
            index=0,
        )

        # Case 1: First random slice is 4 beats (2s), second is 4 beats (2s)
        # Total virtual duration is 4.0s. This fits exactly 2 segments.
        with patch("random.randint", side_effect=[4, 4, 4]):
            segments = source.pre_slice()
            assert len(segments) == 2
            assert segments[0].start == 0.0
            assert segments[0].duration == 2.0
            assert segments[1].start == 0.0
            assert segments[1].duration == 2.0

        # Case 2: First random slice is 8 beats (4s)
        # Total virtual duration is 4.0s. This fits exactly 1 segment.
        with patch("random.randint", side_effect=[8, 8]):
            segments = source.pre_slice()
            assert len(segments) == 1
            assert segments[0].start == 0.0
            assert segments[0].duration == 4.0
