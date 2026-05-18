
import pytest

from video_frame_extractor import (
    ExtractionOptions,
    build_ffmpeg_command,
    find_ffmpeg,
    validate_inputs,
)


def test_find_ffmpeg_prefers_executable_on_path(tmp_path, monkeypatch):
    fake = tmp_path / "ffmpeg"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    assert find_ffmpeg() == fake


def test_validate_inputs_rejects_missing_files():
    options = ExtractionOptions(fps=1, image_format="png", digits=3)

    with pytest.raises(ValueError, match="select at least one video"):
        validate_inputs([], options)


def test_validate_inputs_rejects_invalid_fps(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"placeholder")
    options = ExtractionOptions(fps=0, image_format="png", digits=3)

    with pytest.raises(ValueError, match="FPS must be greater than 0"):
        validate_inputs([video], options)


def test_build_ffmpeg_command_creates_numbered_output_pattern(tmp_path):
    ffmpeg = tmp_path / "ffmpeg"
    video = tmp_path / "sample.mp4"
    output_dir = tmp_path / "frames"
    options = ExtractionOptions(fps=5, image_format="jpg", digits=4, output_dir=output_dir)

    command = build_ffmpeg_command(ffmpeg, video, options)

    assert command == [
        str(ffmpeg),
        "-y",
        "-i",
        str(video),
        "-r",
        "5",
        str(output_dir / "sample_%04d.jpg"),
    ]


def test_build_ffmpeg_command_supports_start_and_end_times(tmp_path):
    ffmpeg = tmp_path / "ffmpeg"
    video = tmp_path / "sample.mp4"
    options = ExtractionOptions(
        fps=2,
        image_format="png",
        digits=3,
        start_time="00:00:03",
        end_time="00:00:07",
    )

    command = build_ffmpeg_command(ffmpeg, video, options)

    assert command[:4] == [str(ffmpeg), "-y", "-ss", "00:00:03"]
    assert "-to" in command
    assert command[command.index("-to") + 1] == "00:00:07"
    assert command[-1].endswith("sample/sample_%03d.png")
