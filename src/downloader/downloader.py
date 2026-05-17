import os
import time
import random
import threading
import yt_dlp
from src.downloader import friendly_error

MAX_RETRIES = 3
RETRY_BASE_DELAY = 5


class Downloader:
    def __init__(self, output_dir: str = None, cookie_path: str = None):
        app_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
        self._output_dir = output_dir or os.path.join(app_root, "output")
        self._cookie_path = cookie_path
        self._ffmpeg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ffmpeg")
        self._cancel_event = threading.Event()
        self._current_thread = None

    @property
    def output_dir(self) -> str:
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value: str):
        self._output_dir = value

    def download(self, url: str, quality: str = "80", on_progress=None, on_complete=None, on_retry=None):
        self._cancel_event.clear()

        def _progress_hook(d):
            if self._cancel_event.is_set():
                raise yt_dlp.utils.DownloadCancelled()

            if d["status"] == "downloading" and on_progress:
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("speed", 0)
                eta = d.get("eta", 0)

                progress = downloaded / total if total > 0 else 0
                speed_str = self._format_speed(speed) if speed else ""
                eta_str = self._format_eta(eta) if eta else ""

                on_progress(progress, speed_str, eta_str)

            elif d["status"] == "finished" and on_progress:
                on_progress(1.0, "", "合并中...")

        def _run():
            try:
                opts = {
                    "format": f"bv*[height<={self._quality_to_height(quality)}]+ba/bv*+ba/b",
                    "outtmpl": os.path.join(self._output_dir, "%(title)s", "%(title)s.%(ext)s"),
                    "merge_output_format": "mp4",
                    "progress_hooks": [_progress_hook],
                    "quiet": True,
                    "no_warnings": True,
                    "ffmpeg_location": self._ffmpeg_dir,
                    "retries": 3,
                    "fragment_retries": 5,
                }
                if self._cookie_path:
                    opts["cookiefile"] = self._cookie_path

                last_error = None
                for attempt in range(MAX_RETRIES):
                    if self._cancel_event.is_set():
                        raise yt_dlp.utils.DownloadCancelled()
                    try:
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            ydl.download([url])
                        last_error = None
                        break
                    except yt_dlp.utils.DownloadCancelled:
                        raise
                    except Exception as e:
                        last_error = e
                        if attempt < MAX_RETRIES - 1:
                            delay = RETRY_BASE_DELAY * (attempt + 1) + random.uniform(1, 3)
                            if on_retry:
                                on_retry(attempt + 1, MAX_RETRIES, delay)
                            elapsed = 0.0
                            while elapsed < delay:
                                if self._cancel_event.is_set():
                                    raise yt_dlp.utils.DownloadCancelled()
                                time.sleep(min(0.5, delay - elapsed))
                                elapsed += 0.5

                if last_error:
                    if on_complete:
                        on_complete(False, friendly_error(str(last_error)))
                else:
                    if on_complete:
                        on_complete(True, "下载完成")
            except yt_dlp.utils.DownloadCancelled:
                if on_complete:
                    on_complete(False, "下载已取消")
            except Exception as e:
                if on_complete:
                    on_complete(False, friendly_error(str(e)))

        self._current_thread = threading.Thread(target=_run, daemon=True)
        self._current_thread.start()

    def cancel(self):
        self._cancel_event.set()

    @staticmethod
    def _quality_to_height(quality: str) -> int:
        mapping = {
            "120": 2160,
            "116": 1080,
            "112": 1080,
            "80": 1080,
            "64": 720,
            "32": 480,
            "16": 360,
        }
        return mapping.get(quality, 1080)

    @staticmethod
    def _format_speed(speed):
        if not speed:
            return ""
        if speed >= 1024 * 1024:
            return f"{speed / (1024 * 1024):.1f} MB/s"
        elif speed >= 1024:
            return f"{speed / 1024:.1f} KB/s"
        return f"{speed:.0f} B/s"

    @staticmethod
    def _format_eta(eta):
        if not eta or eta < 0:
            return ""
        eta = int(eta)
        if eta >= 3600:
            return f"剩余 {eta // 3600}h{(eta % 3600) // 60}m"
        elif eta >= 60:
            return f"剩余 {eta // 60}m{eta % 60}s"
        return f"剩余 {eta}s"
