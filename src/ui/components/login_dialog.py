import threading
import customtkinter as ctk
from PIL import Image
from io import BytesIO
from src.ui.theme import Colors, Fonts, Sizes
from src.auth.bilibili_auth import BilibiliAuth


class LoginDialog(ctk.CTkToplevel):
    def __init__(self, master, auth: BilibiliAuth = None, on_login_success=None, **kwargs):
        super().__init__(master, **kwargs)

        self.title("B站登录")
        self.geometry(f"{Sizes.LOGIN_DIALOG_WIDTH}x{Sizes.LOGIN_DIALOG_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=Colors.BG_MAIN)
        self.transient(master)
        self.grab_set()

        self._auth = auth or BilibiliAuth()
        self._on_login_success = on_login_success
        self._polling = False
        self._stop_event = threading.Event()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(100, self._load_qrcode)

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="扫码登录B站",
            font=(Fonts.TITLE_FAMILY, Fonts.TITLE_SIZE, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            self, text="使用B站手机客户端扫描二维码",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY
        ).pack(pady=(0, 16))

        self.qr_frame = ctk.CTkFrame(
            self, width=Sizes.QR_CODE_SIZE + 20,
            height=Sizes.QR_CODE_SIZE + 20,
            fg_color=Colors.BG_CARD,
            corner_radius=Sizes.CARD_RADIUS
        )
        self.qr_frame.pack(pady=(0, 16))
        self.qr_frame.pack_propagate(False)

        self.qr_label = ctk.CTkLabel(
            self.qr_frame, text="正在获取二维码...",
            font=(Fonts.BODY_FAMILY, Fonts.SMALL_SIZE),
            text_color=Colors.TEXT_SECONDARY
        )
        self.qr_label.place(relx=0.5, rely=0.5, anchor="center")

        self.status_label = ctk.CTkLabel(
            self, text="等待扫码...",
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            text_color=Colors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=(0, 12))

        self.refresh_btn = ctk.CTkButton(
            self, text="刷新二维码", width=120, height=Sizes.BUTTON_HEIGHT,
            font=(Fonts.BODY_FAMILY, Fonts.BODY_SIZE),
            fg_color="transparent", border_color=Colors.ACCENT,
            border_width=1, hover_color=Colors.BG_CARD,
            text_color=Colors.ACCENT,
            command=self._on_refresh
        )
        self.refresh_btn.pack(pady=(0, 20))

    def _load_qrcode(self):
        try:
            _, qrcode_key, qr_buf = self._auth.generate_qrcode()

            pil_img = Image.open(qr_buf)
            pil_img = pil_img.resize((Sizes.QR_CODE_SIZE, Sizes.QR_CODE_SIZE), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img,
                                   size=(Sizes.QR_CODE_SIZE, Sizes.QR_CODE_SIZE))
            self.qr_label.configure(image=ctk_img, text="")
            self._qr_image = ctk_img

            self._polling = True
            self._stop_event.clear()
            self._auth.poll_login(
                qrcode_key,
                on_status=lambda msg: self.after(0, self._set_status, msg),
                on_success=lambda: self.after(0, self._login_success),
                on_fail=lambda msg: self.after(0, self._login_fail, msg),
                stop_event=self._stop_event,
            )

        except Exception as e:
            self.qr_label.configure(text=f"获取失败: {e}")

    def _set_status(self, text: str, color: str = None):
        if not self.winfo_exists():
            return
        self.status_label.configure(
            text=text,
            text_color=color or Colors.TEXT_SECONDARY
        )

    def _login_success(self):
        if not self.winfo_exists():
            return
        self._polling = False
        self._set_status("登录成功！", Colors.SUCCESS)
        self.after(800, self._close_success)

    def _login_fail(self, message: str):
        if not self.winfo_exists():
            return
        self._polling = False
        self._set_status(message, Colors.ERROR)

    def _on_refresh(self):
        self.qr_label.configure(image=None, text="正在获取二维码...")
        self._set_status("等待扫码...")
        self._polling = False
        self._stop_event.set()
        self.after(200, self._load_qrcode)

    def _on_close(self):
        self._polling = False
        self._stop_event.set()
        self.grab_release()
        self.destroy()

    def _close_success(self):
        self._polling = False
        cookie_path = self._auth.get_netscape_cookie_path()
        if self._on_login_success:
            self._on_login_success(cookie_path)
        self.grab_release()
        self.destroy()
