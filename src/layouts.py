from dataclasses import dataclass


@dataclass(frozen=True)
class Layout:
    id: str
    name: str
    description: str
    has_webcam: bool
    has_overlay: bool


LAYOUTS: list[Layout] = [
    Layout(
        id="stacked",
        name="Stacked",
        description="Webcam top\nGameplay bottom\nLogo & name",
        has_webcam=True,
        has_overlay=True,
    ),
    Layout(
        id="stacked_clean",
        name="Stacked Clean",
        description="Webcam top\nGameplay bottom\nNo overlay",
        has_webcam=True,
        has_overlay=False,
    ),
    Layout(
        id="webcam_bottom",
        name="Webcam Bottom",
        description="Gameplay top\nWebcam bottom\nLogo & name",
        has_webcam=True,
        has_overlay=True,
    ),
    Layout(
        id="webcam_bottom_clean",
        name="Webcam Bottom Clean",
        description="Gameplay top\nWebcam bottom\nNo overlay",
        has_webcam=True,
        has_overlay=False,
    ),
    Layout(
        id="gameplay_only",
        name="Gameplay Only",
        description="Full-width gameplay\nNo webcam",
        has_webcam=False,
        has_overlay=False,
    ),
]

LAYOUT_BY_ID: dict[str, Layout] = {layout.id: layout for layout in LAYOUTS}
