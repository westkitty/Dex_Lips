# Mouth sets

## `generic_muzzle/` — shipped

Nine Rhubarb mouth states (X, A–H) for a dog-like muzzle, **procedurally drawn** by `src/dex_lips/muzzle_template.py`
(regenerate with `PYTHONPATH=src python -m dex_lips.muzzle_template --out assets/mouth_sets/generic_muzzle`).
It is a generic template: it is not derived from, and not a likeness of, any character (not Dexter, not Tiger).
Sprites are top-anchored: the philtrum/upper lip stays put under the nose and the lower jaw drops.
See `contact_sheet.png`. X is a closed resting mouth line because the template is stand-alone art.

| Shape | State |
|---|---|
| X | rest: closed muzzle line |
| A | closed, lips pressed (P B M) |
| B | slightly open, teeth nearly together (most consonants, EE) |
| C | open, lower jaw dropped, tongue low (EH AE) |
| D | wide open, canines and tongue visible (AA) |
| E | slightly rounded opening (AO ER) |
| F | puckered small round opening (OO OW W) |
| G | upper teeth resting on lower lip (F V) |
| H | open with tongue tip raised (L) |

In the app, the **muzzle-template** construction mode draws the same shapes sized to your selected box and tints the outline from the surrounding paint.

## `dexter_muzzle/` — shipped (built only from the approved sheet)

Source: `assets/reference/dexter/dexter_reference_sheet.png` ("DEXTER 'Furious Little Stinkweasel' – Character Reference Sheet"),
supplied and approved by the owner on 2026-11-20, sha256 `ed81548c07c3e3b47a189a0aa2a502fe171146a1f2a96060d790e22091c12c41`.
Rebuild with `python scripts/build_dexter_mouths.py` (needs Pillow, numpy, opencv-python; refuses to run if the sheet hash differs).
Nothing was drawn freehand: every pixel is cut from the sheet, then edited as listed. See `contact_sheet.png`.

Cells used (row/column counted on the sheet; header text as printed on the sheet, typos included):

| Cell | Header on sheet | What it shows | Used for |
|---|---|---|---|
| row 1, col 3 | "Left-Proflle" | front-facing head, relaxed closed mouth | base still (`assets/reference/dexter/dexter_front_still.png`), the fur around every sprite, X |
| row 1, col 1 | "Front-01" | front-facing head, pressed downturned mouth | A |
| row 1, col 4 | "Profile" | front-facing head, open mouth with teeth and tongue | C, D, E, F, H |
| row 2, col 4 | "Determinted" | front-facing head, teeth showing | B, G |

Not used: back, three-quarter, lying-down and side views; the tongue-out tilted head (row 2 col 3); the palette strip (colours come straight from the cells).

| Shape | Source cell | Edit |
|---|---|---|
| X | row 1 col 3 | none (base mouth) |
| A | row 1 col 1 | none |
| B | row 2 col 4 | none |
| C | row 1 col 4 | none |
| D | row 1 col 4 | mouth stretched 1.40x downward from the upper lip |
| E | row 1 col 4 | 0.74x wide, 1.15x tall (rounder) |
| F | row 1 col 4 | 0.52x wide, 0.85x tall (small puckered opening) |
| G | row 2 col 4 | 0.88x wide, 0.70x tall (flatter, teeth on lip) |
| H | row 1 col 4 | 0.92x wide, 1.20x tall (tongue visible) |

How it is assembled: each sprite is a 148x88 px muzzle patch (4x LANCZOS upscale of a 37x22 px area under the nose). The base cell's own mouth line is removed by OpenCV inpainting, the source cell's mouth pixels are colour-matched to the base fur and composited in, and the patch fades out with a feathered ellipse. The four cells share one scale (their noses measure 18–19 px wide), so they are aligned on the nose with no resizing.

Limits, stated plainly:
- The sheet is small: each mouth is about 30x12 px, so the sprites are soft upscales.
- The sheet has no rounded or puckered mouth, so E and F are scaled edits of the "Profile" open mouth, and G is a flattened "Determined" mouth. They are not separate drawings on the sheet; replace them if the owner draws dedicated ones.
- The jaw does not move; only the mouth area changes, as in the sheet's own front-facing heads.
- `rig.template.json` anchors the sprites for `dexter_front_still.png`; on other pictures you have to re-place and re-scale them.
