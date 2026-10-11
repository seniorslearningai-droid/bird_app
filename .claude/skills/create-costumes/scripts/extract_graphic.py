"""Pull the printed graphic (logo, text, picture) off a garment photo.

Picture garments are recreated on the character as the body-fitted shape in
the garment's main colour PLUS this graphic placed on top - a flat product
photo can't bend to the body, but its print can sit on the fitted shape.

Run remove_bg.py on the garment first, then give this the cut-out. Pixels that
differ clearly from the fabric colour (well inside the garment, away from its
outline and shadows) are kept; everything else becomes transparent.

Usage:
  python extract_graphic.py GARMENT_CUTOUT.png OUT.png [--fabric #ff6a00] [--thresh 80] [--inset 0.06]
"""
import argparse
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, __import__("os").path.dirname(__file__))
from costume_lib import components, dominant_color, erode4, hex_rgb, rgb_hex   # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--fabric", help="garment colour (default: auto-detected)")
    ap.add_argument("--thresh", type=int, default=80)
    ap.add_argument("--inset", type=float, default=0.06, help="ignore this fraction of width near the garment edge")
    a = ap.parse_args()

    im = Image.open(a.inp).convert("RGBA")
    arr = np.asarray(im).astype(int)
    rgb, al = arr[..., :3], arr[..., 3]
    fabric = hex_rgb(a.fabric) if a.fabric else dominant_color(im)
    garment = al > 200
    inner = erode4(garment, max(1, int(a.inset * im.width)))   # skip outline/shadows
    differs = np.abs(rgb - np.array(fabric)).max(axis=2) > a.thresh
    graphic = inner & differs
    if graphic.sum() < 30:
        raise SystemExit(f"No graphic found that differs from fabric {rgb_hex(fabric)} - try a lower --thresh")

    # keep the main cluster of print (plus pieces near it, e.g. separate letters)
    comps = components(graphic)
    big = comps[0]
    cy = big[0].mean()
    span = (big[0].max() - big[0].min() + 1) * 2.5 + im.height * 0.03
    keep = np.zeros_like(graphic)
    for ys, xs in comps:
        if abs(ys.mean() - cy) <= span and len(ys) >= 10:
            keep[ys, xs] = True

    out = arr.copy()
    out[..., 3] = np.where(keep, 255, 0)
    ys, xs = np.nonzero(keep)
    pad = 6
    res = Image.fromarray(out.astype(np.uint8)).crop(
        (max(0, xs.min() - pad), max(0, ys.min() - pad),
         min(im.width, xs.max() + pad + 1), min(im.height, ys.max() + pad + 1)))
    res.save(a.out)
    print(f"saved {a.out}  size={res.size}  fabric colour={rgb_hex(fabric)}  aspect w/h={res.width/res.height:.2f}")


if __name__ == "__main__":
    main()
