"""table shadow. the fly only sees this.

area is a smooth function of height. drawing can round pixels; the loom
features never do — stepped A was making eta spike and the flies panic.
"""
from __future__ import annotations

import math

import pygame

from flygame import config as C


class Shadow:
    def __init__(self, silhouette: pygame.Surface | None = None):
        self.sil = silhouette
        self.cx = 0.0
        self.cy = 0.0
        self.r = C.SHADOW_R_HIGH
        self.a = math.pi * self.r * self.r
        self.prev_a = self.a
        self.alpha = C.SHADOW_A_HIGH
        self.wrist_x = 0.0
        self._prev_theta: dict[int, float] = {}
        self._blob: dict[int, pygame.Surface] = {}

    def sync(self, hand, dt: float):
        z = max(0.0, min(1.0, hand.z))
        k = 1.0 - z
        self.r = C.SHADOW_R_HIGH + (C.SHADOW_R_LOW - C.SHADOW_R_HIGH) * k
        self.prev_a = self.a
        self.a = math.pi * self.r * self.r
        self.alpha = C.SHADOW_A_HIGH + (C.SHADOW_A_LOW - C.SHADOW_A_HIGH) * k
        self.cx = hand.x + z * C.SHADOW_OFF_X
        self.cy = hand.y + z * C.SHADOW_OFF_Y
        self.wrist_x = hand.x

    def loom_features(self, fx: float, fy: float, dt: float, key: int = 0) -> dict:
        dx = self.cx - fx
        dy = self.cy - fy
        dist = math.hypot(dx, dy) + 1e-3
        theta = 2.0 * math.atan2(self.r, dist)
        prev = self._prev_theta.get(key)
        dtheta = 0.0 if prev is None else (theta - prev) / max(dt, 1e-4)
        self._prev_theta[key] = theta
        eta = (self.a - self.prev_a) / max(dt, 1e-4) / max(self.a, 1.0)
        return {
            "theta": theta,
            "dtheta": dtheta,
            "eta": eta,
            "A": self.a,
            "cover": max(0.0, 1.0 - dist / (self.r + 40.0)),
            "side": "L" if dx < 0 else "R",
            "dx": dx,
            "dy": dy,
            "dist": dist,
            "r": self.r,
            "alpha": self.alpha,
        }

    def _disc(self, rad: int) -> pygame.Surface:
        img = self._blob.get(rad)
        if img is None:
            s = rad * 2 + 4
            img = pygame.Surface((s, s), pygame.SRCALPHA)
            pygame.draw.ellipse(img, (*C.SHADOW_RGB, 255), img.get_rect())
            self._blob[rad] = img
        return img

    def draw(self, surf: pygame.Surface):
        alpha = int(255 * self.alpha)
        rad = max(4, int(round(self.r)))
        left = int(min(self.cx - rad, self.wrist_x - rad * 0.35) - 2)
        top = int(self.cy - rad - 2)
        w = int(max(self.cx + rad, self.wrist_x + rad * 0.35) + 2) - left
        h = C.H + 8 - top
        if w < 2 or h < 2:
            return
        scratch = pygame.Surface((w, h), pygame.SRCALPHA)
        ox, oy = -left, -top
        # forearm band down to the bottom of the frame, same blob as the palm
        half = rad * 0.32
        pygame.draw.polygon(
            scratch,
            (*C.SHADOW_RGB, 255),
            [
                (self.cx - half + ox, self.cy + oy),
                (self.cx + half + ox, self.cy + oy),
                (self.wrist_x + half * 1.15 + ox, h),
                (self.wrist_x - half * 1.15 + ox, h),
            ],
        )
        disc = self._disc(rad)
        scratch.blit(disc, disc.get_rect(center=(int(self.cx + ox), int(self.cy + oy))))
        scratch.set_alpha(alpha)
        surf.blit(scratch, (left, top))
