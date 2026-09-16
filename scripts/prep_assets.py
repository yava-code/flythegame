"""cut sprites out of the gemini sheets.

the sheets have labels ("IDLE", "DEAD") and a baked drop shadow on the hand,
so a plain rectangle crop drags junk in. we label connected blobs instead and
keep the ones that look like the thing we want:
  fly  -> blob containing red eye pixels
  hand -> blob containing skin pixels
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

RAW = Path(__file__).resolve().parents[1] / "assets" / "raw"
OUT = Path(__file__).resolve().parents[1] / "assets"

FLY_W = 30      # on-table fly width in px
HAND_W = 190


def _find(key: str) -> Path:
    for p in RAW.glob("*.png"):
        if key in p.name:
            return p
    raise FileNotFoundError(key)


def _blobs(mask: np.ndarray, min_area: int):
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        sel = lab == i
        if sel.sum() < min_area:
            continue
        ys, xs = np.nonzero(sel)
        out.append({
            "mask": sel,
            "box": (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1),
            "cx": xs.mean(),
            "cy": ys.mean(),
        })
    return out


def _cut(rgb: np.ndarray, blob: dict, pad: int = 2) -> Image.Image:
    """rgba of one blob only; grows 1px so the dark outline comes along"""
    grown = ndimage.binary_dilation(blob["mask"], iterations=1)
    dark = rgb.sum(axis=2) < 300
    keep = blob["mask"] | (grown & dark)
    keep = ndimage.binary_fill_holes(keep)

    x0, y0, x1, y1 = blob["box"]
    x0 = max(0, x0 - pad); y0 = max(0, y0 - pad)
    x1 = min(rgb.shape[1], x1 + pad); y1 = min(rgb.shape[0], y1 + pad)

    sub_rgb = rgb[y0:y1, x0:x1]
    sub_a = (keep[y0:y1, x0:x1] * 255).astype(np.uint8)
    rgba = np.dstack([sub_rgb, sub_a])
    return Image.fromarray(rgba, "RGBA")


def _knock_blue(im: Image.Image) -> Image.Image:
    """leftover panel blue around the cut must go, or the forearm never shows"""
    arr = np.asarray(im).copy()
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    blue = (b > r + 18) & (b > g + 8) & (b > 70) & (r < 140)
    arr[..., 3] = np.where(blue, 0, a)
    return Image.fromarray(arr, "RGBA")


def _scale_w(im: Image.Image, w: int) -> Image.Image:
    if im.width == w:
        return im
    h = max(1, round(im.height * w / im.width))
    return im.resize((w, h), Image.NEAREST)


def cut_flies():
    rgb = np.asarray(Image.open(_find("mc1k33")).convert("RGB"))
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)

    not_white = rgb.sum(axis=2) < 700
    red_eye = (r > 110) & (r > g + 45) & (r > b + 45)

    flies = [bl for bl in _blobs(not_white, 400)
             if red_eye[bl["mask"]].any() and (bl["box"][2] - bl["box"][0]) > 24]
    if not flies:
        raise RuntimeError("no flies found in sheet")

    # rows by y, then species column by x
    flies.sort(key=lambda b: b["cy"])
    rows, cur = [], [flies[0]]
    for bl in flies[1:]:
        if abs(bl["cy"] - cur[-1]["cy"]) < 40:
            cur.append(bl)
        else:
            rows.append(cur)
            cur = [bl]
    rows.append(cur)
    for row in rows:
        row.sort(key=lambda b: b["cx"])

    print(f"  fly rows: {[len(r) for r in rows]}")
    # species A = leftmost column of each row
    def pick(row_i, col_i=0):
        row = rows[min(row_i, len(rows) - 1)]
        return row[min(col_i, len(row) - 1)]

    want = {"idle": (0, 0), "fly0": (1, 0), "fly1": (1, 1), "dead": (3, 0)}
    (OUT / "fly").mkdir(parents=True, exist_ok=True)
    for name, (ri, ci) in want.items():
        im = _scale_w(_cut(rgb, pick(ri, ci)), FLY_W)
        im.save(OUT / "fly" / f"{name}.png")
        print(f"  fly/{name}.png {im.size}")


def cut_hand():
    rgb = np.asarray(Image.open(_find("251j9x")).convert("RGB"))
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)

    # backdrop and the baked drop shadow are both blue dominant
    blue = (b > r * 1.22) & (b > g * 1.12)
    skin = (r > 180) & (g > 130) & (b > 100) & (r > b + 40)

    blobs = [bl for bl in _blobs(~blue, 3000) if skin[bl["mask"]].sum() > 500]
    blobs.sort(key=lambda x: x["cx"])
    if len(blobs) < 3:
        raise RuntimeError(f"expected 3 hand poses, found {len(blobs)}")

    (OUT / "hand").mkdir(parents=True, exist_ok=True)
    for name, bl in zip(("idle", "swat", "miss"), blobs):
        im = _scale_w(_knock_blue(_cut(rgb, bl)), HAND_W)
        im.save(OUT / "hand" / f"{name}.png")
        print(f"  hand/{name}.png {im.size}")
        if name == "idle":
            a = np.asarray(im)[..., 3]
            sil = np.zeros((*a.shape, 4), np.uint8)
            sil[..., :3] = (10, 18, 42)
            sil[..., 3] = (a > 40) * 255
            Image.fromarray(sil, "RGBA").save(OUT / "hand" / "shadow.png")


def main():
    print("cutting sheets")
    cut_flies()
    cut_hand()
    Image.open(_find("v3bql6")).convert("RGBA").save(OUT / "table.png")
    for junk in ("hand/overhand.png", "fly/impact.png", "_debug_flies.png"):
        p = OUT / junk
        if p.exists():
            p.unlink()
    print("done")


if __name__ == "__main__":
    main()
