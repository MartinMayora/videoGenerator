import customtkinter as ctk
from ..constants import PURPLE, BG_CARD, TEXT_MUTED


class WelcomeMixin:

    def _show_welcome(self):
        self._clear_main()
        center = ctk.CTkFrame(self.main, fg_color="transparent")
        center.place(relx=0.5, rely=0.48, anchor="center")

        ctk.CTkLabel(
            center, text="⬡",
            font=ctk.CTkFont(size=90), text_color=PURPLE,
        ).pack()

        ctk.CTkLabel(
            center,
            text="TWITCH SHORTS GENERATOR",
            font=ctk.CTkFont(family="Courier", size=22, weight="bold"),
            text_color="#ffffff",
        ).pack(pady=(8, 4))

        ctk.CTkLabel(
            center,
            text="configure settings on the left  ·  click Fetch & Process to begin",
            font=ctk.CTkFont(size=13), text_color=TEXT_MUTED,
        ).pack()

        pills = ctk.CTkFrame(center, fg_color="transparent")
        pills.pack(pady=28)
        for num, label in [
            ("01", "Pick source"),
            ("02", "Download clips"),
            ("03", "Mark webcam"),
            ("04", "Export shorts"),
        ]:
            pill = ctk.CTkFrame(pills, fg_color=BG_CARD, corner_radius=20)
            pill.pack(side="left", padx=6)
            ctk.CTkLabel(
                pill, text=num,
                font=ctk.CTkFont(family="Courier", size=11, weight="bold"),
                text_color=PURPLE,
            ).pack(side="left", padx=(14, 4), pady=8)
            ctk.CTkLabel(
                pill, text=label,
                font=ctk.CTkFont(size=11), text_color="#ffffff",
            ).pack(side="left", padx=(0, 14), pady=8)
