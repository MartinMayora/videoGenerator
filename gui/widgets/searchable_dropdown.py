import tkinter as tk
import customtkinter as ctk

from ..constants import BG_CARD, BG_PANEL, PURPLE, BORDER


class SearchableDropdown(ctk.CTkFrame):
    """
    A text entry with a live-filtered dropdown popup.

    Usage:
        dd = SearchableDropdown(parent, values=["Just Chatting", ...], placeholder="Search…")
        dd.pack(fill="x")
        name = dd.get()
        dd.set("Just Chatting")
        dd.set_values(["a", "b", "c"])   # replace the full list at any time
    """

    _MAX_VISIBLE = 8   # items shown before scrolling kicks in
    _ITEM_H     = 32   # px per item row

    def __init__(self, master, values=None, placeholder="", font=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._all_values: list[str] = list(values or [])
        self._filtered:   list[str] = self._all_values[:]
        self._popup:      tk.Toplevel | None = None
        self._mouse_in_popup = False

        self._entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            fg_color=BG_PANEL,
            border_color="#3a3a45",
            border_width=1,
            corner_radius=6,
            font=font or ctk.CTkFont(size=13),
        )
        self._entry.pack(fill="x")

        self._entry.bind("<KeyRelease>", self._on_key)
        self._entry.bind("<FocusIn>",    self._on_focus_in)
        self._entry.bind("<FocusOut>",   self._on_focus_out)
        self._entry.bind("<Down>",       self._focus_first_item)
        self._entry.bind("<Escape>",     lambda _e: self._hide())
        self._entry.bind("<Return>",     self._on_enter)

        self.bind("<Destroy>", lambda _e: self._destroy_popup())

    # ── Public API ────────────────────────────────────────────────────────

    def get(self) -> str:
        return self._entry.get()

    def set(self, value: str):
        self._entry.delete(0, "end")
        self._entry.insert(0, value)

    def set_values(self, values: list[str]):
        self._all_values = list(values)
        if self._popup and self._popup.winfo_exists():
            self._on_key()

    # ── Internal events ───────────────────────────────────────────────────

    def _on_key(self, _event=None):
        typed = self._entry.get().strip().lower()
        self._filtered = (
            [v for v in self._all_values if typed in v.lower()]
            if typed else self._all_values[:]
        )
        if self._filtered:
            self._show()
        else:
            self._hide()

    def _on_focus_in(self, _event=None):
        # Show full list when entry is clicked with no text
        if not self._entry.get().strip() and self._all_values:
            self._filtered = self._all_values[:]
            self._show()

    def _on_focus_out(self, _event=None):
        # Delay so a click inside the popup registers before we hide it
        self.after(180, self._maybe_hide)

    def _maybe_hide(self):
        if not self._mouse_in_popup:
            self._hide()

    def _on_enter(self, _event=None):
        if self._filtered:
            self._select(self._filtered[0])

    # ── Popup lifecycle ───────────────────────────────────────────────────

    def _show(self):
        if self._popup is None or not self._popup.winfo_exists():
            self._build_popup()
        self._populate()
        self._reposition()
        self._popup.deiconify()
        self._popup.lift()

    def _hide(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.withdraw()

    def _destroy_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()

    def _build_popup(self):
        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.configure(bg=BORDER)   # 1px border colour
        self._popup.withdraw()

        self._popup.bind("<Enter>", lambda _e: setattr(self, "_mouse_in_popup", True))
        self._popup.bind("<Leave>", lambda _e: setattr(self, "_mouse_in_popup", False))

        # Inner scrollable list
        self._list = ctk.CTkScrollableFrame(
            self._popup,
            fg_color=BG_CARD,
            corner_radius=6,
            scrollbar_button_color="#3a3a45",
            scrollbar_button_hover_color=PURPLE,
        )
        self._list.pack(fill="both", expand=True, padx=1, pady=1)

    def _populate(self):
        for w in self._list.winfo_children():
            w.destroy()

        for value in self._filtered[:40]:
            btn = ctk.CTkButton(
                self._list,
                text=value,
                anchor="w",
                height=self._ITEM_H,
                fg_color="transparent",
                hover_color=BG_PANEL,
                text_color="#ffffff",
                font=ctk.CTkFont(size=13),
                corner_radius=4,
                command=lambda v=value: self._select(v),
            )
            btn.pack(fill="x", padx=4, pady=1)
            btn.bind("<Up>",     self._nav_up)
            btn.bind("<Down>",   self._nav_down)
            btn.bind("<Return>", lambda _e, v=value: self._select(v))
            btn.bind("<Escape>", lambda _e: self._hide())

    def _reposition(self):
        self.update_idletasks()

        entry_x = self._entry.winfo_rootx()
        entry_y = self._entry.winfo_rooty()
        entry_w = self._entry.winfo_width()
        entry_h = self._entry.winfo_height()

        n_items  = min(len(self._filtered), self._MAX_VISIBLE)
        popup_h  = n_items * (self._ITEM_H + 2) + 16   # item rows + padding
        popup_y  = entry_y + entry_h + 2

        self._popup.geometry(f"{entry_w}x{popup_h}+{entry_x}+{popup_y}")

    # ── Selection ─────────────────────────────────────────────────────────

    def _select(self, value: str):
        self.set(value)
        self._mouse_in_popup = False
        self._hide()
        self._entry.focus_set()

    # ── Keyboard navigation inside the list ──────────────────────────────

    def _focus_first_item(self, _event=None):
        if self._popup and self._popup.winfo_exists():
            items = self._list.winfo_children()
            if items:
                items[0].focus_set()

    def _nav_up(self, event):
        items = self._list.winfo_children()
        try:
            idx = items.index(event.widget)
        except ValueError:
            return
        if idx > 0:
            items[idx - 1].focus_set()
        else:
            self._entry.focus_set()

    def _nav_down(self, event):
        items = self._list.winfo_children()
        try:
            idx = items.index(event.widget)
        except ValueError:
            return
        if idx < len(items) - 1:
            items[idx + 1].focus_set()
