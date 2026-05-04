import os
import customtkinter as ctk
from src.ui.theme import Colors, Fonts, Sizes
from src.ui.components.console import ConsolePanel
from src.ui.components.url_input import UrlInput
from src.ui.components.video_info import VideoInfo
from src.ui.components.download_panel import DownloadPanel
from src.downloader.bilibili_api import BilibiliAPI
from src.downloader.downloader import Downloader
from src.auth.bilibili_auth import BilibiliAuth


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("B站视频下载器")
        self.geometry(f"{Sizes.WINDOW_WIDTH}x{Sizes.WINDOW_HEIGHT}")
        self.minsize(Sizes.WINDOW_MIN_WIDTH, Sizes.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=Colors.BG_MAIN)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._auth = BilibiliAuth()
        self._api = BilibiliAPI(cookie_path=self._auth.get_netscape_cookie_path())
        self._downloader = Downloader(cookie_path=self._auth.get_netscape_cookie_path())
        self._current_video_url = None

        self._build_layout()

        if self._auth.is_logged_in:
            self.login_status_label.configure(text="已登录", text_color=Colors.SUCCESS)
            self.login_button.configure(text="已登录", state="disabled")
            self.console.log("已检测到登录状态。", "ok")

    def _build_layout(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._build_title_bar()

        self.url_input = UrlInput(self, on_parse=self._on_parse_url)
        self.url_input.grid(row=1, column=0, sticky="ew", padx=Sizes.PADDING_X, pady=(Sizes.PADDING_Y, 0))

        self.video_info = VideoInfo(self)
        self.video_info.grid(row=2, column=0, sticky="nsew", padx=Sizes.PADDING_X, pady=Sizes.PADDING_Y)

        self.download_panel = DownloadPanel(
            self, on_download=self._on_download, on_cancel=self._on_cancel_download
        )
        self.download_panel.grid(row=3, column=0, sticky="ew", padx=Sizes.PADDING_X, pady=(0, 4))

        self.console = ConsolePanel(self)
        self.console.grid(row=4, column=0, sticky="ew", padx=Sizes.PADDING_X, pady=(0, Sizes.PADDING_Y))

        self.console.log("B站视频下载器已启动，请粘贴视频链接开始使用。", "ok")

    def _build_title_bar(self):
        self.title_frame = ctk.CTkFrame(self, height=Sizes.TITLE_BAR_HEIGHT, fg_color=Colors.BG_MAIN, corner_radius=0)
        self.title_frame.grid(row=0, column=0, sticky="ew", padx=Sizes.PADDING_X, pady=(8, 0))
        self.title_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            self.title_frame, text="B站视频下载器",
            font=(Fonts.TITLE_FAMILY, Fonts.TITLE_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w")

        right_frame = ctk.CTkFrame(self.title_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="e")

        self.login_status_label = ctk.CTkLabel(
            right_frame, text="未登录",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY
        )
        self.login_status_label.pack(side="left", padx=(0, 8))

        self.login_button = ctk.CTkButton(
            right_frame, text="登录", width=60, height=30,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            fg_color="transparent", border_color=Colors.ACCENT,
            border_width=1, hover_color=Colors.BG_CARD,
            text_color=Colors.ACCENT,
            command=self._on_login_click
        )
        self.login_button.pack(side="left")

    def _on_parse_url(self, url: str):
        self.console.log(f"开始解析：{url}")
        self.url_input.set_loading(True)
        self.video_info.show_loading()

        self._api.extract_info(url, callback=lambda ok, data: self.after(0, self._on_info_result, ok, data))

    def _on_info_result(self, success: bool, data):
        self.url_input.set_loading(False)
        self.video_info.hide_loading()

        if success:
            self._current_video_url = data.get("webpage_url", self.url_input.get_url())
            self.video_info.show_info(
                title=data["title"],
                author=data["author"],
                duration=data["duration"],
                views=data["views"],
            )
            self.console.log(f"解析成功：{data['title']}", "ok")
        else:
            self.video_info.show_placeholder()
            self.console.log(f"解析失败：{data}", "error")

    def _on_download(self, quality: str):
        if not self._current_video_url:
            self.console.log("请先解析视频链接。", "warn")
            return

        output_dir = self.download_panel.get_output_dir()
        self._downloader.output_dir = output_dir
        self.console.log(f"开始下载，目标画质：{quality}，保存到：{output_dir}")
        self.download_panel.set_downloading(True)

        def on_progress(progress, speed, eta):
            status = eta if eta else f"{progress * 100:.1f}%"
            self.after(0, self.download_panel.update_progress, progress, status, speed)

        def on_complete(success, message):
            self.after(0, self._on_download_complete, success, message)

        self._downloader.download(
            self._current_video_url, quality,
            on_progress=on_progress,
            on_complete=on_complete
        )

    def _on_download_complete(self, success: bool, message: str):
        self.download_panel.reset()
        if success:
            self.console.log(f"下载完成！文件保存在：{self._downloader.output_dir}", "ok")
        else:
            self.console.log(f"下载失败：{message}", "error")

    def _on_cancel_download(self):
        self._downloader.cancel()
        self.console.log("正在取消下载...", "warn")

    def _on_login_click(self):
        from src.ui.components.login_dialog import LoginDialog
        LoginDialog(self, auth=self._auth, on_login_success=self._on_login_success)

    def _on_login_success(self, cookie_path: str = None):
        self.login_status_label.configure(text="已登录", text_color=Colors.SUCCESS)
        self.login_button.configure(text="已登录", state="disabled")
        self.console.log("登录成功！", "ok")
        if cookie_path:
            current_output_dir = self._downloader.output_dir
            self._api = BilibiliAPI(cookie_path=cookie_path)
            self._downloader = Downloader(cookie_path=cookie_path)
            self._downloader.output_dir = current_output_dir
