"""Render a costume on the adult AND kid figures before touching the page.

Draws the same thing create-character.html will: skin-coloured body, fitted
garment shape (clipped to the body), chest graphic, eyes, then any head piece
on top. Positions use the page's CSS units (% of the figure wrapper), so the
numbers you settle on here go straight into the CSS.

Head pieces (masks/helmets/hats) - top-left anchored like .helmet-overlay:
  --image MASK.png --adult W,L,T --kid W,L,T      width%, left%, top%  (top may be negative)
  --holes LX,RX,Y        eye-hole centres as fractions of the image (from find_holes.py);
                         eyes are moved into the holes and the CSS for them is printed
  --cls NAME-on          body class name used in the printed CSS

Garments - fitted to the body:
  --use-page-shape shirt|pants          reuse the shape already on the page, or
  --shape-adult "SVG d" --shape-kid "SVG d"
  --shape-color "#hex"
  --graphic LOGO.png --graphic-adult CX,CY,W --graphic-kid CX,CY,W   centred, like .fs-logo
  --garment-image CUTOUT.png --garment-adult X0,Y0,X1,Y1 --garment-kid X0,Y0,X1,Y1
                         the garment photo itself stretched into this viewBox box and
                         clipped to the body (like the Blue Jeans)
  --garment-limit-kid "SVG d" / --garment-limit-adult "SVG d"
                         extra clip, e.g. to keep the kid's hands at the hips uncovered
  --garment-fill-adult "SVG d" / --garment-fill-kid "SVG d"
                         area ADDED to the body clip, e.g. the notch between the legs
                         below the crotch that real pants would cover

General:
  --out preview.png  --crop head|torso|legs|full  --skin "#d49a63"

Example (Peregrine mask as it is on the page):
  python preview.py --image ../../../../North_American_Birds/Costumes/peregrine_falcon_mask_front.png \
     --adult 58,24,-1.3 --kid 68,22,-2.16 --holes 0.327,0.709,0.473 --cls peregrine-on --crop head
"""
import argparse
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, __import__("os").path.dirname(__file__))
from costume_lib import (VIEWBOX, body_mask, default_eyes, border,   # noqa: E402
                         hex_rgb, page_html, page_shape, rasterize, reconstruct)

SCALE = {"adult": 5.0, "kid": 9.0}       # both figures render ~1000px tall
PAD = 0.12                                # room above the head for tall hats


def triple(s):
    return tuple(float(v) for v in s.split(","))


def hole_width_frac(img, fx, fy):
    """Width of the enclosed hole at (fx,fy) as a fraction of the image width."""
    f = min(1.0, 500 / max(img.size))
    small = img.resize((max(1, int(img.width * f)), max(1, int(img.height * f))), Image.NEAREST)
    clear = np.asarray(small)[..., 3] < 40
    H, W = clear.shape
    x, y = min(W - 1, int(fx * W)), min(H - 1, int(fy * H))
    if not clear[y, x]:
        return None
    seed = np.zeros_like(clear); seed[y, x] = True
    hole = reconstruct(seed, clear)
    if (hole & border(hole)).any():
        return None
    xs = np.nonzero(hole)[1]
    return (xs.max() - xs.min() + 1) / W


def draw_eye(dr, cx, cy, w):
    h = w / 1.5
    dr.ellipse([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=(255, 255, 255), outline=(50, 50, 50))
    r = h * 0.46
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(40, 110, 230))
    r2 = r * 0.5
    dr.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(0, 0, 0))


def render(who, a, html, eyes_css, img):
    vw, vh = VIEWBOX[who]
    sc = SCALE[who]
    W, H = int(vw * sc), int(vh * sc)
    pad = int(H * PAD)
    canvas = Image.new("RGB", (W, H + pad), (255, 248, 234))
    body = body_mask(html, who, sc)
    arr = np.asarray(canvas).copy()
    sub = arr[pad:pad + body.shape[0], :body.shape[1]]
    sub[body] = hex_rgb(a.skin)

    # garment photo stretched into a box and clipped to the body (+ optional limit)
    gbox = getattr(a, f"garment_{who}")
    if a.garment_image and gbox:
        x0, y0, x1, y1 = (float(v) for v in gbox.split(","))
        clip = body.copy()
        fill = getattr(a, f"garment_fill_{who}")
        if fill:
            clip |= rasterize(fill, vw, vh, sc)[:body.shape[0], :body.shape[1]]
        lim = getattr(a, f"garment_limit_{who}")
        if lim:
            clip &= rasterize(lim, vw, vh, sc)[:body.shape[0], :body.shape[1]]
        g = Image.open(a.garment_image).convert("RGBA").resize(
            (max(1, round((x1 - x0) * sc)), max(1, round((y1 - y0) * sc))), Image.LANCZOS)
        layer = np.zeros(sub.shape[:2] + (4,), float)
        X0, Y0 = round(x0 * sc), round(y0 * sc)
        ga = np.asarray(g, float)
        hh, ww = min(ga.shape[0], layer.shape[0] - Y0), min(ga.shape[1], layer.shape[1] - X0)
        layer[Y0:Y0 + hh, X0:X0 + ww] = ga[:hh, :ww]
        al = layer[..., 3:] / 255 * clip[..., None]
        sub[:] = (sub * (1 - al) + layer[..., :3] * al).astype(np.uint8)

    # fitted garment, clipped to the body like the page's clipPath
    d = getattr(a, f"shape_{who}") or (page_shape(html, a.use_page_shape, who) if a.use_page_shape else None)
    if d:
        sm = rasterize(d, vw, vh, sc)[:body.shape[0], :body.shape[1]]
        sub[sm & body] = hex_rgb(a.shape_color)
    arr[pad:pad + body.shape[0], :body.shape[1]] = sub
    canvas = Image.fromarray(arr)
    dr = ImageDraw.Draw(canvas)

    if a.graphic and getattr(a, f"graphic_{who}"):
        g = Image.open(a.graphic).convert("RGBA")
        cx, cy, gw = triple(getattr(a, f"graphic_{who}"))
        pw = int(gw / 100 * W); ph = int(pw * g.height / g.width)
        g = g.resize((max(1, pw), max(1, ph)), Image.LANCZOS)
        canvas.paste(g, (int(cx / 100 * W - pw / 2), pad + int(cy / 100 * H - ph / 2)), g)

    e = eyes_css[who]
    for x in (e["left"], e["right"]):
        draw_eye(dr, x / 100 * W, pad + e["top"] / 100 * H, e["width"] / 100 * W)

    if img is not None and getattr(a, who):
        mw, ml, mt = triple(getattr(a, who))
        pw = int(mw / 100 * W); ph = int(pw * img.height / img.width)
        m = img.resize((max(1, pw), max(1, ph)), Image.LANCZOS)
        canvas.paste(m, (int(ml / 100 * W), pad + int(mt / 100 * H)), m)

    crops = {"head": (0, 0.40), "torso": (0.12, 0.62), "legs": (0.45, 1.0), "full": (0, 1.0)}
    t0, t1 = crops[a.crop]
    canvas = canvas.crop((0, 0 if t0 == 0 else pad + int(t0 * H), W, pad + int(t1 * H)))
    ImageDraw.Draw(canvas).text((6, 4), who.upper(), fill=(0, 0, 0))
    return canvas


def main():
    ap = argparse.ArgumentParser(description="Preview a costume on both figures", add_help=True)
    ap.add_argument("--out", default="costume_preview.png")
    ap.add_argument("--skin", default="#d49a63")
    ap.add_argument("--crop", default="full", choices=["head", "torso", "legs", "full"])
    ap.add_argument("--image"); ap.add_argument("--adult"); ap.add_argument("--kid")
    ap.add_argument("--holes"); ap.add_argument("--cls", default="NAME-on")
    ap.add_argument("--use-page-shape", choices=["shirt", "pants"])
    ap.add_argument("--shape-adult"); ap.add_argument("--shape-kid")
    ap.add_argument("--shape-color", default="#2a7fff")
    ap.add_argument("--graphic"); ap.add_argument("--graphic-adult"); ap.add_argument("--graphic-kid")
    ap.add_argument("--garment-image"); ap.add_argument("--garment-adult"); ap.add_argument("--garment-kid")
    ap.add_argument("--garment-limit-adult"); ap.add_argument("--garment-limit-kid")
    ap.add_argument("--garment-fill-adult"); ap.add_argument("--garment-fill-kid")
    a = ap.parse_args()

    html = page_html()
    eyes = default_eyes(html)
    img = Image.open(a.image).convert("RGBA") if a.image else None

    if img is not None and a.holes:
        lx, rx, hy = triple(a.holes)
        aspect = img.height / img.width
        print("/* eyes moved into the holes while this piece is worn */")
        fracs = []
        for who in ("adult", "kid"):
            if not getattr(a, who):
                continue
            vw, vh = VIEWBOX[who]
            mw, ml, mt = triple(getattr(a, who))
            L, R = ml + lx * mw, ml + rx * mw
            T = mt + hy * mw * (vw / vh) * aspect
            eyes[who].update(left=round(L, 2), right=round(R, 2), top=round(T, 2))
            print(f"body.{a.cls} .{who}-eye.eye-left  {{ left: {L:.2f}%; top: {T:.2f}%; }}")
            print(f"body.{a.cls} .{who}-eye.eye-right {{ left: {R:.2f}%; top: {T:.2f}%; }}")
            fracs.append(eyes[who]["width"] / mw)
        if fracs:
            ef = sum(fracs) / len(fracs)
            hw = hole_width_frac(img, lx, hy)
            print(f"\neye width = {ef:.3f} of the image width  (use: shrink_holes.py --eye-frac {ef:.3f})")
            if hw:
                ratio = hw / ef
                verdict = "too big - shrink the holes" if ratio > 1.45 else ("too small - eyes will be cut off" if ratio < 1.0 else "good fit")
                print(f"hole width = {hw:.3f} of the image = {ratio:.2f}x the eye -> {verdict}")

    tiles = [render(w, a, html, eyes, img) for w in ("adult", "kid")]
    h = max(t.height for t in tiles)
    out = Image.new("RGB", (sum(t.width for t in tiles) + 20, h), (255, 255, 255))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0)); x += t.width + 20
    out.save(a.out)
    print(f"\nsaved {a.out}")


if __name__ == "__main__":
    main()
