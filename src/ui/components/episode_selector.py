import customtkinter as ctk
from src.ui.theme import Colors, Fonts, Sizes


class EpisodeSelector(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=Colors.BG_CARD, corner_radius=Sizes.CARD_RADIUS, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._episodes = []
        self._checkboxes = []
        self._checkbox_vars = []

        self._build_toolbar()
        self._build_list()
        self.grid_remove()

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=Sizes.CARD_PADDING, pady=(Sizes.CARD_PADDING, 8))
        toolbar.grid_columnconfigure(0, weight=1)

        self._title_label = ctk.CTkLabel(
            toolbar, text="分集列表",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        )
        self._title_label.grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        self._select_all_btn = ctk.CTkButton(
            btn_frame, text="全选", width=70, height=28,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            fg_color="transparent", border_color=Colors.ACCENT,
            border_width=1, hover_color=Colors.BG_INPUT,
            text_color=Colors.ACCENT,
            command=self.select_all
        )
        self._select_all_btn.grid(row=0, column=0, padx=(0, 6))

        self._deselect_all_btn = ctk.CTkButton(
            btn_frame, text="取消全选", width=70, height=28,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            fg_color="transparent", border_color=Colors.ACCENT,
            border_width=1, hover_color=Colors.BG_INPUT,
            text_color=Colors.ACCENT,
            command=self.deselect_all
        )
        self._deselect_all_btn.grid(row=0, column=1, padx=(0, 8))

        self._count_label = ctk.CTkLabel(
            btn_frame, text="已选: 0集",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY
        )
        self._count_label.grid(row=0, column=2)

    def _build_list(self):
        self.grid_rowconfigure(1, weight=1)
        self._scroll_frame = ctk.CTkScrollableFrame(
            self, height=120,
            fg_color=Colors.BG_INPUT,
            corner_radius=Sizes.BORDER_RADIUS,
            scrollbar_button_color=Colors.ACCENT,
            scrollbar_button_hover_color=Colors.ACCENT_DARK
        )
        self._scroll_frame.grid(row=1, column=0, sticky="nsew", padx=Sizes.CARD_PADDING, pady=(0, Sizes.CARD_PADDING))
        self._scroll_frame.grid_columnconfigure(0, weight=1)

    def set_episodes(self, episodes: list):
        self._episodes = episodes
        self._checkboxes = []
        self._checkbox_vars = []

        for widget in self._scroll_frame.winfo_children():
            widget.destroy()

        for ep in episodes:
            var = ctk.IntVar(value=0)
            self._checkbox_vars.append(var)

            text = f"{ep['index']}. {ep['title']}"
            cb = ctk.CTkCheckBox(
                self._scroll_frame, text=text, variable=var,
                font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
                fg_color=Colors.BG_INPUT, hover_color=Colors.BG_CARD,
                checkmark_color=Colors.ACCENT, border_color=Colors.ACCENT,
                text_color=Colors.TEXT_PRIMARY,
                command=self._on_checkbox_change
            )
            cb.grid(sticky="w", pady=2)
            self._checkboxes.append(cb)

        self._title_label.configure(text=f"分集列表 (共{len(episodes)}集)")
        self._update_count()

    def get_selected(self) -> list:
        selected = []
        for i, var in enumerate(self._checkbox_vars):
            if var.get() == 1:
                selected.append(self._episodes[i])
        return selected

    def show(self):
        self.grid()

    def hide(self):
        self.grid_remove()

    def select_all(self):
        for var in self._checkbox_vars:
            var.set(1)
        self._update_count()

    def deselect_all(self):
        for var in self._checkbox_vars:
            var.set(0)
        self._update_count()

    def _on_checkbox_change(self):
        self._update_count()

    def _update_count(self):
        count = sum(1 for var in self._checkbox_vars if var.get() == 1)
        self._count_label.configure(text=f"已选: {count}集")

    def _format_duration(self, seconds: int) -> str:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"
