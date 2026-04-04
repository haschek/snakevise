from pathlib import Path
from src.utils import unescape_path, resolve_path, relativize_path


def test_unescape_path():
    assert unescape_path("file\\ name.mp4") == "file name.mp4"
    assert unescape_path("path/with\\ spaces/file.mp4") == "path/with spaces/file.mp4"
    assert unescape_path("brackets\\[\\]\\{\\}.mp4") == "brackets[]{}.mp4"


def test_resolve_path_absolute():
    abs_path = "/tmp/test.mp4"
    resolved = resolve_path(abs_path)
    assert str(resolved) == abs_path


def test_resolve_path_home():
    home_path = "~/test.mp4"
    expected = Path.home() / "test.mp4"
    resolved = resolve_path(home_path)
    assert resolved == expected


def test_resolve_path_relative_with_base():
    base = Path("/tmp/project")
    rel = "data/video.mp4"
    expected = Path("/tmp/project/data/video.mp4")
    resolved = resolve_path(rel, base)
    assert resolved == expected


def test_relativize_path_simple():
    base = Path("/tmp/project")
    target = "/tmp/project/data/video.mp4"
    # Note: os.path.relpath returns 'data/video.mp4'
    rel = relativize_path(target, base)
    assert rel == "data/video.mp4"


def test_relativize_path_with_escapes():
    base = Path("/tmp/project")
    # Simulate a path that was input with escapes
    target = "/tmp/project/folder\\ with\\ space/video.mp4"
    rel = relativize_path(target, base)
    assert rel == "folder with space/video.mp4"


def test_relativize_path_no_long_chains():
    # If the file is in the same directory but we use a weird path
    base = Path("/tmp/project/sub")
    target = "/tmp/project/sub/video.mp4"
    rel = relativize_path(target, base)
    assert rel == "video.mp4"
