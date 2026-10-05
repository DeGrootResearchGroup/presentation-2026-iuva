#!/usr/bin/env python3
"""Where the dispersion models put particles near the Sozzi reactor's walls.

    python3 scripts/sozzi_wall_occupancy.py        # then: python3 scripts/make_plots.py

Reads the snapshot runs in $IUVA_SOZZI/wallsnap/<model>: the deck's tracker (of-optical-radiation
b23582b), flow (uvmesh, k-omega SST at 2059), seeding and seed, with three instances stopped at
maxTime 1.5, 2 and 2.5 s. The tracker ends the last step at maxTime, so the end points of the
tracks still inside then ("timedOut") are where the particles are at that time: a snapshot.

Particles in the annulus between the sleeve (r = 10 mm) and the chamber wall (r = 44.5 mm), with
0.1 < x < 0.7 m, pooled over the three snapshots, are counted in shells by distance from each wall
and divided by the count the shell's share of the annulus volume would hold. A well-mixed model
keeps a uniform distribution uniform, but one injection has not yet filled the slow water next to
the walls 1.5 to 2.5 s in, so the reference is not 1 there: it is rd05, the random displacement
(diffusion) walk with a 0.5 ms step, which is well mixed by construction.

Writes data/sozzi_wall_occupancy.json.
"""

import csv
import json

import numpy as np
from common import DATA, SOZZI

RS, RW = 0.010, 0.0445
X_RANGE = (0.1, 0.7)
# Shell edges [m]. The sleeve's first cell is 20 um thick, the chamber wall's 100 um.
EDGES = [0, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3, 3e-3]
MODELS = {
    "drw": "discrete random walk, uncorrected (as in OpenFOAM and Fluent)",
    "drw_wm": "discrete random walk with the well-mixed corrections",
    "lgv": "Langevin model (used for every result in the talk)",
    "rd05": "random displacement, 0.5 ms steps (well-mixed reference)",
}


def positions(case):
    pos = []
    for f in sorted((case / "postProcessing").glob("snap*/*/doseDistribution.csv")):
        rows = csv.reader(line for line in f.open() if not line.startswith("#"))
        pos += [[float(v) for v in row[4:7]] for row in rows if row[1] == "timedOut"]
    return np.array(pos)


def main():
    out = {"edges_m": EDGES, "x_range_m": X_RANGE, "models": {}}
    ann = RW**2 - RS**2
    for name, label in MODELS.items():
        p = positions(SOZZI / "wallsnap" / name)
        r = np.hypot(p[:, 1], p[:, 2])
        sel = (p[:, 0] > X_RANGE[0]) & (p[:, 0] < X_RANGE[1]) & (r < RW + 1e-4)
        r = r[sel]
        n = len(r)
        walls = {}
        for wall, d, outer in (("sleeve", r - RS, False), ("chamber", RW - r, True)):
            ratio, err, counts = [], [], []
            for a, b in zip(EDGES[:-1], EDGES[1:]):
                share = (((RW - a) ** 2 - (RW - b) ** 2) if outer
                         else ((RS + b) ** 2 - (RS + a) ** 2)) / ann
                lo = -1.0 if a == 0 else a  # the shell next to the wall includes the facet sag
                k = int(np.sum((d >= lo) & (d < b)))
                expected = n * share
                counts.append(k)
                ratio.append(k / expected)
                err.append(np.sqrt(max(k, 1)) / expected)
            walls[wall] = {"ratio": ratio, "poisson_se": err, "counts": counts}
        out["models"][name] = {"label": label, "particles_in_annulus": n, **walls}
        print(f"{name}: {n} particles; sleeve " +
              " ".join(f"{v:.2f}" for v in walls["sleeve"]["ratio"]) + "; chamber " +
              " ".join(f"{v:.2f}" for v in walls["chamber"]["ratio"]))
    (DATA / "sozzi_wall_occupancy.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
