"""save a few frames to png so the scene can be eyeballed without playing"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from flygame import config as C  # noqa: E402
from flygame.main import Game  # noqa: E402

OUT = C.ROOT / "assets" / "_shots"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = Game(headless=True)
    g.flies[0].x, g.flies[0].y = 360, 250
    g.flies[1].x, g.flies[1].y = 620, 330
    g.flies[2].x, g.flies[2].y = g.crumb[0] + 8, g.crumb[1]
    g.flies[1].state = "hop"

    for name, z in (("high", 0.9), ("mid", 0.5), ("low", 0.08)):
        g.hand.x, g.hand.y = 480, 380
        g.hand.z = z
        g.shadow.sync(g.hand, C.DT)
        g.shadow.sync(g.hand, C.DT)
        g.draw()
        pygame.image.save(g.screen, str(OUT / f"{name}.png"))
        print("saved", name, f"shadow w={g.shadow.w:.0f} alpha={g.shadow.alpha:.2f}")

    g.hand.z = 0.8
    g.hand.start_swat()
    for _ in range(6):
        g.hand.update(C.DT)
        g.shadow.sync(g.hand, C.DT)
    g.draw()
    pygame.image.save(g.screen, str(OUT / "swat.png"))
    print("saved swat")


if __name__ == "__main__":
    main()
