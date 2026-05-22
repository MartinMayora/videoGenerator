import customtkinter as ctk
from .constants import PURPLE, BG_CARD, BORDER, TEXT_MUTED


class TitleBarMixin:
    """
    Removes the OS window frame and replaces it with a custom title bar.

    Provides:
      - Drag-to-move  (click + drag anywhere on the bar)
      - Minimize       (− button)
      - Close          (× button)
      - 1 px coloured border around the whole window
    """

    def _build_title_bar(self):
        self.overrideredirect(True)
        self._drag_start_x = 0
        self._drag_start_y = 0

        # overrideredirect windows don't receive WM focus on X11/WSL.
        # On every click: first force the window to get X11 keyboard focus,
        # then immediately give tkinter focus back to the clicked widget so
        # entry fields can still receive keystrokes.
        self.bind_all("<Button-1>", self._on_click_focus, add=True)

        # 1 px coloured border — achieved by setting the window bg to the
        # border colour and padding everything inside by 1 px.
        self.configure(fg_color=BORDER)

        # ── Bar ───────────────────────────────────────────────────────────
        self._title_bar = ctk.CTkFrame(
            self, height=36, fg_color=BG_CARD, corner_radius=0,
        )
        self._title_bar.pack(side="top", fill="x", padx=1, pady=(1, 0))
        self._title_bar.pack_propagate(False)

        # Left: icon + name
        left = ctk.CTkFrame(self._title_bar, fg_color="transparent")
        left.pack(side="left", padx=10)
        icon = ctk.CTkLabel(
            left, text="⬡",
            font=ctk.CTkFont(size=15), text_color=PURPLE,
        )
        icon.pack(side="left", padx=(0, 6))
        name = ctk.CTkLabel(
            left, text="SHORTS GENERATOR",
            font=ctk.CTkFont(family="Courier", size=11, weight="bold"),
            text_color=TEXT_MUTED,
        )
        name.pack(side="left")

        # Right: window controls
        right = ctk.CTkFrame(self._title_bar, fg_color="transparent")
        right.pack(side="right", padx=6)

        ctk.CTkButton(
            right, text="×", width=30, height=26,
            fg_color="transparent", hover_color="#c0392b",
            text_color="#cccccc",             font=ctk.CTkFont(size=18), corner_radius=4,
            command=self.destroy,
        ).pack(side="right", padx=(2, 0))

        ctk.CTkButton(
            right, text="−", width=30, height=26,
            fg_color="transparent", hover_color="#3a3a45",
            text_color="#cccccc",             font=ctk.CTkFont(size=18), corner_radius=4,
            command=self._minimize,
        ).pack(side="right", padx=2)

        # Drag bindings — attach to bar and its non-interactive children
        for widget in (self._title_bar, left, icon, name):
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>",     self._on_drag_motion)

    # ── Focus ─────────────────────────────────────────────────────────────

    def _on_click_focus(self, event):
        # focus_force() on the clicked widget sets both X11 keyboard focus
        # (so the OS routes keystrokes to this window) and tkinter focus
        # (so the entry receives them) in a single call.
        event.widget.focus_force()

    # ── Drag ──────────────────────────────────────────────────────────────

    def _on_drag_start(self, event):
        self._drag_start_x = event.x_root - self.winfo_x()
        self._drag_start_y = event.y_root - self.winfo_y()

    def _on_drag_motion(self, event):
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self.geometry(f"+{x}+{y}")

    # ── Minimize ──────────────────────────────────────────────────────────

    def _minimize(self):
        # overrideredirect windows can't be iconified directly.
        # Temporarily restore normal mode, iconify, then re-apply on restore.
        self.overrideredirect(False)
        self.iconify()
        self.bind("<Map>", self._on_restore)

    def _on_restore(self, _event):
        self.unbind("<Map>")
        self.overrideredirect(True)
        self.lift()
