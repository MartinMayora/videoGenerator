import os
import subprocess

import src.comando as comando
import src.cleanUp as cleanUp
from src.models import ClipConfig
from src.layouts import LAYOUT_BY_ID


def _is_ready(clip: ClipConfig) -> bool:
    layout = LAYOUT_BY_ID.get(clip.layout, LAYOUT_BY_ID["stacked"])
    if not layout.has_webcam:
        return True
    return clip.webcam_x is not None and clip.webcam_y is not None


class ProcessMixin:

    def _process_worker(self) -> None:
        valid = [c for c in self.clips_data if _is_ready(c)]

        if not valid:
            self._log("No clips ready to process.")
            self.after(0, self._show_done_view)
            return

        total = len(valid)
        self._log(f"Processing {total} clip(s)…")

        for i, clip in enumerate(valid, 1):
            tag = f"[{clip.name}]"
            self._log(f"\n═══  {tag}  ({clip.video})  ═══")

            cmd = comando.crearComandoShort(clip)
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd()
            )

            for path in comando.tmp_files_for(clip):
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass

            self.after(0, lambda f=i / total: self.proc_progress.set(f))
            self.after(0, lambda d=i, t=total: self.proc_status.configure(
                text=f"Processing…  {d} / {t} done",
            ))

            if result.returncode == 0:
                self._log(f"{tag}  ✓  ./build/output/{clip.video}")
            else:
                self._log(f"{tag}  ✗  FFmpeg error (exit {result.returncode})")
                err = (result.stderr or "")[-600:]
                if err:
                    self._log(err)

        self.after(0, lambda: self.proc_progress.set(1.0))
        self.after(0, lambda: self.proc_status.configure(text="Done!"))
        self._log("\n✓  All videos exported to  ./build/output/")

        try:
            cleanUp.clear_videos_folder()
            self._log("Temporary files cleaned up.")
        except Exception as exc:
            self._log(f"Cleanup warning: {exc}")

        self.after(600, self._show_done_view)
