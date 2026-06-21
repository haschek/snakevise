from unittest.mock import MagicMock, patch
from pathlib import Path
import numpy as np
from src.renderer import Renderer
from src.models import RenderConfig, Snippet


@patch("src.renderer.Image")
@patch("src.renderer.ImageOps")
@patch("src.renderer.ImageClip")
@patch("src.renderer.reframe")
@patch("src.renderer.EffectEngine")
def test_image_orientation_transpose(
    mock_effect_engine, mock_reframe, mock_image_clip, mock_image_ops, mock_image
):
    # Setup mock config
    config = RenderConfig(
        output_path=Path("/tmp/fake_out.mp4"),
        temp_dir=Path("/tmp/fake_temp"),
        crop=["crop-to-fit"],
        resolution=(1920, 1080),
        fps=24,
        codec="libx264",
        optimize=False,
        audio_path=None,
        subtitles_path=None,
        subtitle_fonts=[],
        subtitle_fontsizes=[],
        subtitle_strokewidths=[],
        subtitle_colors=[],
        subtitle_stroke_colors=[],
        target_duration=None,
        fade_in=0.0,
        fade_out=0.0,
        fade_color="#000000",
        dry_run=False,
        bpm=120.0,
    )

    # Setup snippet
    snippet = Snippet(
        index=0,
        source_path=Path("/tmp/fake_image.jpg"),
        duration=5.0,
        start_time=0.0,
        vfx=[],
        crop="crop-to-fit",
        is_image=True,
    )

    # Mock Path.exists to return True
    with patch.object(Path, "exists", return_value=True):
        # Mock PIL image
        mock_pil_img = MagicMock()
        mock_pil_img.mode = "RGB"
        mock_image.open.return_value.__enter__.return_value = mock_pil_img

        # Mock transposed image
        mock_transposed_pil = MagicMock()
        mock_transposed_pil.mode = "RGB"

        # To handle np.array(mock_transposed_pil), we mock __array__ or return a numpy array
        fake_array = np.zeros((600, 800, 3), dtype=np.uint8)
        mock_transposed_pil.__array__ = MagicMock(return_value=fake_array)
        mock_image_ops.exif_transpose.return_value = mock_transposed_pil

        # Mock clip setup
        mock_clip = MagicMock()
        mock_image_clip.return_value = mock_clip
        mock_clip.set_duration.return_value = mock_clip

        # Mock reframe & effects
        mock_reframe.return_value = mock_clip
        mock_effect_engine.apply.return_value = mock_clip

        # Instantiate renderer and process
        renderer = Renderer(config)
        renderer._process_snippet(snippet)

        # Assert PIL open was called with snippet's path
        mock_image.open.assert_called_once_with(snippet.source_path)

        # Assert exif_transpose was called with the PIL image
        mock_image_ops.exif_transpose.assert_called_once_with(mock_pil_img)

        # Assert ImageClip was initialized with the numpy array from the transposed image
        called_arg = mock_image_clip.call_args[0][0]
        assert isinstance(called_arg, np.ndarray)
        assert called_arg.shape == (600, 800, 3)
