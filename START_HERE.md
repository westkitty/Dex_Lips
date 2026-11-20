# Start here

Dex_Lips makes a talking-mouth MP4 from **a picture or video**, **a voice recording** and **nine mouth pictures**.
There are two parts:

| Part | What it is for | Where it runs |
|---|---|---|
| **Website** – https://westkitty.github.io/Dex_Lips/ | Make and review the nine mouth pictures (X, A–H) from your own art, entirely in your browser. Nothing is uploaded. | Any modern browser |
| **Local app** – `python3 app.py` | Detect mouth timing from the voice, edit it, and render the MP4. | Your own computer, at `http://127.0.0.1:7860` only |

## 1 · Install the local app (once)

Needs Python 3.11+ and FFmpeg (with libx264 and AAC).

```bash
git clone https://github.com/westkitty/Dex_Lips.git && cd Dex_Lips
python3 -m pip install -r requirements-ui.txt
python3 -m unittest discover -s tests      # optional self-check
python3 app.py                             # then open http://127.0.0.1:7860
```

The app never creates a public link (`share=False`, bound to 127.0.0.1).

## 2 · Install a mouth-timing engine (pick one or both)

Without an engine, automatic timing is **BLOCKED** and you type or paste the timing yourself. The app never pretends.

**Rhubarb Lip Sync (recommended, small, MIT license)**

1. Download the release for your system from https://github.com/DanielSWolf/rhubarb-lip-sync/releases (tested: v1.14.0).
2. Unzip it anywhere and keep the `rhubarb` program next to its `res` folder.
3. Put that folder on your `PATH` (or make a tiny wrapper script called `rhubarb` that runs it).
4. Check: `rhubarb --version` → `Rhubarb Lip Sync version 1.14.0`.

SHA-256 of the Linux zip that was tested (`Rhubarb-Lip-Sync-1.14.0-Linux.zip`):
`a9a9074862cff47b2d59b8bf399a678a3b0b74f9452ad6ad94cb292913dd8667` (GitHub does not publish a digest for this release; this is the value observed on 2026-11-20 and pinned in CI).
On macOS, the first run may need *System Settings → Privacy & Security → Open anyway*.

**wav2vec2 phoneme recognizer (bigger, Apache-2.0, more accurate on the test set)**

```bash
python3 -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python3 -m pip install -r requirements-engines.txt
PYTHONPATH=src python3 -m dex_lips.engines --fetch-model   # one explicit ~1.3 GB download
PYTHONPATH=src python3 -m dex_lips.engines --status
```

After the one-time download the model is loaded **offline** from the Hugging Face cache; the app never downloads it silently.
It needs roughly 2 GB of free RAM (1.6 GB peak was measured on a 4-second clip; 30-second clips need more). On an 8 GB Mac, close other big apps first, or use Rhubarb.

Which is better? See [ACCURACY.md](ACCURACY.md) (8 short English clips, reviewer-judged reference; read the caveats).

## 3 · Make a video

1. **Upload** the picture/video and the voice recording.
2. **Click the mouth** on the reference frame (sliders fine-tune it).
3. **Mouth pictures:** generate a draft (trace the source mouth, a graphic shape, or the generic muzzle template; pick a *jaw mode* – human, muzzle, beak or wide jaw), or upload your own ZIP of nine transparent PNGs. Review them.
4. **Timing:** press *Analyze the actual audio*. Check the waveform strip, fix rows in the cue table, press *Apply*.
5. **Preview** 2 seconds, then **Render verified MP4**. Download the MP4 and the receipt.

**Dexter:** a ready-made Dexter mouth set, cut only from the owner-approved reference sheet, is in `assets/mouth_sets/dexter_muzzle/` (zip its nine PNGs to upload them), with the matching front-facing still at `assets/reference/dexter/dexter_front_still.png`. See `demos/demo_dexter_*.mp4`.

Phone videos: variable or 29.97 fps clips are converted to a constant-rate working copy, and if the voice and video lengths differ you choose **trim** or **pad**. If the video already has a moving mouth, either confirm it is neutral or pick a **mouth cover** (patch or inpaint).

## What stays private

- Everything runs on your computer. No uploads, accounts, telemetry or paid services.
- The website has no backend; your art never leaves the browser.
- Scratch files live in your temp folder and are pruned after an hour.
- **This GitHub repository is public.** Do not commit your private art, voices or footage. See `docs/SECURITY_PRIVACY.md` and `docs/RIGHTS.md`.

## Decisions still open (owner)

- **Code license: UNDECIDED.** Nothing in this repo grants a license yet. See `docs/RIGHTS.md`.
- **Tiger reference images** are in this public repo although `docs/RIGHTS.md` says they should not be rehosted publicly. Decide whether to keep or remove them.
