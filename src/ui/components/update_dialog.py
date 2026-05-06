"""
更新对话框组件
包含 6 个对话框：有新版本、已是最新版本、进度、完成、网络错误、更新失败
"""
import customtkinter as ctk
from typing import Callable
from src.ui.theme import Colors, Fonts, Sizes


class BaseUpdateDialog(ctk.CTkToplevel):
    """更新对话框基类"""

    def __init__(self, parent, title: str, width: int, height: int, **kwargs):
        super().__init__(parent, **kwargs)

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color=Colors.BG_CARD)
        self.transient(parent)
        self.grab_set()

        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{x}+{y}")

    def _close(self):
        """关闭对话框"""
        self.grab_release()
        self.destroy()


class UpdateAvailableDialog(BaseUpdateDialog):
    """有新版本对话框"""

    def __init__(
        self,
        parent,
        current_version: str,
        latest_version: str,
        changelog: str,
        on_confirm: Callable,
        on_cancel: Callable,
        **kwargs
    ):
        super().__init__(parent, "yt-dlp 更新可用", 500, 500, **kwargs)

        self._on_confirm = on_confirm
        self._on_cancel = on_cancel

        self._build_ui(current_version, latest_version, changelog)
        self.protocol("WM_DELETE_WINDOW", self._handle_cancel)

    def _build_ui(self, current_version: str, latest_version: str, changelog: str):
        # 标题
        ctk.CTkLabel(
            self,
            text="yt-dlp 更新可用",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(20, 16))

        # 版本信息框
        version_frame = ctk.CTkFrame(self, fg_color=Colors.BG_INPUT, corner_radius=Sizes.BORDER_RADIUS)
        version_frame.pack(padx=20, pady=(0, 12), fill="x")

        # 当前版本
        ctk.CTkLabel(
            version_frame,
            text=f"当前版本: {current_version}",
            font=("Consolas", Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY
        ).pack(pady=(12, 4), padx=16, anchor="w")

        # 最新版本
        ctk.CTkLabel(
            version_frame,
            text=f"最新版本: {latest_version}",
            font=("Consolas", Fonts.SMALL_SIZE),
            text_color=Colors.SUCCESS
        ).pack(pady=(4, 12), padx=16, anchor="w")

        # 分隔线
        separator = ctk.CTkFrame(self, height=1, fg_color=Colors.BORDER)
        separator.pack(padx=20, pady=(0, 12), fill="x")

        # 更新内容标题
        ctk.CTkLabel(
            self,
            text="更新内容:",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(padx=20, pady=(0, 8), anchor="w")

        # 更新内容文本框（可滚动）
        changelog_frame = ctk.CTkFrame(self, fg_color=Colors.BG_INPUT, corner_radius=Sizes.BORDER_RADIUS)
        changelog_frame.pack(padx=20, pady=(0, 16), fill="both", expand=True)

        changelog_text = ctk.CTkTextbox(
            changelog_frame,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.BG_INPUT,
            wrap="word",
            height=200
        )
        changelog_text.pack(padx=8, pady=8, fill="both", expand=True)
        changelog_text.insert("1.0", changelog)
        changelog_text.configure(state="disabled")

        # 按钮区域
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(padx=20, pady=(0, 20), fill="x")

        # 取消按钮
        ctk.CTkButton(
            button_frame,
            text="取消",
            width=100,
            height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color="transparent",
            border_color=Colors.BORDER,
            border_width=1,
            hover_color=Colors.BG_CARD,
            text_color=Colors.TEXT_SECONDARY,
            command=self._handle_cancel
        ).pack(side="left", padx=(0, 8))

        # 立即更新按钮
        ctk.CTkButton(
            button_frame,
            text="立即更新",
            width=120,
            height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color=Colors.ACCENT,
            hover_color=Colors.ACCENT_DARK,
            text_color=Colors.TEXT_PRIMARY,
            command=self._handle_confirm
        ).pack(side="right")

    def _handle_confirm(self):
        self._close()
        if self._on_confirm:
            self._on_confirm()

    def _handle_cancel(self):
        self._close()
        if self._on_cancel:
            self._on_cancel()


class AlreadyLatestDialog(BaseUpdateDialog):
    """已是最新版本对话框"""

    def __init__(self, parent, version: str, **kwargs):
        super().__init__(parent, "已是最新版本", 400, 150, **kwargs)

        self._build_ui(version)
        self.protocol("WM_DELETE_WINDOW", self._close)

        # 3 秒后自动关闭
        self.after(3000, self._close)

    def _build_ui(self, version: str):
        # 标题
        ctk.CTkLabel(
            self,
            text="已是最新版本",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(20, 12))

        # 内容
        ctk.CTkLabel(
            self,
            text=f"当前版本 {version} 已是最新版本",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY
        ).pack(pady=(0, 16))

        # 确定按钮
        ctk.CTkButton(
            self,
            text="确定",
            width=100,
            height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color=Colors.ACCENT,
            hover_color=Colors.ACCENT_DARK,
            text_color=Colors.TEXT_PRIMARY,
            command=self._close
        ).pack(pady=(0, 20))


class ProgressDialog(BaseUpdateDialog):
    """进度对话框"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, "正在更新 yt-dlp", 400, 180, **kwargs)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用关闭按钮

    def _build_ui(self):
        # 标题
        ctk.CTkLabel(
            self,
            text="正在更新 yt-dlp",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(20, 16))

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(
            self,
            width=360,
            height=20,
            corner_radius=Sizes.PROGRESS_RADIUS,
            fg_color=Colors.BG_PROGRESS,
            progress_color=Colors.ACCENT
        )
        self.progress_bar.pack(pady=(0, 12))
        self.progress_bar.set(0)

        # 状态文字
        self.status_label = ctk.CTkLabel(
            self,
            text="准备中...",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=(0, 16))

        # 警告
        warning_frame = ctk.CTkFrame(self, fg_color=Colors.BG_INPUT, corner_radius=Sizes.BORDER_RADIUS)
        warning_frame.pack(padx=20, pady=(0, 20), fill="x")

        ctk.CTkLabel(
            warning_frame,
            text="⚠️ 请勿关闭软件",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.WARNING
        ).pack(pady=8)

    def update_progress(self, progress: float, status: str):
        """更新进度

        Args:
            progress: 进度值 (0.0-1.0)
            status: 状态文字
        """
        if not self.winfo_exists():
            return
        self.progress_bar.set(progress)
        self.status_label.configure(text=status)


class UpdateSuccessDialog(BaseUpdateDialog):
    """更新完成对话框"""

    def __init__(
        self,
        parent,
        version: str,
        on_restart: Callable,
        on_later: Callable,
        **kwargs
    ):
        super().__init__(parent, "更新完成", 400, 220, **kwargs)

        self._on_restart = on_restart
        self._on_later = on_later

        self._build_ui(version)
        self.protocol("WM_DELETE_WINDOW", self._handle_later)

    def _build_ui(self, version: str):
        # 标题
        ctk.CTkLabel(
            self,
            text="更新完成",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(20, 12))

        # 成功图标
        ctk.CTkLabel(
            self,
            text="✓",
            font=(Fonts.BODY_FAMILY, 36),
            text_color=Colors.SUCCESS
        ).pack(pady=(0, 12))

        # 内容
        ctk.CTkLabel(
            self,
            text=f"yt-dlp 已更新到 {version}",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(0, 8))

        # 提示
        ctk.CTkLabel(
            self,
            text="请重启软件以使更新生效",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY
        ).pack(pady=(0, 16))

        # 按钮区域
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(padx=20, pady=(0, 20), fill="x")

        # 稍后按钮
        ctk.CTkButton(
            button_frame,
            text="稍后",
            width=100,
            height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color="transparent",
            border_color=Colors.BORDER,
            border_width=1,
            hover_color=Colors.BG_CARD,
            text_color=Colors.TEXT_SECONDARY,
            command=self._handle_later
        ).pack(side="left", padx=(0, 8))

        # 重启按钮
        ctk.CTkButton(
            button_frame,
            text="重启",
            width=100,
            height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color=Colors.ACCENT,
            hover_color=Colors.ACCENT_DARK,
            text_color=Colors.TEXT_PRIMARY,
            command=self._handle_restart
        ).pack(side="right")

    def _handle_restart(self):
        self._close()
        if self._on_restart:
            self._on_restart()

    def _handle_later(self):
        self._close()
        if self._on_later:
            self._on_later()


class NetworkErrorDialog(BaseUpdateDialog):
    """网络错误对话框"""

    def __init__(self, parent, error_message: str, **kwargs):
        super().__init__(parent, "检查更新失败", 450, 280, **kwargs)

        self._build_ui(error_message)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_ui(self, error_message: str):
        # 标题
        ctk.CTkLabel(
            self,
            text="检查更新失败",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(20, 12))

        # 错误图标
        ctk.CTkLabel(
            self,
            text="✕",
            font=(Fonts.BODY_FAMILY, 36),
            text_color=Colors.ERROR
        ).pack(pady=(0, 12))

        # 错误信息
        ctk.CTkLabel(
            self,
            text=error_message,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_PRIMARY,
            wraplength=400
        ).pack(pady=(0, 12), padx=20)

        # 可能原因
        reasons_frame = ctk.CTkFrame(self, fg_color=Colors.BG_INPUT, corner_radius=Sizes.BORDER_RADIUS)
        reasons_frame.pack(padx=20, pady=(0, 12), fill="x")

        ctk.CTkLabel(
            reasons_frame,
            text="可能原因:",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(8, 4), padx=12, anchor="w")

        reasons = [
            "• 网络未连接",
            "• 需要配置代理",
            "• GitHub 服务不可用"
        ]
        for reason in reasons:
            ctk.CTkLabel(
                reasons_frame,
                text=reason,
                font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
                text_color=Colors.TEXT_SECONDARY
            ).pack(pady=2, padx=20, anchor="w")

        ctk.CTkLabel(
            reasons_frame,
            text="",
            height=4
        ).pack()

        # 建议
        ctk.CTkLabel(
            self,
            text="请检查网络代理设置后重试",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.WARNING
        ).pack(pady=(0, 16))

        # 确定按钮
        ctk.CTkButton(
            self,
            text="确定",
            width=100,
            height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color=Colors.ACCENT,
            hover_color=Colors.ACCENT_DARK,
            text_color=Colors.TEXT_PRIMARY,
            command=self._close
        ).pack(pady=(0, 20))


class UpdateFailedDialog(BaseUpdateDialog):
    """更新失败对话框"""

    def __init__(self, parent, error_message: str, backup_path: str, **kwargs):
        super().__init__(parent, "更新失败", 500, 350, **kwargs)

        self._build_ui(error_message, backup_path)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_ui(self, error_message: str, backup_path: str):
        # 标题
        ctk.CTkLabel(
            self,
            text="更新失败",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(20, 12))

        # 错误图标
        ctk.CTkLabel(
            self,
            text="✕",
            font=(Fonts.BODY_FAMILY, 36),
            text_color=Colors.ERROR
        ).pack(pady=(0, 12))

        # 主要信息
        ctk.CTkLabel(
            self,
            text="yt-dlp 更新失败，已自动回滚到旧版本",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(0, 12))

        # 错误详情标题
        ctk.CTkLabel(
            self,
            text="错误详情:",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(padx=20, pady=(0, 8), anchor="w")

        # 错误详情文本框
        error_frame = ctk.CTkFrame(self, fg_color=Colors.BG_INPUT, corner_radius=Sizes.BORDER_RADIUS)
        error_frame.pack(padx=20, pady=(0, 12), fill="both", expand=True)

        error_text = ctk.CTkTextbox(
            error_frame,
            font=(Fonts.CONSOLE_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.BG_INPUT,
            wrap="word",
            height=100
        )
        error_text.pack(padx=8, pady=8, fill="both", expand=True)
        error_text.insert("1.0", error_message)
        error_text.configure(state="disabled")

        # 建议
        ctk.CTkLabel(
            self,
            text="请以管理员身份运行软件后重试",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.WARNING
        ).pack(pady=(0, 8))

        # 备份位置
        backup_frame = ctk.CTkFrame(self, fg_color=Colors.BG_INPUT, corner_radius=Sizes.BORDER_RADIUS)
        backup_frame.pack(padx=20, pady=(0, 16), fill="x")

        ctk.CTkLabel(
            backup_frame,
            text=f"备份位置: {backup_path}",
            font=(Fonts.CONSOLE_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY
        ).pack(pady=8, padx=12)

        # 确定按钮
        ctk.CTkButton(
            self,
            text="确定",
            width=100,
            height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color=Colors.ACCENT,
            hover_color=Colors.ACCENT_DARK,
            text_color=Colors.TEXT_PRIMARY,
            command=self._close
        ).pack(pady=(0, 20))
