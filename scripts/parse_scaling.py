#!/usr/bin/env python3
"""Build data/scaling.csv (one row per run) from the logs written by scripts/cluster.

    python3 scripts/parse_scaling.py                      # every scripts/cluster/results*
    python3 scripts/parse_scaling.py --all                # ignore scripts/cluster/exclude.txt
    python3 scripts/parse_scaling.py scripts/cluster/results01 scripts/cluster/results02

scripts/cluster/ (the job scripts, their results and exclude.txt) is kept on the author's machine
only, since its job scripts carry a personal cluster account; data/scaling.csv is what the deck
uses, and REPRODUCIBILITY.md records how the runs were made and which were excluded.

Each results folder may hold np<N>/ or np<N>_r<R>/ run directories; every run directory is one
sample (the rep column is "<folder>/<run>"). Each holds log.foamRun and log.opticalRadiationFoam;
the 16-core runs also hold dose_seconds.txt. Start-up and the first step are excluded. A run
listed in exclude.txt (it shared a node with another of these jobs) is left out.

  flow_s  wall-clock seconds per flow iteration
  dom_s   wall-clock seconds per DO ray sweep (sweeps counted from the log, because the
          number of sweeps per step depends on convergence and on the decomposition)
  dose_s  serial dose tracker, total seconds (blank where it was not run)
  exclusive  1 if the run was on a whole node (results folder name ends in _excl)
"""

import re
import sys
from pathlib import Path

from common import DATA, ROOT

CLOCK = re.compile(r"ExecutionTime = [\d.]+ s\s+ClockTime = (\d+) s")
# One sweep per solve of the first band's first ray, as collect_records.py counts them.
SWEEP = re.compile(r"Solving for I_0_0,")
RUN = re.compile(r"np(\d+)(?:_r(\d+))?$")


def steps(path):
    """Split a log into per-step blocks: list of (text, clocktime)."""
    text = Path(path).read_text(errors="replace")
    out = []
    for b in re.split(r"(?m)^Time = ", text)[1:]:
        m = CLOCK.findall(b)
        if m:
            out.append((b, int(m[-1])))
    return out


def per_unit(path, unit):
    st = steps(path)
    if len(st) < 3:
        sys.exit(f"{path}: too few timed steps ({len(st)})")
    elapsed = st[-1][1] - st[0][1]               # steps 2..N
    if unit == "iteration":
        n = len(st) - 1
    else:
        n = sum(len(SWEEP.findall(b)) for b, _ in st[1:])
        if n == 0:
            sys.exit(f"{path}: no ray sweeps found after the first step")
    return elapsed / n


def excluded(use_all):
    f = ROOT / "scripts" / "cluster" / "exclude.txt"
    if use_all or not f.exists():
        return set()
    return {ln.split("#")[0].strip() for ln in f.read_text().splitlines()
            if ln.split("#")[0].strip()}


def main(folders, use_all=False):
    skip = excluded(use_all)
    runs = []
    for top in folders:
        for p in Path(top).iterdir():
            m = RUN.match(p.name)
            if p.is_dir() and m:
                runs.append((int(m.group(1)), f"{Path(top).name}/{p.name}", p))
    runs.sort()
    rows = ["cores,rep,flow_s,dom_s,dose_s,exclusive"]
    for n, rep, p in runs:
        if rep in skip:
            print(f"excluding {rep} (see scripts/cluster/exclude.txt)", file=sys.stderr)
            continue
        if not (p / "log.foamRun").exists() or not (p / "log.opticalRadiationFoam").exists():
            print(f"skipping {rep}: incomplete (no solver logs)", file=sys.stderr)
            continue
        d = p / "dose_seconds.txt"
        dose = d.read_text().strip() if d.exists() else ""
        rows.append(f"{n},{rep},{per_unit(p / 'log.foamRun', 'iteration'):.4f},"
                    f"{per_unit(p / 'log.opticalRadiationFoam', 'sweep'):.4f},{dose},"
                    f"{int('_excl' in Path(rep).parts[0])}")
    (DATA / "scaling.csv").write_text("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    args = [a for a in sys.argv[1:] if not a.startswith("--")] or sorted(
        str(p) for p in (ROOT / "scripts" / "cluster").glob("results*"))
    main(args, use_all="--all" in flags)
