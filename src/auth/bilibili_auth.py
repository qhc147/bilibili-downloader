import os
import json
import time
import threading
import requests
import qrcode
from io import BytesIO


class BilibiliAuth:
    QRCODE_GENERATE_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    QRCODE_POLL_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"

    def __init__(self, data_dir: str = None):
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._data_dir = data_dir or os.path.join(app_root, "config")
        self._cookie_path = os.path.join(self._data_dir, "cookies.txt")
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com",
        })

    @property
    def cookie_path(self) -> str:
        return self._cookie_path

    @property
    def is_logged_in(self) -> bool:
        return os.path.exists(self._cookie_path)

    def generate_qrcode(self) -> tuple[str, str, object]:
        resp = self._session.get(self.QRCODE_GENERATE_URL)
        data = resp.json()["data"]
        url = data["url"]
        qrcode_key = data["qrcode_key"]

        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="white", back_color="#16213e")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        return url, qrcode_key, buf

    def poll_login(self, qrcode_key: str, on_status=None, on_success=None, on_fail=None, stop_event: threading.Event = None):
        def _poll():
            while True:
                if stop_event and stop_event.is_set():
                    return
                try:
                    resp = self._session.get(
                        self.QRCODE_POLL_URL,
                        params={"qrcode_key": qrcode_key}
                    )
                    data = resp.json()["data"]
                    code = data["code"]

                    if code == 0:
                        self._save_cookies(resp.cookies, data.get("refresh_token", ""))
                        if on_success:
                            on_success()
                        return
                    elif code == 86038:
                        if on_fail:
                            on_fail("二维码已过期")
                        return
                    elif code == 86090:
                        if on_status:
                            on_status("已扫码，请在手机上确认")
                    elif code == 86101:
                        if on_status:
                            on_status("等待扫码...")

                except Exception as e:
                    if on_fail:
                        on_fail(str(e))
                    return

                time.sleep(2)

        t = threading.Thread(target=_poll, daemon=True)
        t.start()
        return t

    def _save_cookies(self, cookies, refresh_token: str):
        os.makedirs(self._data_dir, exist_ok=True)

        cookie_data = {
            "cookies": {k: v for k, v in cookies.items()},
            "refresh_token": refresh_token,
            "saved_at": time.time(),
        }

        with open(self._cookie_path, "w", encoding="utf-8") as f:
            json.dump(cookie_data, f)

        self._write_netscape_cookies(cookies)

    def _write_netscape_cookies(self, cookies):
        lines = ["# Netscape HTTP Cookie File"]
        for name, value in cookies.items():
            lines.append(f".bilibili.com\tTRUE\t/\tFALSE\t0\t{name}\t{value}")

        netscape_path = self._cookie_path.replace(".txt", "_netscape.txt")
        with open(netscape_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def get_netscape_cookie_path(self) -> str | None:
        path = self._cookie_path.replace(".txt", "_netscape.txt")
        return path if os.path.exists(path) else None

    def logout(self):
        if os.path.exists(self._cookie_path):
            os.remove(self._cookie_path)
        netscape = self._cookie_path.replace(".txt", "_netscape.txt")
        if os.path.exists(netscape):
            os.remove(netscape)

    def _load_cookies_for_request(self) -> dict:
        try:
            with open(self._cookie_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("cookies", {})
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def check_vip_status(self, callback=None):
        def _check():
            try:
                cookies = self._load_cookies_for_request()
                resp = self._session.get(
                    "https://api.bilibili.com/x/web-interface/nav",
                    cookies=cookies
                )
                result = resp.json()
                if result.get("code") == 0:
                    data = result.get("data", {})
                    vip_info = {
                        "vip_status": data.get("vipStatus", 0),
                        "vip_type": data.get("vipType", 0),
                    }
                    if callback:
                        callback(True, vip_info)
                else:
                    if callback:
                        callback(False, {"vip_status": 0, "vip_type": 0})
            except Exception:
                if callback:
                    callback(False, {"vip_status": 0, "vip_type": 0})

        t = threading.Thread(target=_check, daemon=True)
        t.start()
        return t
