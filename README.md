# fly swatter + a real fruit fly brain

the fly does not run `if distance < r: jump`.

it only sees your **shadow** on the table. how fast that blob grows (`η = dA/dt / A`)
becomes current in **LC4** and **LPLC2**, taken from the **MaleCNS v1.0** connectome,
stepped by [flybrain](https://pypi.org/project/flybrain/). **DNp01** (giant fiber)
bursts → takeoff. yellow freeze is the tell. slap then. wait and it's gone.

weights are frozen. nothing here was trained to play this.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set FLY_DATA=%CD%\fly-data
flybrain download
run.bat
# or: python -m flygame --windowed
```

python 3.10–3.12 (3.11 here). MaleCNS loads in the background (~260MB). until then
you play a loom-threshold stand-in that reads the same shadow numbers.

## how to play it (and film it)

mouse moves the hand. **RMB** / wheel = height. **LMB** = swat.

watch the log top-right. that's the fly's cells, not a bot.

- freeze (yellow) = LC4/LPLC2 saw looming. that's the hit window
- DNp01 burst = takeoff, you missed
- **T** real wiring vs shuffled (same degrees, random partners)
- **H** hide the hand sprite. the shadow stays. that's the experiment
- Esc = credit

## tweet this

copy `TWEET.txt`. clip ~12s: title card → loom → freeze → slap or miss → hit T.

## credit

Connectome: **MaleCNS v1.0** — HHMI Janelia / University of Cambridge / MRC LMB / Google
Research, [CC BY 4.0](https://male-cns.janelia.org/). Cite Berg et al. 2026, *Cell*.

Simulation: [flybrain](https://github.com/alextitonis/fly.ai) (MIT).

[male-cns.janelia.org](https://male-cns.janelia.org/) ·
[Google Research](https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/) ·
[neuPrint male-cns:v1.0](https://neuprint.janelia.org/)
