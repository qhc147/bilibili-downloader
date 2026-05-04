import re
import customtkinter as ctk
from src.ui.theme import Colors, Fonts, Sizes


class UrlInput(ctk.CTkFrame):
    BILIBILI_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?bilibili\.com/video/(BV[\w]+|av\d+)"
        r"|(?:https?://)?b23\.tv/[\w]+"
    )

    def __init__(self, master, on_parse=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._on_parse = on_parse

        self.entry = ctk.CTkEntry(
            self, height=Sizes.URL_INPUT_HEIGHT,
            placeholder_text="请粘贴B站视频链接...",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_SECONDARY
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self._handle_parse())

        self.parse_btn = ctk.CTkButton(
            self, text="解析", width=80, height=Sizes.URL_INPUT_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color="transparent", border_color=Colors.ACCENT,
            border_width=1, hover_color=Colors.BG_CARD,
            text_color=Colors.ACCENT,
            command=self._handle_parse
        )
        self.parse_btn.grid(row=0, column=1)

    def _handle_parse(self):
        url = self.entry.get().strip()
        if not url:
            return
        if self._on_parse:
            self._on_parse(url)

    def get_url(self) -> str:
        return self.entry.get().strip()

    def set_loading(self, loading: bool):
        if loading:
            self.parse_btn.configure(text="解析中...", state="disabled")
            self.entry.configure(state="disabled")
        else:
            self.parse_btn.configure(text="解析", state="normal")
            self.entry.configure(state="normal")

    @classmethod
    def extract_bvid(cls, url: str) -> str | None:
        m = cls.BILIBILI_PATTERN.search(url)
        if m:
            return m.group(1) if m.group(1) else url
        return None
