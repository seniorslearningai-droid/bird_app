"""Remove a costume picture's background so it can be layered on the character.

The background is grown inward from the image border through pixels that look
like the border colours (several border samples are used, so vignettes and
gradients come off too). Optional --hole seeds clear enclosed areas such as a
mask's eye holes. A short halo pass removes the light fringe that flood fills
leave behind, then the result is trimmed and size-capped for GitHub Pages.

Usage:
  python remove_bg.py IN.png OUT.png
         [--thresh 55]                      background colour tolerance (raise if bits remain)
         [--hole 0.33,0.47 --hole 0.71,0.47] clear an enclosed area at this x,y fraction
         [--hole-thresh 75]                 tolerance for --hole fills
         [--remove-specks]                  drop small loose blobs (NOT for logos/text)
         [--no-trim] [--max-size 1254]
"""
import argparse
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, __import__("os").path.dirname(__file__))
from costume_lib import (border, components, dilate4, dominant_color,   # noqa: E402
                         reconstruct, rgb_hex)


def color_dist(rgb, ref):
    return np.abs(rgb - np.array(ref, dtype=int)).max(axis=2)


def border_refs(rgb, alpha, thresh, samples=48):
    """Background reference colours sampled around the border.

    Only samples that agree with the typical border colour are kept, so a
    costume that touches the edge doesn't get used as 'background'."""
    H, W, _ = rgb.shape
    ring = np.concatenate([rgb[0, :], rgb[-1, :], rgb[:, 0], rgb[:, -1]])
    ring_a = np.concatenate([alpha[0, :], alpha[-1, :], alpha[:, 0], alpha[:, -1]])
    ring = ring[ring_a > 40] if (ring_a > 40).any() else ring
    if len(ring) == 0:
        return []
    typical = np.median(ring, axis=0)
    idx = np.linspace(0, len(ring) - 1, samples).astype(int)
    refs = [tuple(ring[i]) for i in idx
            if np.abs(ring[i] - typical).max() <= thresh * 2.5]
    return refs or [tuple(int(v) for v in typical)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--thresh", type=int, default=55)
    ap.add_argument("--hole", action="append", default=[])
    ap.add_argument("--hole-thresh", type=int, default=75)
    ap.add_argument("--remove-specks", action="store_true")
    ap.add_argument("--no-trim", action="store_true")
    ap.add_argument("--max-size", type=int, default=1254)
    a = ap.parse_args()

    im = Image.open(a.inp).convert("RGBA")
    if max(im.size) > a.max_size:                       # work at the final size
        s = a.max_size / max(im.size)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    arr = np.asarray(im).astype(int)
    rgb, alpha = arr[..., :3], arr[..., 3].copy()
    clear = alpha < 40                                   # already transparent

    # 1) background: grow from the border through background-like pixels
    refs = border_refs(rgb, alpha, a.thresh)
    like_bg = clear.copy()
    for ref in refs:
        like_bg |= color_dist(rgb, ref) <= a.thresh
    bg = reconstruct(border(like_bg) & like_bg, like_bg)

    # 2) enclosed holes (eye holes etc.)
    H, W = clear.shape
    for h in a.hole:
        fx, fy = (float(v) for v in h.split(","))
        x, y = min(W - 1, int(fx * W)), min(H - 1, int(fy * H))
        seed_rgb = tuple(rgb[y, x])
        allowed = (color_dist(rgb, seed_rgb) <= a.hole_thresh) | clear
        seed = np.zeros_like(clear); seed[y, x] = True
        bg |= reconstruct(seed, allowed)

    # 3) halo: background-tinted fringe pixels touching the cut-out
    for _ in range(3):
        edge = ~bg & dilate4(bg)
        halo = np.zeros_like(bg)
        for ref in refs:
            # kept tight so a costume edge close in colour isn't eaten
            halo |= edge & (color_dist(rgb, ref) <= int(a.thresh * 1.2))
        if not halo.any():
            break
        bg |= halo

    alpha[bg] = 0

    # 4) optional: drop loose specks smaller than 1% of the main piece
    if a.remove_specks:
        small = Image.fromarray(((alpha > 40) * 255).astype(np.uint8))
        f = min(1.0, 400 / max(small.size))
        sm = np.asarray(small.resize((max(1, int(small.width * f)), max(1, int(small.height * f))))) > 127
        comps = components(sm)
        if comps:
            keep = np.zeros_like(sm)
            biggest = len(comps[0][0])
            for ys, xs in comps:
                if len(ys) >= biggest * 0.01:
                    keep[ys, xs] = True
            keep_full = np.asarray(Image.fromarray((keep * 255).astype(np.uint8)).resize((W, H))) > 127
            alpha[~keep_full] = 0

    out = np.dstack([rgb, alpha]).astype(np.uint8)
    res = Image.fromarray(out)

    # 5) trim to the costume
    if not a.no_trim:
        ys, xs = np.nonzero(alpha > 40)
        if len(ys):
            pad = 4
            res = res.crop((max(0, xs.min() - pad), max(0, ys.min() - pad),
                            min(W, xs.max() + pad + 1), min(H, ys.max() + pad + 1)))

    res.save(a.out)
    al = np.asarray(res)[..., 3]
    print(f"saved {a.out}  size={res.size}  transparent={100 * (al < 40).mean():.0f}%")
    print(f"background refs used: {len(refs)}  e.g. {rgb_hex(refs[0]) if refs else '-'}")
    print(f"main costume colour (fabric): {rgb_hex(dominant_color(res))}")


if __name__ == "__main__":
    main()
