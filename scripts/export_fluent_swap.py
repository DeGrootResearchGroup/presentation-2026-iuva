#!/usr/bin/env python3
"""The Fluent DO runs of the Sozzi swap set, summarised like the swap harness's summary.json.

    python3 scripts/export_fluent_swap.py        # then: python3 scripts/make_plots.py

Each Fluent DO field (the CGNS exports in fluent_results/) was put into a copy of the swap set's
flow by `of-mesh-converter transfer` and traced like the other swap runs (swap/fluent33 for
3 x 3 divisions per octant, swap/fluent66 for 6 x 6). This reads their doseDistribution.csv and
G and writes data/sozzi_fluent_swap.json: per run the dose statistics and log reductions at the
inactivation constants of data/sozzi_dose_swap.json, and the volume-weighted mean G over the
reactor (cell volumes from the harness's swap/cell_volumes.npy).

  IUVA_SOZZI   the Sozzi runs (default: ~/aquaflux-runs/sozzi_sst_dose_2026-10-01)
"""

import json
import math
import re

import numpy as np
from common import DATA, SOZZI

RUNS ={"fluent72": ("fluent33", "3 × 3"), "fluent288": ("fluent66", "6 × 6")}


def escaped_doses(case):
    f = next((case / "postProcessing" / "radiationDose").glob("*/doseDistribution.csv"))
    rows = [l.split(",") for l in f.read_text().splitlines()[1:] if l.strip()]
    return np.array([float(r[3]) for r in rows if r[1].strip() == "escaped"])


def internal_field(path):
    text = path.read_text()
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", text)
    values = np.array(text[m.end():text.index(")", m.end())].split(), dtype=float)
    assert values.size == int(m.group(1))
    return values


def main():
    swap = json.loads((DATA / "sozzi_dose_swap.json").read_text())
    ks = sorted(swap["runs"]["aquaflux"]["log_reduction"], key=float)
    volumes = np.load(SOZZI / "swap" / "cell_volumes.npy")
    out = {"particles": None, "runs": {}, "volume_mean_all": {}}
    for name, (folder, divisions) in RUNS.items():
        case = SOZZI / "swap" / folder
        d = escaped_doses(case)
        out["particles"] = int(d.size)
        out["runs"][name] = {
            "case": f"swap/{folder}", "divisions_per_octant": divisions, "n": int(d.size),
            "mean": float(d.mean()), "min": float(d.min()), "max": float(d.max()),
            **{f"p{q}": float(np.percentile(d, q)) for q in (1, 5, 50, 95, 99)},
            "log_reduction": {k: -math.log10(float(np.mean(np.exp(-float(k) * d)))) for k in ks},
        }
        g = internal_field(case / "2059" / "G")
        out["volume_mean_all"][name] = float((g * volumes).sum() / volumes.sum())
    (DATA / "sozzi_fluent_swap.json").write_text(json.dumps(out, indent=2) + "\n")
    for name, r in out["runs"].items():
        print(f"{name}: mean {r['mean']:.2f}, LR(0.1) {r['log_reduction']['0.1']:.3f}, "
              f"mean G {out['volume_mean_all'][name]:.2f} W/m2")


if __name__ == "__main__":
    main()
