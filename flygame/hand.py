"""player hand: follow, height, swat, miss recoils back"""
from __future__ import annotations

import math

import pygame

from flygame import config as C


class Hand:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.z = C.Z_IDLE
        self.state = "idle"
        self.timer = 0.0
        self.hide_sprite = False
        self.just_landed = False
        self.still_t = 0.0
        self._rmb = False
        self._last_my = 0
        self._z0 = self.z
        self.swat_len = C.SWAT_T_MIN
        self._home = (x, y, C.Z_IDLE)

    def aim(self, mx: float, my: float, dt: float):
        if self.state in ("rest", "recoil"):
            self.vx = self.vy = 0.0
            return
        a = 1.0 - math.exp(-dt / C.HAND_TAU)
        nx = self.x + (mx - self.x) * a
        ny = self.y + (my - self.y) * a
        self.vx = (nx - self.x) / max(dt, 1e-4)
        self.vy = (ny - self.y) / max(dt, 1e-4)
        self.x = max(40.0, min(C.W - 40.0, nx))
        self.y = max(80.0, min(C.H - 50.0, ny))
        if math.hypot(self.vx, self.vy) < 18:
            self.still_t += dt
        else:
            self.still_t = 0.0

    def on_event(self, ev: pygame.event.Event):
        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 3:
                self._rmb = True
                self._last_my = ev.pos[1]
            elif ev.button == 1 and self.state == "idle":
                self.start_swat()
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 3:
            self._rmb = False
        elif ev.type == pygame.MOUSEMOTION and self._rmb:
            if self.state == "idle":
                dy = self._last_my - ev.pos[1]
                self.z = max(0.08, min(1.0, self.z + dy * 0.006))
            self._last_my = ev.pos[1]
        elif ev.type == pygame.MOUSEWHEEL and self.state == "idle":
            self.z = max(0.08, min(1.0, self.z + ev.y * 0.06))

    def start_swat(self):
        self._home = (self.x, self.y, self.z)
        self.state = "swat"
        self._z0 = max(0.12, self.z)
        self.swat_len = C.SWAT_T_MIN + C.SWAT_T_PER_Z * self._z0
        self.timer = self.swat_len
        self.still_t = 0.0

    def update(self, dt: float):
        if self.state == "swat":
            self.timer -= dt
            t = 1.0 - max(0.0, self.timer) / self.swat_len
            self.z = self._z0 * max(0.0, 1.0 - t ** 1.15)
            if self.timer <= 0:
                self.z = 0.0
                self.state = "rest"
                self.timer = C.REST_ON_TABLE
                self.just_landed = True
        elif self.state == "rest":
            self.timer -= dt
            self.z = 0.0
            if self.timer <= 0:
                self.state = "idle"
                self.z = max(self._home[2], C.Z_IDLE)
        elif self.state == "recoil":
            self.timer -= dt
            hx, hy, hz = self._home
            k = 1.0 - math.exp(-dt * 14.0)
            self.x += (hx - self.x) * k
            self.y += (hy - self.y) * k
            self.z += (max(hz, 0.55) - self.z) * k
            if self.timer <= 0:
                self.x, self.y = hx, hy
                self.z = max(hz, 0.55)
                self.state = "idle"

    def mark_miss(self):
        self.state = "recoil"
        self.timer = C.RECOIL_TIME

    def still(self) -> bool:
        return self.state == "idle" and self.still_t > 0.55
