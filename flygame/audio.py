"""chip sfx + a quiet lo-fi loop.

pygame.init() already starts the mixer, so we pre_init and never call
mixer.init() a second time — that was killing all sound on windows.
"""
from __future__ import annotations

import wave

import numpy as np
import pygame

from flygame import config as C

SR = 22050
SFX_DIR = C.ASSETS / "sfx"
GEN = SFX_DIR / ".gen5"


def pre_init():
    pygame.mixer.pre_init(frequency=SR, size=-16, channels=1, buffer=512)


def _lowpass(x: np.ndarray, k: int = 6) -> np.ndarray:
    return np.convolve(x, np.ones(k) / k, mode="same")


def _env(t: np.ndarray, attack: float, decay: float) -> np.ndarray:
    return np.minimum(t / max(attack, 1e-4), 1.0) * np.exp(-t / decay)


def _write(name: str, x: np.ndarray):
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(x, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(SFX_DIR / name), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def _noise(n, seed):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def _thump(dur, f0, amp, seed):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    body = np.sin(2 * np.pi * f0 * t * (1.0 - 0.4 * t / dur))
    click = _lowpass(_noise(t.size, seed), 8) * np.exp(-t / 0.01)
    return _lowpass((0.65 * body + 0.35 * click) * _env(t, 0.002, dur * 0.5) * amp, 7)


def _zip(dur, f0, amp):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    f = f0 * (1.0 + 1.6 * t / dur)
    sq = np.sign(np.sin(2 * np.pi * f * t)) * 0.45
    return _lowpass(sq * _env(t, 0.003, dur * 0.45) * amp, 8)


def _music(dur=14.0):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    notes = [130.8, 155.6, 174.6, 196.0, 174.6, 155.6, 123.5, 130.8]
    step = dur / len(notes)
    x = np.zeros_like(t)
    for i, f in enumerate(notes):
        m = (t >= i * step) & (t < (i + 1) * step)
        lt = t[m] - i * step
        tri = 2 * np.abs(2 * (lt * f - np.floor(lt * f + 0.5))) - 1
        sub = np.sin(2 * np.pi * (f / 2) * lt)
        x[m] = 0.55 * tri * _env(lt, 0.04, step * 0.7) + 0.22 * sub
    x *= 0.7 + 0.3 * np.sin(2 * np.pi * t / dur)
    return _lowpass(x * 0.55, 12)


def ensure_sfx():
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    need = not GEN.exists() or not (SFX_DIR / "loop.wav").exists()
    if not need:
        return
    for old in SFX_DIR.glob("*.wav"):
        old.unlink()
    _write("swat.wav", _thump(0.10, 68, 0.7, 1))
    _write("hit.wav", _thump(0.13, 52, 0.85, 2))
    _write("miss.wav", _thump(0.08, 90, 0.5, 3))
    _write("escape.wav", _zip(0.11, 420, 0.62))
    _write("buzz.wav", _zip(0.10, 240, 0.32))
    _write("hop.wav", _thump(0.06, 140, 0.35, 7))
    t = np.linspace(0, 0.28, int(SR * 0.28), endpoint=False)
    wing = 0.22 * np.sin(2 * np.pi * 210 * t)
    wing += 0.12 * _lowpass(_noise(t.size, 9), 4)
    wing *= 0.45 + 0.55 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 62 * t)))
    _write("wings.wav", _lowpass(wing * 0.55, 5))
    _write("loop.wav", _music())
    GEN.write_text("audible chip\n")


class Audio:
    def __init__(self):
        self.muted = False
        self.enabled = False
        self.sfx: dict[str, pygame.mixer.Sound] = {}
        self.wings = None
        try:
            ensure_sfx()
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=SR, size=-16, channels=1, buffer=512)
        except Exception as e:
            print(f"[audio] off ({e})")
            return
        self.enabled = True
        for name in ("swat", "hit", "miss", "escape", "buzz", "hop"):
            p = SFX_DIR / f"{name}.wav"
            if p.exists():
                s = pygame.mixer.Sound(str(p))
                s.set_volume(C.SFX_VOL * (0.55 if name == "hop" else 1.0))
                self.sfx[name] = s
        self.wings = None
        wp = SFX_DIR / "wings.wav"
        if wp.exists():
            try:
                self.wings = pygame.mixer.Sound(str(wp))
                self.wings.set_volume(0.0)
                self.wings.play(-1)
            except Exception as e:
                print(f"[audio] wings off ({e})")
                self.wings = None
        loop = SFX_DIR / "loop.wav"
        if loop.exists():
            try:
                pygame.mixer.music.load(str(loop))
                pygame.mixer.music.set_volume(C.MUSIC_VOL)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print(f"[audio] music off ({e})")
        print(f"[audio] on  mixer={pygame.mixer.get_init()}  sfx={list(self.sfx)}")

    def play(self, name: str):
        if not self.enabled or self.muted:
            return
        s = self.sfx.get(name)
        if s:
            s.play()

    def set_wings(self, k: float):
        if not self.enabled or self.wings is None:
            return
        if self.muted:
            self.wings.set_volume(0.0)
            return
        self.wings.set_volume(max(0.0, min(0.22, 0.16 * k)))

    def toggle_mute(self):
        self.muted = not self.muted
        if not self.enabled:
            return
        pygame.mixer.music.set_volume(0.0 if self.muted else C.MUSIC_VOL)
        if self.wings is not None:
            self.wings.set_volume(0.0)
        return self.muted
