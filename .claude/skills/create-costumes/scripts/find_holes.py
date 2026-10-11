"""Find the see-through holes inside a transparent costume (e.g. mask eye holes).

A hole is a transparent area completely surrounded by the costume (not
connected to the outside). Positions are printed as fractions of the image
width/height - exactly what preview.py --holes and shrink_holes.py --hole take.

Usage:
  python find_holes.py COSTUME.png
"""
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, __import__("os").path.dirname(__file__))
from costume_lib import border, components, reconstruct   # noqa: E402


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    im = Image.open(sys.argv[1]).convert("RGBA")
    W0, H0 = im.size
    f = min(1.0, 500 / max(im.size))                    # label at <=500px for speed
    small = im.resize((max(1, int(W0 * f)), max(1, int(H0 * f))), Image.NEAREST)
    clear = np.asarray(small)[..., 3] < 40
    H, W = clear.shape
    outside = reconstruct(border(clear) & clear, clear)
    holes = clear & ~outside
    comps = components(holes, min_px=max(4, int(H * W * 0.0005)))
    if not comps:
        print("No enclosed holes found.")
        return
    rows = []
    for ys, xs in comps:
        rows.append(dict(cx=(xs.min() + xs.max() + 1) / 2 / W, cy=(ys.min() + ys.max() + 1) / 2 / H,
                         w=(xs.max() - xs.min() + 1) / W, h=(ys.max() - ys.min() + 1) / H,
                         area=100 * len(ys) / (H * W)))
    print("holes (fractions of the image):")
    for i, r in enumerate(rows):
        print(f"  #{i}: center=({r['cx']:.3f}, {r['cy']:.3f})  size w={r['w']:.3f} h={r['h']:.3f}  area={r['area']:.2f}%")

    # Best eye pair: similar height, similar size, on opposite sides of centre.
    best, score = None, 1e9
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = sorted((rows[i], rows[j]), key=lambda r: r["cx"])
            if not (a["cx"] < 0.5 < b["cx"]):
                continue
            s = abs(a["cy"] - b["cy"]) * 4 + abs(a["area"] - b["area"]) / max(a["area"], b["area"]) \
                + abs((a["cx"] + b["cx"]) / 2 - 0.5)
            if s < score:
                best, score = (a, b), s
    if best:
        a, b = best
        y = (a["cy"] + b["cy"]) / 2
        print(f"\nlikely eye holes: left x={a['cx']:.3f}, right x={b['cx']:.3f}, y={y:.3f}")
        print(f"  -> preview.py --holes {a['cx']:.3f},{b['cx']:.3f},{y:.3f}")
        print(f"  -> hole size about {max(a['w'], b['w']):.3f} of the image width")


if __name__ == "__main__":
    main()
