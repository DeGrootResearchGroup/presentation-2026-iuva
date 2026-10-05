#!/usr/bin/env python3
"""Export slide 10's data from a traced Sozzi case (needs pyvista).

    python3 scripts/export_sozzi_data.py <case> --time 2060                    # this work's DO
    python3 scripts/export_sozzi_data.py <case> --time 2059 --series fluent    # Fluent's DO

Writes data/sozzi_G_<series>.csv (r_m,G_W_m2 at the lamp mid-plane, cell-averaged over the azimuth
and in radial bins) and copies the run's doseDistribution.csv to data/sozzi_dose_<series>.csv.
The series is "this" (this work's DO, the default; the deck's case is case/slide10_dom6_lu_B under
the Sozzi run directory) or "fluent" (a case whose G is Fluent's DO, put on the OpenFOAM mesh by
of-mesh-converter's transfer: swap/fluent33). The case is read through a file named out.foam
beside constant/. Then run scripts/make_plots.py.
"""

import argparse
import shutil
from pathlib import Path

import numpy as np
import pyvista as pv

from common import DATA

X_MEAN_WINDOW = (0.405, 0.05)  # centre and half-width in x; the lamp arc is 0 to 0.81 m
R_LAMP, R_BODY = 0.010, 0.0445


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("case", type=Path, help="the traced case (see the module docstring)")
    ap.add_argument("--time", type=float, required=True, help="the time holding G (2060 or 2059)")
    ap.add_argument("--series", choices=("this", "fluent"), default="this")
    a = ap.parse_args()

    reader = pv.OpenFOAMReader(str(a.case / "out.foam"))
    reader.set_active_time_value(a.time)
    reader.cell_to_point_creation = False
    mesh = reader.read()["internalMesh"]
    cc, g = mesh.cell_centers().points, mesh.cell_data["G"]
    # Azimuthal ring average about the lamp axis: a single line can sit on a direction-bin edge
    # and misrepresent a DO solution with ray effects.
    rad = np.hypot(cc[:, 1], cc[:, 2])
    sel = (abs(cc[:, 0] - X_MEAN_WINDOW[0]) < X_MEAN_WINDOW[1]) & (rad > R_LAMP)
    r, gs = rad[sel], g[sel]
    edges = np.linspace(R_LAMP, R_BODY, 16)
    idx = np.digitize(r, edges)
    rows = [(r[idx == i].mean(), gs[idx == i].mean()) for i in range(1, len(edges)) if (idx == i).any()]
    DATA.mkdir(exist_ok=True)
    np.savetxt(DATA / f"sozzi_G_{a.series}.csv", rows, delimiter=",", header="r_m,G_W_m2", comments="", fmt="%.6g")
    dose = next((a.case / "postProcessing" / "radiationDose").glob("*/doseDistribution.csv"))
    shutil.copy(dose, DATA / f"sozzi_dose_{a.series}.csv")
    print(f"wrote {len(rows)} radial points and {dose}")


if __name__ == "__main__":
    main()
