"""constants + paths. pixel sizes get rescaled to the actual monitor in apply_display()."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

os.environ.setdefault("FLY_DATA", str(ROOT / "fly-data"))

BASE_W, BASE_H = 1920, 1080
W, H = BASE_W, BASE_H
SCALE = 1.0
FPS = 60
DT = 1.0 / FPS

HAND_TAU = 0.028
Z_IDLE = 0.72
SWAT_T_MIN = 0.12
SWAT_T_PER_Z = 0.18
REST_ON_TABLE = 0.28
MISS_TIME = 0.28
RECOIL_TIME = 0.28
HIT_R = 48.0

HAND_SCALE_LOW = 1.05
HAND_SCALE_HIGH = 1.45
PALM_FRAC = 0.40
WRIST_CROP = 0.84

SHADOW_R_HIGH = 64.0
SHADOW_R_LOW = 168.0
SHADOW_A_HIGH = 0.34
SHADOW_A_LOW = 0.78
SHADOW_OFF_X = 16.0
SHADOW_OFF_Y = 22.0
SHADOW_RGB = (12, 22, 48)

TABLE_L, TABLE_T = 280, 200
TABLE_R, TABLE_B = W - 280, H - 240

FLY_WALK_SPEED = (28.0, 52.0)
FLY_HOP_SPEED = (120.0, 180.0)
FLY_ESCAPE_SPEED = (420.0, 560.0)
FLY_DASH_DRAG = 5.0
FLY_SIZE = 56
FREEZE_TIME = 0.18

DTHETA_KNEE = 0.70
LC4_GAIN = 0.16
SIZE_GAIN = 0.72
RF_REACH = 2.4
INJECT_CAP = 1.2
FREEZE_THREAT = 0.16
STARTLE_ETA = 0.70
STARTLE_DTHETA = 0.55
STARTLE_COVER = 0.12

DNP01_WINDOW = 3
DNP01_BURST = 2

BRAIN_DT = 0.020
N_FLIES = 3

MUSIC_VOL = 0.14
SFX_VOL = 0.40

UI_FONT_SIZE = 32
UI_FONT_SM = 20
UI_FONT_LG = 48
BG = (28, 48, 92)
SKIN = (238, 194, 166)
SKIN_SHADE = (214, 164, 137)
INK = (26, 20, 34)
ROPE_N = 14


def dpi_aware():
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def desktop_size():
    dpi_aware()
    try:
        import ctypes
        w = int(ctypes.windll.user32.GetSystemMetrics(0))
        h = int(ctypes.windll.user32.GetSystemMetrics(1))
        if w >= 1024 and h >= 700:
            return w, h
    except Exception:
        pass
    return BASE_W, BASE_H


def apply_display(w: int, h: int):
    """fit every pixel size to the real window. call once after set_mode."""
    g = globals()
    g["W"], g["H"] = int(w), int(h)
    s = min(w / BASE_W, h / BASE_H)
    g["SCALE"] = s
    g["HIT_R"] = 48.0 * s
    g["SHADOW_R_HIGH"] = 64.0 * s
    g["SHADOW_R_LOW"] = 168.0 * s
    g["SHADOW_OFF_X"] = 16.0 * s
    g["SHADOW_OFF_Y"] = 22.0 * s
    g["TABLE_L"] = int(0.14 * w)
    g["TABLE_T"] = int(0.16 * h)
    g["TABLE_R"] = int(0.86 * w)
    g["TABLE_B"] = int(0.78 * h)
    g["FLY_WALK_SPEED"] = (28.0 * s, 52.0 * s)
    g["FLY_HOP_SPEED"] = (120.0 * s, 180.0 * s)
    g["FLY_ESCAPE_SPEED"] = (420.0 * s, 560.0 * s)
    g["FLY_SIZE"] = max(44, int(62 * s))
    g["HAND_SCALE_LOW"] = 1.05 * s
    g["HAND_SCALE_HIGH"] = 1.45 * s
    g["UI_FONT_SIZE"] = max(28, int(32 * s))
    g["UI_FONT_SM"] = max(16, int(18 * s))
    g["UI_FONT_LG"] = max(40, int(46 * s))
