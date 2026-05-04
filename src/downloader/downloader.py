import os
import threading
import yt_dlp


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

    def download(self, url: str, quality: str = "80", on_progress=None, on_complete=None):
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
                }
                if self._cookie_path:
                    opts["cookiefile"] = self._cookie_path

                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])

                if on_complete:
                    on_complete(True, "下载完成")
            except yt_dlp.utils.DownloadCancelled:
                if on_complete:
                    on_complete(False, "下载已取消")
            except Exception as e:
                if on_complete:
                    on_complete(False, str(e))

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
