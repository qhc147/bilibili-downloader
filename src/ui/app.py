import os
import sys
import random
import customtkinter as ctk
from src.ui.theme import Colors, Fonts, Sizes
from src.ui.components.console import ConsolePanel
from src.ui.components.url_input import UrlInput
from src.ui.components.video_info import VideoInfo
from src.ui.components.download_panel import DownloadPanel
from src.downloader.bilibili_api import BilibiliAPI
from src.downloader.downloader import Downloader
from src.auth.bilibili_auth import BilibiliAuth
from src.updater.update_manager import UpdateManager
from src.ui.components.update_dialog import WarningDialog
from src.ui.components.episode_selector import EpisodeSelector


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("B站视频下载器")
        self.geometry(f"{Sizes.WINDOW_WIDTH}x{Sizes.WINDOW_HEIGHT}")
        self.minsize(Sizes.WINDOW_MIN_WIDTH, Sizes.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=Colors.BG_MAIN)

        self._set_icon()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._auth = BilibiliAuth()
        self._api = BilibiliAPI(cookie_path=self._auth.get_netscape_cookie_path())
        self._downloader = Downloader(cookie_path=self._auth.get_netscape_cookie_path())
        self._update_manager = UpdateManager(self)
        self._current_video_url = None
        self._current_episodes = None
        self._vip_status = 0
        self._batch_urls = []
        self._batch_index = 0
        self._batch_cancelled = False
        self._batch_after_id = None

        self._build_layout()

        if self._auth.is_logged_in:
            self.login_status_label.configure(text="已登录", text_color=Colors.SUCCESS)
            self.login_button.configure(text="已登录", state="disabled")
            self.logout_button.configure(state="normal")
            self.console.log("已检测到登录状态。", "ok")
            self._auth.check_vip_status(callback=lambda ok, data: self.after(0, self._on_vip_check, ok, data))

    def _set_icon(self):
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(app_root, "logo", "app.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
                self.after(200, lambda: self.iconbitmap(icon_path))
            except Exception:
                pass

    def _build_layout(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_title_bar()

        self._main_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.ACCENT,
            scrollbar_button_hover_color=Colors.ACCENT_DARK
        )
        self._main_scroll.grid(row=1, column=0, sticky="nsew", padx=Sizes.PADDING_X, pady=(0, Sizes.PADDING_Y))
        self._main_scroll.grid_columnconfigure(0, weight=1)

        self.url_input = UrlInput(self._main_scroll, on_parse=self._on_parse_url)
        self.url_input.grid(row=0, column=0, sticky="ew", pady=(Sizes.PADDING_Y, 0))

        self.video_info = VideoInfo(self._main_scroll)
        self.video_info.grid(row=1, column=0, sticky="ew", pady=Sizes.PADDING_Y)

        self.episode_selector = EpisodeSelector(self._main_scroll)
        self.episode_selector.grid(row=2, column=0, sticky="ew", pady=(0, Sizes.PADDING_Y))
        self.episode_selector.grid_remove()

        self.download_panel = DownloadPanel(
            self._main_scroll, on_download=self._on_download, on_cancel=self._on_cancel_download
        )
        self.download_panel.grid(row=3, column=0, sticky="ew", pady=(0, 4))

        self.console = ConsolePanel(self._main_scroll)
        self.console.grid(row=4, column=0, sticky="ew", pady=(0, Sizes.PADDING_Y))

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

        self.update_button = ctk.CTkButton(
            right_frame, text="检查更新", width=80, height=30,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            fg_color="transparent", border_color=Colors.ACCENT,
            border_width=1, hover_color=Colors.BG_CARD,
            text_color=Colors.ACCENT,
            command=self._on_check_update_click
        )
        self.update_button.pack(side="left", padx=(0, 8))

        self.login_button = ctk.CTkButton(
            right_frame, text="登录", width=60, height=30,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            fg_color="transparent", border_color=Colors.ACCENT,
            border_width=1, hover_color=Colors.BG_CARD,
            text_color=Colors.ACCENT,
            command=self._on_login_click
        )
        self.login_button.pack(side="left")

        self.logout_button = ctk.CTkButton(
            right_frame, text="退出登录", width=80, height=30,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            fg_color="transparent", border_color=Colors.ACCENT,
            border_width=1, hover_color=Colors.BG_CARD,
            text_color=Colors.ACCENT,
            command=self._on_logout_click,
            state="disabled"
        )
        self.logout_button.pack(side="left", padx=(8, 0))

    def _on_parse_url(self, url: str):
        self.console.log(f"开始解析：{url}")
        self.url_input.set_loading(True)
        self.video_info.show_loading()
        self.episode_selector.hide()
        self._current_video_url = None
        self._current_episodes = None
        self._api.extract_info_flat(url, callback=lambda ok, data: self.after(0, self._on_flat_info_result, ok, data, url))

    def _on_flat_info_result(self, success: bool, data, original_url: str):
        self.url_input.set_loading(False)
        self.video_info.hide_loading()

        if not success:
            self.video_info.show_placeholder()
            self.console.log(f"解析失败：{data}", "error")
            return

        if data.get("is_playlist"):
            self._current_video_url = data.get("webpage_url") or original_url
            self._current_episodes = data["episodes"]
            self.video_info.show_info(
                title=data["title"],
                author=data["author"],
                episodes=f"共{data['episode_count']}集",
            )
            if not data["episodes"]:
                self.episode_selector.hide()
                self.console.log("解析成功但未获取到分集信息，请尝试重新解析", "warn")
                return
            self.episode_selector.set_episodes(data["episodes"])
            self.episode_selector.show()
            self.console.log(f"解析成功：{data['title']}（共{data['episode_count']}集）", "ok")
            if data["episodes"]:
                first_url = data["episodes"][0]["url"]
                self._api.extract_info(first_url, callback=lambda ok, d: self.after(0, self._on_formats_ready, ok, d))
        else:
            self._current_video_url = data.get("webpage_url") or original_url
            self._current_episodes = None
            self.video_info.show_info(
                title=data["title"],
                author=data["author"],
                duration=data.get("duration", ""),
                views=data.get("views", ""),
            )
            self.episode_selector.hide()
            self.console.log(f"解析成功：{data['title']}", "ok")
            self.download_panel.update_quality_options(self._vip_status)

    def _on_formats_ready(self, success: bool, data):
        if success:
            self.download_panel.update_quality_options(self._vip_status)

    def _on_download(self, quality: str):
        if self._update_manager.is_busy():
            self.console.log("更新进行中，请稍候...", "warn")
            return

        if not self._current_video_url:
            self.console.log("请先解析视频链接。", "warn")
            WarningDialog(self, "提示", "请先粘贴链接并点击解析按钮，解析完成后再下载")
            return

        if self._current_episodes:
            selected = self.episode_selector.get_selected()
            if not selected:
                self.console.log("请至少选择一集进行下载。", "warn")
                WarningDialog(self, "提示", "请至少选择一集进行下载")
                return
            self._batch_urls = [ep["url"] for ep in selected]
            self._batch_index = 0
            self._batch_cancelled = False
            self.console.log(f"开始批量下载，共{len(self._batch_urls)}集，目标画质：{quality}")
            self.download_panel.set_downloading(True)
            self._download_next_in_batch(quality)
        else:
            output_dir = self.download_panel.get_output_dir()
            self._downloader.output_dir = output_dir
            self.console.log(f"开始下载，目标画质：{quality}，保存到：{output_dir}")
            self.download_panel.set_downloading(True)

            def on_progress(progress, speed, eta):
                status = eta if eta else f"{progress * 100:.1f}%"
                self.after(0, self.download_panel.update_progress, progress, status, speed)

            def on_retry(attempt, max_retries, delay):
                self.after(0, self.console.log, f"下载失败，正在重试（{attempt}/{max_retries}），等待 {delay:.0f} 秒...", "warn")

            def on_complete(success, message):
                self.after(0, self._on_download_complete, success, message)

            self._downloader.download(
                self._current_video_url, quality,
                on_progress=on_progress,
                on_complete=on_complete,
                on_retry=on_retry
            )

    def _on_download_complete(self, success: bool, message: str):
        self.download_panel.reset()
        if success:
            self.console.log(f"下载完成！文件保存在：{self._downloader.output_dir}", "ok")
        else:
            self.console.log(f"下载失败：{message}", "error")

    def _download_next_in_batch(self, quality: str):
        if self._batch_index >= len(self._batch_urls):
            self.download_panel.reset()
            self.console.log(f"批量下载完成！共{len(self._batch_urls)}集", "ok")
            return

        url = self._batch_urls[self._batch_index]
        total = len(self._batch_urls)
        self.console.log(f"正在下载第 {self._batch_index + 1}/{total} 集...")

        output_dir = self.download_panel.get_output_dir()
        self._downloader.output_dir = output_dir

        def on_progress(progress, speed, eta):
            overall = (self._batch_index + progress) / total
            status = f"[{self._batch_index + 1}/{total}] {eta}" if eta else f"[{self._batch_index + 1}/{total}] {progress * 100:.1f}%"
            self.after(0, self.download_panel.update_progress, overall, status, speed)

        def on_retry(attempt, max_retries, delay):
            self.after(0, self.console.log, f"第 {self._batch_index + 1} 集下载失败，正在重试（{attempt}/{max_retries}），等待 {delay:.0f} 秒...", "warn")

        def on_complete(success, message):
            self.after(0, self._on_batch_item_complete, success, message, quality)

        self._downloader.download(url, quality, on_progress=on_progress, on_complete=on_complete, on_retry=on_retry)

    def _on_batch_item_complete(self, success: bool, message: str, quality: str):
        if self._batch_cancelled:
            return
        if success:
            self._batch_index += 1
            if self._batch_index < len(self._batch_urls):
                delay_ms = int(random.uniform(3, 8) * 1000)
                self.console.log(f"等待 {delay_ms / 1000:.1f} 秒后继续下载...")
                self._batch_after_id = self.after(delay_ms, self._download_next_in_batch, quality)
            else:
                self._download_next_in_batch(quality)
        else:
            self.download_panel.reset()
            self.console.log(f"第 {self._batch_index + 1} 集下载失败：{message}", "error")

    def _on_vip_check(self, success: bool, data: dict):
        self._vip_status = data.get("vip_status", 0)
        if self._vip_status >= 1:
            vip_label = "年度大会员" if data.get("vip_type") == 2 else "大会员"
            self.console.log(f"当前账号：{vip_label}", "ok")
        self.download_panel.update_quality_options(self._vip_status)

    def _on_cancel_download(self):
        self._downloader.cancel()
        self._batch_cancelled = True
        if self._batch_after_id:
            self.after_cancel(self._batch_after_id)
            self._batch_after_id = None
        self._batch_urls = []
        self._batch_index = 0
        self.console.log("正在取消下载...", "warn")

    def _on_login_click(self):
        from src.ui.components.login_dialog import LoginDialog
        LoginDialog(self, auth=self._auth, on_login_success=self._on_login_success)

    def _on_logout_click(self):
        if self.download_panel._is_downloading:
            self.console.log("下载中不可退出登录", "warn")
            return

        try:
            self._auth.logout()
        except Exception as e:
            self.console.log(f"退出登录失败：{e}", "error")
            return

        self.login_status_label.configure(text="未登录", text_color=Colors.TEXT_SECONDARY)
        self.login_button.configure(text="登录", state="normal")
        self.logout_button.configure(state="disabled")

        self._current_video_url = None
        self._current_episodes = None
        self._vip_status = 0
        self.episode_selector.hide()
        self.video_info.show_placeholder()

        self._downloader.cancel()
        self._reinit_api(cookie_path=None)

        self.console.log("已退出登录", "ok")

    def _on_login_success(self, cookie_path: str = None):
        self.login_status_label.configure(text="已登录", text_color=Colors.SUCCESS)
        self.login_button.configure(text="已登录", state="disabled")
        self.logout_button.configure(state="normal")
        self.console.log("登录成功！", "ok")
        if cookie_path:
            self._reinit_api(cookie_path)
        self._auth.check_vip_status(callback=lambda ok, data: self.after(0, self._on_vip_check, ok, data))

    def _reinit_api(self, cookie_path):
        current_output_dir = self._downloader.output_dir
        self._api = BilibiliAPI(cookie_path=cookie_path)
        self._downloader = Downloader(cookie_path=cookie_path)
        self._downloader.output_dir = current_output_dir

    def _on_check_update_click(self):
        """用户点击「检查更新」按钮"""
        if self._update_manager.is_busy():
            self.console.log("操作进行中，请稍候...", "warn")
            return

        # 禁用按钮，显示「检查中...」
        self.update_button.configure(text="检查中...", state="disabled")
        self.console.log("正在检查 yt-dlp 更新...")

        # 后台检查
        self._update_manager.check_update(
            on_result=lambda success, data: self.after(0, self._on_check_result, success, data)
        )

    def _on_check_result(self, success: bool, data):
        """检查更新结果回调"""
        # 恢复按钮
        self.update_button.configure(text="检查更新", state="normal")

        if not success:
            # 网络错误
            from src.ui.components.update_dialog import NetworkErrorDialog
            NetworkErrorDialog(self, error_message=str(data))
            self.console.log(f"检查更新失败：{data}", "error")
            return

        version_info = data
        if not version_info.has_update:
            # 已是最新版本
            from src.ui.components.update_dialog import AlreadyLatestDialog
            AlreadyLatestDialog(self, version=version_info.current)
            self.console.log(f"当前版本 {version_info.current} 已是最新版本", "ok")
            return

        # 有新版本
        from src.ui.components.update_dialog import UpdateAvailableDialog
        UpdateAvailableDialog(
            self,
            current_version=version_info.current,
            latest_version=version_info.latest,
            changelog=version_info.changelog,
            on_confirm=self._on_confirm_update,
            on_cancel=lambda: self.console.log("已取消更新", "warn")
        )
        self.console.log(f"发现新版本：{version_info.latest}", "ok")

    def _on_confirm_update(self):
        """用户确认更新"""
        from src.ui.components.update_dialog import ProgressDialog

        # 显示进度对话框
        progress_dialog = ProgressDialog(self)

        # 禁用检查更新按钮和下载按钮
        self.update_button.configure(state="disabled")
        self.download_panel.set_downloading(True)  # 禁用下载功能

        self.console.log("开始更新 yt-dlp...")

        def on_progress(status: str):
            self.after(0, progress_dialog.update_progress, 0.5, status)

        def on_complete(success: bool, message: str):
            self.after(0, self._on_update_complete, success, message, progress_dialog)

        self._update_manager.start_update(on_progress, on_complete)

    def _on_update_complete(self, success: bool, message: str, progress_dialog):
        """更新完成回调"""
        progress_dialog.destroy()

        # 恢复按钮状态
        self.update_button.configure(state="normal")
        self.download_panel.set_downloading(False)

        if success:
            # 更新成功
            from src.ui.components.update_dialog import UpdateSuccessDialog
            import yt_dlp
            new_version = yt_dlp.version.__version__

            # 重新初始化 yt-dlp 相关模块，确保使用新版本
            cookie_path = self._auth.get_netscape_cookie_path()
            self._reinit_api(cookie_path)

            UpdateSuccessDialog(
                self,
                version=new_version,
                on_restart=self._on_restart_app,
                on_later=lambda: self.console.log("请稍后手动重启软件", "warn")
            )
            self.console.log(f"更新完成！新版本：{new_version}", "ok")
        else:
            # 更新失败
            from src.ui.components.update_dialog import UpdateFailedDialog
            # 从错误信息中提取备份路径（如果有）
            backup_path = "未知"
            if "备份路径" in message or "备份位置" in message:
                # 简单提取
                lines = message.split("\n")
                for line in lines:
                    if "备份路径" in line or "backup_path" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            backup_path = parts[-1].strip()
                            break

            UpdateFailedDialog(self, error_message=message, backup_path=backup_path)
            self.console.log(f"更新失败：{message}", "error")

    def _on_restart_app(self):
        """重启软件"""
        self.console.log("正在关闭软件，请手动重启...", "warn")
        sys.exit(0)
