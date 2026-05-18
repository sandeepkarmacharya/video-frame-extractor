from pathlib import Path


def test_readme_explains_installation_usage_and_limitations():
    text = Path("README.md").read_text(encoding="utf-8")

    required_sections = [
        "## Features",
        "## Requirements",
        "## Quick Start",
        "## Usage",
        "## Development",
        "## Roadmap",
    ]
    for section in required_sections:
        assert section in text

    assert "ffmpeg" in text.lower()
    assert "python" in text.lower()
    assert "video-frame-extractor.py" in text


def test_readme_mentions_no_bundled_ffmpeg_binary():
    text = Path("README.md").read_text(encoding="utf-8").lower()

    assert "ffmpeg" in text
    assert "path" in text
    assert "bundled" in text or "not included" in text
