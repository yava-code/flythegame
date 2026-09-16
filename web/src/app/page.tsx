import { DemoVideo } from "@/components/DemoVideo";

const GH = "https://github.com/yava-code/flythegame";
const MALE = "https://male-cns.janelia.org/";
const CELL = "https://www.cell.com/";
const FLYBRAIN = "https://pypi.org/project/flybrain/";

export default function Page() {
  return (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>

      <header className="nav">
        <div className="wrap nav-inner">
          <a className="brand" href="#top" translate="no">
            Fly Swatter
          </a>
          <nav className="nav-links" aria-label="Primary">
            <a href="#how">How it works</a>
            <a href="#demo">Demo</a>
            <a href="#play">Play</a>
            <a href="#links">Links</a>
            <a href={GH} target="_blank" rel="noreferrer">
              GitHub
            </a>
          </nav>
        </div>
      </header>

      <main id="main">
        <section className="hero wrap" id="top">
          <div className="hero-bg" aria-hidden="true">
            <DemoVideo src="/media/loop.mp4" poster="/media/poster.jpg" loop />
          </div>
          <div className="hero-copy">
            <p className="eyebrow">tech demo · MaleCNS v1.0</p>
            <h1>
              Fly Swatter
              <span>a real fruit-fly brain in the loop</span>
            </h1>
            <p className="lede">
              The fly never sees your hand. It sees the shadow on the table —
              then ~166k frozen neurons decide whether to freeze or take off.
            </p>
            <div className="cta-row">
              <a className="btn btn-primary" href="#demo">
                Watch the demo
                <span className="arrow" aria-hidden="true">
                  ↓
                </span>
              </a>
              <a className="btn btn-ghost" href={GH} target="_blank" rel="noreferrer">
                GitHub
                <span className="arrow" aria-hidden="true">
                  ↗
                </span>
              </a>
            </div>
          </div>
        </section>

        <section className="section wrap" id="how">
          <h2>How a slap becomes an escape</h2>
          <p className="sub">
            No scripted “if close then jump.” Same looming math the fly’s visual
            system uses, wired through the real MaleCNS connectome.
          </p>

          <div className="pipeline">
            <article className="step">
              <div className="n">01 · stimulus</div>
              <h3>Shadow only</h3>
              <p>
                The hand sprite is decoration. The fly’s input is the table
                blob: area, growth, coverage of its receptive field.
              </p>
            </article>
            <article className="step">
              <div className="n">02 · loom</div>
              <h3>
                η = dA/dt / A
              </h3>
              <p>
                Angular expansion rate. Fast-growing shadow = “something is
                about to hit me.”
              </p>
            </article>
            <article className="step">
              <div className="n">03 · cells</div>
              <h3>LC4 + LPLC2</h3>
              <p>
                LC4 tracks angular velocity. LPLC2 tracks size. Together they
                arm the escape circuit.
              </p>
            </article>
            <article className="step">
              <div className="n">04 · burst</div>
              <h3>DNp01</h3>
              <p>
                Giant fiber fires → takeoff in ~50–150&nbsp;ms. Yellow freeze is
                your hit window. Wait and it’s gone.
              </p>
            </article>
          </div>

          <p className="formula">
            pathway: <code>shadow → LC4 + LPLC2 → DNp01 → takeoff</code>
            <br />
            weights: frozen · never trained to play this game
          </p>

          <div className="frame" style={{ marginTop: "1.75rem" }}>
            <div className="frame-inner">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                className="pathway-img"
                src="/media/pathway.png"
                alt="Diagram: shadow to eta to LC4/LPLC2 to DNp01 escape"
                width={1536}
                height={1024}
                loading="lazy"
              />
            </div>
            <p className="caption">one-screen version of the circuit for sharing</p>
          </div>
        </section>

        <section className="section wrap" id="demo">
          <h2>32 seconds of the experiment</h2>
          <p className="sub">
            Mute demo. Watch the thinking log top-right — that’s cell activity,
            not a bot script.
          </p>

          <div className="split">
            <div>
              <div className="frame">
                <div className="frame-inner">
                  <DemoVideo src="/media/demo.mp4" poster="/media/poster.jpg" />
                </div>
              </div>
              <p className="caption">
                full muted capture · 1920×1080 · system audio stripped for the web
              </p>
            </div>
            <div>
              <ul className="list">
                <li>
                  <span className="tag">tell</span>
                  <div>
                    <strong>Yellow freeze</strong>
                    <span>LC4/LPLC2 saw loom. Slap now — that’s the skill window.</span>
                  </div>
                </li>
                <li>
                  <span className="tag">miss</span>
                  <div>
                    <strong>DNp01 burst</strong>
                    <span>Giant fiber takeoff. Hand recoil. Fly lives.</span>
                  </div>
                </li>
                <li>
                  <span className="tag">ctrl</span>
                  <div>
                    <strong>T = real vs shuffled</strong>
                    <span>
                      Same synapse degrees, random partners. Escape gets worse —
                      that’s the control.
                    </span>
                  </div>
                </li>
                <li>
                  <span className="tag">ctrl</span>
                  <div>
                    <strong>H = hide the hand</strong>
                    <span>Sprite off, shadow stays. Proves the fly never needed the art.</span>
                  </div>
                </li>
              </ul>
              <div className="badge-row">
                <span className="badge ok">REAL WIRING</span>
                <span className="badge warn">SHUFFLED</span>
                <span className="badge">CC BY 4.0 · Berg et al. 2026, Cell</span>
              </div>
            </div>
          </div>
        </section>

        <section className="section wrap" id="shot">
          <h2>What you see on screen</h2>
          <p className="sub">
            HUD is the science: title, timer, wiring badge, and a live log of
            what one fly’s cells are doing.
          </p>
          <div className="frame">
            <div className="frame-inner">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/media/screenshot.png"
                alt="Gameplay screenshot: hand over blue table, fly thinking log open"
                width={1600}
                height={900}
                loading="lazy"
              />
            </div>
          </div>
          <div className="sprites" aria-hidden="true">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/sprites/hand.png" alt="" width={120} height={64} />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/sprites/fly.png" alt="" width={48} height={48} />
          </div>
        </section>

        <section className="section wrap" id="play">
          <h2>Run it locally</h2>
          <p className="sub">
            Python 3.10–3.12, pygame, flybrain. MaleCNS loads in the background
            (~260&nbsp;MB). Until then you get a loom-threshold stand-in on the
            same shadow numbers.
          </p>
          <pre
            style={{
              margin: 0,
              padding: "1.1rem 1.2rem",
              borderRadius: "1rem",
              border: "1px solid var(--line)",
              background: "rgba(0,0,0,0.35)",
              overflowX: "auto",
              fontSize: "0.82rem",
              color: "var(--cyan)",
            }}
          >{`git clone ${GH}.git
cd flythegame
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
set FLY_DATA=%CD%\\fly-data
flybrain download
python -m flygame --windowed`}</pre>
          <div className="cta-row" style={{ marginTop: "1.25rem" }}>
            <a className="btn btn-primary" href={GH} target="_blank" rel="noreferrer">
              Open repository
              <span className="arrow" aria-hidden="true">
                ↗
              </span>
            </a>
            <a className="btn btn-ghost" href={MALE} target="_blank" rel="noreferrer">
              MaleCNS site
            </a>
          </div>
        </section>

        <section className="section wrap" id="links">
          <h2>Links & credit</h2>
          <p className="sub">
            Connectome is open science. Game is a thin pygame shell around frozen
            weights — cite the paper if you remix.
          </p>
          <div className="links">
            <a className="link-card" href={GH} target="_blank" rel="noreferrer">
              <small>code</small>
              <strong translate="no">GitHub</strong>
              <p>yava-code/flythegame · run, fork, film</p>
            </a>
            <a className="link-card" href={MALE} target="_blank" rel="noreferrer">
              <small>connectome</small>
              <strong translate="no">MaleCNS v1.0</strong>
              <p>~166k neurons · HHMI Janelia / Cambridge / MRC LMB / Google</p>
            </a>
            <a className="link-card" href={FLYBRAIN} target="_blank" rel="noreferrer">
              <small>sim</small>
              <strong translate="no">flybrain</strong>
              <p>LIF stepping of the frozen connectome (MIT)</p>
            </a>
          </div>
          <p className="caption" style={{ marginTop: "1.25rem" }}>
            Cite Berg et al. 2026, <em>Cell</em>. License of the connectome: CC BY 4.0.{" "}
            <a href={CELL} target="_blank" rel="noreferrer">
              Cell
            </a>
          </p>
        </section>
      </main>

      <footer className="footer">
        <div className="wrap">
          <span translate="no">Fly Swatter · MaleCNS tech demo</span>
          <span>built to explain looming escape in one scroll</span>
        </div>
      </footer>
    </>
  );
}
