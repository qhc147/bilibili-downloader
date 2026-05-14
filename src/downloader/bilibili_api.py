import threading
import yt_dlp
from src.downloader import friendly_error


class BilibiliAPI:
    def __init__(self, cookie_path: str = None):
        self._cookie_path = cookie_path

    def _base_opts(self) -> dict:
        opts = {
            "quiet": True,
            "no_warnings": True,
        }
        if self._cookie_path:
            opts["cookiefile"] = self._cookie_path
        return opts

    def extract_info(self, url: str, callback=None):
        def _run():
            try:
                opts = self._base_opts()
                opts["extract_flat"] = False
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                if callback:
                    callback(True, self._normalize_info(info))
            except Exception as e:
                if callback:
                    callback(False, friendly_error(str(e)))

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def _normalize_info(self, info: dict) -> dict:
        duration_sec = info.get("duration", 0) or 0
        minutes, seconds = divmod(int(duration_sec), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            duration_str = f"{minutes}:{seconds:02d}"

        view_count = info.get("view_count", 0) or 0
        if view_count >= 10000:
            views_str = f"{view_count / 10000:.1f}万"
        else:
            views_str = str(view_count)

        formats = []
        for f in info.get("formats", []):
            if f.get("vcodec", "none") != "none":
                formats.append({
                    "format_id": f.get("format_id", ""),
                    "quality": f.get("quality", 0),
                    "height": f.get("height", 0),
                    "format_note": f.get("format_note", ""),
                    "filesize": f.get("filesize") or f.get("filesize_approx", 0),
                })

        return {
            "id": info.get("id", ""),
            "title": info.get("title", "未知标题"),
            "author": info.get("uploader", "未知UP主"),
            "duration": duration_str,
            "views": views_str,
            "thumbnail": info.get("thumbnail", ""),
            "description": info.get("description", ""),
            "formats": formats,
            "webpage_url": info.get("webpage_url", ""),
        }
