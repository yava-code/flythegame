"""stretchy forearm, wrist → bottom of the frame.

verlet rubber — like a fantastic-four arm, not a string. thickness comes
from the hand sprite's wrist so the join actually matches.
"""
from __future__ import annotations

import math

import pygame

from flygame import config as C


class ArmRope:
    def __init__(self):
        self.n = C.ROPE_N
        self.pos = [(0.0, 0.0)] * self.n
        self.prev = [(0.0, 0.0)] * self.n
        self.ready = False
        self.hw0 = 28.0
        self.hw1 = 44.0

    def pin(self, wrist: tuple[float, float], dt: float, wrist_half: float = 28.0):
        wx, wy = wrist
        if not math.isfinite(wx) or not math.isfinite(wy):
            return
        self.hw0 = max(16.0, float(wrist_half))
        self.hw1 = self.hw0 * 1.55
        ax = C.W * 0.5 + (wx - C.W * 0.5) * 0.10
        ay = C.H + self.hw1
        span = math.hypot(wx - ax, wy - ay)
        # unstretched arm; extra distance is rubber stretch
        natural = max(C.H * 0.42, 220.0 * C.SCALE)
        rest = natural / (self.n - 1)
        if not self.ready:
            self.pos = [
                (wx + (ax - wx) * i / (self.n - 1), wy + (ay - wy) * i / (self.n - 1))
                for i in range(self.n)
            ]
            self.prev = list(self.pos)
            self.ready = True

        g = 900.0 * C.SCALE
        dt = min(dt, 0.04)
        for i in range(1, self.n - 1):
            x, y = self.pos[i]
            px, py = self.prev[i]
            vx, vy = (x - px) * 0.94, (y - py) * 0.94
            self.prev[i] = (x, y)
            self.pos[i] = (x + vx, y + vy + g * dt * dt)

        self.pos[0] = (wx, wy)
        self.prev[0] = (wx, wy)
        self.pos[-1] = (ax, ay)
        self.prev[-1] = (ax, ay)

        # fewer passes = more stretch, like skin
        for _ in range(6):
            self.pos[0] = (wx, wy)
            self.pos[-1] = (ax, ay)
            for i in range(self.n - 1):
                x1, y1 = self.pos[i]
                x2, y2 = self.pos[i + 1]
                dx, dy = x2 - x1, y2 - y1
                d = math.hypot(dx, dy)
                if d < 1e-3:
                    continue
                extra = d - rest
                nx, ny = dx / d, dy / d
                # stretch more than compress
                k = 0.42 if extra > 0 else 0.62
                if i == 0:
                    self.pos[i + 1] = (x2 - nx * extra * k, y2 - ny * extra * k)
                elif i + 1 == self.n - 1:
                    self.pos[i] = (x1 + nx * extra * k, y1 + ny * extra * k)
                else:
                    self.pos[i] = (x1 + nx * extra * k * 0.5, y1 + ny * extra * k * 0.5)
                    self.pos[i + 1] = (x2 - nx * extra * k * 0.5, y2 - ny * extra * k * 0.5)

        if span > 1.0:
            # keep it from folding into a knot when the hand is low
            for i in range(self.n):
                x, y = self.pos[i]
                if not math.isfinite(x) or not math.isfinite(y):
                    self.ready = False
                    return

    def _edges(self):
        n = self.n
        left, right = [], []
        for i in range(n):
            t = i / (n - 1)
            hw = self.hw0 + (self.hw1 - self.hw0) * t
            x, y = self.pos[i]
            if i == 0:
                dx, dy = self.pos[1][0] - x, self.pos[1][1] - y
            elif i == n - 1:
                dx, dy = x - self.pos[i - 1][0], y - self.pos[i - 1][1]
            else:
                dx = self.pos[i + 1][0] - self.pos[i - 1][0]
                dy = self.pos[i + 1][1] - self.pos[i - 1][1]
            L = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / L, dx / L
            left.append((x + nx * hw, y + ny * hw))
            right.append((x - nx * hw, y - ny * hw))
        return left, right

    def draw(self, surf: pygame.Surface):
        if not self.ready:
            return
        left, right = self._edges()
        poly = left + right[::-1]
        if len(poly) < 6:
            return
        pygame.draw.polygon(surf, C.SKIN, poly)
        shade = []
        n = len(left)
        for i in range(n):
            lx, ly = left[i]
            rx, ry = right[i]
            shade.append((lx * 0.22 + rx * 0.78, ly * 0.22 + ry * 0.78))
        pygame.draw.polygon(surf, C.SKIN_SHADE, shade + right[::-1])
        pygame.draw.lines(surf, C.INK, False, left, max(2, int(3 * C.SCALE)))
        pygame.draw.lines(surf, C.INK, False, right, max(2, int(2 * C.SCALE)))
        # stretch creases
        step = max(2, self.n // 5)
        for i in range(step, self.n - 1, step):
            pygame.draw.line(surf, C.SKIN_SHADE, left[i], right[i], max(2, int(2 * C.SCALE)))
        pygame.draw.circle(surf, C.SKIN, (int(self.pos[0][0]), int(self.pos[0][1])), int(self.hw0))
