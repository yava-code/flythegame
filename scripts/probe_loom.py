"""print what the loom encoder actually feeds the brain during a swat"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from flygame.brain_driver import BrainDriver  # noqa: E402
from flygame.hand import Hand  # noqa: E402
from flygame.shadow import Shadow  # noqa: E402

DT = 1 / 60


def run(start_z=0.85, fly_off=0.0):
    b = BrainDriver("real", 1)._loaded()
    h = Hand(480, 300)
    h.z = start_z
    sh = Shadow(None)
    sh.sync(h, DT)
    sh.sync(h, DT)
    fx, fy = 480 + fly_off, 300
    for _ in range(30):
        h.update(DT)
        sh.sync(h, DT)
        b.step_all([sh.loom_features(fx, fy, DT)], DT, [0.0])

    print(f"--- slam from z={start_z}, fly offset {fly_off}px, fall {h.z:.2f} ---")
    h.start_swat()
    print(f"swat length {h.swat_len * 1000:.0f} ms")
    for i in range(16):
        h.update(DT)
        sh.sync(h, DT)
        f = sh.loom_features(fx, fy, DT)
        i4, il = b._feat_currents(f, 0.0, 1.0)
        o = b.step_all([f], DT, [0.0])[0]
        print(
            f"{i * DT * 1000:5.0f}ms z={h.z:.3f} th={f['theta']:.2f} "
            f"dth={f['dtheta']:6.2f} alpha={f['alpha']:.2f} dist={f['dist']:5.1f} "
            f"LC4={i4:.3f} LPLC2={il:.3f} burst={int(b._ring.sum())} esc={o['escape']}"
        )


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((64, 64))
    run(0.85)
    run(0.30)
