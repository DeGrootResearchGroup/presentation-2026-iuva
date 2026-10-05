#!/usr/bin/env python3
"""Each Sozzi fluence rate's mean dose from its volume integral, against the tracked mean dose.

    python3 scripts/sozzi_mean_dose.py

In a steady flow the dose averaged over the outflow is the volume integral of G divided by the flow
rate, whatever the flow's pattern: a fluid parcel's dose is the integral of G along its path, and
weighting the paths by the flux they carry turns the sum into an integral over the volume. A
tracker whose particles stay distributed as the fluid is must return that mean, so a tracked mean
above it means the particles spent more time than the fluid does in bright water.

Writes data/sozzi_mean_dose.json, plotted by make_plots.py (sozzi_mean_dose):

- Sozzi & Taghipour (2006): their radial (infinite line, eq. 3) and multiple-point-source (MPSS,
  eq. 5) lamp models, integrated over their reactor (Table 1: 8.9 cm body, 88.9 cm long, 1 cm sleeve
  radius, 80 cm arc, 35 W, 70 % UVT) at 25 GPM (15.8e-4 m^3/s, as they state). The arc's position
  along the body is not given; it is centred here. Their MPSS Lagrangian mean dose, 68 mJ/cm^2, is
  from their section 4.3; they give none for the radial model.
- The same MPSS integral for the industrial prototype reactor of their Table 1 and Fig. 1c (8.6 cm
  body, 101 cm long, 2.26 cm lamp, 88 cm arc, 35 W), at the same 70 % UVT and 25 GPM, written under
  "prototype". The lamp holder and the outlet reduction ring are not in the integral.
- This work, uvmesh mesh: the integrals and tracked means of aquaflux validation/sozzi_radiation/
  uvmesh_swap.py (data/sozzi_dose_swap.json), and the line source's tracked mean
  (data/sozzi_dose_analytical.csv; the line source is their eq. 3 on the arc, so its integral is the
  radial model's).
- The same line source on the tutorial's snappyHexMesh mesh and SST flow, traced with the
  uncorrected random walk, the corrected one and the Langevin model (summary.dat of case/arc,
  case/arc_wm and case/arc_lgv89 under IUVA_SOZZI).
"""

import json
import math
from dataclasses import dataclass

import numpy as np
from common import DATA, SOZZI, load_doses, summary_value

SIGMA = -math.log(0.7)  # absorption coefficient, 1/cm (their eq. 4: 70 % UVT)
P = 35000.0  # lamp UV output, mW
Q = 15.8e-4 * 1e6  # flow rate, cm^3/s (25 US gal/min)
N_SOURCES = 200  # MPSS point sources (they found no change above 100)


@dataclass(frozen=True)
class Reactor:
    """An annular reactor of Sozzi & Taghipour's Table 1, in cm: the arc's length, the sleeve's and
    the body's radii, and the body's length (the arc centred in it)."""

    arc: float
    sleeve: float
    body_radius: float
    body_length: float


SIMULATED = Reactor(arc=80.0, sleeve=1.0, body_radius=4.45, body_length=88.9)
PROTOTYPE = Reactor(arc=88.0, sleeve=1.13, body_radius=4.3, body_length=101.0)


def radial_integral(reactor=SIMULATED):
    """Their eq. 3 over the annulus along the arc, in closed form [mW cm]."""
    return P * (1 - math.exp(-SIGMA * (reactor.body_radius - reactor.sleeve))) / SIGMA


def mpss_field(r, z, reactor=SIMULATED):
    """Their eq. 5: point sources on the axis along the arc, water path l (r - r_L) / r [mW/cm^2]."""
    zs = (np.arange(N_SOURCES) + 0.5) / N_SOURCES * reactor.arc
    g = np.zeros(np.broadcast(r, z).shape)
    for zi in zs:
        l2 = r**2 + (z - zi) ** 2
        g += P / N_SOURCES / (4 * math.pi * l2) * np.exp(-SIGMA * (r - reactor.sleeve) * np.sqrt(l2) / r)
    return g


def mpss_integral(reactor=SIMULATED):
    """Their eq. 5 over the whole annular body, the arc centred in it [mW cm]."""
    gap = (reactor.body_length - reactor.arc) / 2
    r = np.linspace(reactor.sleeve, reactor.body_radius, 701)
    r = 0.5 * (r[1:] + r[:-1])
    z = np.linspace(-gap, reactor.arc + gap, 1801)
    z = 0.5 * (z[1:] + z[:-1])
    rr, zz = np.meshgrid(r, z, indexing="ij")
    return float(np.sum(mpss_field(rr, zz, reactor) * 2 * math.pi * rr) * (r[1] - r[0]) * (z[1] - z[0]))


def summary_mean(case):
    """The tracked mean dose of a case under the Sozzi run directory's case/ [mJ/cm^2]."""
    f = next((SOZZI / "case" / case / "postProcessing" / "radiationDose").glob("*/summary.dat"))
    return summary_value(f, "meanDose_mJcm2")


def main():
    swap = json.loads((DATA / "sozzi_dose_swap.json").read_text())
    integral = swap["fields_compared"]["mean_dose_from_integral"]
    radial = radial_integral() / Q  # mW s / cm^2 = mJ/cm^2
    rows = [
        {"label": "Sozzi & Taghipour, MPSS lamp", "integral": mpss_integral() / Q, "tracked": 68.0,
         "group": "paper"},
        {"label": "This work: line source (their eq. 3)", "integral": radial,
         "tracked": float(load_doses(DATA / "sozzi_dose_analytical.csv").mean()), "group": "this"},
        {"label": "This work: DO, 288 directions", "integral": integral["dom288"],
         "tracked": swap["runs"]["dom288"]["mean"], "group": "this"},
        {"label": "This work: aquaflux", "integral": integral["aquaflux"],
         "tracked": swap["runs"]["aquaflux"]["mean"], "group": "this"},
    ]
    snappy = {
        "uncorrected random walk": summary_mean("arc"),
        "corrected random walk": summary_mean("arc_wm"),
        "Langevin": summary_mean("arc_lgv89"),
    }
    out = {
        "note": "mJ/cm^2. 'integral' is integral(G dV) / Q; 'tracked' the tracker's mean over escaped particles.",
        "paper_radial_integral": radial,
        "prototype": {"integral": mpss_integral(PROTOTYPE) / Q, "simulated_integral": mpss_integral() / Q,
                      "note": "Sozzi & Taghipour Table 1 prototype (Fig. 1c), their MPSS lamp model, 35 W, 70 % UVT, "
                              "25 GPM, arc centred in the body; lamp holder and outlet ring not included"},
        "rows": rows,
        "snappy_line_source": {"integral": radial, "tracked": snappy,
                               "configuration": "tutorial snappyHexMesh mesh, SST flow, line source on the arc, seed 42, 3 threads; "
                                                "tracker: uncorrected walk OOR 659ec4a, corrected walk OOR 7f11000 plus the "
                                                "drift-correction change later merged as PR #88, Langevin OOR ebadf6e"},
    }
    (DATA / "sozzi_mean_dose.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"{'prototype (MPSS)':>32}: integral {out['prototype']['integral']:.1f}")
    for row in rows:
        print(f"{row['label']:>32}: integral {row['integral']:.1f}, tracked {row['tracked']:.1f}")
    print(f"{'snappy line source':>32}: integral {radial:.1f}, tracked " +
          ", ".join(f"{k} {v:.1f}" for k, v in snappy.items()))


if __name__ == "__main__":
    main()
