"""MaleCNS driver via flybrain — real wiring or scrambled.

two things matter here. the brain never runs on the game thread: one step of the
whole connectome costs about 10 ms on a desktop CPU and would eat the frame. and
one brain is simulated, not one per fly — a batch of three costs ~36 ms a step,
which is slower than real time, and a fly that reacts late is worse than a fly
that shares a nervous system. the brain is handed to whichever fly the palm is
actually threatening; the others have no shadow growing over them, so with the
burst rule they could not take off anyway. set FLY_BATCH=3 if your machine can
afford a brain per fly.
"""
from __future__ import annotations

import math
import os
import threading
import traceback

import numpy as np

from flygame import config as C


class BrainDriver:
    def __init__(self, mode: str = "real", n_flies: int = C.N_FLIES):
        self.mode = mode
        self.n = n_flies
        self.batch = max(1, min(n_flies, int(os.environ.get("FLY_BATCH", "1"))))
        self.ok = False
        self.ready = False
        self.loading = False
        self.status = "starting…"
        self.error = ""
        self.brain = None
        self.dt = C.BRAIN_DT
        self.step_ms = 0.0
        self.target = -1

        self._has_ppl = False
        self._lc4: dict[str, np.ndarray] = {}
        self._lplc2: dict[str, np.ndarray] = {}
        self._dnp01: dict[str, np.ndarray] = {}
        self._ppl: dict[str, np.ndarray] = {}
        self._lc10: dict[str, np.ndarray] = {}
        self._lb3c: dict[str, np.ndarray] = {}

        self._miss_boost = np.zeros(n_flies, dtype=np.float32)
        self._ring = np.zeros((n_flies, C.DNP01_WINDOW), dtype=np.int16)
        self._ring_i = 0
        self._dn_side = ["L"] * n_flies
        self._wiring_real = None

        self._lock = threading.Lock()
        self._io = threading.Lock()
        self._thread = None
        self._stop = False
        self._pending = None            # latest (feats, dt, pulls) from the game
        self._escapes: list[tuple[int, str]] = []
        self._mode_request = None
        self._miss_request = 0

    # ---- loading ---------------------------------------------------------

    def start_async(self):
        if self._thread and self._thread.is_alive():
            return
        self.loading = True
        self.status = "loading MaleCNS (~260MB)…"
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop = True

    def _loaded(self):
        """blocking load, for scripts and tests"""
        self._load_worker()
        return self

    def _load_worker(self):
        try:
            from flybrain import FlyBrain

            self.status = "reading weights.npz…"
            brain = FlyBrain(device="cpu", batch=self.batch, dt=self.dt)

            self.status = "indexing cell types…"
            cells = {}
            for side in ("L", "R"):
                cells[("lc4", side)] = brain.cells(["LC4"], side=side)
                cells[("lplc2", side)] = brain.cells(["LPLC2"], side=side)
                cells[("dnp01", side)] = brain.cells(["DNp01"], side=side)
                cells[("ppl", side)] = self._safe_cells(brain, ["PPL101"], side)
                cells[("lc10", side)] = self._safe_cells(brain, ["LC10a"], side)
                cells[("lb3c", side)] = self._safe_cells(brain, ["LB3c"], side)

            self.status = "compiling numba (first step)…"
            lc = cells[("lc4", "L")]
            brain.step(inject=[(lc, 0.3)] if len(lc) else ())

            wiring_real = brain.indices.copy()
            if self.mode == "shuffled":
                np.random.shuffle(brain.indices)

            with self._lock:
                self.brain = brain
                self._wiring_real = wiring_real
                for side in ("L", "R"):
                    self._lc4[side] = cells[("lc4", side)]
                    self._lplc2[side] = cells[("lplc2", side)]
                    self._dnp01[side] = cells[("dnp01", side)]
                    self._ppl[side] = cells[("ppl", side)]
                    self._lc10[side] = cells[("lc10", side)]
                    self._lb3c[side] = cells[("lb3c", side)]
                    if len(self._ppl[side]):
                        self._has_ppl = True
                self.ok = True
                self.ready = True
                self.loading = False
                self.status = "ready"
            print(
                f"[brain] ready · mode={self.mode} · batch={self.batch} · "
                f"LC4={len(self._lc4['L'])}+{len(self._lc4['R'])} "
                f"DNp01={len(self._dnp01['L'])}+{len(self._dnp01['R'])}"
            )
        except Exception as e:
            self.error = str(e)
            self.status = f"fallback ({e})"
            self.loading = False
            self.ready = True
            self.ok = False
            traceback.print_exc()

    @staticmethod
    def _safe_cells(brain, types: list[str], side: str) -> np.ndarray:
        try:
            return brain.cells(types, side=side)
        except Exception:
            return np.array([], dtype=int)

    # ---- the brain's own thread -----------------------------------------

    def _run(self):
        self._load_worker()
        if not self.ok:
            return
        while not self._stop:
            with self._io:
                job = self._pending
                self._pending = None
                mode_req = self._mode_request
                self._mode_request = None
                misses = self._miss_request
                self._miss_request = 0

            if mode_req is not None:
                self._apply_mode(mode_req)
            for _ in range(misses):
                self._pulse_ppl()

            if job is None:
                # nothing new to see; keep the loop cheap
                threading.Event().wait(0.004)
                continue

            feats, dt, pulls = job
            outs = self.step_all(feats, dt, pulls)
            hits = [(i, o["side"]) for i, o in enumerate(outs) if o["escape"]]
            if hits:
                with self._io:
                    self._escapes.extend(hits)

    def submit(self, feats: list[dict], dt: float, pulls: list[float]):
        """hand the current scene to the brain thread; never blocks"""
        if not self.ok:
            self._sync_out = self.step_all(feats, dt, pulls)
            return
        with self._io:
            self._pending = (feats, dt, pulls)

    def flush(self):
        """run the latest pending step now so a slap can lose to DNp01."""
        if not self.ok:
            return
        with self._io:
            job = self._pending
            self._pending = None
        if job is None:
            return
        feats, dt, pulls = job
        outs = self.step_all(feats, dt, pulls)
        hits = [(i, o["side"]) for i, o in enumerate(outs) if o["escape"]]
        if hits:
            with self._io:
                self._escapes.extend(hits)

    def poll(self) -> list[tuple[int, str]]:
        """escapes the brain decided on since the last call"""
        if not self.ok:
            outs = getattr(self, "_sync_out", [])
            return [(i, o["side"]) for i, o in enumerate(outs) if o["escape"]]
        with self._io:
            out = self._escapes
            self._escapes = []
        return out

    # ---- mode -----------------------------------------------------------

    def set_mode(self, mode: str):
        if mode == self.mode:
            return
        self.mode = mode
        if not self.ok:
            return
        if self._thread and self._thread.is_alive():
            with self._io:
                self._mode_request = mode      # ~200ms of shuffling, off-thread
        else:
            self._apply_mode(mode)

    def _apply_mode(self, mode: str):
        """swap which neuron each synapse lands on.

        out-degree per neuron, the in-degree sequence and every synaptic weight
        (so every sign) stay exactly as the EM data has them — only the partners
        change. same statistics, wrong connectome.
        """
        if self.brain is None or self._wiring_real is None:
            return
        with self._lock:
            if mode == "real":
                self.brain.indices[:] = self._wiring_real
            else:
                self.brain.indices[:] = np.random.permutation(self._wiring_real)
            self.brain.reset()
            self._ring[:] = 0
        print(f"[brain] mode -> {mode}")

    # ---- encoding -------------------------------------------------------

    def read_currents(self, feats: list[dict], pulls: list[float]) -> list[tuple[float, float]]:
        out = []
        for i, feat in enumerate(feats):
            boost = 1.0 + float(self._miss_boost[min(i, self.n - 1)])
            out.append(self._feat_currents(feat, pulls[i] if i < len(pulls) else 0.0, boost))
        return out

    def _feat_currents(self, feat: dict, crumb_pull: float, boost: float) -> tuple[float, float]:
        """LC4 gets angular velocity, LPLC2 gets angular size (Ache et al. 2019)."""
        dtheta = float(feat["dtheta"]) - C.DTHETA_KNEE
        if dtheta <= 0.0:
            return 0.0, 0.0
        rf = max(0.0, 1.0 - feat["dist"] / (C.RF_REACH * max(feat["r"], 1.0)))
        if rf <= 0.0:
            return 0.0, 0.0
        # pale high-hand shadow still expands on the retina; don't zero it out
        contrast = 0.55 + 0.45 * min(1.0, float(feat["alpha"]) / C.SHADOW_A_LOW)
        theta_n = min(1.0, float(feat["theta"]) / math.pi)
        expanding = min(1.0, float(feat["dtheta"]) / 2.0)
        i_lc4 = min(C.INJECT_CAP, dtheta * C.LC4_GAIN * rf * contrast * boost)
        i_lplc = min(C.INJECT_CAP, theta_n * C.SIZE_GAIN * rf * expanding * contrast * boost)
        return i_lc4, i_lplc

    def _fallback(self, feats: list[dict]) -> list[dict]:
        outs = []
        for i, feat in enumerate(feats):
            boost = 1.0 + float(self._miss_boost[min(i, self.n - 1)])
            i_lc4, i_lplc = self._feat_currents(feat, 0.0, boost)
            esc = (i_lc4 + i_lplc) > 0.65
            outs.append({"escape": esc, "side": feat["side"], "dnp01": esc})
        return outs

    def step_all(self, feats: list[dict], dt: float, crumb_pulls: list[float]) -> list[dict]:
        """one brain step for the scene. synchronous — the thread above calls it."""
        self._miss_boost = np.maximum(0.0, self._miss_boost - dt * 0.35)
        n = len(feats)
        outs = [{"escape": False, "side": f["side"], "dnp01": False} for f in feats]

        if not self.ok or self.brain is None:
            return self._fallback(feats)

        drive = []
        for i, feat in enumerate(feats):
            boost = 1.0 + float(self._miss_boost[min(i, self.n - 1)])
            drive.append(self._feat_currents(feat, crumb_pulls[i], boost))

        # with one brain, the fly under the most threatening shadow gets it
        if self.batch < n:
            best = max(range(n), key=lambda i: drive[i][0] + drive[i][1])
            if drive[best][0] + drive[best][1] <= 0.0:
                best = self.target if 0 <= self.target < n else 0
            if best != self.target:
                self._ring[:] = 0
                self.target = best
            slots = [best]
        else:
            slots = list(range(min(n, self.batch)))

        lc4 = {"L": np.zeros(self.batch, np.float32), "R": np.zeros(self.batch, np.float32)}
        lp = {"L": np.zeros(self.batch, np.float32), "R": np.zeros(self.batch, np.float32)}
        crumb = {"L": np.zeros(self.batch, np.float32), "R": np.zeros(self.batch, np.float32)}
        for slot, i in enumerate(slots):
            side = feats[i]["side"]
            lc4[side][slot] = drive[i][0]
            lp[side][slot] = drive[i][1]
            crumb[side][slot] = crumb_pulls[i]

        inject = []
        for side in ("L", "R"):
            if lc4[side].any() and len(self._lc4[side]):
                inject.append((self._lc4[side], lc4[side]))
            if lp[side].any() and len(self._lplc2[side]):
                inject.append((self._lplc2[side], lp[side]))
            if crumb[side].any():
                for cells in (self._lc10[side], self._lb3c[side]):
                    if len(cells):
                        inject.append((cells, np.minimum(crumb[side], 0.9)))

        with self._lock:
            fired = self.brain.step(inject=inject if inject else ())
        per = fired if isinstance(fired, list) else [fired]

        self._ring_i = (self._ring_i + 1) % C.DNP01_WINDOW
        self._ring[:, self._ring_i] = 0
        for slot, i in enumerate(slots):
            if slot >= len(per):
                break
            fset = set(np.asarray(per[slot]).tolist())
            for s in ("L", "R"):
                idx = self._dnp01[s]
                if len(idx) and fset.intersection(idx.tolist()):
                    self._ring[i, self._ring_i] += 1
                    self._dn_side[i] = s

        # DNp01 ticks over on its own about once a second, so one spike is not a
        # takeoff — a real loom makes it burst
        burst = self._ring.sum(axis=1)
        for i in slots:
            if burst[i] >= C.DNP01_BURST:
                outs[i] = {"escape": True, "side": self._dn_side[i], "dnp01": True}
                self._ring[i, :] = 0
        return outs

    # ---- misses ---------------------------------------------------------

    def pulse_miss(self, fly_i: int = 0):
        self._miss_boost[fly_i] = min(1.2, float(self._miss_boost[fly_i]) + 0.7)
        self._miss_boost = np.minimum(1.2, self._miss_boost + 0.25)
        if not self.ok or not self._has_ppl:
            return
        if self._thread and self._thread.is_alive():
            with self._io:
                self._miss_request += 1
        else:
            self._pulse_ppl()

    def _pulse_ppl(self):
        amt = np.full(self.batch, 0.9, np.float32)
        inj = [(self._ppl[s], amt) for s in ("L", "R") if len(self._ppl[s])]
        if not inj:
            return
        try:
            with self._lock:
                self.brain.step(inject=inj)
        except Exception:
            pass

    def label(self) -> str:
        if self.loading or not self.ready:
            return f"loading… {self.status}"
        if self.ok:
            tag = "real wiring" if self.mode == "real" else "shuffled"
            extra = "" if self.batch >= self.n else " · 1 brain, time-shared"
            return f"{tag} · MaleCNS v1.0{extra}"
        return f"loom fallback · {self.error or 'no flybrain'}"

    def badge(self) -> tuple[str, tuple]:
        if self.loading or not self.ready:
            return "LOADING MaleCNS", (255, 200, 120)
        if not self.ok:
            return "LOOM FALLBACK", (200, 180, 140)
        if self.mode == "real":
            return "REAL WIRING", (120, 220, 140)
        return "SHUFFLED", (255, 110, 90)
