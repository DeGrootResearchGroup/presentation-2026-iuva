#!/usr/bin/env python3
"""Slide 8's refractive-interface render and data, from a finished refractiveInterface2D run.

    python3 scripts/render_refractive.py <case> [--time 1]

The case is of-optical-radiation's tutorials/refractiveInterface2D after ./Allrun (two 50 x 25
regions of 1 cm cells, glass on the right). Writes data/refractive.json (G at the tutorial's
./validate probes, which make_plots.py's refractive_bars compares with the analytical values) and
figures/renders/refractive-render.png (the G field as a 4:1 strip).
"""

import argparse
import json
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from common import DATA, RENDERS

NX, NY, DX = 50, 25, 0.01  # cells per region along x and y, and their size (m)
THETA = math.radians(11.25)  # the beam's angle from the x axis in the air
Y0 = 0.10  # beam source height (x = 0)


def read_G(path):
    """G of one region, from an ASCII volScalarField, as a (NY, NX) array."""
    txt = Path(path).read_text()
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*\n(\d+)\n\(([^)]+)\)",
                  txt, re.S)
    return np.array(m.group(2).split(), float).reshape(NY, NX)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("case", type=Path, help="the finished refractiveInterface2D case")
    ap.add_argument("--time", default="1", help="its time directory (default 1)")
    a = ap.parse_args()
    GA = read_G(a.case / a.time / "mediumA" / "G")
    GB = read_G(a.case / a.time / "mediumB" / "G")

    # Probes identical to the tutorial's ./validate
    tan = math.tan(THETA)
    ga = GA[int((0.10 + 0.30 * tan) / DX), int(0.30 / DX)]
    gb = GB[int((0.10 + 0.70 * tan) / DX), int((0.70 - 0.5) / DX)]
    (DATA / "refractive.json").write_text(
        json.dumps({"G_A_sim": float(ga), "G_B_sim": float(gb)}, indent=2) + "\n")
    print(f"G_A_sim = {ga:.4f}, G_B_sim = {gb:.4f}")

    G = np.hstack([GA, GB])
    fig = plt.figure(figsize=(12, 3.0), dpi=200)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.imshow(G, origin="lower", extent=[0, 1, 0, 0.25], cmap="magma",
              vmin=0, vmax=20, interpolation="nearest", aspect="equal")
    ax.axvline(0.5, color="white", lw=2, ls=(0, (5, 3)))
    ax.text(0.25, 0.235, "$n$ = 1.0", color="white", ha="center", va="top", fontsize=22)
    ax.text(0.75, 0.235, "$n$ = 1.5", color="white", ha="center", va="top", fontsize=22)
    # beam axis (incident and refracted)
    thB = math.asin(math.sin(THETA) / 1.5)
    yi = Y0 + 0.5 * tan
    ax.plot([0, 0.5], [Y0, yi], color="#7fd6ff", lw=1.5, ls=":")
    ax.plot([0.5, 1.0], [yi, yi + 0.5 * math.tan(thB)], color="#7fd6ff", lw=1.5, ls=":")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.25)
    ax.axis("off")
    RENDERS.mkdir(parents=True, exist_ok=True)
    fig.savefig(RENDERS / "refractive-render.png", bbox_inches="tight", pad_inches=0.02)


if __name__ == "__main__":
    main()
