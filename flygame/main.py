"""Fly Swatter Adventures — MaleCNS looming escape demo"""
from __future__ import annotations

import math
import os
import random
import sys

import pygame

from flygame import config as C
from flygame.arena import Arena
from flygame.arm_rope import ArmRope
from flygame.audio import Audio, pre_init
from flygame.brain_driver import BrainDriver
from flygame.fly_body import FlyBody, loom_startle
from flygame.fly_log import FlyLog
from flygame.fx import Dust
from flygame.hand import Hand
from flygame.shadow import Shadow

MATCH_SEC = 60.0


def _open_screen(fullscreen: bool) -> tuple[pygame.Surface, bool]:
    w, h = C.desktop_size()
    # exclusive pygame.FULLSCREEN changes the video mode and hard-crashes
    # some windows+sdl setups. borderless at desktop size is the same look.
    if fullscreen:
        os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
        try:
            screen = pygame.display.set_mode((w, h), pygame.NOFRAME)
            return screen, True
        except pygame.error as e:
            print(f"[display] borderless refused: {e}")
            os.environ.pop("SDL_VIDEO_WINDOW_POS", None)
            return pygame.display.set_mode((max(1280, int(w * 0.9)), max(720, int(h * 0.9)))), False
    os.environ.pop("SDL_VIDEO_WINDOW_POS", None)
    return pygame.display.set_mode((max(1280, int(w * 0.90)), max(720, int(h * 0.90)))), False


class Game:
    def __init__(self, fullscreen: bool = True, headless: bool = False):
        C.dpi_aware()
        pre_init()
        pygame.init()
        pygame.display.set_caption("Fly Swatter · MaleCNS")
        self.screen, self.fullscreen = _open_screen(fullscreen)
        C.apply_display(*self.screen.get_size())
        print(f"[display] {C.W}x{C.H}  scale={C.SCALE:.2f}  fs={self.fullscreen}")
        self.clock = pygame.time.Clock()
        self._make_fonts()
        self._shake_buf = None

        self._splash("loading assets…")
        self.arena = Arena()
        self.rope = ArmRope()
        self.fx = Dust()
        self.log = FlyLog()
        self.audio = Audio()

        self.mode = "real"
        self.brain = BrainDriver(self.mode)
        if not headless:
            self.brain.start_async()

        self.shadow = Shadow(self.arena.shadow_spr)
        self.paused = False
        self.killcam = None
        self.best_escape = None
        self.reset_match()

    def _make_fonts(self):
        self.font = pygame.font.SysFont("consolas", C.UI_FONT_SIZE)
        self.font_sm = pygame.font.SysFont("consolas", C.UI_FONT_SM)
        self._text_cache: dict[tuple, pygame.Surface] = {}

    def text(self, font: pygame.font.Font, s: str, col) -> pygame.Surface:
        key = (id(font), s, col)
        img = self._text_cache.get(key)
        if img is None:
            img = font.render(s, True, col)
            if len(self._text_cache) > 400:
                self._text_cache.clear()
            self._text_cache[key] = img
        return img

    def _splash(self, msg: str):
        self.screen.fill(C.BG)
        title = self.font.render("Fly Swatter · MaleCNS", True, (240, 230, 200))
        body = self.font_sm.render(msg, True, (180, 200, 220))
        self.screen.blit(title, (C.W // 2 - title.get_width() // 2, C.H // 2 - 28))
        self.screen.blit(body, (C.W // 2 - body.get_width() // 2, C.H // 2 + 8))
        pygame.display.flip()
        pygame.event.pump()

    def reset_match(self):
        self.time_left = MATCH_SEC
        self.score = 0
        self.hand = Hand(C.W / 2, C.H * 0.70)
        self.crumb = (
            random.uniform(C.TABLE_L + 90, C.TABLE_R - 90),
            random.uniform(C.TABLE_T + 60, C.TABLE_B - 120),
        )
        self.flies = [FlyBody(*self._spawn(), self.arena.fly) for _ in range(C.N_FLIES)]
        self.impact_t = 0.0
        self.impact_pos = (0, 0)
        self.killcam = None
        self.best_escape = None
        self.fx = Dust()
        self.log = FlyLog()
        self.rope = ArmRope()
        self.shadow.sync(self.hand, C.DT)
        self.shadow.sync(self.hand, C.DT)

    def _spawn(self) -> tuple[float, float]:
        for _ in range(30):
            x = random.uniform(C.TABLE_L + 30, C.TABLE_R - 30)
            y = random.uniform(C.TABLE_T + 30, C.TABLE_B - 60)
            if math.hypot(x - self.hand.x, y - self.hand.y) > 190:
                return x, y
        return C.TABLE_L + 60, C.TABLE_T + 60

    def toggle_mode(self):
        if not self.brain.ok:
            return
        self.mode = "shuffled" if self.mode == "real" else "real"
        self.brain.set_mode(self.mode)

    def try_hit(self):
        hit = False
        for fly in self.flies:
            if not fly.alive or fly.state == "dash":
                continue
            # freeze = committed crouch, bigger target. walking fly is a small one.
            rad = C.HIT_R * (1.30 if fly.state == "freeze" else 0.62)
            if math.hypot(fly.x - self.hand.x, fly.y - self.hand.y) < rad:
                fly.kill()
                self.score += 1
                hit = True
                self.impact_pos = (fly.x, fly.y)
                self.fx.bang(fly.x, fly.y, n=26, shake=16)
                self.log.note("contact · fly down", (255, 200, 120))
        if hit:
            self.audio.play("hit")
        else:
            self.hand.mark_miss()
            self.brain.pulse_miss()
            self.audio.play("miss")
            self.fx.bang(self.hand.x, self.hand.y, n=12, shake=7)
            self.log.note("miss · hand recoils", (200, 160, 160))

    def update(self, dt: float):
        if self.killcam is not None:
            self.killcam["t"] -= dt
            if self.killcam["t"] <= 0:
                self.killcam = None

        if self.paused:
            return

        mx, my = pygame.mouse.get_pos()
        self.hand.aim(mx, my, dt)
        was_swat = self.hand.state == "swat"
        landed = False
        self.hand.update(dt)
        if self.hand.state == "swat" and not was_swat:
            self.audio.play("swat")
        if self.hand.just_landed:
            self.hand.just_landed = False
            landed = True
        self.shadow.sync(self.hand, dt)

        feats = [self.shadow.loom_features(f.x, f.y, dt, key=i)
                 for i, f in enumerate(self.flies)]
        pulls = [f.crumb_pull(self.crumb) if f.alive else 0.0 for f in self.flies]
        self.brain.submit(feats, dt, pulls)
        if landed:
            self.brain.flush()

        currents = self.brain.read_currents(feats, pulls)

        # visual loom startles into a freeze *before* DNp01. that's the tell.
        for i, fly in enumerate(self.flies):
            if not fly.alive or fly.state in ("dash", "dead", "freeze"):
                continue
            feat = feats[i]
            i4, il = currents[i]
            if loom_startle(feat) or (i4 + il) >= C.FREEZE_THREAT:
                if fly.freeze(feat):
                    self.audio.play("buzz")
                    why = "η rising · freeze" if feat["eta"] >= feat["dtheta"] else "dθ/dt · freeze"
                    self.log.note(f"{why}", (120, 200, 255))

        for i, _side in self.brain.poll():
            fly = self.flies[i]
            if not fly.alive or fly.state == "dash":
                continue
            feat = feats[i]
            if fly.state != "freeze":
                if fly.freeze(feat):
                    self.audio.play("buzz")
                    self.log.note("DNp01 · freeze", (255, 210, 90))
            fly.arm_takeoff(feat)
            self.log.note("DNp01 burst queued", (255, 90, 70))
            score = feat["dtheta"] * feat["cover"]
            if score > 3.0 and (self.best_escape is None or score > self.best_escape[0]):
                self.best_escape = (score, feat, (fly.x, fly.y))
                self.killcam = {"t": 0.55, "pos": (fly.x, fly.y)}

        # giant fiber first, then the slap — otherwise you always win
        if landed:
            self.try_hit()

        buzz = 0.0
        for fly in self.flies:
            fly.update(dt, crumb=self.crumb, hand=self.hand)
            if fly.dust_req:
                fly.dust_req = False
                n = 14 if fly.state == "dash" else 8
                self.fx.bang(fly.x, fly.y, n=n, shake=5 if fly.state == "dash" else 2)
            if fly.sfx_req:
                name = fly.sfx_req
                fly.sfx_req = None
                if name != "buzz":
                    self.audio.play(name)
                if name == "escape":
                    self.log.note("DNp01 burst · takeoff", (255, 90, 70))
            if fly.alive:
                if fly.state in ("walk", "hop", "dash"):
                    buzz = max(buzz, 1.0 if fly.state == "dash" else 0.55)
                elif fly.state == "sit":
                    buzz = max(buzz, 0.18)
        self.audio.set_wings(buzz)

        self.fx.update(dt)
        wrist = self.arena.hand_rect(self.hand)
        self.rope.pin(
            (wrist.centerx, wrist.bottom - 6),
            dt,
            self.arena.wrist_half(self.hand),
        )

        focus = max(
            range(len(self.flies)),
            key=lambda i: currents[i][0] + currents[i][1] if self.flies[i].alive else -1,
        )
        self.log.focus = focus
        self.log.think(
            feats[focus], currents[focus][0], currents[focus][1],
            self.flies[focus].state, self.flies[focus].armed,
        )

        self.time_left = max(0.0, self.time_left - dt)

    def draw_ui(self):
        lines = [
            (self.font, f"{int(self.time_left):02d}s   swats {self.score}", (240, 230, 200)),
            (self.font, self.brain.label(),
             (255, 200, 120) if self.brain.loading else (240, 230, 200)),
            (self.font_sm,
             "slap the freeze  ·  LMB  ·  RMB height  ·  T wiring  ·  F fullscreen  ·  M mute",
             (175, 190, 210)),
        ]
        y = 10
        for font, line, col in lines:
            s = self.text(font, line, col)
            self.screen.blit(s, (16, y))
            y += s.get_height() + 3

        gx, gy, gh = 16, int(C.H * 0.42), int(280 * C.SCALE)
        pygame.draw.rect(self.screen, (18, 32, 62), (gx, gy, 14, gh), border_radius=3)
        fh = int(gh * self.hand.z)
        pygame.draw.rect(self.screen, (200, 170, 110), (gx, gy + gh - fh, 14, fh), border_radius=3)
        self.screen.blit(self.text(self.font_sm, "z", (175, 190, 210)), (gx, gy + gh + 4))

        if self.killcam is not None:
            ov = pygame.Surface((C.W, C.H), pygame.SRCALPHA)
            ov.fill((30, 14, 0, 90))
            self.screen.blit(ov, (0, 0))
            px, py = self.killcam["pos"]
            pygame.draw.circle(self.screen, (255, 210, 60), (int(px), int(py)), 26, 2)
            t = self.text(self.font, "DNp01", (255, 230, 100))
            self.screen.blit(t, (int(px) - t.get_width() // 2, int(py) - 46))

        if self.paused:
            ov = pygame.Surface((C.W, C.H), pygame.SRCALPHA)
            ov.fill((0, 0, 20, 185))
            self.screen.blit(ov, (0, 0))
            credit = [
                "paused",
                "",
                "wiring: MaleCNS v1.0 connectome",
                "HHMI Janelia / University of Cambridge / MRC LMB / Google Research",
                "CC BY 4.0 · Berg et al. 2026, Cell",
                "",
                "simulation: flybrain — frozen weights, never trained to play this",
                "the fly sees the shadow only: dA/dt / A drives LC4 + LPLC2, DNp01 takes off",
                "freeze is the tell. slap during the crouch. miss and the hand snaps back.",
                "",
                "real wiring = EM synapse graph · shuffled = same degrees, scrambled partners",
            ]
            cy = C.H // 2 - 130
            for line in credit:
                s = self.text(self.font_sm, line, (222, 224, 232))
                self.screen.blit(s, (C.W // 2 - s.get_width() // 2, cy))
                cy += int(22 * max(1.0, C.SCALE))

        if self.time_left <= 0:
            msg = self.text(self.font, f"time · {self.score} swats · R to restart", (255, 240, 200))
            box = msg.get_rect(center=(C.W // 2, C.H // 2))
            pygame.draw.rect(self.screen, (14, 24, 48), box.inflate(28, 20), border_radius=6)
            self.screen.blit(msg, box)

    def draw(self):
        ox, oy = self.fx.offset()
        target = self.screen
        if ox or oy:
            if self._shake_buf is None or self._shake_buf.get_size() != (C.W, C.H):
                self._shake_buf = pygame.Surface((C.W, C.H))
            target = self._shake_buf
        self.arena.draw_bg(target)

        pygame.draw.circle(target, (168, 128, 74), (int(self.crumb[0]), int(self.crumb[1])), max(5, int(7 * C.SCALE)))
        pygame.draw.circle(target, (96, 66, 34), (int(self.crumb[0]), int(self.crumb[1])), max(5, int(7 * C.SCALE)), 1)

        self.shadow.draw(target)
        for fly in self.flies:
            fly.draw(target)
        self.fx.draw(target)

        if not self.hand.hide_sprite:
            self.rope.draw(target)
        self.arena.draw_hand(target, self.hand)

        if ox or oy:
            self.screen.fill((0, 0, 0))
            self.screen.blit(target, (ox, oy))
        self.draw_ui()
        self.log.draw(self.screen, self.font, self.font_sm, self.text)
        pygame.display.flip()

    def _toggle_fullscreen(self):
        self.screen, self.fullscreen = _open_screen(not self.fullscreen)
        C.apply_display(*self.screen.get_size())
        self._make_fonts()
        self.arena.refit()
        self.rope.ready = False
        self._shake_buf = None
        print(f"[display] {C.W}x{C.H}  scale={C.SCALE:.2f}  fs={self.fullscreen}")

    def run(self):
        while True:
            dt = min(self.clock.tick(C.FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.brain.stop()
                    pygame.quit()
                    sys.exit(0)
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.paused = not self.paused
                    elif ev.key == pygame.K_r:
                        self.reset_match()
                    elif ev.key == pygame.K_t:
                        self.toggle_mode()
                    elif ev.key == pygame.K_h:
                        self.hand.hide_sprite = not self.hand.hide_sprite
                    elif ev.key == pygame.K_m:
                        self.audio.toggle_mute()
                    elif ev.key in (pygame.K_f, pygame.K_F11):
                        self._toggle_fullscreen()
                if not self.paused and self.time_left > 0:
                    self.hand.on_event(ev)

            if self.time_left > 0 or self.killcam is not None:
                self.update(dt)
            self.draw()


def main():
    fs = "--windowed" not in sys.argv
    if "--fullscreen" in sys.argv:
        fs = True
    try:
        Game(fullscreen=fs).run()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        try:
            (C.ROOT / "crash.log").write_text(tb, encoding="utf-8")
        except Exception:
            pass
        try:
            pygame.quit()
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
