"""screen shake + dust puffs"""
from __future__ import annotations

import math
import random

import pygame

from flygame import config as C


class Dust:
    def __init__(self):
        self.bits: list[list] = []  # x y vx vy life max r
        self.shake_t = 0.0
        self.shake_mag = 0.0

    def bang(self, x: float, y: float, n: int = 18, shake: float = 10.0):
        s = C.SCALE
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            sp = random.uniform(50, 260) * s
            life = random.uniform(0.22, 0.55)
            self.bits.append([
                x, y,
                math.cos(ang) * sp, math.sin(ang) * sp - 50 * s,
                life, life,
                random.uniform(2.5, 6.5) * s,
            ])
        self.shake_t = max(self.shake_t, 0.22)
        self.shake_mag = max(self.shake_mag * (self.shake_t / 0.22), shake * s)

    def update(self, dt: float):
        live = []
        for b in self.bits:
            b[0] += b[2] * dt
            b[1] += b[3] * dt
            b[3] += 480 * C.SCALE * dt
            b[2] *= 0.90
            b[4] -= dt
            if b[4] > 0:
                live.append(b)
        self.bits = live
        self.shake_t = max(0.0, self.shake_t - dt)
        if self.shake_t <= 0:
            self.shake_mag = 0.0

    def offset(self) -> tuple[int, int]:
        if self.shake_t <= 0:
            return 0, 0
        k = self.shake_t / 0.22
        m = self.shake_mag * k * k
        return int(random.uniform(-m, m)), int(random.uniform(-m, m))

    def draw(self, surf: pygame.Surface):
        for x, y, vx, vy, life, mx, r in self.bits:
            a = max(0, min(255, int(210 * (life / max(mx, 1e-4)))))
            d = max(2, int(r) * 2 + 2)
            blob = pygame.Surface((d, d), pygame.SRCALPHA)
            pygame.draw.circle(blob, (214, 198, 162, a), (d // 2, d // 2), max(1, int(r)))
            surf.blit(blob, (int(x) - d // 2, int(y) - d // 2))
