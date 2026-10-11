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
pants (z1), shirts (z2), `.fs-logo` (z2), kid hair (z3), head pieces (z4).

State lives in classes on `<body>`:

| Class | Meaning |
|---|---|
| `kid-mode` | kid figure shown (absent = adult) |
| `helmet-on`, `peregrine-on` | head pieces - only one at a time |
| `shirt-on`, `flightscore-on` | shirts - only one at a time |
| `pants-on` | colour pants |
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

Today pants are a single independent toggle (`pants-on` + colour slider,
built by `makePantsBox`). The first picture pants (e.g. `blue_jeans.png`)
turn pants into a group like shirts:

1. Add `makePantsOption(box, kind, innerHTML)` - same as `makeShirtOption`
   but with `data-pants`, removing `'pants-on', 'NAME-on'`.
2. Make the colour box use it (keep its icon + "Choose Your Color" label).
3. CSS for the new pants, reusing the fitted shapes:
   ```css
   body.NAME-on:not(.kid-mode) .adult-pants { display: block; }
   body.NAME-on.kid-mode       .kid-pants   { display: block; }
   body.NAME-on .pants-overlay > path { fill: #HEX; }
   ```
   The colour slider (`.pants-color-bar`) stays tied to `pants-on` only.
   Details such as jean seams or pockets can be extra `<path>`s inside the
   pants SVGs with a class shown only under `body.NAME-on`; give them
   `fill: none` and a darker stroke, and keep them inside the clip.
4. `selectPart`: `else if (part === 'Pants' && i === 1) { makePantsOption(...) }`
5. save/restore: section 6.

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
- Pants: same pattern as shirts.

Test by: choose the costume as a kid, go back to Profile, re-open Create Your
Character - the kid must still be wearing it.
