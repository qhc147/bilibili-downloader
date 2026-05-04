import customtkinter as ctk
from src.ui.theme import Colors, Fonts, Sizes


class ConsolePanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._line_count = 0

        header = ctk.CTkFrame(self, fg_color=Colors.BG_CONSOLE, corner_radius=Sizes.CARD_RADIUS)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="控制台",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=Sizes.CONSOLE_PADDING, pady=4)

        clear_btn = ctk.CTkButton(
            header, text="清空", width=50, height=24,
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            fg_color="transparent", hover_color=Colors.BG_CARD,
            text_color=Colors.TEXT_SECONDARY, command=self.clear
        )
        clear_btn.grid(row=0, column=1, padx=Sizes.CONSOLE_PADDING, pady=4)

        self.textbox = ctk.CTkTextbox(
            self, height=150,
            fg_color=Colors.BG_CONSOLE, corner_radius=Sizes.CARD_RADIUS,
            font=(Fonts.CONSOLE_FAMILY, Fonts.CONSOLE_SIZE),
            text_color=Colors.LOG_INFO, wrap="word",
            state="disabled"
        )
        self.textbox.grid(row=1, column=0, sticky="ew")

        self._tag_colors = {
            "info": Colors.LOG_INFO,
            "warn": Colors.LOG_WARN,
            "error": Colors.LOG_ERROR,
            "ok": Colors.LOG_OK,
        }

    def log(self, message: str, level: str = "info"):
        self.textbox.configure(state="normal")

        if self._line_count >= Sizes.CONSOLE_MAX_LINES:
            self.textbox.delete("1.0", "2.0")
        else:
            self._line_count += 1

        tag = f"tag_{self._line_count}"
        self.textbox.insert("end", message + "\n", tag)

        color = self._tag_colors.get(level, Colors.LOG_INFO)
        self.textbox.tag_config(tag, foreground=color)

        self.textbox.configure(state="disabled")
        self.textbox.see("end")

    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
        self._line_count = 0
