"""drosophila on the table.

        sit, short walk, rare hop. takeoff only from the brain. side-view
        sprites stay horizontal — just flipped left/right.
"""
from __future__ import annotations

import math
import random

import pygame

from flygame import config as C


def _angle_diff(a: float, b: float) -> float:
    return (a - b + math.pi) % math.tau - math.pi


def loom_startle(feat: dict) -> bool:
    if feat["cover"] < C.STARTLE_COVER:
        return False
    return feat["eta"] > C.STARTLE_ETA or feat["dtheta"] > C.STARTLE_DTHETA


class FlyBody:
    def __init__(self, x: float, y: float, sprites: dict[str, pygame.Surface]):
        self.sprites = sprites
        self._rot: dict[tuple, pygame.Surface] = {}
        self.reset(x, y)

    def reset(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.heading = random.uniform(0, math.tau)
        self.alive = True
        self.state = "sit"
        self.timer = random.uniform(0.8, 2.2)
        self.anim = random.uniform(0, 20)
        self.perched = False
        self.on_crumb = False
        self.escape_flash = 0.0
        self.last_escape_feat = None
        self.target = None
        self.pending_dash = None
        self.armed = False
        self.bob = 0.0
        self.dust_req = False
        self.sfx_req = None
        self.trail: list[tuple[float, float, float]] = []
        self.groom = random.uniform(0, math.tau)

    def freeze(self, feat: dict):
        if not self.alive or self.state in ("dash", "dead"):
            return False
        if self.state == "freeze":
            return False
        self.state = "freeze"
        self.timer = C.FREEZE_TIME
        self.vx = self.vy = 0.0
        self.pending_dash = dict(feat)
        self.armed = False
        self.target = None
        self.sfx_req = "buzz"
        return True

    def arm_takeoff(self, feat: dict | None = None):
        if feat is not None:
            self.pending_dash = dict(feat)
        self.armed = True

    def escape(self, feat: dict, mean: bool = False):
        ang = math.atan2(-feat["dy"], -feat["dx"]) + random.uniform(-0.25, 0.25)
        lo, hi = C.FLY_ESCAPE_SPEED
        speed = hi if mean else random.uniform(lo, hi)
        self.heading = ang
        self.vx = math.cos(ang) * speed
        self.vy = math.sin(ang) * speed
        self.state = "dash"
        self.timer = 0.22 if mean else 0.16
        self.perched = False
        self.on_crumb = False
        self.escape_flash = 1.1
        self.last_escape_feat = dict(feat)
        self.pending_dash = None
        self.armed = False
        self.target = None
        self.dust_req = True
        self.sfx_req = "escape"

    def kill(self):
        self.alive = False
        self.state = "dead"
        self.vx = self.vy = 0.0
        self.perched = False
        self.on_crumb = False
        self.armed = False

    def update(self, dt: float, crumb=None, hand=None):
        if self.escape_flash > 0:
            self.escape_flash -= dt
        if not self.alive:
            return

        self.timer -= dt
        self.groom += dt * 3.2
        if self.state == "dash":
            self.vx *= max(0.0, 1.0 - C.FLY_DASH_DRAG * dt)
            self.vy *= max(0.0, 1.0 - C.FLY_DASH_DRAG * dt)
            self.trail.append((self.x, self.y, 0.18))
            if self.timer <= 0:
                self._go_sit(random.uniform(0.35, 0.8))
        elif self.state == "freeze":
            self.vx = self.vy = 0.0
            if self.armed and self.pending_dash is not None and self.timer <= 0:
                self.escape(self.pending_dash)
            elif self.timer <= 0:
                # loom faded, giant fiber never burst
                self.pending_dash = None
                self.armed = False
                self._go_sit(random.uniform(0.2, 0.45))
        elif self.state == "sit":
            self._sit(dt, crumb, hand)
        elif self.state == "walk":
            self._walk(dt, crumb, hand)
        elif self.state == "hop":
            self._hop(dt)

        self.x += self.vx * dt
        self.y += self.vy * dt
        self._keep_inside()

        live = []
        for tx, ty, life in self.trail:
            life -= dt
            if life > 0:
                live.append((tx, ty, life))
        self.trail = live[-8:]

        speed = math.hypot(self.vx, self.vy)
        self.anim += dt * (22.0 if self.state in ("hop", "dash") else 7.0)
        self.bob += dt * (16.0 if self.state == "walk" else 9.0)
        if speed > 8:
            self.heading = math.atan2(self.vy, self.vx)

    def _go_sit(self, t: float):
        self.state = "sit"
        self.timer = t
        self.vx = self.vy = 0.0
        self.target = None

    def _sit(self, dt: float, crumb, hand):
        self.vx = self.vy = 0.0
        # tiny groom twitch so idle isn't a sticker
        self.heading += math.sin(self.groom) * 0.35 * dt
        if self._maybe_perch(hand):
            return
        if self._crumb_near(crumb) and not self.on_crumb:
            self._start_walk(toward=crumb)
            return
        if self.timer <= 0:
            self.on_crumb = False
            roll = random.random()
            if roll < 0.78:
                self._start_walk()
            elif roll < 0.90:
                self._start_hop()
            else:
                self._go_sit(random.uniform(0.6, 1.8))

    def _start_walk(self, toward=None):
        self.state = "walk"
        self.timer = random.uniform(0.45, 1.1)
        if toward is not None:
            self.heading = math.atan2(toward[1] - self.y, toward[0] - self.x)
            self.timer = 1.8
            self.target = toward
        else:
            self.heading += random.uniform(-0.8, 0.8)
            self.target = None
        sp = random.uniform(*C.FLY_WALK_SPEED)
        self.vx = math.cos(self.heading) * sp
        self.vy = math.sin(self.heading) * sp

    def _walk(self, dt: float, crumb, hand):
        if self._maybe_perch(hand):
            return
        sp = math.hypot(self.vx, self.vy) or C.FLY_WALK_SPEED[0]
        self.heading += random.uniform(-0.9, 0.9) * dt
        if self.target is not None:
            want = math.atan2(self.target[1] - self.y, self.target[0] - self.x)
            self.heading += _angle_diff(want, self.heading) * min(1.0, dt * 4.0)
            if math.hypot(self.target[0] - self.x, self.target[1] - self.y) < 12:
                self.on_crumb = True
                self._go_sit(random.uniform(1.4, 2.6))
                return
        self.vx = math.cos(self.heading) * sp
        self.vy = math.sin(self.heading) * sp
        if self.timer <= 0:
            self._go_sit(random.uniform(0.7, 2.0))

    def _start_hop(self):
        self.state = "hop"
        d = random.uniform(50, 110)
        for _ in range(8):
            ang = random.uniform(0, math.tau)
            tx = self.x + math.cos(ang) * d
            ty = self.y + math.sin(ang) * d
            if C.TABLE_L + 20 < tx < C.TABLE_R - 20 and C.TABLE_T + 20 < ty < C.TABLE_B - 20:
                break
        else:
            tx = random.uniform(C.TABLE_L + 40, C.TABLE_R - 40)
            ty = random.uniform(C.TABLE_T + 40, C.TABLE_B - 40)
        self.target = (tx, ty)
        self.heading = math.atan2(ty - self.y, tx - self.x)
        sp = random.uniform(*C.FLY_HOP_SPEED)
        self.vx = math.cos(self.heading) * sp
        self.vy = math.sin(self.heading) * sp
        self.timer = min(0.7, d / sp + 0.04)
        self.on_crumb = False
        self.sfx_req = "hop"
        self.dust_req = True

    def _hop(self, dt: float):
        if self.target is not None:
            if math.hypot(self.target[0] - self.x, self.target[1] - self.y) < 12:
                self._go_sit(random.uniform(0.5, 1.4))
                return
        if self.timer <= 0:
            self._go_sit(random.uniform(0.5, 1.4))

    def _maybe_perch(self, hand) -> bool:
        if self.state == "freeze":
            return False
        if hand is None or not hand.still() or hand.z > 0.28:
            self.perched = False
            return False
        d = math.hypot(hand.x - self.x, hand.y - self.y)
        if d > 48:
            self.perched = False
            return False
        if d > 12:
            ang = math.atan2(hand.y - self.y, hand.x - self.x)
            sp = C.FLY_WALK_SPEED[0]
            self.vx = math.cos(ang) * sp
            self.vy = math.sin(ang) * sp
            self.state = "walk"
            self.timer = 0.35
        else:
            self.perched = True
            self.vx = self.vy = 0.0
            self.state = "sit"
            self.timer = 0.4
        return True

    def _keep_inside(self):
        bounced = False
        if self.x < C.TABLE_L:
            self.x = C.TABLE_L + 1
            self.vx = abs(self.vx) * 0.4
            bounced = True
        elif self.x > C.TABLE_R:
            self.x = C.TABLE_R - 1
            self.vx = -abs(self.vx) * 0.4
            bounced = True
        if self.y < C.TABLE_T:
            self.y = C.TABLE_T + 1
            self.vy = abs(self.vy) * 0.4
            bounced = True
        elif self.y > C.TABLE_B:
            self.y = C.TABLE_B - 1
            self.vy = -abs(self.vy) * 0.4
            bounced = True
        if bounced:
            self.heading = math.atan2(self.vy, self.vx)
            self.target = None
            if self.state == "dash":
                self._go_sit(0.4)

    def crumb_pull(self, crumb) -> float:
        if crumb is None or not self.alive:
            return 0.0
        d = math.hypot(crumb[0] - self.x, crumb[1] - self.y)
        if d > 60:
            return 0.0
        return (1.0 - d / 60.0) * (1.0 if self.on_crumb else 0.5)

    def _crumb_near(self, crumb) -> bool:
        if crumb is None:
            return False
        return math.hypot(crumb[0] - self.x, crumb[1] - self.y) < 70

    def _sprite(self, name: str) -> pygame.Surface | None:
        img = self.sprites.get(name) or self.sprites.get("idle")
        if img is None:
            return None
        face = 1 if math.cos(self.heading) >= 0 else -1
        key = (name, face, C.FLY_SIZE)
        out = self._rot.get(key)
        if out is None:
            tw = C.FLY_SIZE
            th = max(1, round(img.get_height() * tw / max(1, img.get_width())))
            out = pygame.transform.scale(img, (tw, th))
            if face > 0:
                out = pygame.transform.flip(out, True, False)
            self._rot[key] = out
        return out

    def _wings(self, surf, cx, cy, face):
        flap = 0.35 + 0.65 * abs(math.sin(self.anim * (8 if self.state in ("hop", "dash", "walk") else 3)))
        if self.state == "freeze":
            flap = 0.15
        w = max(2, int(10 * C.SCALE * flap))
        h = max(2, int(4 * C.SCALE))
        col = (210, 220, 230, 140)
        wing = pygame.Surface((w * 2 + 4, h * 2 + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(wing, col, (0, 2, w * 2, h))
        ox = int(6 * C.SCALE) * face
        surf.blit(wing, (cx - w - ox, cy - int(8 * C.SCALE)))
        surf.blit(wing, (cx - w + ox, cy - int(6 * C.SCALE)))

    def draw(self, surf: pygame.Surface):
        s = C.SCALE
        for tx, ty, life in self.trail:
            a = int(90 * (life / 0.18))
            tw = max(2, int(16 * s))
            th = max(2, int(10 * s))
            blob = pygame.Surface((tw, th), pygame.SRCALPHA)
            pygame.draw.ellipse(blob, (40, 30, 20, a), blob.get_rect())
            surf.blit(blob, blob.get_rect(center=(int(tx), int(ty))))

        if not self.alive:
            img = self._sprite("dead")
        elif self.state == "freeze":
            img = self._sprite("fly0")
        elif self.state in ("hop", "dash"):
            img = self._sprite("fly0" if int(self.anim) % 2 == 0 else "fly1")
        elif self.state == "walk":
            img = self._sprite("idle" if int(self.bob) % 2 == 0 else "fly1")
        else:
            img = self._sprite("idle")

        oy = 0
        sx, sy = 1.0, 1.0
        if self.state == "walk":
            oy = int(math.sin(self.bob * 7) * 2.4 * s)
        elif self.state == "hop":
            oy = int(-abs(math.sin(self.anim * 3.2)) * 10 * s)
        elif self.state == "freeze":
            oy = int(3 * s)
            sy = 0.78
            sx = 1.12
        elif self.state == "sit":
            oy = int(math.sin(self.groom * 2) * 1.2 * s)

        cx, cy = int(self.x), int(self.y + oy)
        shw, shh = max(2, int(28 * s)), max(2, int(12 * s))
        sh = pygame.Surface((shw, shh), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (20, 24, 40, 90), sh.get_rect())
        surf.blit(sh, sh.get_rect(center=(cx, int(self.y + 8 * s))))

        face = 1 if math.cos(self.heading) >= 0 else -1
        if img is None:
            pygame.draw.circle(
                surf, (190, 120, 60) if self.alive else (90, 80, 70),
                (cx, cy), 5,
            )
        else:
            if sx != 1.0 or sy != 1.0:
                img = pygame.transform.scale(
                    img, (max(1, int(img.get_width() * sx)), max(1, int(img.get_height() * sy)))
                )
            surf.blit(img, img.get_rect(center=(cx, cy)))
            if self.alive:
                self._wings(surf, cx, cy, face)

        if self.state == "freeze":
            pulse = 0.55 + 0.45 * abs(math.sin(self.anim * 6))
            r = max(6, int(22 * s * (0.8 + 0.2 * pulse)))
            ring = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 220, 80, int(120 * pulse)), (r + 2, r + 2), r, max(2, int(2 * s)))
            surf.blit(ring, ring.get_rect(center=(cx, cy)))
            bw = max(2, int(3 * s))
            pygame.draw.rect(surf, (255, 230, 90), (cx + int(14 * s), cy - int(20 * s), bw, int(12 * s)))
            pygame.draw.rect(surf, (255, 230, 90), (cx + int(14 * s), cy - int(6 * s), bw, bw))

        if self.escape_flash > 0:
            a = int(160 * max(0.0, self.escape_flash / 1.1))
            rr = max(6, int(18 * s))
            ring = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 220, 90, a), (rr, rr), rr - 2, 2)
            surf.blit(ring, ring.get_rect(center=(cx, cy)))
