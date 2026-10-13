# create-character.html - costume anatomy

How the character page draws costumes, and every spot a new one must touch.
Line numbers drift, so search for the names shown here.

## Contents
1. Coordinate system
2. Layers and state
3. Adding a head piece
4. Adding a shirt
5. Adding pants
6. Save / restore

## 1. Coordinate system

- Everything sits inside `.figure-wrap`, which has the figure's aspect ratio:
  adult SVG viewBox `0 0 97 200`, kid `0 0 55 113`. The kid figure is shown
  at `--age-scale: 0.82`.
- Overlay CSS uses **% of the wrapper**: `left` / `width` are % of its width,
  `top` is % of its height. A negative `top` lifts a hat above the crown.
- `<img>` overlays are anchored top-left; `.fs-logo` is centred
  (`transform: translate(-50%,-50%)`).
- Default eyes: adult left 50.5% / right 57.5%, top 9.5%, width 5.5%;
  kid 53% / 61%, top 11.5%, width 6.5%. Eye positions while a mask is worn
  come from preview.py; the eye **width never changes**.
- Garment SVGs use the figure's own viewBox coordinates and are clipped by a
  `<clipPath>` holding the figure outline (copy it from an existing garment).

## 2. Layers and state

Order inside `.figure-wrap` (later = on top): figure SVG, eyes, mouths,
pants and jeans (z1), shirts (z2), `.fs-logo` (z2), kid hair (z3), head pieces (z4).

State lives in classes on `<body>`:

| Class | Meaning |
|---|---|
| `kid-mode` | kid figure shown (absent = adult) |
| `helmet-on`, `peregrine-on` | head pieces - only one at a time |
| `shirt-on`, `flightscore-on` | shirts - only one at a time |
| `pants-on`, `jeans-on` | pants - only one at a time |
| `has-hair` | kid hairstyle chosen |

Show rules always come in adult/kid pairs:
`body.X-on:not(.kid-mode) .adult-thing` and `body.X-on.kid-mode .kid-thing`.

Option boxes are built in `selectPart()` from `PART_OPTIONS`
(`Helmet: 6, Shirt: 6, Pants: 6`); each box index is one option.

## 3. Adding a head piece (class `NAME-on`)

**CSS** - after the peregrine block:
```css
/* ── NAME overlay ── */
.NAME-overlay {
  position: absolute; display: none; z-index: 4; pointer-events: none;
  width: W%; left: L%; top: T%;               /* adult, from preview.py */
}
body.kid-mode .NAME-overlay { width: W%; left: L%; top: T%; }
body.NAME-on .NAME-overlay { display: block; }

body.NAME-on .adult-eye.eye-left  { left: ..%; top: ..%; }   /* printed by preview.py */
body.NAME-on .adult-eye.eye-right { left: ..%; top: ..%; }
body.NAME-on .kid-eye.eye-left    { left: ..%; top: ..%; }
body.NAME-on .kid-eye.eye-right   { left: ..%; top: ..%; }
```
If the piece hides the mouth or hair, also add
`body.NAME-on .mouth { display: none; }` / `body.NAME-on .kid-hair { display: none; }`.

**Markup** - after the peregrine `<img>` at the end of `.figure-wrap`:
```html
<img class="NAME-overlay" src="North_American_Birds/Costumes/NAME_front.png" alt="..."/>
```

**JS** - add `'NAME-on'` everywhere the head-piece group is listed:
- `makeMaskBox`: `classList.remove('helmet-on', 'peregrine-on', 'NAME-on')`
- `saveCharacter`: the `mask` chain gets another
  `: document.body.classList.contains('NAME-on') ? 'NAME-on'`
- `restoreCharacter`: the `remove(...)` list and the allowed `s.mask` values
- `selectPart`: `else if (part === 'Helmet' && i === N) { makeMaskBox(box, 'North_American_Birds/Costumes/NAME_front.png', 'Alt text', 'NAME-on'); }`

Tip: if there are going to be many head pieces, replace the hard-coded lists
with one `const MASKS = ['helmet-on', 'peregrine-on', ...]` and use
`remove(...MASKS)` / `MASKS.includes(s.mask)`.

## 4. Adding a shirt (class `NAME-on`)

Picture shirts reuse the fitted shirt shapes (`.adult-shirt`, `.kid-shirt`)
with a fixed colour, plus an optional chest graphic - see the FlightScore
block (`flightscore-on`, `.fs-logo`) and copy it:

```css
body.NAME-on:not(.kid-mode) .adult-shirt { display: block; }
body.NAME-on.kid-mode       .kid-shirt   { display: block; }
body.NAME-on .shirt-overlay > path { fill: #HEX; }
.adult-NAMElogo { left: CX%; top: CY%; width: W%; }   /* class fs-logo gives centring */
.kid-NAMElogo   { left: CX%; top: CY%; width: W%; }
body.NAME-on:not(.kid-mode) .adult-NAMElogo { display: block; }
body.NAME-on.kid-mode       .kid-NAMElogo   { display: block; }
```
```html
<img class="fs-logo adult-NAMElogo" src="North_American_Birds/Costumes/NAME_logo.png" alt="..."/>
<img class="fs-logo kid-NAMElogo"   src="North_American_Birds/Costumes/NAME_logo.png" alt="..."/>
```
The `.fs-logo` rules hide every logo by default; only the `NAME-on` rules
show this one.

A different cut needs its own `<svg class="shirt-overlay adult-NAME">` (copy
an existing shirt SVG, give the clipPath a new unique id, replace the shape
`d`) and show rules for it instead of `.adult-shirt`.

**JS**:
- `makeShirtOption`: `classList.remove('shirt-on', 'flightscore-on', 'NAME-on')`
- `selectPart`: `else if (part === 'Shirt' && i === N) { makeShirtOption(box, 'NAME-on', '<img class="option-img" src="North_American_Birds/Costumes/NAME.png" alt="..."/>'); }`
  (the option box shows the original garment picture)
- save/restore: see section 6.

## 5. Adding pants

Pants are a group like shirts (only one at a time), built by
`makePantsOption(box, kind, innerHTML)` with `data-pants`:
box 0 = colour pants (`pants-on`, uses the Pants Color slider),
box 1 = Blue Jeans (`jeans-on`).

**Photo pants (copy the Blue Jeans).** CSS:
```css
.NAME-overlay { position: absolute; inset: 0; width: 100%; height: 100%;
                display: none; z-index: 1; pointer-events: none; }
body.NAME-on:not(.kid-mode) .adult-NAME { display: block; }
body.NAME-on.kid-mode       .kid-NAME   { display: block; }
```
Markup, next to the jeans SVGs (copy them and rename the clipPath ids - ids
must be unique on the page). Each clipPath holds the figure outline (copied
from `adultPantsClip` / `kidPantsClip`) **plus** the between-the-legs fill
path; the kid image also has its own hands-limit clip:
```html
<svg class="NAME-overlay adult-NAME" viewBox="0 0 97 200" preserveAspectRatio="xMidYMid meet">
  <defs><clipPath id="adultNAMEClip"><path d="FIGURE OUTLINE"/><path d="M43,100 H63 V186.5 H43 Z"/></clipPath></defs>
  <g clip-path="url(#adultNAMEClip)"><image href="North_American_Birds/Costumes/NAME_cutout.png"
     x="31.5" y="100" width="43" height="86.5" preserveAspectRatio="none"/></g></svg>
<svg class="NAME-overlay kid-NAME" viewBox="0 0 55 113" preserveAspectRatio="xMidYMid meet">
  <defs><clipPath id="kidNAMEClip"><path d="FIGURE OUTLINE"/><path d="M27.5,66 H37 V104 H27.5 Z"/></clipPath>
        <clipPath id="kidNAMEHands"><path d="M18,60 L47,60 L47,70.5 L41.9,71.8 L41.3,81.5 L46,104 L18,104 L23.6,81.5 L23.1,71.8 L18,70.5 Z"/></clipPath></defs>
  <g clip-path="url(#kidNAMEClip)"><image href="North_American_Birds/Costumes/NAME_cutout.png"
     x="20.5" y="66" width="24" height="38" preserveAspectRatio="none" clip-path="url(#kidNAMEHands)"/></g></svg>
```
x/y/width/height come from the `--garment-adult/--garment-kid` boxes you
settled on in preview.py (width = X1-X0, height = Y1-Y0).

**Fitted colour pants** reuse `.adult-pants` / `.kid-pants` instead:
```css
body.NAME-on:not(.kid-mode) .adult-pants { display: block; }
body.NAME-on.kid-mode       .kid-pants   { display: block; }
body.NAME-on .pants-overlay > path { fill: #HEX; }
```
The Pants Color slider stays tied to `pants-on` only.

**JS**:
- `makePantsOption`: `classList.remove('pants-on', 'jeans-on', 'NAME-on')`
- `selectPart`: `else if (part === 'Pants' && i === N) { makePantsOption(box, 'NAME-on', '<img class="option-img" src="North_American_Birds/Costumes/NAME_cutout.png" alt="..."/>'); }`
- save/restore: section 6.

## 6. Save / restore

`saveCharacter()` writes one object to localStorage key
`flightScoreCharacter`; `restoreCharacter()` reads it on load. `suppressSave`
stops the start-up calls from overwriting the saved character - leave that
alone.

- Head pieces: `mask` already stores the class name - just extend the lists.
- Shirts currently save two booleans (`shirt`, `flightscore`). For a third
  shirt, add another boolean the same way (`NAME: classList.contains('NAME-on')`
  and `toggle('NAME-on', !!s.NAME)`), or switch to one `shirtKind` string -
  but keep reading the old `shirt` / `flightscore` keys so characters people
  already saved still load.
- Pants: `pants` and `jeans` booleans; restore does
  `toggle('pants-on', !!s.pants && !s.jeans)` and `toggle('jeans-on', !!s.jeans)`.
  Add `NAME` the same way (and add `&& !s.NAME` to the others so two pants
  can never come back on together).

The Profile page shows the same character by loading
`create-character.html?view` in an iframe (`html.view-mode` hides the controls
and never saves), so a new costume appears there automatically. It labels its
button "Edit your character" when the save key exists, which is why the page
only saves after a user action - don't add a save call on page load.

Test by: choose the costume as a kid, go back to Profile, re-open Create Your
Character - the kid must still be wearing it.
