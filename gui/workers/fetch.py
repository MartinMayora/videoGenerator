import os
import time
import threading
from tkinter import messagebox

from src.conseguirVideos import (
    get_access_token,
    get_category_id,
    get_creator_id,
    get_top_clips,
    get_top_clips_creator,
    download_clip,
)
from src.models import ClipConfig


class FetchMixin:
    """Handles clip fetching and downloading from Twitch."""

    def _start_fetch(self):
        if not self._client_id or not self._client_secret:
            messagebox.showerror(
                "Missing API Keys",
                "Create a .env file with:\n  twitch_client_id=…\n  twitch_client_secret=…",
            )
            return

        amount_str = self.amount_entry.get().strip()
        if not amount_str.isdigit() or int(amount_str) < 1:
            messagebox.showerror("Invalid Input", "Enter a valid number of clips (1 or more).")
            return

        mode = self.mode_var.get()
        if mode == "Category" and not self.cat_dropdown.get().strip():
            messagebox.showerror("Missing Input", "Enter or select a category name.")
            return
        if mode == "Creator" and not self.cre_entry.get().strip():
            messagebox.showerror("Missing Input", "Enter a creator username.")
            return

        self.fetch_btn.configure(state="disabled")
        self._show_progress_view()
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        try:
            os.makedirs("./build/videos", exist_ok=True)
            os.makedirs("./build/output", exist_ok=True)

            self._log("Getting Twitch access token…")
            token = get_access_token(self._client_id, self._client_secret)
            if not token:
                self._log("ERROR: Could not obtain access token. Check your credentials.")
                self.after(0, lambda: self.fetch_btn.configure(state="normal"))
                return

            amount   = int(self.amount_entry.get().strip())
            mode     = self.mode_var.get()
            language = self.lang_var.get()

            fetch_amount = amount * 3 if language != "none" else amount

            if mode == "Category":
                cat_name = self.cat_dropdown.get().strip()
                date_str = self.date_entry.get().strip() or "01/2024"
                self._log(f"Looking up category  '{cat_name}'…")
                cat_id = get_category_id(cat_name, self._client_id, token)
                if not cat_id:
                    self._log(f"ERROR: Category '{cat_name}' not found on Twitch.")
                    self.after(0, lambda: self.fetch_btn.configure(state="normal"))
                    return
                self._log(f"Fetching top clips  [{date_str}]…")
                all_clips = get_top_clips(cat_id, self._client_id, token, fetch_amount, date_str)
            else:
                creator = self.cre_entry.get().strip()
                self._log(f"Looking up creator  '{creator}'…")
                creator_id = get_creator_id(creator, self._client_id, token)
                if not creator_id:
                    self._log(f"ERROR: Creator '{creator}' not found on Twitch.")
                    self.after(0, lambda: self.fetch_btn.configure(state="normal"))
                    return
                self._log(f"Fetching top clips for  '{creator}'…")
                all_clips = get_top_clips_creator(creator_id, self._client_id, token, fetch_amount)

            if language != "none":
                lang_code = {"english": "en", "spanish": "es"}.get(language, language[:2])
                before = len(all_clips)
                all_clips = [c for c in all_clips if c.get("language", "").lower() == lang_code]
                self._log(f"Language filter ({language}): {before} → {len(all_clips)} clips")

            clips_to_dl = all_clips[:amount]
            self._log(f"\nFound {len(all_clips)} clip(s) — downloading {len(clips_to_dl)}…\n")

            self.clips_data = []

            for i, clip in enumerate(clips_to_dl, 1):
                self.after(0, lambda f=(i - 1) / len(clips_to_dl): self.progress_bar.set(f))
                self.after(
                    0,
                    lambda i=i, n=len(clips_to_dl):
                        self.status_label.configure(text=f"Downloading clip {i} of {n}…"),
                )
                self._log(f"[{i}/{len(clips_to_dl)}]  {clip.get('title', 'untitled')[:60]}")

                download_clip(clip, i)
                time.sleep(0.4)

                if os.path.exists(f"./build/videos/{i}.mp4") and \
                   os.path.exists(f"./build/videos/{i}.jpg"):
                    self.clips_data.append(ClipConfig(
                        name=clip["broadcaster_name"],
                        video=f"{i}.mp4",
                        thumbnail=f"{i}.jpg",
                    ))
                    self._log(f"  ✓  {i}.mp4")
                else:
                    self._log(f"  ✗  download failed for clip {i}")

            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.status_label.configure(text="All clips downloaded."))
            self._log(f"\n{len(self.clips_data)} clip(s) ready.  Moving to webcam picker…")

            if self.clips_data:
                self.after(800, self._show_pick_view)
            else:
                self._log("\nNo clips downloaded successfully. Check your inputs and try again.")
                self.after(0, lambda: self.fetch_btn.configure(state="normal"))

        except Exception as exc:
            import traceback
            self._log(f"\nFATAL ERROR: {exc}")
            self._log(traceback.format_exc())
            self.after(0, lambda: self.fetch_btn.configure(state="normal"))
