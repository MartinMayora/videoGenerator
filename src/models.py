from dataclasses import dataclass
from config import WEBCAM_CROP_W, WEBCAM_CROP_H


@dataclass
class ClipConfig:
    name: str
    video: str
    thumbnail: str
    layout: str = "stacked"
    webcam_x: int | None = None
    webcam_y: int | None = None
    webcam_w: int = WEBCAM_CROP_W
    webcam_h: int = WEBCAM_CROP_H
