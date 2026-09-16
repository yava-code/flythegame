"""save a poster frame. this is the tweet still."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from flygame import config as C
from flygame.main import Game

OUT = C.ROOT / "assets" / "_shots"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = Game(fullscreen=False, headless=True)
    g.intro = 0.0
    g.coach_t = 4.0
    g.flies[0].x, g.flies[0].y = C.TABLE_L + 180, C.TABLE_T + 140
    g.flies[1].x, g.flies[1].y = C.W * 0.46, C.H * 0.52
    g.flies[2].x, g.flies[2].y = g.crumb[0] + 10, g.crumb[1]
    g.hand.x, g.hand.y = g.flies[1].x + 90, g.flies[1].y - 20
    g.hand.z = 0.38
    g.shadow.sync(g.hand, C.DT)
    g.shadow.sync(g.hand, C.DT)
    feat = g.shadow.loom_features(g.flies[1].x, g.flies[1].y, C.DT, 1)
    g.flies[1].freeze(feat)
    g.flies[1].arm_takeoff(feat)
    g.log.note("LC4/LPLC2 loom · freeze", (120, 200, 255))
    g.log.note("DNp01 burst queued", (255, 90, 70))
    g.log.think(feat, 0.7, 0.45, "freeze", True)
    g.log.focus = 1
    wrist = g.arena.hand_rect(g.hand)
    g.rope.pin((wrist.centerx, wrist.bottom - 6), C.DT, g.arena.wrist_half(g.hand))
    g.draw()
    pygame.image.save(g.screen, str(OUT / "poster.png"))
    print("saved poster", g.screen.get_size(), "shadow r", round(g.shadow.r), "alpha", round(g.shadow.alpha, 2))


if __name__ == "__main__":
    main()
