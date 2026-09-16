# fly swatter + a real fruit fly brain

short kitchen-table swatter. the fly does not run `if distance < r: jump`.

it only ever sees your **shadow** on the table. how big that blob looks from where it
sits, and how fast it is growing, become current in looming detectors taken straight
from the **MaleCNS v1.0** connectome, stepped by [`flybrain`](https://pypi.org/project/flybrain/).
when the giant fiber bursts, the fly bolts.

weights are frozen. nothing here was trained to play the game.

```bash
python -m venv .venv
# windows: .venv\Scripts\activate
pip install -r requirements.txt
set FLY_DATA=%CD%\fly-data
flybrain download          # ~260MB once
python -m flygame            # 1920×1080 fullscreen. --windowed for a window
```

python 3.10–3.12 (3.11 here). the window opens right away and MaleCNS loads in the
background — the status line tells you where it is. until it's up you play against a
loom-threshold stand-in that reads the *same* shadow numbers, then it flips to
`real wiring`. on windows `run.bat` does the venv dance for you.

## controls

| | |
|---|---|
| mouse | hand follows the cursor |
| **RMB drag** up/down (or wheel) | hand height. high = small pale shadow |
| **LMB** | swat |
| **T** | `real wiring` / `shuffled` |
| **H** | hide hand sprite, keep the shadow |
| **F** / F11 | toggle fullscreen |
| **M** | mute |
| **Esc** | pause + MaleCNS credit |
| **R** | restart the 60s |

the one thing worth learning: bring the hand in **high** and drop it **straight onto**
the fly. a naive slap from low is loud — the shadow is already big, LC4 sees it grow,
DNp01 fires ~50–150 ms before you land, and the cloth is empty. that's the game.

## what is actually simulated

| what happens | cells (MaleCNS names, checked against the dataset) |
|---|---|
| how fast the shadow is growing | `LC4` — angular velocity |
| how big it looks | `LPLC2` — angular size |
| crumb on the table | `LC10a`, plus `LB3c` when the dataset has it |
| a miss slapping the table | `PPL101` |
| takeoff | `DNp01`, the giant fiber |

the split follows Ache et al. 2019: LC4 carries expansion speed, LPLC2 carries size, and
DNp01 adds them up. drive is scaled by shadow contrast too, so the washed-out penumbra
of a high hand is a much weaker stimulus than a hard contact shadow.

`DNp01` is one neuron a side and it ticks over on its own at roughly a spike a second in
this model, so a lone spike is not a takeoff — the fly leaves on a burst (2 spikes inside
~60 ms). without that you get a fly that jumps at nothing.

two things about running 166,700 neurons next to a 60 fps game loop, both worth knowing
before you believe anything on screen:

* the brain gets its own thread. a step costs ~10 ms here, so stepping it inside the frame
  pinned the game at 20 fps.
* **one** brain is simulated, and it goes to whichever fly the palm is threatening. a
  batch of three costs ~36 ms a step, which is slower than the 20 ms it is meant to
  represent, and a fly reacting in slow motion is worse than a shared nervous system. the
  other flies have no shadow growing over them, so under the burst rule they could not
  take off anyway. `FLY_BATCH=3` gives every fly its own brain if your machine can take it.

**shuffled** keeps every synaptic weight, every sign and each neuron's out-degree, and
only changes which neuron each synapse lands on. same statistics, wrong connectome. in
the check below the real wiring dodges 8/8 swats and the scrambled one mostly doesn't —
if they ever start behaving the same, the shadow encoder is doing the work and needs
fixing, not the UI.

## checking it

```bash
.venv\Scripts\python.exe scripts\verify_flies.py    # behaviour + the loom path
.venv\Scripts\python.exe scripts\probe_loom.py      # currents, frame by frame, during a swat
.venv\Scripts\python.exe scripts\balance_sweep.py   # hit rate vs hit radius and aim
.venv\Scripts\python.exe scripts\shot.py            # png of the scene, no playing
```

what `verify_flies.py` asserts, roughly: flies sit / walk / hop instead of drifting, stay
on the table without gluing themselves to the edges, linger on a crumb, will perch on a
hand that stopped moving; a still hand, a slow creep-down and a swat on the far side of
the table set off nothing; sweeping in low gets noticed 5/5 while sneaking in high gets
noticed 0/5; a swat from height fires DNp01 at ~83 ms while the palm lands at 151 ms; only
the threatened fly reacts when the brain is shared; escapes go away from the palm; and
real wiring survives swats that scrambled wiring does not (last run: 4/8 vs 2/8).

numbers come out of the script, uncurated. if you change the shadow maths, run it again —
that is what it is for.

## art / sound

pixel sheets in `assets/`, cut out of the source images by `scripts/prep_assets.py`
(blob masks, so labels and the baked drop shadow don't come along). the shadow is its own
silhouette, scaled and faded by height, never painted into the hand. sfx and the loop are
generated wavs — soft attack, low volume, chip-ish.

## credit

Connectome: **MaleCNS v1.0** — HHMI Janelia / University of Cambridge / MRC LMB / Google
Research, [CC BY 4.0](https://male-cns.janelia.org/). Cite Berg et al. 2026, *Cell*.

Simulation: [flybrain](https://github.com/alextitonis/fly.ai) (MIT), neuron model after Fly64.

[male-cns.janelia.org](https://male-cns.janelia.org/) ·
[Google Research writeup](https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/) ·
[neuPrint `male-cns:v1.0`](https://neuprint.janelia.org/)
