"""table, sprites, hand that actually reaches in from the bottom"""
from __future__ import annotations

from pathlib import Path

import pygame

from flygame import config as C


def load_image(path: Path) -> pygame.Surface | None:
    if not path.exists():
        return None
    return pygame.image.load(str(path)).convert_alpha()


def _crop_stub(spr: pygame.Surface) -> pygame.Surface:
    """sheet hands end in a square cut. drop that stub so the arm can join."""
    h = max(8, int(spr.get_height() * C.WRIST_CROP))
    return spr.subsurface((0, 0, spr.get_width(), h)).copy()


class Arena:
    def __init__(self):
        self._table_raw = load_image(C.ASSETS / "table.png")
        self.table = None
        self._hand_cache: dict[tuple[str, int], pygame.Surface] = {}
        self.refit()
        self.hand = {}
        for name in ("idle", "swat", "miss"):
            raw = load_image(C.ASSETS / "hand" / f"{name}.png")
            self.hand[name] = _crop_stub(raw) if raw is not None else None
        self.shadow_spr = load_image(C.ASSETS / "hand" / "shadow.png")
        self.fly = {
            name: load_image(C.ASSETS / "fly" / f"{name}.png")
            for name in ("idle", "fly0", "fly1", "dead")
        }

    def refit(self):
        if self._table_raw:
            self.table = pygame.transform.smoothscale(self._table_raw, (C.W, C.H))
        else:
            self.table = None
        self._hand_cache.clear()

    def draw_bg(self, surf: pygame.Surface):
        if self.table:
            surf.blit(self.table, (0, 0))
        else:
            surf.fill(C.BG)

    def _pose(self, hand) -> str:
        if hand.state == "swat":
            return "swat"
        if hand.state in ("miss", "recoil"):
            return "miss"
        return "idle"

    def _hand_img(self, pose: str, z: float) -> pygame.Surface | None:
        spr = self.hand.get(pose) or self.hand.get("idle")
        if spr is None:
            return None
        zq = int(max(0.0, min(1.0, z)) * 16)
        key = (pose, zq)
        img = self._hand_cache.get(key)
        if img is None:
            s = C.HAND_SCALE_LOW + (C.HAND_SCALE_HIGH - C.HAND_SCALE_LOW) * (zq / 16.0)
            img = pygame.transform.scale(
                spr, (max(1, int(spr.get_width() * s)), max(1, int(spr.get_height() * s)))
            )
            self._hand_cache[key] = img
        return img

    def hand_rect(self, hand) -> pygame.Rect:
        img = self._hand_img(self._pose(hand), hand.z)
        if img is None:
            return pygame.Rect(int(hand.x) - 40, int(hand.y) - 40, 80, 80)
        rect = img.get_rect()
        rect.centerx = int(hand.x)
        rect.top = int(hand.y - img.get_height() * C.PALM_FRAC)
        return rect

    def wrist_half(self, hand) -> float:
        img = self._hand_img(self._pose(hand), hand.z)
        if img is None:
            return 28.0 * C.SCALE
        return self._wrist_half(img)

    def _wrist_half(self, img: pygame.Surface) -> float:
        y = max(0, img.get_height() - 3)
        xs = [x for x in range(img.get_width()) if img.get_at((x, y))[3] > 40]
        if len(xs) < 2:
            return max(18.0, img.get_width() * 0.18)
        return max(18.0, (xs[-1] - xs[0]) * 0.50)

    def draw_hand(self, surf: pygame.Surface, hand):
        if hand.hide_sprite:
            return
        img = self._hand_img(self._pose(hand), hand.z)
        if img is None:
            pygame.draw.circle(surf, C.SKIN, (int(hand.x), int(hand.y)), 40)
            return
        surf.blit(img, self.hand_rect(hand))
