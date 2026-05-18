"""Video frame extraction GUI and ffmpeg helpers."""

from __future__ import annotations

import argparse
import queue
import shutil
import subprocess
import threading
import tkinter as tk
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox

SUPPORTED_FORMATS = ("png", "jpg", "jpeg")
VIDEO_FILETYPES = (
    ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.m4v"),
    ("MP4", "*.mp4"),
    ("AVI", "*.avi"),
    ("MOV", "*.mov"),
    ("All files", "*.*"),
)


@dataclass(frozen=True)
class ExtractionOptions:
    """Options used to build and run ffmpeg frame extraction."""

    fps: int = 5
    image_format: str = "png"
    digits: int = 3
    output_dir: Path | None = None
    start_time: str | None = None
    end_time: str | None = None


def find_ffmpeg() -> Path | None:
    """Return the ffmpeg executable available on PATH, if any."""

    ffmpeg = shutil.which("ffmpeg")
    return Path(ffmpeg) if ffmpeg else None


def default_output_dir(video_path: Path) -> Path:
    """Return default output directory for a video."""

    return video_path.with_suffix("")


def validate_inputs(video_paths: Iterable[Path | str], options: ExtractionOptions) -> list[Path]:
    """Validate extraction inputs and return normalized paths.

    Raises:
        ValueError: if user options or files are invalid.
    """

    paths = [Path(path) for path in video_paths]
    if not paths:
        raise ValueError("Please select at least one video file.")

    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise ValueError("Video file not found: " + ", ".join(missing))

    if options.fps <= 0:
        raise ValueError("FPS must be greater than 0.")

    if options.digits <= 0:
        raise ValueError("Filename digits must be greater than 0.")

    image_format = options.image_format.lower()
    if image_format not in SUPPORTED_FORMATS:
        raise ValueError(
            "Output format must be one of: " + ", ".join(SUPPORTED_FORMATS)
        )

    return paths


def build_ffmpeg_command(
    ffmpeg_path: Path | str,
    video_path: Path | str,
    options: ExtractionOptions,
) -> list[str]:
    """Build the ffmpeg command for one video."""

    video = Path(video_path)
    output_dir = Path(options.output_dir) if options.output_dir else default_output_dir(video)
    extension = options.image_format.lower()
    pattern = output_dir / f"{video.stem}_%0{options.digits}d.{extension}"

    command = [str(ffmpeg_path), "-y"]
    if options.start_time:
        command.extend(["-ss", options.start_time])
    command.extend(["-i", str(video)])
    if options.end_time:
        command.extend(["-to", options.end_time])
    command.extend(["-r", str(options.fps), str(pattern)])
    return command


def extract_frames(
    video_paths: Iterable[Path | str],
    options: ExtractionOptions,
    ffmpeg_path: Path | str | None = None,
    progress: Callable[[str], None] | None = None,
) -> list[Path]:
    """Extract frames from videos and return output directories."""

    ffmpeg = Path(ffmpeg_path) if ffmpeg_path else find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg was not found. Install ffmpeg and make sure it is available on PATH."
        )

    videos = validate_inputs(video_paths, options)
    output_dirs: list[Path] = []

    for index, video in enumerate(videos, start=1):
        output_dir = Path(options.output_dir) if options.output_dir else default_output_dir(video)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dirs.append(output_dir)

        if progress:
            progress(f"Extracting {video.name} ({index}/{len(videos)})...")

        command = build_ffmpeg_command(ffmpeg, video, options)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            details = (result.stderr or result.stdout or "ffmpeg failed").strip()
            raise RuntimeError(f"Failed to extract frames from {video.name}: {details}")

    if progress:
        progress(f"Done. Extracted frames for {len(videos)} video(s).")
    return output_dirs


class VideoFrameExtractorApp:
    """Tkinter GUI for video frame extraction."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Video Frame Extractor")
        self.video_paths: list[Path] = []
        self.messages: queue.Queue[tuple[str, str]] = queue.Queue()
        self.worker: threading.Thread | None = None

        self.fps_var = tk.IntVar(value=5)
        self.format_var = tk.StringVar(value="png")
        self.digits_var = tk.IntVar(value=3)
        self.start_var = tk.StringVar(value="")
        self.end_var = tk.StringVar(value="")
        self.output_dir_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Select video files to begin.")

        self._build_ui()
        self.root.after(100, self._poll_messages)

    def _build_ui(self) -> None:
        loading_frame = tk.LabelFrame(self.root, text="Videos", padx=8, pady=8)
        loading_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.file_list = tk.Text(loading_frame, width=70, height=8, state="disabled")
        self.file_list.grid(row=0, column=0, columnspan=3, sticky="nsew")
        scroll_bar = tk.Scrollbar(loading_frame, orient="vertical", command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scroll_bar.set)
        scroll_bar.grid(row=0, column=3, sticky="ns")

        tk.Button(loading_frame, text="Load Videos", command=self.load_files).grid(
            row=1, column=0, padx=4, pady=6, sticky="ew"
        )
        tk.Button(loading_frame, text="Clear", command=self.clear).grid(
            row=1, column=1, padx=4, pady=6, sticky="ew"
        )
        tk.Button(loading_frame, text="Output Folder", command=self.choose_output_dir).grid(
            row=1, column=2, padx=4, pady=6, sticky="ew"
        )

        options_frame = tk.LabelFrame(self.root, text="Extraction options", padx=8, pady=8)
        options_frame.pack(fill="x", padx=8, pady=8)

        tk.Label(options_frame, text="Frames/sec").grid(row=0, column=0, padx=4, sticky="w")
        tk.Entry(options_frame, textvariable=self.fps_var, width=8).grid(row=1, column=0, padx=4)

        tk.Label(options_frame, text="Image format").grid(row=0, column=1, padx=4, sticky="w")
        tk.OptionMenu(options_frame, self.format_var, "png", "jpg", "jpeg").grid(
            row=1, column=1, padx=4, sticky="ew"
        )

        tk.Label(options_frame, text="Filename digits").grid(row=0, column=2, padx=4, sticky="w")
        tk.Spinbox(options_frame, from_=1, to=8, textvariable=self.digits_var, width=8).grid(
            row=1, column=2, padx=4
        )

        tk.Label(options_frame, text="Start time (optional)").grid(
            row=0, column=3, padx=4, sticky="w"
        )
        tk.Entry(options_frame, textvariable=self.start_var, width=14).grid(
            row=1, column=3, padx=4
        )

        tk.Label(options_frame, text="End time (optional)").grid(
            row=0, column=4, padx=4, sticky="w"
        )
        tk.Entry(options_frame, textvariable=self.end_var, width=14).grid(row=1, column=4, padx=4)

        output_frame = tk.Frame(self.root)
        output_frame.pack(fill="x", padx=8)
        tk.Label(output_frame, text="Output folder:").pack(side="left")
        tk.Label(output_frame, textvariable=self.output_dir_var, anchor="w").pack(
            side="left", fill="x", expand=True, padx=4
        )

        action_frame = tk.LabelFrame(self.root, text="Run", padx=8, pady=8)
        action_frame.pack(fill="x", padx=8, pady=8)
        self.start_button = tk.Button(action_frame, text="Start Extraction", command=self.start)
        self.start_button.pack(side="left", padx=4)
        tk.Label(action_frame, textvariable=self.status_var, anchor="w").pack(
            side="left", fill="x", expand=True, padx=8
        )

    def load_files(self) -> None:
        filenames = filedialog.askopenfilenames(
            title="Select video files", filetypes=VIDEO_FILETYPES
        )
        self.video_paths = [Path(name) for name in filenames]
        self._refresh_file_list()
        self.status_var.set(f"Loaded {len(self.video_paths)} video(s).")

    def choose_output_dir(self) -> None:
        dirname = filedialog.askdirectory(title="Select output folder")
        if dirname:
            self.output_dir_var.set(dirname)

    def clear(self) -> None:
        self.video_paths = []
        self._refresh_file_list()
        self.status_var.set("Selection cleared.")

    def start(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo(
                "Extraction running",
                "Please wait for the current extraction to finish.",
            )
            return

        try:
            options = self._options_from_ui()
            validate_inputs(self.video_paths, options)
        except (tk.TclError, ValueError) as exc:
            messagebox.showwarning("Invalid settings", str(exc))
            return

        if not find_ffmpeg():
            messagebox.showerror(
                "ffmpeg not found",
                "Install ffmpeg and make sure the ffmpeg command is available on PATH.",
            )
            return

        self.start_button.configure(state="disabled")
        self.status_var.set("Starting extraction...")
        self.worker = threading.Thread(
            target=self._run_extraction,
            args=(list(self.video_paths), options),
            daemon=True,
        )
        self.worker.start()

    def _options_from_ui(self) -> ExtractionOptions:
        output_dir_text = self.output_dir_var.get().strip()
        return ExtractionOptions(
            fps=int(self.fps_var.get()),
            image_format=self.format_var.get().lower(),
            digits=int(self.digits_var.get()),
            output_dir=Path(output_dir_text) if output_dir_text else None,
            start_time=self.start_var.get().strip() or None,
            end_time=self.end_var.get().strip() or None,
        )

    def _run_extraction(self, paths: list[Path], options: ExtractionOptions) -> None:
        try:
            extract_frames(
                paths,
                options,
                progress=lambda message: self.messages.put(("status", message)),
            )
            self.messages.put(("done", "Extraction complete."))
        except Exception as exc:  # GUI boundary: show user-friendly error.
            self.messages.put(("error", str(exc)))

    def _poll_messages(self) -> None:
        while True:
            try:
                kind, message = self.messages.get_nowait()
            except queue.Empty:
                break

            self.status_var.set(message)
            if kind in {"done", "error"}:
                self.start_button.configure(state="normal")
                if kind == "done":
                    messagebox.showinfo("Done", message)
                else:
                    messagebox.showerror("Extraction failed", message)

        self.root.after(100, self._poll_messages)

    def _refresh_file_list(self) -> None:
        self.file_list.configure(state="normal")
        self.file_list.delete("1.0", "end")
        if self.video_paths:
            self.file_list.insert("end", "\n".join(str(path) for path in self.video_paths))
        self.file_list.configure(state="disabled")


def main() -> None:
    """Run the Tkinter app."""

    root = tk.Tk()
    VideoFrameExtractorApp(root)
    root.mainloop()


def cli(argv: list[str] | None = None) -> int:
    """Small command-line entry point for automation and smoke testing."""

    parser = argparse.ArgumentParser(description="Extract image frames from videos with ffmpeg.")
    parser.add_argument("videos", nargs="+", type=Path, help="Video files to process")
    parser.add_argument("--fps", type=int, default=5, help="Frames per second to extract")
    parser.add_argument(
        "--format", choices=SUPPORTED_FORMATS, default="png", help="Output image format"
    )
    parser.add_argument("--digits", type=int, default=3, help="Digits in output numbering")
    parser.add_argument("--output-dir", type=Path, help="Optional shared output directory")
    parser.add_argument("--start", dest="start_time", help="Optional ffmpeg start timestamp")
    parser.add_argument("--end", dest="end_time", help="Optional ffmpeg end timestamp")
    args = parser.parse_args(argv)

    options = ExtractionOptions(
        fps=args.fps,
        image_format=args.format,
        digits=args.digits,
        output_dir=args.output_dir,
        start_time=args.start_time,
        end_time=args.end_time,
    )
    extract_frames(args.videos, options, progress=print)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
