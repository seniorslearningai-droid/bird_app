"""Shared helpers for the create-costumes scripts.

Reads the character figures straight out of create-character.html so every
measurement and preview matches what the live page actually draws.
"""
import re
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[4]          # .../BirdApp
PAGE = REPO / "create-character.html"
COSTUMES = REPO / "North_American_Birds" / "Costumes"

# SVG viewBox of each figure (width, height). Overlay CSS percentages are
# relative to the figure wrapper, which has exactly this aspect ratio.
VIEWBOX = {"adult": (97.0, 200.0), "kid": (55.0, 113.0)}

# Fallback eye placement (CSS % of the wrapper) if the page can't be parsed.
_DEFAULT_EYES = {
    "adult": {"left": 50.5, "right": 57.5, "top": 9.5, "width": 5.5},
    "kid":   {"left": 53.0, "right": 61.0, "top": 11.5, "width": 6.5},
}


def page_html(path=None):
    return Path(path or PAGE).read_text(encoding="utf-8")


def figure_d(html, who):
    """The SVG path data of the adult or kid silhouette."""
    m = re.search(rf'character-figure {who}-fig".*?<path[^>]*\sd="([^"]+)"', html, re.S)
    if not m:
        raise SystemExit(f"Could not find the {who} figure in create-character.html")
    return m.group(1)


def page_shape(html, kind, who):
    """Current garment shape on the page: kind='shirt' or 'pants'."""
    m = re.search(rf'{kind}-overlay {who}-{kind}.*?</clipPath></defs><path d="([^"]+)"', html, re.S)
    return m.group(1) if m else None


def default_eyes(html=None):
    """Read the normal (no-mask) eye placement from the page CSS."""
    eyes = {k: dict(v) for k, v in _DEFAULT_EYES.items()}
    if html is None:
        return eyes
    for who in ("adult", "kid"):
        for side in ("left", "right"):
            m = re.search(
                rf'^\s*\.{who}-eye\.eye-{side}\s*\{{\s*left:\s*([\d.]+)%;\s*top:\s*([\d.]+)%;\s*width:\s*([\d.]+)%',
                html, re.M)
            if m:
                eyes[who][side] = float(m.group(1))
                eyes[who]["top"] = float(m.group(2))
                eyes[who]["width"] = float(m.group(3))
    return eyes


# ---------------------------------------------------------------- SVG paths
_TOK = re.compile(r"([MLHVQCZmlhvqcz])([^MLHVQCZmlhvqcz]*)")
_NUM = re.compile(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?")


def flatten(d, steps=12):
    """SVG path data -> list of subpaths, each a list of (x, y) points."""
    subs, seg = [], []
    cur = start = (0.0, 0.0)
    for cmd, arg in _TOK.findall(d):
        n = [float(v) for v in _NUM.findall(arg)]
        rel = cmd.islower()
        c = cmd.upper()
        if c == "Z":
            if seg:
                seg.append(start)
                subs.append(seg)
                seg = []
            cur = start
            continue
        i = 0
        while i < len(n) or (c == "Z"):
            ox, oy = (cur if rel else (0.0, 0.0))
            if c == "M":
                if seg:
                    subs.append(seg)
                cur = (ox + n[i], oy + n[i + 1]); i += 2
                start = cur
                seg = [cur]
                c = "L"                      # implicit lineto after moveto
            elif c == "L":
                cur = (ox + n[i], oy + n[i + 1]); i += 2
                seg.append(cur)
            elif c == "H":
                cur = ((cur[0] if rel else 0) + n[i], cur[1]); i += 1
                seg.append(cur)
            elif c == "V":
                cur = (cur[0], (cur[1] if rel else 0) + n[i]); i += 1
                seg.append(cur)
            elif c == "Q":
                cx, cy = ox + n[i], oy + n[i + 1]
                x, y = ox + n[i + 2], oy + n[i + 3]; i += 4
                for k in range(1, steps + 1):
                    t = k / steps
                    seg.append(((1 - t) ** 2 * cur[0] + 2 * (1 - t) * t * cx + t * t * x,
                                (1 - t) ** 2 * cur[1] + 2 * (1 - t) * t * cy + t * t * y))
                cur = (x, y)
            elif c == "C":
                x1, y1 = ox + n[i], oy + n[i + 1]
                x2, y2 = ox + n[i + 2], oy + n[i + 3]
                x, y = ox + n[i + 4], oy + n[i + 5]; i += 6
                for k in range(1, steps + 1):
                    t = k / steps
                    mt = 1 - t
                    seg.append((mt ** 3 * cur[0] + 3 * mt * mt * t * x1 + 3 * mt * t * t * x2 + t ** 3 * x,
                                mt ** 3 * cur[1] + 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t ** 3 * y))
                cur = (x, y)
            else:
                break
            if i >= len(n):
                break
    if seg:
        subs.append(seg)
    return subs


def rasterize(d, vw, vh, scale):
    """Fill an SVG path at `scale` pixels per viewBox unit -> bool mask."""
    W, H = int(round(vw * scale)), int(round(vh * scale))
    img = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(img)
    for seg in flatten(d):
        if len(seg) >= 3:
            dr.polygon([(x * scale, y * scale) for x, y in seg], fill=255)
    return np.asarray(img) > 0


def body_mask(html, who, scale):
    vw, vh = VIEWBOX[who]
    return rasterize(figure_d(html, who), vw, vh, scale)


# ------------------------------------------------------------- mask helpers
def dilate4(m):
    o = m.copy()
    o[1:, :] |= m[:-1, :]
    o[:-1, :] |= m[1:, :]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    return o


def erode4(m, n=1):
    for _ in range(n):
        m = ~dilate4(~m)
    return m


def reconstruct(seed, allowed):
    """Grow `seed` through 4-connected `allowed` pixels until it stops."""
    cur = seed & allowed
    while True:
        nxt = dilate4(cur) & allowed
        if (nxt == cur).all():
            return cur
        cur = nxt


def border(m):
    b = np.zeros_like(m)
    b[0, :] = b[-1, :] = b[:, 0] = b[:, -1] = True
    return b


def components(m, min_px=1):
    """4-connected components of a bool mask -> list of (ys, xs) arrays, largest first."""
    H, W = m.shape
    seen = np.zeros_like(m)
    out = []
    for y0, x0 in zip(*np.nonzero(m)):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        ys, xs = [], []
        while q:
            y, x = q.popleft()
            ys.append(y); xs.append(x)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        if len(ys) >= min_px:
            out.append((np.array(ys), np.array(xs)))
    out.sort(key=lambda c: len(c[0]), reverse=True)
    return out


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(c):
    return "#%02x%02x%02x" % tuple(int(v) for v in c)


def dominant_color(rgba):
    """Median colour of the opaque, non-white, non-black pixels (the 'fabric')."""
    a = np.asarray(rgba.convert("RGBA")).astype(int)
    rgb, al = a[..., :3], a[..., 3]
    s = rgb.sum(axis=2)
    pick = (al > 200) & (s > 90) & (s < 690)
    if pick.sum() < 50:
        pick = al > 200
    return tuple(int(v) for v in np.median(rgb[pick], axis=0))
