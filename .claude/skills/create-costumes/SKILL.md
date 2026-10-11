---
name: create-costumes
description: Add a new costume to the Flight Score "Create Your Character" page (create-character.html) from a picture in North_American_Birds/Costumes. Handles all three kinds - head pieces (helmets, masks, hats), shirts, and pants - for both the adult and the kid figure, then commits and pushes. Use this whenever the user wants to add, put on, fit, resize, or fix a costume, helmet, mask, hat, shirt, t-shirt, pants, jeans, or other outfit on the character, or drops a new image into the Costumes folder, even if they don't say "costume".
---

# Create Costumes

Turns a costume picture into a wearable option on `create-character.html`
(repo root of the BirdApp project, published on GitHub Pages). The user will
say which kind of costume it is - **head piece**, **shirt**, or **pants** -
and which picture. If they didn't say the kind, it is usually obvious from
the picture; only ask if it truly isn't.

The user is not a programmer. Report results in plain words ("the mask now
covers the whole head and the eyes peek through"), not CSS.

## What the user cares about (learned the hard way)

These came from the user's own corrections, so treat them as requirements:

- **Never resize the character's eyes to fit a mask.** Make the mask's eye
  holes fit the eyes (shrink_holes.py) or resize the mask. Eyes stay the same
  size everywhere.
- **Head pieces cover the entire head**, like a helmet - not a small face
  mask. Only the eyes peek out, centred in the eye holes.
- **Clean the art.** Remove leftover background, halos, and anything the
  user calls out (e.g. stray brown bits on the cardinal helmet).
- **Shirts** fit the body: cover a little of the neck, short sleeves, and
  everything is clipped to the body outline so nothing sticks out.
- **Pants** fit the legs the same way, under the shirt at the waist.
- **Nothing covers the eyes** except a mask with holes.
- **Both kid and adult** must look right. Always check both.
- **The costume must be remembered** after closing the tab or pressing back
  (localStorage save/restore).

## Tools

All scripts are in `scripts/` next to this file. Run them with `python`
(numpy + Pillow). They read the figures directly from `create-character.html`,
so measurements always match the live page. Each prints usage with `-h`.
Work on copies in the scratchpad; only copy finished art into
`North_American_Birds/Costumes/`. Never re-run cleanup on an already-cleaned
file in place - earlier hand fixes get lost.

| Script | Purpose |
|---|---|
| `remove_bg.py IN OUT [--hole fx,fy]...` | Remove the background (and clear enclosed eye holes). Prints the main fabric colour. |
| `find_holes.py IMG` | Find see-through eye holes; prints `--holes LX,RX,Y` for preview. |
| `shrink_holes.py IN OUT --hole fx,fy ... --eye-frac F` | Redraw eye holes just larger than the eyes. |
| `measure_figure.py [head\|torso\|legs]` | Where the body is on each row, for sizing. |
| `extract_graphic.py CUTOUT OUT` | Lift a logo/print off a garment photo. |
| `preview.py ...` | Render the costume on adult + kid exactly as the page will; prints eye CSS and a hole-fit verdict. |

Look at every preview image yourself (Read the PNG) before touching the page.
Browser-pane screenshots are unreliable here, so the preview is the main check.

## Workflow

### 1. Prepare the art
1. Find the picture (usually `North_American_Birds/Costumes/<name>.png`, or
   wherever the user says). View it.
2. If it has a background: `remove_bg.py`. For masks, pass `--hole` at each
   eye hole's approximate position so the holes become see-through. Raise
   `--thresh` if background remains; lower it if the costume gets eaten.
3. Save the cleaned file as `<name>_front.png` (head pieces) or
   `<name>_cutout.png` in a scratch folder first; view it on a coloured
   background to spot halos.

### 2. Fit it - by kind

**Head piece (helmet / mask / hat)** - an `<img>` overlay on top of everything.
1. `find_holes.py` on the cleaned image -> hole centres.
2. Start from an existing head piece's size and adjust (adult W,L,T then kid):
   cardinal helmet `58,25,-4.75` / `68,22.5,-5.5`; peregrine `58,24,-1.3` /
   `68,22,-2.16`. Width covers the whole head plus a little; top is negative
   so it sits over the crown.
3. `preview.py --image X --adult W,L,T --kid W,L,T --holes LX,RX,Y --cls NAME-on --crop head`.
   Iterate until both figures have the whole head covered and the eyes are
   centred in the holes. The kid usually needs a slightly larger width %.
4. If the verdict says the holes are too big, run `shrink_holes.py` with the
   printed `--eye-frac`, then preview again. Don't shrink the eyes.
5. Note the printed eye CSS - it goes into the page.

**Shirt** - a fitted SVG shape clipped to the body (`.shirt-overlay`).
- Plain-colour shirt: reuse the page's shirt shape with a fixed colour.
- Picture shirt (logo/print): fitted shape in the shirt's main colour (from
  `remove_bg.py`) + the print from `extract_graphic.py` placed on the chest,
  exactly like the FlightScore shirt. Preview with
  `--use-page-shape shirt --shape-color "#hex" --graphic logo.png --graphic-adult CX,CY,W --graphic-kid CX,CY,W --crop torso`.
  FlightScore logo sits at adult `54.6,32,30`, kid `58,38,30`.
- A different cut (long sleeves, tank top) means a new shape: draw it with
  `measure_figure.py torso` and pass `--shape-adult/--shape-kid`.

**Pants** - a fitted SVG shape clipped to the body (`.pants-overlay`, below
the shirt). Same idea as shirts: page shape in the garment's main colour,
optional details (pockets, seams) drawn as extra paths, preview with
`--use-page-shape pants --crop legs`. A flat product photo of jeans can't be
pasted onto the legs - it won't follow the pose - so recreate it as the fitted
shape in the denim colour.

### 3. Wire it into the page
Read `references/page-anatomy.md` - it lists every place a new costume touches
(CSS, markup, option box, mutual exclusivity, save, restore) with copyable
templates. Quick way to find them all: search the page for the most similar
existing costume's class, e.g. `grep -n "peregrine-on" create-character.html`
for a head piece or `grep -n "flightscore-on"` for a picture shirt; every hit
needs a sibling for the new costume.

Put the new costume in the next free option box of its section.

### 4. Check
1. `git check-attr filter -- North_American_Birds/Costumes/<file>.png` must
   say `unset`. (LFS files show up broken on GitHub Pages; `.gitattributes`
   already excludes `North_American_Birds/Costumes/*.png`. Images stored
   elsewhere need their own line.)
2. Syntax-check the page script: extract each `<script>` block to a temp `.js`
   file and run `node --check` on it.
3. Re-run `preview.py` with the final numbers and view it for both ages.
4. Make sure saving works: the new class is in `saveCharacter()`, restored in
   `restoreCharacter()`, and cleared by the other options in its group.

### 5. Commit and push
Stage only the page and the new costume files (the Costumes folder has other
untracked work in progress - don't sweep it in). Commit with a plain message
like "Add Blue Jeans to the Pants section" and push to `master`. Tell the user
it will be live on the site in a minute or two, and that a hard refresh
(Ctrl+F5) may be needed.

## Windows notes
- Prefer the PowerShell tool for running Python; Git Bash can eat `$` signs.
- For inline Python in PowerShell use `@' ... '@ | python -`.
