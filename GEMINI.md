# vidseqpy Context

## Project Goals
- Provide a robust Python script for video sequence processing.
- Maintain high performance and readability.
- Follow Python best practices (PEP 8, modern packaging).

## Tech Stack
- **Language**: Python 3.8+
- **Core Libraries**: 
  - `opencv-python` (cv2): Image and video processing.
  - `numpy`: Numerical operations on frame data.
  - `tqdm`: Progress bars for long-running operations.
  - `moviepy`: High-level video editing (optional but included in dependencies).

## Coding Standards
- Use type hints wherever possible.
- Documentation should follow Google or NumPy style.
- Use `argparse` for CLI interactions.
- Ensure all resources (file handles, video captures) are properly closed using `try...finally` or context managers.

## Development Workflow
- All new features should be implemented in separate modules in the `src/` directory.
- `vidseq.py` acts as the entry point.
- Use `pytest` for testing (to be added).
- Format code using `black` or `ruff`.

## Important Notes
- Video processing is CPU/GPU intensive. Be mindful of memory usage when handling large sequences.
- OpenCV's `VideoCapture` and `VideoWriter` are sensitive to codec availability on the host system.
