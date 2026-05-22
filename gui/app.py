import os
import sys
import queue
import threading
import subprocess

import customtkinter as ctk

from .constants import PURPLE, BG_DARK, BG_CARD, BG_PANEL, BORDER, TEXT_MUTED
from src.models import ClipConfig
from .sidebar import SidebarMixin
from .views import WelcomeMixin, PickerMixin, ProgressViewMixin, ProcessingViewMixin, DoneViewMixin
from .workers import FetchMixin, ProcessMixin


class App(
    ctk.CTk,
    SidebarMixin,
    WelcomeMixin,
    PickerMixin,
    ProgressViewMixin,
    ProcessingViewMixin,
    DoneViewMixin,
    FetchMixin,
    ProcessMixin,
):
    """
    Main application window.

    Responsibilities kept here:
      - Window setup and top-level layout (sidebar + main panel)
      - Shared state initialisation (clips_data, log_queue, picker state…)
      - Shared utilities: _clear_main, _log, _poll_logs, _log_box, _open_output, _reset
      - Shared widget helpers: _divider, _section_label, _field_label, _entry

    Everything else lives in the mixin modules.
    To add a new feature: create a mixin, add it to the inheritance list above.
    """

    def __init__(self, client_id: str, client_secret: str):
        super().__init__()
        self._client_id = client_id
        self._client_secret = client_secret

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Twitch Shorts Generator")
        self.geometry("1340x780")
        self.minsize(960, 620)
        self.configure(fg_color=BG_DARK)

        # ── Shared state ──────────────────────────────────────────────────
        self.clips_data: list[ClipConfig] = []
        self.pick_index: int = 0
        self.log_queue: queue.Queue[str] = queue.Queue()
        self._all_categories: list[str] = []

        # Coordinate-picker state — reset on each clip load
        self._pick_x: int | None = None
        self._pick_y: int | None = None
        self._pick_rect_w: int = 0
        self._pick_rect_h: int = 0
        self._pick_thumb_path: str = ""
        self._pick_scale = 1.0
        self._pick_img_offset = (0, 0)
        self._pick_pil_img = None
        self._pick_img_ref = None
        self._hover_cx = None
        self._hover_cy = None

        self._build_ui()
        self._poll_logs()

        if client_id and client_secret:
            threading.Thread(target=self._fetch_categories_bg, daemon=True).start()

    # ── Top-level layout ──────────────────────────────────────────────────

    def _build_ui(self):
        self.sidebar = ctk.CTkFrame(self, width=272, corner_radius=0, fg_color=BG_CARD)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_DARK)
        self.main.pack(side="right", fill="both", expand=True)

        self._build_sidebar()
        self._show_welcome()

    def _clear_main(self):
        for w in self.main.winfo_children():
            w.destroy()

    # ── Shared widget helpers ─────────────────────────────────────────────

    def _divider(self, parent, pady=12):
        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(
            fill="x", padx=16, pady=pady
        )

    def _section_label(self, parent, text):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(family="Courier", size=10, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(padx=16, pady=(12, 6), anchor="w")

    def _field_label(self, parent, text):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(8, 2))

    def _entry(self, parent, placeholder):
        e = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            fg_color=BG_PANEL,
            border_color="#3a3a45",
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=13),
        )
        e.pack(fill="x")
        return e

    def _log_box(self) -> ctk.CTkTextbox:
        box = ctk.CTkTextbox(
            self.main,
            state="disabled",
            font=ctk.CTkFont(family="Courier", size=12),
            fg_color=BG_CARD,
            border_color=BORDER,
            border_width=1,
            corner_radius=8,
            text_color="#c8c8d0",
        )
        box.pack(fill="both", expand=True, padx=24, pady=(0, 22))
        return box

    # ── Logging ───────────────────────────────────────────────────────────

    def _log(self, msg: str):
        self.log_queue.put(msg)

    def _poll_logs(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if hasattr(self, "log_text") and self.log_text.winfo_exists():
                    self.log_text.configure(state="normal")
                    self.log_text.insert("end", msg + "\n")
                    self.log_text.see("end")
                    self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self._poll_logs)

    # ── Utilities ─────────────────────────────────────────────────────────

    def _open_output(self):
        path = os.path.abspath("./build/output")
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                try:
                    with open("/proc/version") as fh:
                        if "microsoft" in fh.read().lower():
                            win_path = subprocess.check_output(
                                ["wslpath", "-w", path]
                            ).decode().strip()
                            subprocess.Popen(["explorer.exe", win_path])
                            return
                except Exception:
                    pass
                subprocess.Popen(["xdg-open", path])
        except Exception:
            from tkinter import messagebox
            messagebox.showinfo("Output Folder", f"Videos saved to:\n{path}")

    def _reset(self) -> None:
        self.clips_data = []
        self.pick_index = 0
        self.fetch_btn.configure(state="normal")
        self._show_welcome()
