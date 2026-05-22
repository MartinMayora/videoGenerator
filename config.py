"""Central configuration for all tuneable values."""

# Webcam crop region (pixels, full 1920x1080 space)
WEBCAM_CROP_W: int = 360
WEBCAM_CROP_H: int = 240

# Output video dimensions
OUTPUT_W: int = 720
OUTPUT_H: int = 1280

# Gameplay crop dimensions (bottom panel)
GAMEPLAY_CROP_W: int = 720
GAMEPLAY_CROP_H: int = 800

# Webcam panel scaled dimensions (top panel)
WEBCAM_PANEL_W: int = 720
WEBCAM_PANEL_H: int = 480

# Overlay
OVERLAY_LOGO_W: int = 86
OVERLAY_LOGO_H: int = 100
OVERLAY_LOGO_X: int = 100
OVERLAY_LOGO_Y: int = 430
OVERLAY_NAME_X: int = 200
OVERLAY_NAME_Y: int = 440
OVERLAY_FONT_SIZE: int = 60

# Gameplay-only crop (9:16 from 1920x1080, centred)
GAMEPLAY_ONLY_CROP_W: int = 608
GAMEPLAY_ONLY_CROP_H: int = 1080

# Build paths
BUILD_VIDEOS_DIR: str = "./build/videos"
BUILD_OUTPUT_DIR: str = "./build/output"
FONT_PATH: str = "./src/utils/TwitchyTV.ttf"
LOGO_PATH: str = "./src/utils/twitchLogo.png"
