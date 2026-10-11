"""Shrink a mask's eye holes so they hug the character's eyes.

The user's rule: change the HOLES to fit the eyes, never resize the eyes.
Each hole is redrawn as an almond-shaped opening just a little larger than
an eye, and the space it no longer needs is filled with the rim colour that
already surrounds the hole.

--eye-frac is the eye width as a fraction of the mask image width, i.e.
  (eye width % on the page) / (mask width % on the page).
  preview.py prints it for you once you know the mask's on-page size.

Usage:
  python shrink_holes.py MASK.png OUT.png --hole 0.327,0.473 --hole 0.709,0.472 --eye-frac 0.095
"""
import argparse
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, __import__("os").path.dirname(__file__))
from costume_lib import dilate4, reconstruct, rgb_hex   # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--hole", action="append", required=True)
    ap.add_argument("--eye-frac", type=float, required=True)
    ap.add_argument("--margin", type=float, default=1.2, help="opening size vs eye (1.2 = 20%% roomier)")
    a = ap.parse_args()

    im = Image.open(a.inp).convert("RGBA")
    arr = np.asarray(im).copy()
    H, W = arr.shape[:2]
    clear = arr[..., 3] < 60
    eye_w = a.eye_frac * W
    rx = eye_w / 2 * a.margin
    ry = eye_w / 1.5 / 2 * (a.margin + 0.1)        # eyes are 1.5:1 almonds
    yy, xx = np.mgrid[0:H, 0:W]

    for h in a.hole:
        fx, fy = (float(v) for v in h.split(","))
        x, y = min(W - 1, int(fx * W)), min(H - 1, int(fy * H))
        if not clear[y, x]:
            print(f"hole {h}: that point isn't see-through - check find_holes.py output")
            continue
        seed = np.zeros_like(clear); seed[y, x] = True
        hole = reconstruct(seed, clear)
        if hole[0].any() or hole[-1].any() or hole[:, 0].any() or hole[:, -1].any():
            print(f"hole {h}: connects to the outside, skipped (not an enclosed hole)")
            continue
        ys, xs = np.nonzero(hole)
        cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
        ring = hole.copy()
        for _ in range(6):
            ring = dilate4(ring)
        ring &= ~hole & ~clear
        rim = np.median(arr[ring][:, :3], axis=0).astype(np.uint8) if ring.any() else np.array([30, 30, 30], np.uint8)
        outside_ellipse = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 > 1.0
        fill = hole & outside_ellipse
        arr[fill, :3] = rim
        arr[fill, 3] = 255
        print(f"hole at ({fx:.3f},{fy:.3f}): was {xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}px, "
              f"now {2*rx:.0f}x{2*ry:.0f}px opening, rim {rgb_hex(rim)}, filled {int(fill.sum())}px")

    Image.fromarray(arr).save(a.out)
    print(f"saved {a.out}")


if __name__ == "__main__":
    main()
