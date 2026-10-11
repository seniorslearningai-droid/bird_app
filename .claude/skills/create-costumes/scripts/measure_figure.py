"""Measure the adult and kid figures so a costume can be sized to them.

Prints, for rows down the body, where the silhouette is (in viewBox units and
as % of the figure width). Several 'runs' on one row mean separate pieces -
e.g. arm | torso | arm, or two legs.

Usage:
  python measure_figure.py [head|torso|legs|all]
"""
import sys

import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__file__))
from costume_lib import VIEWBOX, body_mask, default_eyes, page_html   # noqa: E402

RANGES = {"head": (0, 30, 3), "torso": (18, 60, 4), "legs": (45, 99, 4), "all": (0, 99, 5)}


def runs(row, scale):
    xs = np.nonzero(row)[0]
    if not len(xs):
        return []
    out, s, p = [], xs[0], xs[0]
    for v in xs[1:]:
        if v - p > 1:
            out.append((s, p)); s = v
        p = v
    out.append((s, p))
    return [(a / scale, b / scale) for a, b in out]


def main():
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    lo, hi, step = RANGES.get(part, RANGES["all"])
    html = page_html()
    eyes = default_eyes(html)
    for who in ("adult", "kid"):
        vw, vh = VIEWBOX[who]
        sc = 8
        m = body_mask(html, who, sc)
        top = next(y for y in range(m.shape[0]) if m[y].any()) / sc
        e = eyes[who]
        print(f"== {who.upper()}  viewBox {vw:g}x{vh:g}  top of head y={top:.1f}  "
              f"eyes at left {e['left']}% / {e['right']}%, top {e['top']}%, width {e['width']}%")
        for pct in range(lo, hi + 1, step):
            y = int(vh * pct / 100 * sc)
            if y >= m.shape[0]:
                continue
            r = runs(m[y], sc)
            txt = "  ".join(f"[{a:.0f}-{b:.0f}]" for a, b in r) or "(empty)"
            pcts = "  ".join(f"[{100*a/vw:.0f}%-{100*b/vw:.0f}%]" for a, b in r)
            print(f"  y={vh*pct/100:6.1f} ({pct:2d}%)  {len(r)} run(s)  {txt:<34} {pcts}")
        print()


if __name__ == "__main__":
    main()
