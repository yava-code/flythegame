"""right-side log of what this fly's own cells are doing"""
from __future__ import annotations

import pygame

from flygame import config as C


class FlyLog:
    def __init__(self):
        self.lines: list[tuple[str, tuple]] = []
        self.focus = 0
        self.lc4 = 0.0
        self.lplc2 = 0.0
        self.dnp01 = False
        self.state = "—"
        self.why = "quiet · no loom in RF"
        self.eta = 0.0

    def note(self, text: str, col=(220, 220, 210)):
        if self.lines and self.lines[-1][0] == text:
            return
        self.lines.append((text, col))
        self.lines = self.lines[-7:]

    def think(self, feat: dict, i4: float, il: float, state: str, armed: bool):
        self.lc4, self.lplc2 = i4, il
        self.eta = float(feat.get("eta", 0.0))
        self.dnp01 = armed or state == "dash"
        self.state = state
        cover = float(feat.get("cover", 0.0))
        if state == "dash":
            self.why = "DNp01 burst · takeoff away from loom"
        elif state == "freeze" and armed:
            self.why = "giant fiber armed · jump imminent"
        elif state == "freeze":
            self.why = "LC4/LPLC2 loom · freeze, waiting DNp01"
        elif cover < 0.08:
            self.why = "shadow outside RF · ignore"
        elif i4 + il < 0.04:
            self.why = "dθ/dt below LC4 knee · quiet"
        elif i4 >= il:
            self.why = f"LC4  η={self.eta:.2f}  angular vel"
        else:
            self.why = f"LPLC2  θ={feat['theta']:.2f}  size"

    def draw(self, surf: pygame.Surface, font, font_sm, t_fn):
        pad = int(14 * C.SCALE)
        box_w = min(460, int(C.W * 0.30))
        x = C.W - box_w - pad
        y = pad
        h = int(320 * C.SCALE)
        box = pygame.Surface((box_w, h), pygame.SRCALPHA)
        box.fill((8, 14, 28, 210))
        surf.blit(box, (x, y))
        title = t_fn(font, f"fly {self.focus + 1}  ·  {self.state}", (255, 230, 160))
        surf.blit(title, (x + 12, y + 8))

        def bar(label, v, yy, col):
            surf.blit(t_fn(font_sm, label, (180, 190, 210)), (x + 12, yy))
            bw = box_w - 24
            pygame.draw.rect(surf, (20, 32, 58), (x + 12, yy + 20, bw, 11))
            fw = int(bw * min(1.0, max(0.0, v)))
            if fw > 0:
                pygame.draw.rect(surf, col, (x + 12, yy + 20, fw, 11))

        bar("LC4  dθ/dt", self.lc4, y + 44, (120, 200, 255))
        bar("LPLC2  size", self.lplc2, y + 84, (255, 180, 90))
        dcol = (255, 90, 70) if self.dnp01 else (80, 90, 110)
        surf.blit(t_fn(font_sm, "DNp01  giant fiber", dcol), (x + 12, y + 124))
        surf.blit(
            t_fn(font_sm, "BURST" if self.dnp01 else "silent", dcol),
            (x + 12, y + 144),
        )
        why = t_fn(font_sm, self.why, (210, 220, 200))
        surf.blit(why, (x + 12, y + 168))

        yy = y + 196
        for line, col in self.lines[-5:]:
            surf.blit(t_fn(font_sm, line, col), (x + 12, yy))
            yy += int(20 * C.SCALE)
