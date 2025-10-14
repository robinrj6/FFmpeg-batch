import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles FFmpeg video processing operations."""

    def __init__(self):
        self.ffmpeg_path = "ffmpeg"
        self.ffprobe_path = "ffprobe"

    def get_video_info(self, input_path: str) -> Dict:
        """Extract video metadata using ffprobe."""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                input_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)

            video_stream = next(
                (s for s in info.get("streams", []) if s["codec_type"] == "video"),
                None
            )

            if not video_stream:
                raise ValueError("No video stream found")

            return {
                "duration": float(info["format"].get("duration", 0)),
                "size": int(info["format"].get("size", 0)),
                "bitrate": int(info["format"].get("bit_rate", 0)),
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "codec": video_stream.get("codec_name"),
                "fps": eval(video_stream.get("r_frame_rate", "0/1"))
            }
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            raise

    def transcode(
        self,
        input_path: str,
        output_path: str,
        codec: str = "libx264",
        preset: str = "medium",
        crf: int = 23,
        audio_codec: str = "aac",
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """Transcode video to different format/codec."""

        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-c:v", codec,
            "-preset", preset,
            "-crf", str(crf),
            "-c:a", audio_codec,
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            "-y",
            output_path
        ]

        return self._execute_ffmpeg(cmd, input_path, progress_callback)

    def compress(
        self,
        input_path: str,
        output_path: str,
        target_size_mb: Optional[float] = None,
        scale: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """Compress video with optional target size."""

        video_info = self.get_video_info(input_path)
        duration = video_info["duration"]

        cmd = [self.ffmpeg_path, "-i", input_path]

        if target_size_mb:
            # Calculate target bitrate
            target_bitrate = int((target_size_mb * 8192) / duration) - 128  # Leave room for audio
            cmd.extend(["-b:v", f"{target_bitrate}k", "-maxrate", f"{target_bitrate * 1.5}k", "-bufsize", f"{target_bitrate * 2}k"])

        if scale:
            cmd.extend(["-vf", f"scale={scale}"])

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            "-y",
            output_path
        ])

        return self._execute_ffmpeg(cmd, input_path, progress_callback)

    def add_watermark(
        self,
        input_path: str,
        output_path: str,
        watermark_path: str,
        position: str = "bottom-right",
        opacity: float = 0.7,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """Add watermark to video."""

        position_map = {
            "top-left": "10:10",
            "top-right": "W-w-10:10",
            "bottom-left": "10:H-h-10",
            "bottom-right": "W-w-10:H-h-10",
            "center": "(W-w)/2:(H-h)/2"
        }

        overlay_pos = position_map.get(position, "W-w-10:H-h-10")

        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-i", watermark_path,
            "-filter_complex", f"[1]format=rgba,colorchannelmixer=aa={opacity}[wm];[0][wm]overlay={overlay_pos}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "copy",
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            "-y",
            output_path
        ]

        return self._execute_ffmpeg(cmd, input_path, progress_callback)

    def generate_thumbnail(
        self,
        input_path: str,
        output_path: str,
        timestamp: str = "00:00:01",
        size: str = "1280x720"
    ) -> Dict:
        """Generate thumbnail from video."""

        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-ss", timestamp,
            "-vframes", "1",
            "-vf", f"scale={size}",
            "-y",
            output_path
        ]

        return self._execute_ffmpeg(cmd, input_path, None)

    def extract_audio(
        self,
        input_path: str,
        output_path: str,
        audio_format: str = "mp3",
        bitrate: str = "192k",
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """Extract audio from video."""

        codec_map = {
            "mp3": "libmp3lame",
            "aac": "aac",
            "wav": "pcm_s16le",
            "flac": "flac"
        }

        codec = codec_map.get(audio_format, "libmp3lame")

        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-vn",
            "-c:a", codec,
            "-b:a", bitrate,
            "-progress", "pipe:1",
            "-y",
            output_path
        ]

        return self._execute_ffmpeg(cmd, input_path, progress_callback)

    def create_gif(
        self,
        input_path: str,
        output_path: str,
        start_time: str = "00:00:00",
        duration: int = 5,
        fps: int = 10,
        scale: int = 480,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """Convert video segment to GIF."""

        cmd = [
            self.ffmpeg_path,
            "-ss", start_time,
            "-t", str(duration),
            "-i", input_path,
            "-vf", f"fps={fps},scale={scale}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", "0",
            "-progress", "pipe:1",
            "-y",
            output_path
        ]

        return self._execute_ffmpeg(cmd, input_path, progress_callback)

    def concatenate_videos(
        self,
        input_paths: List[str],
        output_path: str,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """Concatenate multiple videos."""

        # Create a temporary file list
        concat_file = Path(output_path).parent / "concat_list.txt"
        with open(concat_file, "w") as f:
            for path in input_paths:
                f.write(f"file '{path}'\n")

        try:
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                "-progress", "pipe:1",
                "-y",
                output_path
            ]

            return self._execute_ffmpeg(cmd, input_paths[0], progress_callback)
        finally:
            if concat_file.exists():
                concat_file.unlink()

    def trim_video(
        self,
        input_path: str,
        output_path: str,
        start_time: str,
        end_time: Optional[str] = None,
        duration: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """Trim video to specific duration."""

        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-ss", start_time
        ]

        if end_time:
            cmd.extend(["-to", end_time])
        elif duration:
            cmd.extend(["-t", str(duration)])

        cmd.extend([
            "-c", "copy",
            "-progress", "pipe:1",
            "-y",
            output_path
        ])

        return self._execute_ffmpeg(cmd, input_path, progress_callback)

    def _execute_ffmpeg(
        self,
        cmd: List[str],
        input_path: str,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """Execute FFmpeg command with progress tracking."""

        start_time = datetime.now()

        try:
            # Get total duration for progress calculation
            video_info = self.get_video_info(input_path)
            total_duration = video_info["duration"]

            logger.info(f"Executing: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # Parse progress
            for line in process.stdout:
                if progress_callback:
                    # Parse out_time_ms from ffmpeg progress
                    match = re.search(r'out_time_ms=(\d+)', line)
                    if match:
                        current_ms = int(match.group(1))
                        current_sec = current_ms / 1_000_000
                        progress_pct = min(100, (current_sec / total_duration) * 100) if total_duration > 0 else 0
                        progress_callback(progress_pct)

            process.wait()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            return {
                "success": True,
                "processing_time": processing_time,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }

        except Exception as e:
            logger.error(f"FFmpeg execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
