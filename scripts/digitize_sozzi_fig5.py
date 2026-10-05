#!/usr/bin/env python3
"""Digitize Sozzi & Taghipour (2006) Fig. 5, the Lagrangian dose histogram (needs numpy, Pillow).

    python3 scripts/digitize_sozzi_fig5.py fig5.png

`fig5.png` is a screen capture of the figure from the paper (L-shape reactor, 25 GPM, MPSS lamp
model), axes included; the capture is not kept in this repository. Writes
data/sozzi_fig5_digitized.csv: one row per bar, its dose range and its particle count.

The axes are found as the longest dark row and column, and calibrated by their tick marks (x: 0 to
160 mJ/cm2, y: 0 to 400 particles). Bar edges are the dark runs along a row just above the x axis;
each bar's height is the median, over its interior columns, of the darkness-weighted centre of the
first dark run below the top of the plot. The paper clips the figure at 150 mJ/cm2 (doses reached
270), so the bars cover only the particles below that.
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sozzi_fig5_digitized.csv"
X_TICKS = (0, 160)  # first and last labelled x tick, mJ/cm2
Y_TICKS = (0, 400)  # first and last labelled y tick, particles
DARK = 150  # grey level below which a pixel is ink


def runs(indices):
    """Centres of runs of consecutive integers."""
    out, cur = [], [indices[0]]
    for a in indices[1:]:
        if a - cur[-1] <= 1:
            cur.append(a)
        else:
            out.append(np.mean(cur))
            cur = [a]
    out.append(np.mean(cur))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    a = ap.parse_args()
    im = np.asarray(Image.open(a.image).convert("L")).astype(float)
    ink = im < DARK
    x_axis = int(np.argmax(ink.sum(axis=1)))  # row of the x axis
    y_axis = int(np.argmax(ink.sum(axis=0)))  # column of the y axis

    # Tick marks: short dark runs just outside each axis.
    xt = runs([c for c in range(im.shape[1]) if ink[x_axis + 3 : x_axis + 8, c].sum() >= 4])
    yt = runs([r for r in range(im.shape[0]) if ink[r, y_axis - 9 : y_axis - 2].sum() >= 5])
    xt = [c for c in xt if c >= y_axis - 1]  # drop marks left of the axis (the y label)
    yt = [r for r in yt if r <= x_axis + 1]  # drop marks below the axis (the caption)
    c0, c1 = xt[0], xt[-1]
    r0, r1 = yt[-1], yt[0]
    dose = lambda c: X_TICKS[0] + (c - c0) / (c1 - c0) * (X_TICKS[1] - X_TICKS[0])
    count = lambda r: Y_TICKS[0] + (r0 - r) / (r0 - r1) * (Y_TICKS[1] - Y_TICKS[0])

    row = x_axis - 5
    edges = runs([c for c in range(y_axis + 5, im.shape[1]) if im[row, c] < DARK])
    rows = []
    for e0, e1 in zip(edges[:-1], edges[1:]):
        tops = []
        for c in range(int(round(e0)) + 2, int(round(e1)) - 1):
            r = int(np.argmax(ink[int(r1) - 6 : x_axis - 1, c])) + int(r1) - 6
            run = [r]
            while ink[run[-1] + 1, c]:
                run.append(run[-1] + 1)
            w = 255 - im[run, c]
            tops.append(np.sum(np.array(run) * w) / w.sum())
        rows.append((dose(e0), dose(e1), count(np.median(tops))))
    rows = np.array(rows)
    OUT.write_text(
        "# Sozzi & Taghipour (2006), Fig. 5: Lagrangian dose histogram, L-shape reactor, 25 GPM,\n"
        "# MPSS lamp model; digitized by scripts/digitize_sozzi_fig5.py. Clipped at 150 mJ/cm2.\n"
        "dose_lo_mJ_cm2,dose_hi_mJ_cm2,count\n"
        + "".join(f"{lo:.2f},{hi:.2f},{n:.1f}\n" for lo, hi, n in rows)
    )
    print(f"wrote {OUT}: {len(rows)} bars, {rows[:, 2].sum():.0f} particles below 150 mJ/cm2")


if __name__ == "__main__":
    main()
