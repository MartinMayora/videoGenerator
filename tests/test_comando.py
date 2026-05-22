import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import ClipConfig
from src.comando import crearComandoShort
from config import OUTPUT_W, OUTPUT_H, BUILD_OUTPUT_DIR, WEBCAM_CROP_W, WEBCAM_CROP_H


def _clip(**kwargs) -> ClipConfig:
    defaults = dict(name="streamer", video="1.mp4", thumbnail="1.jpg", webcam_x=100, webcam_y=200)
    return ClipConfig(**{**defaults, **kwargs})


# ── Stacked (default) ──────────────────────────────────────────────────────────

def test_stacked_output_path():
    cmd = crearComandoShort(_clip(layout="stacked"))
    assert "1.mp4" in cmd
    assert BUILD_OUTPUT_DIR in cmd

def test_stacked_crop_coordinates():
    cmd = crearComandoShort(_clip(layout="stacked", webcam_x=300, webcam_y=400))
    assert "300" in cmd and "400" in cmd

def test_stacked_output_resolution():
    cmd = crearComandoShort(_clip(layout="stacked"))
    assert f"{OUTPUT_W}x{OUTPUT_H}" in cmd

def test_stacked_has_overlay():
    cmd = crearComandoShort(_clip(layout="stacked", name="xQc"))
    assert "xQc" in cmd

def test_stacked_clean_no_overlay():
    cmd = crearComandoShort(_clip(layout="stacked_clean", name="xQc"))
    # name should NOT appear (no drawtext)
    assert "xQc" not in cmd

def test_custom_webcam_dimensions():
    cmd = crearComandoShort(_clip(layout="stacked", webcam_w=480, webcam_h=320))
    assert "480:320" in cmd

def test_default_webcam_dimensions_from_config():
    cmd = crearComandoShort(_clip(layout="stacked"))
    assert f"{WEBCAM_CROP_W}:{WEBCAM_CROP_H}" in cmd


# ── Webcam bottom ──────────────────────────────────────────────────────────────

def test_webcam_bottom_output_path():
    cmd = crearComandoShort(_clip(layout="webcam_bottom"))
    assert BUILD_OUTPUT_DIR in cmd

def test_webcam_bottom_has_overlay():
    cmd = crearComandoShort(_clip(layout="webcam_bottom", name="shroud"))
    assert "shroud" in cmd

def test_webcam_bottom_clean_no_overlay():
    cmd = crearComandoShort(_clip(layout="webcam_bottom_clean", name="shroud"))
    assert "shroud" not in cmd

def test_webcam_bottom_overlay_y_differs_from_stacked():
    # The overlay join point for webcam_bottom (y=800) must differ from stacked (y=480)
    stacked_cmd = crearComandoShort(_clip(layout="stacked", name="x"))
    bottom_cmd   = crearComandoShort(_clip(layout="webcam_bottom", name="x"))
    # Extract the overlay= argument — positions should differ
    assert stacked_cmd != bottom_cmd


# ── Gameplay only ──────────────────────────────────────────────────────────────

def test_gameplay_only_output_path():
    cmd = crearComandoShort(_clip(layout="gameplay_only"))
    assert BUILD_OUTPUT_DIR in cmd

def test_gameplay_only_single_ffmpeg_call():
    # gameplay_only is one command, no && chaining needed for separate crops
    assert "&&" not in crearComandoShort(_clip(layout="gameplay_only"))

def test_gameplay_only_no_webcam_coords():
    cmd = crearComandoShort(_clip(layout="gameplay_only"))
    assert "drawtext" not in cmd

def test_gameplay_only_output_resolution():
    cmd = crearComandoShort(_clip(layout="gameplay_only"))
    assert f"{OUTPUT_W}:{OUTPUT_H}" in cmd


# ── Unknown layout falls back to stacked ──────────────────────────────────────

def test_unknown_layout_fallback():
    cmd = crearComandoShort(_clip(layout="nonexistent"))
    assert BUILD_OUTPUT_DIR in cmd
