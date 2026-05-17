import customtkinter as ctk
from src.ui.theme import Colors, Fonts, Sizes


class VideoInfo(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=Colors.BG_CARD, corner_radius=Sizes.CARD_RADIUS, **kwargs)

        self._placeholder = ctk.CTkLabel(
            self, text="粘贴视频链接，即可开始下载",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            text_color=Colors.TEXT_SECONDARY
        )
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self._info_frame = ctk.CTkFrame(self, fg_color="transparent")

        self._build_info_layout()

    def _build_info_layout(self):
        self._info_frame.grid_columnconfigure(1, weight=1)

        self._thumbnail_label = ctk.CTkLabel(
            self._info_frame, text="",
            width=240, height=135,
            fg_color=Colors.BG_INPUT,
            corner_radius=Sizes.BORDER_RADIUS
        )
        self._thumbnail_label.grid(row=0, column=0, rowspan=4, padx=Sizes.CARD_PADDING, pady=Sizes.CARD_PADDING, sticky="nw")

        self._title_label = ctk.CTkLabel(
            self._info_frame, text="",
            font=(Fonts.BODY_FAMILY, 16, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w", wraplength=400
        )
        self._title_label.grid(row=0, column=1, sticky="ew", padx=(0, Sizes.CARD_PADDING), pady=(Sizes.CARD_PADDING, 4))

        self._meta_labels = {}
        meta_fields = [
            ("author", "UP主"),
            ("duration", "时长"),
            ("views", "播放"),
            ("episodes", "集数"),
        ]
        for i, (key, label_text) in enumerate(meta_fields, start=1):
            row_frame = ctk.CTkFrame(self._info_frame, fg_color="transparent")
            row_frame.grid(row=i, column=1, sticky="w", padx=(0, Sizes.CARD_PADDING), pady=2)

            ctk.CTkLabel(
                row_frame, text=f"{label_text}：",
                font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
                text_color=Colors.TEXT_SECONDARY
            ).pack(side="left")

            val_label = ctk.CTkLabel(
                row_frame, text="",
                font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
                text_color=Colors.TEXT_PRIMARY
            )
            val_label.pack(side="left")
            self._meta_labels[key] = val_label

    def show_placeholder(self):
        self._info_frame.pack_forget()
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def show_info(self, title: str, author: str = "", duration: str = "", views: str = "", episodes: str = "", thumbnail_image=None):
        self._placeholder.place_forget()
        self._info_frame.pack(fill="both", expand=True)

        self._title_label.configure(text=title)
        self._meta_labels["author"].configure(text=author)
        self._meta_labels["duration"].configure(text=duration)
        self._meta_labels["views"].configure(text=views)
        self._meta_labels["episodes"].configure(text=episodes)

        if thumbnail_image:
            self._thumbnail_label.configure(image=thumbnail_image, text="")
        else:
            self._thumbnail_label.configure(image=None, text="无封面")

    def show_loading(self):
        self._placeholder.place_forget()
        self._info_frame.pack_forget()
        loading = ctk.CTkLabel(
            self, text="正在解析视频信息...",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            text_color=Colors.TEXT_SECONDARY
        )
        loading.place(relx=0.5, rely=0.5, anchor="center")
        self._loading_label = loading

    def hide_loading(self):
        if hasattr(self, "_loading_label"):
            self._loading_label.place_forget()
            del self._loading_label
