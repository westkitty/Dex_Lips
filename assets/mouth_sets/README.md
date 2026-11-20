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

## Dexter muzzle set — NOT built yet (waiting on art access)

The owner supplied and approved a Dexter reference sheet on 2026-11-20 ("DEXTER 'Furious Little Stinkweasel' – Character Reference Sheet").
The automated build environment could not read that file (it is held as a private attachment), so it is **not** in this repo and **no Dexter mouths were drawn**. Dexter's likeness was not invented or approximated.

To build the Dexter set, the sheet needs to be placed at `assets/reference/dexter/dexter_reference_sheet.png` (the owner has approved this), after which the nine states are cut and edited only from these cells:

| Needed from the sheet | Used for |
|---|---|
| Front-facing neutral head (closed mouth) | X (rest), A (pressed), base for B/G/H |
| Front-facing joyful/open mouth with tongue | C, D, H (open shapes, tongue) |
| Determined pose showing teeth | B (teeth together), G (teeth on lip) |
| Profile with open mouth (if present) | jaw-drop distance and tongue reference for C/D |
| Palette strip | exact line, fur, gum, tongue and teeth colours |

If the sheet lacks a usable rounded/puckered mouth for E and F, those two would have to be drawn by the owner (or approved as edits of the open-mouth cell); they will not be invented.
