from config import (
    WEBCAM_PANEL_W, WEBCAM_PANEL_H,
    GAMEPLAY_CROP_W, GAMEPLAY_CROP_H,
    GAMEPLAY_ONLY_CROP_W, GAMEPLAY_ONLY_CROP_H,
    OUTPUT_W, OUTPUT_H,
    OVERLAY_LOGO_W, OVERLAY_LOGO_H,
    OVERLAY_LOGO_X, OVERLAY_LOGO_Y,
    OVERLAY_NAME_X, OVERLAY_NAME_Y, OVERLAY_FONT_SIZE,
    BUILD_VIDEOS_DIR, BUILD_OUTPUT_DIR,
    FONT_PATH, LOGO_PATH,
)
from src.models import ClipConfig
from src.layouts import LAYOUT_BY_ID


def crearComandoShort(clip: ClipConfig) -> str:
    layout = LAYOUT_BY_ID.get(clip.layout, LAYOUT_BY_ID["stacked"])

    if not layout.has_webcam:
        return _gameplay_only(clip)
    if clip.layout in ("stacked", "stacked_clean"):
        return _stacked(clip, overlay=layout.has_overlay)
    return _webcam_bottom(clip, overlay=layout.has_overlay)


def tmp_files_for(clip: ClipConfig) -> list[str]:
    """Intermediate files written during processing. Empty for gameplay_only."""
    layout = LAYOUT_BY_ID.get(clip.layout, LAYOUT_BY_ID["stacked"])
    if not layout.has_webcam:
        return []
    base = clip.video.replace(".mp4", "")
    return [f"tmp_top_{base}.mp4", f"tmp_bot_{base}.mp4"]


# ── Layout builders ────────────────────────────────────────────────────────────

def _overlay_filter(clip: ClipConfig, join_y: int) -> str:
    # OVERLAY_LOGO_Y / OVERLAY_NAME_Y are calibrated for a join at WEBCAM_PANEL_H.
    # Compute the equivalent distance above whatever join_y is passed in.
    logo_y = join_y - (WEBCAM_PANEL_H - OVERLAY_LOGO_Y)
    name_y = join_y - (WEBCAM_PANEL_H - OVERLAY_NAME_Y)
    return (
        f'[2:v]scale={OVERLAY_LOGO_W}:{OVERLAY_LOGO_H}[logo]; '
        f'[video][logo]overlay={OVERLAY_LOGO_X}:{logo_y},'
        f'drawtext=text=\'{clip.name}\''
        f':fontfile={FONT_PATH}:x={OVERLAY_NAME_X}:y={name_y}'
        f':fontsize={OVERLAY_FONT_SIZE}:fontcolor=white'
    )


def _stacked(clip: ClipConfig, overlay: bool) -> str:
    """Webcam on top, gameplay on bottom."""
    top_tmp, bot_tmp = tmp_files_for(clip)
    webcam_cmd = (
        f'ffmpeg -y -i {BUILD_VIDEOS_DIR}/{clip.video} '
        f'-vf "scale=1920:1080,crop={clip.webcam_w}:{clip.webcam_h}:{clip.webcam_x}:{clip.webcam_y},'
        f'scale={WEBCAM_PANEL_W}:{WEBCAM_PANEL_H}" {top_tmp}'
    )
    gameplay_cmd = (
        f'ffmpeg -y -i {BUILD_VIDEOS_DIR}/{clip.video} '
        f'-vf "scale=1920:1080,crop={GAMEPLAY_CROP_W}:{GAMEPLAY_CROP_H}:(in_w-{GAMEPLAY_CROP_W})/2:(in_h-{GAMEPLAY_CROP_H})" {bot_tmp}'
    )

    if overlay:
        compose_cmd = (
            f'ffmpeg -y -i {bot_tmp} -i {top_tmp} -i {LOGO_PATH} '
            f'-filter_complex "[1:v][0:v]vstack=inputs=2[video]; {_overlay_filter(clip, join_y=WEBCAM_PANEL_H)}" '
            f'-s {OUTPUT_W}x{OUTPUT_H} {BUILD_OUTPUT_DIR}/{clip.video}'
        )
    else:
        compose_cmd = (
            f'ffmpeg -y -i {bot_tmp} -i {top_tmp} '
            f'-filter_complex "[1:v][0:v]vstack=inputs=2" '
            f'-s {OUTPUT_W}x{OUTPUT_H} {BUILD_OUTPUT_DIR}/{clip.video}'
        )

    return f'{webcam_cmd} && {gameplay_cmd} && {compose_cmd}'


def _webcam_bottom(clip: ClipConfig, overlay: bool) -> str:
    """Gameplay on top, webcam on bottom."""
    top_tmp, bot_tmp = tmp_files_for(clip)
    gameplay_cmd = (
        f'ffmpeg -y -i {BUILD_VIDEOS_DIR}/{clip.video} '
        f'-vf "scale=1920:1080,crop={GAMEPLAY_CROP_W}:{GAMEPLAY_CROP_H}:(in_w-{GAMEPLAY_CROP_W})/2:(in_h-{GAMEPLAY_CROP_H})" {top_tmp}'
    )
    webcam_cmd = (
        f'ffmpeg -y -i {BUILD_VIDEOS_DIR}/{clip.video} '
        f'-vf "scale=1920:1080,crop={clip.webcam_w}:{clip.webcam_h}:{clip.webcam_x}:{clip.webcam_y},'
        f'scale={WEBCAM_PANEL_W}:{WEBCAM_PANEL_H}" {bot_tmp}'
    )

    if overlay:
        compose_cmd = (
            f'ffmpeg -y -i {top_tmp} -i {bot_tmp} -i {LOGO_PATH} '
            f'-filter_complex "[0:v][1:v]vstack=inputs=2[video]; {_overlay_filter(clip, join_y=GAMEPLAY_CROP_H)}" '
            f'-s {OUTPUT_W}x{OUTPUT_H} {BUILD_OUTPUT_DIR}/{clip.video}'
        )
    else:
        compose_cmd = (
            f'ffmpeg -y -i {top_tmp} -i {bot_tmp} '
            f'-filter_complex "[0:v][1:v]vstack=inputs=2" '
            f'-s {OUTPUT_W}x{OUTPUT_H} {BUILD_OUTPUT_DIR}/{clip.video}'
        )

    return f'{gameplay_cmd} && {webcam_cmd} && {compose_cmd}'


def _gameplay_only(clip: ClipConfig) -> str:
    """Centre-crop to 9:16, no webcam."""
    return (
        f'ffmpeg -y -i {BUILD_VIDEOS_DIR}/{clip.video} '
        f'-vf "scale=1920:1080,'
        f'crop={GAMEPLAY_ONLY_CROP_W}:{GAMEPLAY_ONLY_CROP_H}:(in_w-{GAMEPLAY_ONLY_CROP_W})/2:0,'
        f'scale={OUTPUT_W}:{OUTPUT_H}" '
        f'{BUILD_OUTPUT_DIR}/{clip.video}'
    )
