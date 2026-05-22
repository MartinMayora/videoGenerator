import threading
import customtkinter as ctk
from ..constants import PURPLE, BG_CARD, BG_PANEL, TEXT_MUTED, GREEN, BORDER


class ProgressViewMixin:
    """Fetch / download progress view."""

    def _show_progress_view(self):
        self._clear_main()

        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(22, 0))
        ctk.CTkLabel(
            top, text="FETCHING  CLIPS",
            font=ctk.CTkFont(family="Courier", size=18, weight="bold"),
            text_color="#ffffff",
        ).pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(
            self.main, height=6, corner_radius=3,
            fg_color=BG_PANEL, progress_color=PURPLE,
        )
        self.progress_bar.pack(fill="x", padx=24, pady=(14, 0))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.main, text="Initialising…",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
        )
        self.status_label.pack(anchor="w", padx=24, pady=(8, 12))

        self.log_text = self._log_box()


class ProcessingViewMixin:
    """FFmpeg processing view."""

    def _show_processing_view(self):
        self._clear_main()

        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(22, 0))
        ctk.CTkLabel(
            top, text="PROCESSING  VIDEOS",
            font=ctk.CTkFont(family="Courier", size=18, weight="bold"),
            text_color="#ffffff",
        ).pack(side="left")

        self.proc_progress = ctk.CTkProgressBar(
            self.main, height=6, corner_radius=3,
            fg_color=BG_PANEL, progress_color=PURPLE,
        )
        self.proc_progress.pack(fill="x", padx=24, pady=(14, 0))
        self.proc_progress.set(0)

        self.proc_status = ctk.CTkLabel(
            self.main, text="Starting FFmpeg…",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
        )
        self.proc_status.pack(anchor="w", padx=24, pady=(8, 12))

        self.log_text = self._log_box()

        threading.Thread(target=self._process_worker, daemon=True).start()


class DoneViewMixin:
    """Completion view."""

    def _show_done_view(self):
        self._clear_main()
        center = ctk.CTkFrame(self.main, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(
            center, text="✓",
            font=ctk.CTkFont(size=76), text_color=GREEN,
        ).pack()

        ctk.CTkLabel(
            center, text="VIDEOS READY",
            font=ctk.CTkFont(family="Courier", size=26, weight="bold"),
            text_color="#ffffff",
        ).pack(pady=(6, 4))

        ctk.CTkLabel(
            center,
            text="Your short-form videos have been exported to  ./build/output/",
            font=ctk.CTkFont(size=13), text_color=TEXT_MUTED,
        ).pack()

        btns = ctk.CTkFrame(center, fg_color="transparent")
        btns.pack(pady=28)

        ctk.CTkButton(
            btns,
            text="Open Output Folder",
            width=200, height=44,
            fg_color=PURPLE, hover_color="#6930C3",
            font=ctk.CTkFont(family="Courier", size=13, weight="bold"),
            command=self._open_output,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btns,
            text="Generate More",
            width=160, height=44,
            fg_color="#1f1f23", hover_color="#2e2e35",
            font=ctk.CTkFont(size=13),
            command=self._reset,
        ).pack(side="left", padx=8)
