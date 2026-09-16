"""check loom encode + fly body without opening a window"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("FLY_DATA", os.path.join(os.path.dirname(__file__), "..", "fly-data"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame

pygame.init()
pygame.display.set_mode((64, 64))

from flygame import config as C
from flygame.brain_driver import BrainDriver
from flygame.fly_body import FlyBody
from flygame.hand import Hand
from flygame.shadow import Shadow


def _shadow_at(z, prev=None, x=None, y=None):
    h = Hand(x or C.W / 2, y or C.H / 2)
    h.z = z
    sh = prev or Shadow()
    sh.sync(h, 1 / 60)
    return sh


def test_shadow_continuous():
    sh = Shadow()
    areas = []
    for z in [1.0, 0.8, 0.6, 0.4, 0.2, 0.0]:
        sh = _shadow_at(z, sh)
        areas.append(sh.a)
    assert areas == sorted(areas), areas
    sh = _shadow_at(0.5)
    a0 = sh.a
    sh = _shadow_at(0.49, sh)
    rel = abs(sh.a - a0) / a0
    assert rel < 0.08, rel
    print("ok shadow continuous", [round(a) for a in areas])


def test_hover_quiet():
    brain = BrainDriver("real", 1)
    cx, cy = C.W / 2, C.H / 2
    sh = _shadow_at(0.85, x=cx, y=cy)
    sh = _shadow_at(0.85, sh, cx, cy)
    fly = FlyBody(cx, cy, {})
    esc = 0
    for _ in range(40):
        f = sh.loom_features(fly.x, fly.y, 1 / 60, 0)
        o = brain.step_all([f], 1 / 60, [0.0])[0]
        if o["escape"]:
            esc += 1
        fly.update(1 / 60)
    assert esc == 0, esc
    print("ok hover quiet", "eta", round(f["eta"], 4))


def test_slam_escape_away():
    brain = BrainDriver("real", 1)
    cx, cy = C.W / 2, C.H / 2
    sh = _shadow_at(0.9, x=cx, y=cy)
    fly = FlyBody(cx, cy, {})
    escaped = False
    feat = None
    for i in range(30):
        if i < 3:
            z = 0.9
        else:
            t = min(1.0, (i - 3) / 8)
            z = 0.9 * (1.0 - t ** 1.15)
        sh = _shadow_at(z, sh, cx, cy)
        feat = sh.loom_features(fly.x, fly.y, 1 / 60, 0)
        o = brain.step_all([feat], 1 / 60, [0.0])[0]
        if o["escape"] and fly.state != "dash":
            fly.escape(feat)
            escaped = True
            break
        fly.update(1 / 60)
    assert escaped, "slam did not trigger escape"
    assert feat["dx"] * fly.vx <= 0 or abs(fly.vx) < 1, (feat["dx"], fly.vx)
    assert feat["dy"] * fly.vy <= 0 or abs(fly.vy) < 1, (feat["dy"], fly.vy)
    print("ok slam escape", "eta", round(feat["eta"], 2), "speed", round(math.hypot(fly.vx, fly.vy)))


def test_stay_on_cloth():
    fly = FlyBody(C.W / 2, C.H / 2, {})
    for _ in range(600):
        fly.update(1 / 60)
        assert C.TABLE_L - 2 <= fly.x <= C.TABLE_R + 2, fly.x
        assert C.TABLE_T - 2 <= fly.y <= C.TABLE_B + 2, fly.y
    print("ok bounds", round(fly.x), round(fly.y), fly.state)


def test_stays_horizontal():
    fly = FlyBody(C.W / 2, C.H / 2, {})
    fly.state = "dash"
    fly.timer = 1
    fly.vx, fly.vy = 80, 40
    fly.update(1 / 60)
    img = fly._sprite("idle")
    # side-view: wider than tall, not a vertical stick
    if img is not None:
        assert img.get_width() >= img.get_height() * 0.7, img.get_size()
    print("ok horizontal sprite", None if img is None else img.get_size())


def test_swat_longer_than_gf():
    # drop from idle height must outlast a 50–150 ms giant-fiber window
    t = C.SWAT_T_MIN + C.SWAT_T_PER_Z * C.Z_IDLE
    assert t >= 0.20, t
    hi = C.SWAT_T_MIN + C.SWAT_T_PER_Z * 1.0
    assert hi > C.FREEZE_TIME + 0.04, (hi, C.FREEZE_TIME)
    print("ok swat duration", round(t, 3), "s  high", round(hi, 3))


def _feat(dx=40.0, dy=10.0):
    return {
        "dx": dx, "dy": dy, "eta": 2.0, "dtheta": 1.4, "cover": 0.8,
        "theta": 0.5, "A": 1000, "side": "L", "dist": 40, "r": 80, "alpha": 0.5,
    }


def test_freeze_then_dash():
    fly = FlyBody(C.W / 2, C.H / 2, {})
    feat = _feat()
    assert fly.freeze(feat)
    fly.arm_takeoff(feat)
    for _ in range(int(C.FREEZE_TIME * 60) + 4):
        fly.update(1 / 60)
    assert fly.state == "dash", fly.state
    print("ok freeze then dash", round(math.hypot(fly.vx, fly.vy)))


def test_freeze_no_gf_recovers():
    fly = FlyBody(C.W / 2, C.H / 2, {})
    fly.freeze(_feat())
    for _ in range(int(C.FREEZE_TIME * 60) + 4):
        fly.update(1 / 60)
    assert fly.state == "sit", fly.state
    print("ok freeze without DNp01 sits")


def test_miss_recoil():
    h = Hand(400, 400)
    h.x, h.y, h.z = 500, 420, 0.0
    h._home = (400, 400, 0.7)
    h.mark_miss()
    for _ in range(30):
        h.update(1 / 60)
    assert h.state == "idle", h.state
    assert abs(h.x - 400) < 2 and abs(h.y - 400) < 2
    print("ok recoil", round(h.x), round(h.z, 2))


if __name__ == "__main__":
    test_shadow_continuous()
    test_hover_quiet()
    test_slam_escape_away()
    test_stay_on_cloth()
    test_stays_horizontal()
    test_swat_longer_than_gf()
    test_freeze_then_dash()
    test_freeze_no_gf_recovers()
    test_miss_recoil()
    print("all fly checks passed")
