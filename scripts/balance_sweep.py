"""how often does a swat land, over hit radius and how well you aimed"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from flygame import config as C  # noqa: E402
from flygame.brain_driver import BrainDriver  # noqa: E402
from flygame.fly_body import FlyBody  # noqa: E402
from flygame.hand import Hand  # noqa: E402
from flygame.shadow import Shadow  # noqa: E402

DT = 1 / 60


def trial(brain, start_z, off, hit_r):
    if brain.brain is not None:
        brain.brain.reset()
    brain._ring[:] = 0
    brain._accum = 0.0
    hand = Hand(480, 300)
    hand.z = start_z
    sh = Shadow(None)
    sh.sync(hand, DT)
    sh.sync(hand, DT)
    fly = FlyBody(480 + off, 300, {})

    for _ in range(int(0.5 / DT)):
        hand.update(DT)
        sh.sync(hand, DT)
        brain.step_all([sh.loom_features(fly.x, fly.y, DT)], DT, [0.0])

    fly.reset(480 + off, 300)
    fly.state, fly.timer = "sit", 99.0
    hand.start_swat()
    while hand.state == "swat":
        hand.update(DT)
        sh.sync(hand, DT)
        f = sh.loom_features(fly.x, fly.y, DT)
        if brain.step_all([f], DT, [0.0])[0]["escape"] and fly.state != "dash":
            fly.escape(f)
        fly.update(DT)
    return math.hypot(fly.x - hand.x, fly.y - hand.y) <= hit_r


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    brain = BrainDriver("real", 1)._loaded()
    n = 6
    print(f"swat length from z=0.85: {(C.SWAT_T_MIN + C.SWAT_T_PER_Z * 0.85) * 1000:.0f} ms")
    print("hit rate (higher = easier for the player)")
    print("  hit_r  off=0   off=20  off=40  off=60")
    for hit_r in (30, 40, 50, 60, 70):
        row = []
        for off in (0, 20, 40, 60):
            hits = sum(trial(brain, 0.85, off, hit_r) for _ in range(n))
            row.append(f"{hits}/{n}")
        print(f"  {hit_r:5d}  " + "   ".join(f"{c:6s}" for c in row))


if __name__ == "__main__":
    main()
