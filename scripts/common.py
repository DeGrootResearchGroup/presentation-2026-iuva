"""What the deck's scripts share: its colours, where the data and the runs are, and the dose helpers.

Imported by the other scripts (they run from the deck root with ``scripts/`` on their path, which
``python3 scripts/<name>.py`` gives them).

Paths to the simulation runs, which are not in this repository, come from the environment:

``IUVA_RUNS``
    The folder holding the run directories (default ``~/aquaflux-runs``).
``IUVA_SOZZI``
    The Sozzi run directory: the uvmesh mesh, its flow, the DO and tracker cases, the slide 15
    swap set and the background grids (default ``$IUVA_RUNS/sozzi_sst_dose_2026-10-01``).
"""

import math
import os
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIGURES = ROOT / "figures"
RENDERS = FIGURES / "renders"

RUNS = Path(os.environ.get("IUVA_RUNS", Path.home() / "aquaflux-runs"))
SOZZI = Path(os.environ.get("IUVA_SOZZI", RUNS / "sozzi_sst_dose_2026-10-01"))

# Series colours, fixed per entity across the whole deck and checked for colour-vision-deficiency
# separation and contrast, every pair against every other.
THIS = "#6b3fa0"  # this work: of-optical-radiation's DO and radiationDose
FLUENT = "#eb6834"  # ANSYS Fluent
AQUA = "#2a78d6"  # aquaflux
INK = "#1a1a1a"  # text and the exact or analytical answer
INK2 = "#52514e"  # secondary text
MUTED = "#8a8894"  # axes, outlines, the ideal-scaling line
GRID = "#e4e2ea"
SURFACE = "#ffffff"


def log_reduction(dose, k):
    """Log reduction of a first-order dose response, ``-log10 mean(exp(-k D))``.

    ``dose`` in mJ/cm^2, ``k`` in cm^2/mJ.
    """
    return -math.log10(float(np.mean(np.exp(-k * np.asarray(dose)))))


def load_doses(path):
    """The doses (mJ/cm^2) of the escaped particles in a radiationDose ``doseDistribution.csv``.

    The file's header row may start with ``#``; a file with no ``endReason`` column is taken as
    escaped particles only.
    """
    with open(path, newline="") as f:
        lines = [line for line in f if line.strip()]
    header = [h.strip() for h in lines[0].lstrip("#").split(",")]
    dose = header.index("dose_mJ_cm2")
    reason = header.index("endReason") if "endReason" in header else None
    out = []
    for line in lines[1:]:
        if line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if reason is not None and parts[reason].lower() not in ("escaped", "escape", "0"):
            continue
        out.append(float(parts[dose]))
    return np.array(out)


def summary_value(path, key):
    """One value from a radiationDose ``summary.dat`` (``key  value`` lines), as a float."""
    match = re.search(rf"^{re.escape(key)}\s+(\S+)", Path(path).read_text(), re.MULTILINE)
    if match is None:
        raise KeyError(f"{key} not in {path}")
    return float(match.group(1))
