import os
import customtkinter as ctk
from tkinter import filedialog
from src.ui.theme import Colors, Fonts, Sizes


class DownloadPanel(ctk.CTkFrame):
    QUALITY_OPTIONS = [
        ("超清 4K", "120"),
        ("高清 1080P60", "116"),
        ("高清 1080P+", "112"),
        ("高清 1080P", "80"),
        ("高清 720P", "64"),
        ("清晰 480P", "32"),
        ("流畅 360P", "16"),
    ]
    DEFAULT_QUALITY = "80"
    _LABEL_TO_QN = {label: qn for label, qn in QUALITY_OPTIONS}
    _QN_TO_LABEL = {qn: label for label, qn in QUALITY_OPTIONS}

    def __init__(self, master, on_download=None, on_cancel=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._on_download = on_download
        self._on_cancel = on_cancel
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self._output_dir = os.path.join(app_root, "output")

        self._build_path_selector()
        self._build_controls()
        self._build_progress()

    def _build_path_selector(self):
        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        path_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            path_frame, text="保存到：",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            text_color=Colors.TEXT_PRIMARY
        ).grid(row=0, column=0, padx=(0, 8))

        self.path_entry = ctk.CTkEntry(
            path_frame, height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY
        )
        self.path_entry.grid(row=0, column=1, sticky="ew")
        self.path_entry.insert(0, self._output_dir)
        self.path_entry.configure(state="disabled")

        self.browse_btn = ctk.CTkButton(
            path_frame, text="浏览", width=60, height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            fg_color="transparent", border_color=Colors.ACCENT,
            border_width=1, hover_color=Colors.BG_CARD,
            text_color=Colors.ACCENT,
            command=self._browse_folder
        )
        self.browse_btn.grid(row=0, column=2, padx=(8, 0))

    def _build_controls(self):
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ctrl.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            ctrl, text="画质：",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            text_color=Colors.TEXT_PRIMARY
        ).grid(row=0, column=0, padx=(0, 8))

        self.quality_var = ctk.StringVar(value=self.DEFAULT_QUALITY)
        self.quality_menu = ctk.CTkOptionMenu(
            ctrl,
            values=[q[0] for q in self.QUALITY_OPTIONS],
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            fg_color=Colors.BG_INPUT,
            button_color=Colors.ACCENT_DARK,
            button_hover_color=Colors.ACCENT,
            dropdown_fg_color=Colors.BG_CARD,
            dropdown_hover_color=Colors.BG_INPUT,
            width=160, height=Sizes.BUTTON_HEIGHT,
            command=self._on_quality_change
        )
        self.quality_menu.set(self._QN_TO_LABEL[self.DEFAULT_QUALITY])
        self.quality_menu.grid(row=0, column=1, sticky="w")

        self.download_btn = ctk.CTkButton(
            ctrl, text="开始下载", width=120, height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE, "bold"),
            fg_color=Colors.ACCENT, hover_color=Colors.ACCENT_DARK,
            text_color="#ffffff",
            command=self._handle_download
        )
        self.download_btn.grid(row=0, column=2, padx=(12, 0))

        self.cancel_btn = ctk.CTkButton(
            ctrl, text="取消", width=70, height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color="transparent", border_color=Colors.ERROR,
            border_width=1, hover_color=Colors.BG_CARD,
            text_color=Colors.ERROR,
            command=self._handle_cancel
        )
        self.cancel_btn.grid(row=0, column=3, padx=(8, 0))
        self.cancel_btn.grid_remove()

    def _browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self._output_dir, title="选择下载保存路径")
        if folder:
            self._output_dir = folder
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)
            self.path_entry.configure(state="disabled")

    def get_output_dir(self) -> str:
        return self._output_dir

    def _build_progress(self):
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=2, column=0, sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_frame.grid_remove()

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, height=Sizes.PROGRESS_HEIGHT,
            fg_color=Colors.BG_PROGRESS,
            progress_color=Colors.ACCENT,
            corner_radius=Sizes.PROGRESS_RADIUS
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)

        status_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        status_frame.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            status_frame, text="",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY, anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        self.speed_label = ctk.CTkLabel(
            status_frame, text="",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY, anchor="e"
        )
        self.speed_label.grid(row=0, column=1, sticky="e")

    def _on_quality_change(self, choice: str):
        qn = self._LABEL_TO_QN.get(choice, self.DEFAULT_QUALITY)
        self.quality_var.set(qn)

    def _handle_download(self):
        if self._on_download:
            self._on_download(self.quality_var.get())

    def _handle_cancel(self):
        if self._on_cancel:
            self._on_cancel()

    def get_quality(self) -> str:
        return self.quality_var.get()

    def set_downloading(self, active: bool):
        if active:
            self.download_btn.grid_remove()
            self.cancel_btn.grid()
            self.progress_frame.grid()
            self.quality_menu.configure(state="disabled")
        else:
            self.cancel_btn.grid_remove()
            self.download_btn.grid()
            self.quality_menu.configure(state="normal")

    def update_progress(self, progress: float, status: str = "", speed: str = ""):
        self.progress_bar.set(progress)
        self.status_label.configure(text=status)
        self.speed_label.configure(text=speed)

    def reset(self):
        self.set_downloading(False)
        self.progress_frame.grid_remove()
        self.progress_bar.set(0)
        self.status_label.configure(text="")
        self.speed_label.configure(text="")
