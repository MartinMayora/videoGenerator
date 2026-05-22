import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk

from ..constants import PURPLE, BG_CARD, BG_PANEL, TEXT_MUTED, GREEN, BORDER
from src.layouts import LAYOUTS, LAYOUT_BY_ID, Layout

HANDLE_RADIUS = 7   # canvas px, half-side of corner handle squares
MIN_W = 60          # minimum webcam crop width in full-res pixels

# Mini schematic colours
_WEBCAM_CLR   = "#7c3aed"
_GAMEPLAY_CLR = "#1a3a5c"
_CANVAS_BG    = "#0d0d0f"


class PickerMixin:
    """
    Webcam coordinate picker view.

    Left panel  : thumbnail canvas. Click to place webcam centre; drag a corner
                  handle to resize while locking aspect ratio.
    Right panel : layout selector. Choosing a layout with no webcam skips the
                  canvas interaction entirely.
    """

    def _show_pick_view(self) -> None:
        self._clear_main()
        self.pick_index = 0
        self._load_pick_clip()

    def _load_pick_clip(self) -> None:
        self._clear_main()

        if self.pick_index >= len(self.clips_data):
            self._show_processing_view()
            return

        clip = self.clips_data[self.pick_index]
        self._pick_thumb_path = f"./build/videos/{clip.thumbnail}"
        n = len(self.clips_data)

        # Restore previously confirmed state (supports Back navigation)
        self._pick_x: int | None = clip.webcam_x
        self._pick_y: int | None = clip.webcam_y
        self._pick_rect_w: int = clip.webcam_w
        self._pick_rect_h: int = clip.webcam_h
        self._aspect_ratio: float = clip.webcam_w / clip.webcam_h
        self._selected_layout_id: str = clip.layout
        self._dragging_handle: str | None = None
        self._drag_center_full: tuple[float, float] = (0.0, 0.0)
        self._pick_scale = 1.0
        self._pick_img_offset = (0, 0)
        self._pick_pil_img = None
        self._pick_img_ref = None
        self._hover_cx = None
        self._hover_cy = None
        self._layout_cards: dict[str, ctk.CTkFrame] = {}

        # ── Header ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self.main, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(18, 0))
        ctk.CTkLabel(
            hdr,
            text=f"MARK WEBCAM  —  clip {self.pick_index + 1} of {n}",
            font=ctk.CTkFont(family="Courier", size=16, weight="bold"),
            text_color="#ffffff",
        ).pack(side="left")

        prog = ctk.CTkProgressBar(
            self.main, height=5, corner_radius=3,
            fg_color=BG_PANEL, progress_color=PURPLE,
        )
        prog.pack(fill="x", padx=24, pady=(10, 0))
        prog.set(self.pick_index / n)

        ctk.CTkLabel(
            self.main,
            text=f"Streamer: {clip.name}   ·   Click to place — drag corners to resize — pick a layout on the right",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=24, pady=(6, 8))

        # ── Content row (canvas left + layout panel right) ─────────────────
        content = ctk.CTkFrame(self.main, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24)

        # Right panel first so it's anchored before canvas expands
        layout_panel = ctk.CTkFrame(content, width=230, fg_color=BG_CARD, corner_radius=10)
        layout_panel.pack(side="right", fill="y", padx=(12, 0))
        layout_panel.pack_propagate(False)
        self._build_layout_panel(layout_panel)

        # Canvas card
        canvas_card = ctk.CTkFrame(
            content, fg_color=BG_CARD,
            corner_radius=10, border_color=BORDER, border_width=1,
        )
        canvas_card.pack(side="left", fill="both", expand=True)

        self.pick_canvas = tk.Canvas(
            canvas_card, bg="#111115", highlightthickness=0, cursor="crosshair",
        )
        self.pick_canvas.pack(fill="both", expand=True, padx=2, pady=2)

        self.pick_canvas.bind("<Configure>",       lambda _e: self._draw_pick_image())
        self.pick_canvas.bind("<Motion>",          self._on_canvas_motion)
        self.pick_canvas.bind("<Button-1>",        self._on_canvas_press)
        self.pick_canvas.bind("<B1-Motion>",       self._on_canvas_drag)
        self.pick_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.pick_canvas.bind("<Leave>",           self._on_canvas_leave)

        # ── Size readout ───────────────────────────────────────────────────
        info_row = ctk.CTkFrame(self.main, fg_color="transparent")
        info_row.pack(fill="x", padx=24, pady=(6, 0))
        self._size_label = ctk.CTkLabel(
            info_row, text=self._size_text(),
            font=ctk.CTkFont(family="Courier", size=11), text_color=TEXT_MUTED,
        )
        self._size_label.pack(side="left")

        # ── Footer ─────────────────────────────────────────────────────────
        ftr = ctk.CTkFrame(self.main, fg_color="transparent")
        ftr.pack(fill="x", padx=24, pady=10)

        if self.pick_index > 0:
            ctk.CTkButton(
                ftr, text="← Back", width=100, height=38,
                fg_color=BG_PANEL, hover_color="#2e2e35",
                font=ctk.CTkFont(size=13),
                command=self._prev_clip,
            ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            ftr, text="Skip Clip", width=110, height=38,
            fg_color=BG_PANEL, hover_color="#2e2e35",
            font=ctk.CTkFont(size=13),
            command=self._skip_clip,
        ).pack(side="left")

        ctk.CTkLabel(
            ftr, text="Click to place  ·  drag corners to resize",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
        ).pack(side="right", padx=(0, 14))

        self.confirm_pick_btn = ctk.CTkButton(
            ftr,
            text="Confirm  →",
            width=160, height=38,
            state=self._confirm_btn_state(),
            fg_color=PURPLE, hover_color="#6930C3",
            font=ctk.CTkFont(family="Courier", size=13, weight="bold"),
            command=self._confirm_pick,
        )
        self.confirm_pick_btn.pack(side="right")

    # ── Layout panel ──────────────────────────────────────────────────────

    def _build_layout_panel(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            parent, text="LAYOUT",
            font=ctk.CTkFont(family="Courier", size=11, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(padx=14, pady=(14, 8), anchor="w")

        for layout in LAYOUTS:
            card = self._layout_card(parent, layout)
            self._layout_cards[layout.id] = card

    def _layout_card(self, parent: ctk.CTkFrame, layout: Layout) -> ctk.CTkFrame:
        selected = layout.id == self._selected_layout_id
        card = ctk.CTkFrame(
            parent,
            fg_color=BG_PANEL,
            corner_radius=8,
            border_color=PURPLE if selected else BORDER,
            border_width=2,
            cursor="hand2",
        )
        card.pack(fill="x", padx=10, pady=(0, 6))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=8)

        # Mini schematic
        preview = tk.Canvas(inner, width=48, height=76, bg=_CANVAS_BG, highlightthickness=0)
        preview.pack(side="left", padx=(0, 8))
        _draw_layout_preview(preview, layout)

        # Text
        text_col = ctk.CTkFrame(inner, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            text_col, text=layout.name,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#ffffff",
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_col, text=layout.description,
            font=ctk.CTkFont(size=10),
            text_color=TEXT_MUTED,
            wraplength=115,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        def _select(_event=None, lid=layout.id) -> None:
            self._update_layout_selection(lid)

        for w in (card, inner, preview, text_col):
            w.bind("<Button-1>", _select)
        for child in text_col.winfo_children():
            child.bind("<Button-1>", _select)

        return card

    def _update_layout_selection(self, layout_id: str) -> None:
        self._selected_layout_id = layout_id
        layout = LAYOUT_BY_ID[layout_id]

        for lid, card in self._layout_cards.items():
            card.configure(border_color=PURPLE if lid == layout_id else BORDER)

        self.confirm_pick_btn.configure(state=self._confirm_btn_state())
        self._draw_canvas_state()

    def _confirm_btn_state(self) -> str:
        layout = LAYOUT_BY_ID.get(self._selected_layout_id, LAYOUT_BY_ID["stacked"])
        if not layout.has_webcam:
            return "normal"
        return "normal" if self._pick_x is not None else "disabled"

    # ── Helpers ───────────────────────────────────────────────────────────

    def _size_text(self) -> str:
        return f"Webcam crop:  {self._pick_rect_w} × {self._pick_rect_h} px"

    def _rect_center_canvas(self) -> tuple[float, float]:
        ox, oy = self._pick_img_offset
        s = self._pick_scale
        return (
            ox + (self._pick_x + self._pick_rect_w / 2) * s,
            oy + (self._pick_y + self._pick_rect_h / 2) * s,
        )

    def _get_handle_at(self, cx: float, cy: float) -> str | None:
        if self._pick_x is None:
            return None
        ccx, ccy = self._rect_center_canvas()
        s = self._pick_scale
        hw = self._pick_rect_w * s / 2
        hh = self._pick_rect_h * s / 2
        corners = {
            "tl": (ccx - hw, ccy - hh),
            "tr": (ccx + hw, ccy - hh),
            "bl": (ccx - hw, ccy + hh),
            "br": (ccx + hw, ccy + hh),
        }
        thresh = HANDLE_RADIUS + 3
        for name, (hx, hy) in corners.items():
            if abs(cx - hx) <= thresh and abs(cy - hy) <= thresh:
                return name
        return None

    # ── Canvas drawing ────────────────────────────────────────────────────

    def _draw_pick_image(self) -> None:
        try:
            img = Image.open(self._pick_thumb_path)
            if img.size != (1920, 1080):
                img = img.resize((1920, 1080), Image.LANCZOS)

            cw = self.pick_canvas.winfo_width()
            ch = self.pick_canvas.winfo_height()
            if cw < 10 or ch < 10:
                return

            scale = min(cw / 1920, ch / 1080)
            self._pick_scale = scale
            dw, dh = int(1920 * scale), int(1080 * scale)

            self._pick_pil_img = img.resize((dw, dh), Image.LANCZOS)
            self._pick_img_ref = ImageTk.PhotoImage(self._pick_pil_img)

            ox = (cw - dw) // 2
            oy = (ch - dh) // 2
            self._pick_img_offset = (ox, oy)

            self.pick_canvas.delete("all")
            self.pick_canvas.create_image(ox, oy, anchor="nw", image=self._pick_img_ref)
            self._draw_canvas_state()
        except Exception as exc:
            print(f"[picker] image load error: {exc}")

    def _draw_canvas_state(self) -> None:
        """Draw the current overlay on the canvas based on layout and pick state."""
        if self._pick_pil_img is None:
            return
        layout = LAYOUT_BY_ID.get(self._selected_layout_id, LAYOUT_BY_ID["stacked"])
        self.pick_canvas.delete("rect")

        if not layout.has_webcam:
            cw = self.pick_canvas.winfo_width()
            ch = self.pick_canvas.winfo_height()
            self.pick_canvas.create_text(
                cw // 2, ch // 2,
                text="No webcam needed\nfor this layout",
                fill=TEXT_MUTED, font=("Courier", 13, "bold"),
                justify="center", tags="rect",
            )
        elif self._pick_x is not None:
            self._draw_confirmed_rect()

    def _canvas_to_full(self, cx: float, cy: float) -> tuple[int, int]:
        ox, oy = self._pick_img_offset
        s = self._pick_scale
        x = max(0, min(int((cx - ox) / s) - self._pick_rect_w // 2, 1920 - self._pick_rect_w))
        y = max(0, min(int((cy - oy) / s) - self._pick_rect_h // 2, 1080 - self._pick_rect_h))
        return x, y

    def _draw_hover_rect(self, cx: float, cy: float) -> None:
        s = self._pick_scale
        rw, rh = self._pick_rect_w * s, self._pick_rect_h * s
        x1, y1 = cx - rw / 2, cy - rh / 2
        x2, y2 = cx + rw / 2, cy + rh / 2
        self.pick_canvas.delete("rect")
        self.pick_canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="#ff4444", width=2, dash=(5, 4), tags="rect",
        )
        self.pick_canvas.create_text(
            cx, y1 - 10, text="Webcam Region",
            fill="#ff4444", font=("Courier", 10, "bold"), tags="rect",
        )

    def _draw_confirmed_rect(self) -> None:
        ccx, ccy = self._rect_center_canvas()
        s = self._pick_scale
        rw, rh = self._pick_rect_w * s, self._pick_rect_h * s
        x1, y1 = ccx - rw / 2, ccy - rh / 2
        x2, y2 = ccx + rw / 2, ccy + rh / 2

        self.pick_canvas.delete("rect")
        self.pick_canvas.create_rectangle(
            x1, y1, x2, y2, outline=GREEN, width=2, tags="rect",
        )
        self.pick_canvas.create_text(
            ccx, y1 - 10, text="✓ Webcam Region",
            fill=GREEN, font=("Courier", 10, "bold"), tags="rect",
        )
        for hx, hy in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
            self.pick_canvas.create_rectangle(
                hx - HANDLE_RADIUS, hy - HANDLE_RADIUS,
                hx + HANDLE_RADIUS, hy + HANDLE_RADIUS,
                fill=GREEN, outline="#ffffff", width=1, tags="rect",
            )

    # ── Canvas events ─────────────────────────────────────────────────────

    def _on_canvas_motion(self, event: tk.Event) -> None:
        if self._pick_pil_img is None:
            return
        layout = LAYOUT_BY_ID.get(self._selected_layout_id, LAYOUT_BY_ID["stacked"])
        if not layout.has_webcam:
            return

        self._hover_cx, self._hover_cy = event.x, event.y
        handle = self._get_handle_at(event.x, event.y)
        self.pick_canvas.config(cursor="sizing" if handle else "crosshair")

        if self._pick_x is not None:
            self._draw_confirmed_rect()
        else:
            self._draw_hover_rect(event.x, event.y)

    def _on_canvas_leave(self, _event: tk.Event) -> None:
        self._hover_cx = self._hover_cy = None
        if self._pick_x is None:
            self.pick_canvas.delete("rect")

    def _on_canvas_press(self, event: tk.Event) -> None:
        if self._pick_pil_img is None:
            return
        layout = LAYOUT_BY_ID.get(self._selected_layout_id, LAYOUT_BY_ID["stacked"])
        if not layout.has_webcam:
            return

        handle = self._get_handle_at(event.x, event.y)
        if handle and self._pick_x is not None:
            self._dragging_handle = handle
            self._drag_center_full = (
                self._pick_x + self._pick_rect_w / 2,
                self._pick_y + self._pick_rect_h / 2,
            )
        else:
            self._dragging_handle = None
            x, y = self._canvas_to_full(event.x, event.y)
            self._pick_x, self._pick_y = x, y
            self._draw_confirmed_rect()
            self.confirm_pick_btn.configure(state="normal")

    def _on_canvas_drag(self, event: tk.Event) -> None:
        if self._dragging_handle is None or self._pick_x is None:
            return

        ox, oy = self._pick_img_offset
        s = self._pick_scale
        cx_full, cy_full = self._drag_center_full

        mx_full = (event.x - ox) / s
        my_full = (event.y - oy) / s

        dx = abs(mx_full - cx_full)
        dy = abs(my_full - cy_full)
        new_half_w = max(dx, dy * self._aspect_ratio)
        new_w = max(MIN_W, int(new_half_w * 2))
        new_h = max(int(MIN_W / self._aspect_ratio), int(new_w / self._aspect_ratio))
        new_w = min(new_w, 1920)
        new_h = min(new_h, 1080)
        new_w = int(new_h * self._aspect_ratio)

        self._pick_rect_w = new_w
        self._pick_rect_h = new_h
        self._pick_x = max(0, min(int(cx_full - new_w / 2), 1920 - new_w))
        self._pick_y = max(0, min(int(cy_full - new_h / 2), 1080 - new_h))

        self._draw_confirmed_rect()
        if hasattr(self, "_size_label") and self._size_label.winfo_exists():
            self._size_label.configure(text=self._size_text())

    def _on_canvas_release(self, _event: tk.Event) -> None:
        self._dragging_handle = None

    # ── Navigation ────────────────────────────────────────────────────────

    def _confirm_pick(self) -> None:
        clip = self.clips_data[self.pick_index]
        clip.webcam_x = self._pick_x
        clip.webcam_y = self._pick_y
        clip.webcam_w = self._pick_rect_w
        clip.webcam_h = self._pick_rect_h
        clip.layout = self._selected_layout_id
        self.pick_index += 1
        self._load_pick_clip()

    def _skip_clip(self) -> None:
        self.clips_data.pop(self.pick_index)
        self._load_pick_clip()

    def _prev_clip(self) -> None:
        self.pick_index = max(0, self.pick_index - 1)
        self._load_pick_clip()


# ── Mini schematic renderer ────────────────────────────────────────────────────

def _draw_layout_preview(canvas: tk.Canvas, layout: Layout) -> None:
    W, H, PAD = 48, 76, 3
    IW, IH = W - 2 * PAD, H - 2 * PAD

    webcam_h = int(IH * 480 / 1280)
    gameplay_h = IH - webcam_h

    canvas.delete("all")
    canvas.create_rectangle(0, 0, W, H, fill=_CANVAS_BG, outline="")

    if layout.id in ("stacked", "stacked_clean"):
        canvas.create_rectangle(PAD, PAD, PAD + IW, PAD + webcam_h, fill=_WEBCAM_CLR, outline="")
        canvas.create_rectangle(PAD, PAD + webcam_h, PAD + IW, PAD + IH, fill=_GAMEPLAY_CLR, outline="")
    elif layout.id in ("webcam_bottom", "webcam_bottom_clean"):
        canvas.create_rectangle(PAD, PAD, PAD + IW, PAD + gameplay_h, fill=_GAMEPLAY_CLR, outline="")
        canvas.create_rectangle(PAD, PAD + gameplay_h, PAD + IW, PAD + IH, fill=_WEBCAM_CLR, outline="")
    else:  # gameplay_only
        canvas.create_rectangle(PAD, PAD, PAD + IW, PAD + IH, fill=_GAMEPLAY_CLR, outline="")

    # Green dot = overlay enabled
    if layout.has_overlay:
        canvas.create_oval(W - 11, H - 11, W - 4, H - 4, fill="#00e676", outline="")
