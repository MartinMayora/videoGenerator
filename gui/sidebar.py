import requests
import customtkinter as ctk
from .constants import (
    PURPLE, PURPLE_DIM, BG_PANEL, TEXT_MUTED, GREEN, RED, BORDER,
)
from .widgets import SearchableDropdown


class SidebarMixin:
    """Builds the left sidebar and manages the category dropdown."""

    def _build_sidebar(self):
        s = self.sidebar

        # ── BOTTOM section — packed FIRST so it's always anchored ─────────
        bottom = ctk.CTkFrame(s, fg_color="transparent")
        bottom.pack(side="bottom", fill="x")

        self.fetch_btn = ctk.CTkButton(
            bottom,
            text="FETCH  &  PROCESS",
            height=46,
            font=ctk.CTkFont(family="Courier", size=13, weight="bold"),
            fg_color=PURPLE,
            hover_color=PURPLE_DIM,
            corner_radius=6,
            command=self._start_fetch,
        )
        self.fetch_btn.pack(padx=16, pady=(0, 20), fill="x")

        ctk.CTkFrame(bottom, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=8)

        api_ok = bool(self._client_id and self._client_secret)
        status_row = ctk.CTkFrame(bottom, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(
            status_row, text="●",
            font=ctk.CTkFont(size=10),
            text_color=GREEN if api_ok else RED,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            status_row,
            text="API keys loaded" if api_ok else "Missing .env keys",
            font=ctk.CTkFont(size=11),
            text_color=GREEN if api_ok else RED,
        ).pack(side="left")

        # ── TOP section ───────────────────────────────────────────────────

        # Brand header
        hdr = ctk.CTkFrame(s, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(26, 16))
        ctk.CTkLabel(
            hdr, text="⬡",
            font=ctk.CTkFont(size=36), text_color=PURPLE,
        ).pack(side="left", padx=(0, 10))
        name_box = ctk.CTkFrame(hdr, fg_color="transparent")
        name_box.pack(side="left")
        ctk.CTkLabel(
            name_box, text="SHORTS",
            font=ctk.CTkFont(family="Courier", size=17, weight="bold"),
            text_color="#ffffff",
        ).pack(anchor="w")
        ctk.CTkLabel(
            name_box, text="generator",
            font=ctk.CTkFont(family="Courier", size=11), text_color=TEXT_MUTED,
        ).pack(anchor="w")

        self._divider(s)

        # Mode toggle
        self._section_label(s, "SOURCE")
        self.mode_var = ctk.StringVar(value="Category")
        ctk.CTkSegmentedButton(
            s,
            values=["Category", "Creator"],
            variable=self.mode_var,
            command=self._on_mode_change,
            fg_color=BG_PANEL,
            selected_color=PURPLE,
            selected_hover_color=PURPLE_DIM,
            unselected_color=BG_PANEL,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(padx=16, fill="x")

        # Dynamic inputs container
        self.inputs_container = ctk.CTkFrame(s, fg_color="transparent")
        self.inputs_container.pack(fill="x")

        # Category sub-frame
        self.cat_frame = ctk.CTkFrame(self.inputs_container, fg_color="transparent")
        self.cat_frame.pack(fill="x", padx=16, pady=(10, 0))
        self._field_label(self.cat_frame, "Category")
        self.cat_dropdown = SearchableDropdown(
            self.cat_frame,
            values=[],
            placeholder="Search or type a category…",
        )
        self.cat_dropdown.pack(fill="x")
        self._field_label(self.cat_frame, "Month / Year")
        self.date_entry = self._entry(self.cat_frame, "MM/YYYY")

        # Creator sub-frame (hidden initially)
        self.cre_frame = ctk.CTkFrame(self.inputs_container, fg_color="transparent")
        self._field_label(self.cre_frame, "Creator Username")
        self.cre_entry = self._entry(self.cre_frame, "e.g.  xQc")

        # Amount
        amt = ctk.CTkFrame(s, fg_color="transparent")
        amt.pack(fill="x", padx=16, pady=(14, 0))
        self._field_label(amt, "Number of Clips")
        self.amount_entry = self._entry(amt, "e.g.  5")

        # Language
        lang = ctk.CTkFrame(s, fg_color="transparent")
        lang.pack(fill="x", padx=16, pady=(14, 0))
        self._field_label(lang, "Language Filter")
        self.lang_var = ctk.StringVar(value="none")
        ctk.CTkOptionMenu(
            lang,
            values=["none", "english", "spanish"],
            variable=self.lang_var,
            fg_color=BG_PANEL,
            button_color=PURPLE,
            button_hover_color=PURPLE_DIM,
            font=ctk.CTkFont(size=13),
        ).pack(fill="x", pady=(4, 0))

    def _on_mode_change(self, value):
        if value == "Category":
            self.cre_frame.pack_forget()
            self.cat_frame.pack(fill="x", padx=16, pady=(10, 0))
        else:
            self.cat_frame.pack_forget()
            self.cre_frame.pack(fill="x", padx=16, pady=(10, 0))

    def _fetch_categories_bg(self):
        """Fetch top 50 Twitch categories and populate the dropdown."""
        try:
            from src.conseguirVideos import get_access_token
            token = get_access_token(self._client_id, self._client_secret)
            if not token:
                return
            resp = requests.get(
                "https://api.twitch.tv/helix/games/top",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Client-Id": self._client_id,
                },
                params={"first": 50},
                timeout=10,
            )
            names = [g["name"] for g in resp.json().get("data", [])]
            if names:
                self._all_categories = names
                self.after(0, lambda: self.cat_dropdown.set_values(names))
        except Exception as exc:
            print(f"[categories] {exc}")
