# Video Frame Extractor

Desktop app for extracting image frames from local video files with Python, Tkinter, and ffmpeg.

The app is designed for quick offline batch extraction: choose one or more videos, select the sampling rate and output format, then export numbered frame images into per-video folders or a shared output folder.

## Features

- GUI built with Python's standard `tkinter` library.
- Batch-select multiple videos.
- Extract frames using ffmpeg at a configurable frames-per-second rate.
- Save frames as `png`, `jpg`, or `jpeg`.
- Configure filename padding, for example `sample_001.png` or `sample_0001.jpg`.
- Optional start and end timestamps for partial extraction.
- Optional shared output folder.
- Background extraction thread so the GUI stays responsive.
- Input validation and user-friendly error messages.
- Small CLI entry point in `video_frame_extractor.py` for automation/testing.

## Requirements

- Python 3.10 or newer.
- ffmpeg installed and available on your system `PATH`.

ffmpeg is **not bundled** in this repository. Earlier versions expected `bin/ffmpeg.exe`, but the current app detects the `ffmpeg` command from your `PATH`. This keeps the repo lightweight and works across Windows, macOS, and Linux.

Install ffmpeg:

```bash
# Windows with winget
winget install Gyan.FFmpeg

# macOS with Homebrew
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install ffmpeg
```

Verify ffmpeg is available:

```bash
ffmpeg -version
```

## Quick Start

```bash
git clone https://github.com/sandeepkarmacharya/video-frame-extractor.git
cd video-frame-extractor
python video-frame-extractor.py
```

No Python package dependencies are required for the GUI.

## Usage

1. Run the app:

   ```bash
   python video-frame-extractor.py
   ```

2. Click **Load Videos** and select one or more video files.
3. Set extraction options:
   - **Frames/sec**: number of frames to extract per second.
   - **Image format**: `png`, `jpg`, or `jpeg`.
   - **Filename digits**: zero-padding width for output numbers.
   - **Start time / End time**: optional ffmpeg timestamps such as `00:00:03`.
   - **Output Folder**: optional shared output directory.
4. Click **Start Extraction**.

Default output behavior:

```text
input:  /videos/sample.mp4
output: /videos/sample/sample_001.png
        /videos/sample/sample_002.png
        ...
```

If a shared output folder is selected, all extracted frames are written there using each video's filename prefix.

## CLI Usage

The importable module also provides a small CLI for automation:

```bash
python -m video_frame_extractor sample.mp4 --fps 2 --format jpg --digits 4
python -m video_frame_extractor sample.mp4 --start 00:00:05 --end 00:00:10
python -m video_frame_extractor sample.mp4 --output-dir ./frames
```

## Development

Install test tooling:

```bash
python -m pip install -e .[dev]
```

Run tests:

```bash
python -m pytest -q
```

Run style checks:

```bash
python -m ruff check .
```

Project layout:

```text
video-frame-extractor.py   # compatibility GUI launcher
video_frame_extractor.py   # app, extraction helpers, CLI
README.md                  # user/developer docs
tests/                     # behavior and README contract tests
.github/workflows/ci.yml   # CI test workflow
```

## Roadmap

- Add progress percentage by parsing ffmpeg output.
- Add cancel support for running ffmpeg processes.
- Add preview thumbnails for extracted frames.
- Add PyInstaller packaging for Windows/macOS/Linux releases.
- Add drag-and-drop video loading.
- Add output filename template customization.

## Troubleshooting

### `ffmpeg not found`

Install ffmpeg and confirm `ffmpeg -version` works in the same terminal environment used to launch the app.

### GUI opens but extraction fails

Check that the input video exists, the output folder is writable, and the chosen timestamps are valid for the video.

### JPG output quality

For archival or analysis workflows, prefer `png`. JPG is smaller but lossy.

## License

No license file is currently included. Add one before distributing packaged releases.
