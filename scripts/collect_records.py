#!/usr/bin/env python3
"""Collect every simulation's settings and commits into data/records/, for the backup tables.

    python3 scripts/collect_records.py            # then: python3 scripts/make_case_tables.py

For each case this reads the runs' own records (record.json, the aquaflux and reference JSON,
provenance.json where a run predates records) and the OpenFOAM dictionaries it ran with, and
writes

  data/records/<case>.json      the tables the backup slides show
  data/records/raw/<case>/...   a copy of every record read, so the deck keeps them even if
                                the run folders move

The runs themselves are not in this repository. Their locations are read from the environment
variables below (defaults under the run archive, IUVA_RUNS, see common.py); each run's settings and
code commits are what this script copies out of them, so the records here are enough to repeat a
run from the public of-optical-radiation and aquaflux repositories. Local paths in the copies are
replaced by placeholders (``<aquaflux>``, ``<of-optical-radiation>``, ``<runs>``). Nothing is
computed from fields, only read; numpy is not needed.

  IUVA_ROOM_CASE      an aquaflux checkout's validation/ray_effects_room, with its work/ outputs
                      (default $IUVA_RUNS/ray_effects_room, a link to that checkout here)
  IUVA_SOZZI          the Sozzi runs of slides 2, 3, 9, 10 and 15: the uvmesh mesh, its k-omega SST
                      flow and every fluence rate and dose (provenance_iuva.json, case/, swap/)
  IUVA_SOZZI_FLOW     that flow's dictionaries and logs (default $IUVA_SOZZI/flow)
  IUVA_REFRACTIVE     the refractiveInterface2D run
  IUVA_BUNNY_STL      the bunny STL's record (sha256 and how it was made)

Run with no argument to collect every record, or name the collectors to run (room, sozzi_slide10,
sozzi_prototype, sozzi_swap, refractive).
"""

import json
import os
import re
import sys
from pathlib import Path

from common import DATA, RUNS, SOZZI, summary_value

OUT = DATA / "records"
HOME = Path.home()

AQ_CASE = Path(os.environ.get("IUVA_ROOM_CASE", RUNS / "ray_effects_room"))
SOZZI_FLOW = Path(os.environ.get("IUVA_SOZZI_FLOW", SOZZI / "flow"))
REFRACTIVE = Path(os.environ.get("IUVA_REFRACTIVE", RUNS / "iuva2026/refractiveInterface2D"))
BUNNY_STL = Path(os.environ.get("IUVA_BUNNY_STL", RUNS / "iuva2026/voronoi_bunny_open.stl.json"))

# Local paths become placeholders in everything written here. A path into a checkout is recognized
# by the repository's own layout: aquaflux keeps its cases under validation/, of-optical-radiation
# its cases under tutorials/. The run archive and anything else under the home directory are
# replaced as well.
_HOME = r"(?:~|%s)" % re.escape(str(HOME))
_LOCAL = [
    (re.compile(_HOME + r"/[^\"\s]*?/(?=validation/)"), "<aquaflux>/"),
    (re.compile(_HOME + r"/[^\"\s]*?/(?=tutorials/)"), "<of-optical-radiation>/"),
    (re.compile(_HOME + r"/aquaflux-runs"), "<runs>"),
    (re.compile(_HOME + r"/[^\"\s]*"), "<local>"),
    (re.compile(r"/private/tmp/[^\"\s]*"), "<scratch>"),
]


def public(text):
    """``text`` with local paths replaced by placeholders."""
    for pattern, placeholder in _LOCAL:
        text = pattern.sub(placeholder, text)
    return text


# ------------------------------------------------------------------ helpers ---
def entry(path, key):
    """The value of ``key value;`` in an OpenFOAM dictionary, or None."""
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s+([^;]+);", Path(path).read_text())
    return m.group(1).strip() if m else None


def patch_type(field, patch):
    text = Path(field).read_text()
    m = re.search(rf"(?s)\b{re.escape(patch)}\s*\{{(.*?)\}}", text)
    return re.search(r"\btype\s+(\w+);", m.group(1)).group(1) if m else None


def build(log):
    m = re.search(r"(?m)^Build\s*:\s*(\S+)", Path(log).read_text(errors="replace"))
    return m.group(1) if m else None


def short(sha):
    return sha[:8] if sha else "not recorded"


def keep(case, src, name=None):
    """Copy a record into data/records/raw/<case>/ and return it parsed.

    Local paths in the copy become placeholders (see ``public``); the record itself is left as it
    is.
    """
    dest = OUT / "raw" / case / (name or src.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(errors="replace")
    dest.write_text(public(text))
    return json.loads(text) if src.suffix == ".json" else None


def dom_settings(case_dir):
    props = case_dir / "constant" / "opticalRadiationProperties"
    return {
        "directions": 2 * int(entry(props, "nPhi")) * int(entry(props, "nTheta")),
        "bins": f"{entry(props, 'nPhi')}×{entry(props, 'nTheta')}",
        "pixels": f"{entry(props, 'nPixelPhi')}×{entry(props, 'nPixelTheta')}",
        "scheme": entry(case_dir / "system" / "fvSchemes", "div(Ji,Ii_h)").replace("bounded Gauss ", ""),
        "convergence": entry(props, "convergence"),
        "max_iter": entry(props, "maxIter"),
    }


def sweeps(case_dir):
    """Ray sweeps a DO solve took: the times its log solves the first ray."""
    return (case_dir / "log.opticalRadiationFoam").read_text().count("Solving for I_0_0,")


def _clean(case):
    """Empty data/records/raw/<case>/ so no copy from an earlier set of runs is left behind."""
    raw = OUT / "raw" / case
    if raw.exists():
        for f in raw.rglob("*"):
            if f.is_file():
                f.unlink()


def _tracker_row(d, label, extra=()):
    """One row of a traced fluence rate: its label, ``extra`` columns, end counts, mean dose and log
    reduction at k = 0.1, read from the case's radiationDose summary."""
    f = next((d / "postProcessing" / "radiationDose").glob("*/summary.dat"))
    counts = {k: int(summary_value(f, k)) for k in ("totalSeeded", "escaped", "timedOut", "stuck")}
    mean, lr = summary_value(f, "meanDose_mJcm2"), summary_value(f, "logReduction_k=0.1")
    return [label, *extra, f"{counts['escaped']:,} / {counts['stuck']} / {counts['timedOut']}", f"{mean:.1f}", f"{lr:.3f}"]


def _report_value(path, label):
    """The value after ``label :`` in a text report (of-mesh-converter's transfer report)."""
    return re.search(rf"(?m)^\s*{re.escape(label)}\s*:\s*(.+)$", Path(path).read_text()).group(1).strip()


def write(case, record):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{case}.json").write_text(public(json.dumps(record, indent=2, ensure_ascii=False)) + "\n")
    print(f"wrote data/records/{case}.json")


# ------------------------------------------------------ ray-effects room ---
#: Room runs whose wall time overlapped other work, and is marked so.
SHARED_ROOM_RUNS = {"bunny_reflecting_nphi6_ntheta6"}


def room():
    case = "ray_effects_room"
    _clean(case)
    template = AQ_CASE / "case"
    scheme = entry(template / "system" / "fvSchemes", "div(Ji,Ii_h)").replace("bounded Gauss ", "")
    meshes = {}
    for mesh in ("bunny", "empty"):
        rec = keep(case, AQ_CASE / "work" / mesh / "case" / "mesh_record.json", f"{mesh}_mesh_record.json")
        meshes[mesh] = rec
    stl = json.loads(BUNNY_STL.read_text())
    dom_rows = []
    for run in sorted((AQ_CASE / "work" / "runs").glob("*/record.json")):
        r = keep(case, run, f"dom_{run.parent.name}.json")
        dom_rows.append([
            run.parent.name,
            str(r["directions"]),
            f"{r['n_pixel_phi']}×{r['n_pixel_theta']}",
            scheme,
            # Records before the reflecting variant carry no wall_reflectance: the black template.
            str(r["wall_reflectance"]) if "wall_reflectance" in r else "0 (template)",
            f"{r['convergence']} / {r['max_iter']}",
            str(r["outer_iterations"]),
            str(r["mpi_ranks"]),
            short(r["of_optical_radiation_commit"]),
            f"{r['wall_seconds']:.0f}" + ("*" if r.get("wall_seconds_note") else "")
            + ("†" if run.parent.name in SHARED_ROOM_RUNS else ""),
        ])
    aq_rows = []
    for name in ("empty", "bunny", "empty_volume", "bunny_volume", "bunny_reflecting"):
        f = AQ_CASE / "work" / "aquaflux" / f"{name}.json"
        if not f.exists():
            continue
        r = keep(case, f, f"aquaflux_{name}.json")
        code = r.get("code", {})
        facets = r.get("refined_lamp_facets") or r.get("lamp_facets")
        if name.endswith("volume"):
            facets = f"{r['lamp_facets']} (cells), {r['refined_lamp_facets']} (slices)"
        seconds = r.get("total_s") or r.get("timing_s", {}).get("total")
        aq_rows.append([
            f"aquaflux {name}",
            str(facets),
            f"{r['room_triangles']} room triangles, ρ = {r['wall_reflectance']}" if "room_triangles" in r else "black",
            f"jax {r['jax']}",
            short(code.get("aquaflux_commit")) + ("" if code.get("worktree_clean", True) else " (dirty)"),
            f"{seconds:.0f}" if seconds else "",
        ])
    for name in ("empty", "bunny", "bunny_stl"):
        f = AQ_CASE / "work" / "reference" / f"{name}.json"
        if not f.exists():
            continue
        r = keep(case, f, f"reference_{name}.json")
        code = r.get("code", {})
        aq_rows.append([
            f"exact {name}",
            f"{r['window_samples']} window samples",
            "black" + (", STL bunny" if r.get("bunny") == "stl" else ""),
            f"trimesh {r['trimesh']} + Embree",
            short(code.get("aquaflux_commit")) + ("" if code.get("worktree_clean", True) else " (dirty)"),
            f"{r['seconds']:.0f}",
        ])
    write(case, {
        "title": "Ray-effects room (slides 13–14)",
        "common": [
            ["Room", "4 × 4 × 3 m, air at 222 nm, transparent, no scattering"],
            ["Lamp", "Ushio B1: `ushio_b1.ies` in the case, identical to this deck's `data/ushio_b1_222nm.ies` (OSLUV via guv-calcs). iesEmitter, 118.826 mW, facing down; the 6 × 4.5 cm window meshed as a 6.25 × 4.375 cm patch"],
            ["Bunny", f"`voronoi_bunny_open.stl` sha256 {stl['sha256'][:12]}…, base at 1.2 m; {stl['made_by'].split('/')[-1]}"],
            ["Meshes", f"bunny {meshes['bunny']['check_mesh']['cells']:,} cells, empty {meshes['empty']['check_mesh']['cells']:,}; snappyHexMesh at OOR {short(meshes['bunny']['of_optical_radiation_commit'])}"],
            ["Case files", "aquaflux `validation/ray_effects_room` (DeGrootResearchGroup/aquaflux#597); DOM runs made by its `generate_dom.py`"],
            ["OpenFOAM", f"build {build(AQ_CASE / 'work' / 'runs' / 'bunny_nphi6_ntheta6' / 'log.opticalRadiationFoam')}, in a Docker image built from of-optical-radiation's `Dockerfile`"],
            ["DO angular grids", "uniform, nPhi = nTheta (of-optical-radiation's nTheta bins span the whole sphere, so the bins are square only then): 6 × 6 = 72 directions, 12 × 12 = 288 (Fluent's 3 × 3 and 6 × 6 θ × φ divisions per octant). Runs of 2026-10-02/03, one at a time; the earlier 8 × 4 and 16 × 8 runs are kept in the case's `work/runs_nonuniform/`"],
        ],
        "tables": [
            {"title": "Discrete ordinates (of-optical-radiation)",
             "columns": ["run", "directions", "pixels", "ray scheme", "walls ρ", "conv. / max iter", "sweeps", "ranks", "OOR commit", "wall s"],
             "rows": dom_rows},
            {"title": "aquaflux and the exact field",
             "columns": ["run", "lamp", "walls", "library", "aquaflux commit", "wall s"],
             "rows": aq_rows},
        ],
        "notes": [f"† {', '.join(sorted(SHARED_ROOM_RUNS))}: shared the machine with the Sozzi renders for its first few minutes, so its time may be a few minutes long."],
    })


# ------------------------------------------------------ Sozzi, slide 10 ---
def sozzi_slide10():
    case = "sozzi_slide10"
    _clean(case)
    prov = keep(case, SOZZI / "provenance_iuva.json")
    # The flow's own dictionaries: no committed script writes that case (see the provenance).
    for rel in ("system/fvSolution", "system/fvSchemes", "system/controlDict", "constant/momentumTransport",
                "constant/physicalProperties", "0/U", "0/p", "0/k", "0/omega", "0/nut"):
        keep(case, SOZZI_FLOW / rel, "flow_" + rel.replace("/", "_"))
    keep(case, SOZZI_FLOW / "log.foamRun.to900", "flow_log.foamRun.to900")
    keep(case, SOZZI_FLOW / "log.foamRun", "flow_log.foamRun.900to2059")
    arc, dom = SOZZI / "case" / "uv_arc_lgvB", SOZZI / "case" / "slide10_dom6_lu_B"
    keep(case, dom / "system" / "postProcess.dict", "tracker_postProcess.dict")
    keep(case, SOZZI / "case" / "uv_dom6_lu" / "constant" / "opticalRadiationProperties", "dom72_opticalRadiationProperties")
    keep(case, SOZZI / "case" / "uv_dom6_lu" / "system" / "fvSchemes", "dom72_fvSchemes")
    keep(case, SOZZI / "case" / "uv_dom6_lu" / "log.opticalRadiationFoam", "dom72_log.opticalRadiationFoam")
    rows = []
    row = _tracker_row(arc, "line source on the lamp arc (setFluenceRate -xStart 0 -xEnd 0.80)", ("—", "—", "—"))
    keep(case, next((arc / "postProcessing" / "radiationDose").glob("*/summary.dat")), "line_source_summary.dat")
    rows.append(row)
    s72 = dom_settings(SOZZI / "case" / "uv_dom6_lu")
    row = _tracker_row(dom, "DO, its own patch values", (f"{s72['directions']} ({s72['bins']})", s72["pixels"], s72["scheme"]))
    keep(case, next((dom / "postProcessing" / "radiationDose").glob("*/summary.dat")), "dom72_summary.dat")
    rows.append(row)
    # Slide 10 shows 288 directions: the swap set's DO 288 field as the solver wrote it.
    dom288 = SOZZI / "swap" / "dom288_native"
    s288 = dom_settings(SOZZI / "case" / "uv_dom12_lu")
    keep(case, SOZZI / "case" / "uv_dom12_lu" / "constant" / "opticalRadiationProperties", "dom288_opticalRadiationProperties")
    rows.append(_tracker_row(dom288, "DO, its own patch values (shown on slide 10)",
                             (f"{s288['directions']} ({s288['bins']})", s288["pixels"], s288["scheme"])))
    keep(case, next((dom288 / "postProcessing" / "radiationDose").glob("*/summary.dat")), "dom288_summary.dat")
    # Fluent's DO G, put into the swap set's copy of this flow by of-mesh-converter transfer.
    for folder, divisions, n_dirs, shown in (("fluent33", "3 × 3", 72, ""), ("fluent66", "6 × 6", 288, " (shown on slide 10)")):
        fluent = SOZZI / "swap" / folder
        rows.append(_tracker_row(fluent, f"Fluent DO, zeroGradient patch values (G copied cell for cell from its CGNS export){shown}",
                                 (f"{n_dirs} ({divisions} per octant)", "not recorded", "not recorded")))
        keep(case, next((fluent / "postProcessing" / "radiationDose").glob("*/summary.dat")), f"fluent{n_dirs}_summary.dat")
        keep(case, fluent / "transfer_report.txt", f"fluent{n_dirs}_transfer_report.txt")
        keep(case, fluent / "README.md", f"fluent{n_dirs}_README.md")
    lamp = patch_type(SOZZI / "case" / "uv_dom6_lu" / "2059" / "I", "lamp0_wall")
    reports = [SOZZI / "swap" / f / "transfer_report.txt" for f in ("fluent33", "fluent66")]
    matched = " and ".join(_report_value(r, "cells matched") for r in reports)
    distance = max(float(_report_value(r, "max distance").split()[0]) for r in reports)
    # dom288_native's cells are the swap set's dom288 field's: only the patch values differ.
    negative = json.loads((SOZZI / "swap" / "summary.json").read_text())["fields_compared"]["negative_cell_fraction"]["dom288"]
    write(case, {
        "title": "Sozzi & Taghipour reactor, uvmesh set (slides 2, 3, 9, 10)",
        "common": [
            ["Mesh", f"uvmesh (OOR `276d992`), the deck's `data/uvmesh/mesh.py`: {prov['mesh']['cells']:,} cells, max non-orthogonality {prov['mesh']['max_non_orthogonality_deg']}°; {prov['mesh']['first_cell'].replace(' um ', ' µm ')}"],
            ["Flow", f"k-ω SST, {prov['flow']['solver']}; {prov['flow']['inlet']}; {prov['flow']['stopped']}; {prov['flow']['legs']}; OpenFOAM {prov['flow']['openfoam_build']}"],
            ["Flow case", "dictionaries from OOR `tutorials/uvReactorSozzi2006` (`659ec4a`) with SST, set up in an unmerged aquaflux branch; no committed script writes the case, so its dictionaries and log are copied into `data/records/raw/sozzi_slide10/flow_*`"],
            ["Lamp and water", f"{lamp} on `lamp0_wall` and `lamp0_tip_B`, M = 696.42 W/m² (35 W over 0.80 m); absorption 35.67 /m; every other wall black"],
            ["DO and setFluenceRate", f"OOR `659ec4a`, 8 MPI ranks, convergence 1e-5 ({sweeps(SOZZI / 'case' / 'uv_dom6_lu')} sweeps at 72 directions, {sweeps(SOZZI / 'case' / 'uv_dom12_lu')} at 288); uniform angular grids, nPhi = nTheta, every bin 30° or 15° square (Fluent: 3 × 3 and 6 × 6 θ × φ divisions per octant)"],
            ["Tracker", "radiationDose at OOR `b23582b` (PR #90: the `langevin` dispersion model, one integrator with a continuous step, on `main` with #88 and #89); " + prov["tracker"]["settings"].replace(" um ", " µm ") + "; one OpenMP thread"],
            ["Fluent DO", "solved in ANSYS Fluent on this mesh with 3 × 3 and 6 × 6 θ × φ divisions per octant (72 and 288 directions); the exports (`sozzi_fluent_3_3.cgns`, `sozzi_fluent_6_6.cgns`, CGNS 4.3) carry `Incident_Radiation` only and do not record the Fluent version, pixelation or scheme. "
             f"of-mesh-converter (github.com/DeGrootResearchGroup/of-mesh-converter) `b654443` (PR #2, open): `transfer` matched their cells by centre ({matched}, largest distance {distance:.2g} m) and wrote G into `swap/fluent33/2059` and `swap/fluent66/2059`, copies of the slide 15 swap set's flow; traced at 2059 like the swap set"],
        ],
        "tables": [{"title": "Fluence rate fields traced (same flow, same tracker settings, same particles)",
                    "columns": ["G", "directions", "pixels", "ray scheme", "escaped / stuck / timed out", "mean dose", "LR k=0.1"],
                    "rows": rows}],
        "notes": [f"Slide 10 shows 288 directions: the DO run with linearUpwind rays and its own patch values, whose G is below zero in {100 * negative:.1f} % of cells (the tracker counts them as zero), and Fluent's 6 × 6. At 72 directions both give a mean dose about 0.3 mJ/cm² and a log reduction about 0.016 lower.",
                  "Mean dose and log reduction are over the escaped particles."],
    })


# ----------------------------------------------------- Sozzi, slide 15 ---
def sozzi_swap():
    case = "sozzi_swap"
    _clean(case)
    swap = SOZZI / "swap"
    summ = keep(case, swap / "summary.json")
    gath = keep(case, swap / "gather.json")
    keep(case, swap / "write.json")
    s288 = dom_settings(SOZZI / "case" / "uv_dom12_lu")
    keep(case, SOZZI / "case" / "uv_dom12_lu" / "constant" / "opticalRadiationProperties", "dom288_opticalRadiationProperties")
    keep(case, SOZZI / "case" / "uv_dom12_lu" / "log.opticalRadiationFoam", "dom288_log.opticalRadiationFoam")
    s72 = dom_settings(SOZZI / "case" / "uv_dom6_lu")
    labels = {"aquaflux": ("—", "—", "—", "zeroGradient"),
              "dom72": (f"{s72['directions']} ({s72['bins']})", s72["pixels"], s72["scheme"], "zeroGradient"),
              "dom288": (f"{s288['directions']} ({s288['bins']})", s288["pixels"], s288["scheme"], "zeroGradient"),
              "dom288_native": (f"{s288['directions']} ({s288['bins']})", s288["pixels"], s288["scheme"], "the solver's own")}
    rows = []
    for name, (dirs, pix, scheme, patches) in labels.items():
        r = summ["runs"][name]
        keep(case, next((swap / name / "postProcessing" / "radiationDose").glob("*/summary.dat")), f"{name}_summary.dat")
        rows.append([name, dirs, pix, scheme, patches, f"{r['mean']:.1f}", f"{r['log_reduction']['0.1']:.3f}", f"{r['log_reduction']['0.5']:.3f}"])
    # Fluent's DO fields, traced in copies of the swap flow (scripts/export_fluent_swap.py).
    fluent = json.loads((DATA / "sozzi_fluent_swap.json").read_text())
    for name, r in fluent["runs"].items():
        folder = r["case"].split("/")[-1]
        keep(case, next((swap / folder / "postProcessing" / "radiationDose").glob("*/summary.dat")), f"{name}_summary.dat")
        keep(case, swap / folder / "transfer_report.txt", f"{name}_transfer_report.txt")
        rows.append([name, f"{name.removeprefix('fluent')} ({r['divisions_per_octant']} per octant)", "not recorded",
                     "not recorded", "zeroGradient", f"{r['mean']:.1f}", f"{r['log_reduction']['0.1']:.3f}",
                     f"{r['log_reduction']['0.5']:.3f}"])
    write(case, {
        "title": "Sozzi & Taghipour reactor, swap set on the uvmesh (slide 15)",
        "common": [
            ["Mesh, flow, tracker", "as the slide 10 set: uvmesh, k-ω SST at iteration 2059, OOR `b23582b` `langevin`, seed 42, one thread, so every run follows the same particles"],
            ["aquaflux G", f"aquaflux `validation/sozzi_radiation/uvmesh_swap.py`: the mesh's own lamp patches ({gath['patch_triangles']:,} triangles) coarsened to {gath['lamp_facets']:,} facets ({gath['lamp_edge_m'] * 1e3:g} mm edge, {gath['lamp_chord_m'] * 1e3:g} mm chord, {gath['coarsened_power_W']:.3f} W); exact visibility through the pipe openings; jax {gath['jax']}, gathered in {gath['gather_seconds']:.0f} s; aquaflux `2ba97418` (PR #598) for the gather, `2f243441` (PR #600, open) for the write and compare stages"],
            ["DO", f"OOR `659ec4a`, 8 MPI ranks, convergence 1e-5 ({sweeps(SOZZI / 'case' / 'uv_dom6_lu')} and {sweeps(SOZZI / 'case' / 'uv_dom12_lu')} sweeps); uniform angular grids, nPhi = nTheta (Fluent: 3 × 3 and 6 × 6 θ × φ divisions per octant)"],
            ["Patch values", "zeroGradient on every ordinary patch for the three compared fields and the Fluent fields (the non-conformal couplings keep their constraint types); `dom288_native` keeps the DO file as written"],
            ["Fluent G", "ANSYS Fluent DO on this mesh, 3 × 3 and 6 × 6 θ × φ divisions per octant, exported to CGNS (`Incident_Radiation` only; the Fluent version, pixelation and scheme are not recorded); of-mesh-converter `b654443` (PR #2, open) `transfer` copied G cell for cell into `swap/fluent33` and `swap/fluent66`; traced like the other runs, all 9,987 particles escaping in 127,033 outer steps as in every run"],
        ],
        "tables": [{"title": "Fluence rate fields traced",
                    "columns": ["G", "directions", "pixels", "ray scheme", "patch values", "mean dose", "LR k=0.1", "LR k=0.5"],
                    "rows": rows}],
        "notes": [f"{summ['escaped']:,} of {summ['particles']:,} particles escaped, the same ones in every run (checked by the harness).",
                  "Volume-weighted mean G over the reactor: " + ", ".join(
                      f"{n} {v:.2f}" for n, v in {**summ["fields_compared"]["volume_mean"]["all"], **fluent["volume_mean_all"]}.items()) + " W/m².",
                  "DO over aquaflux, cell by cell where aquaflux's G exceeds 1e-3 of its peak, percentiles 10 to 90: " + "; ".join(
                      f"{n} {r['p10']:.3f} to {r['p90']:.3f}" for n, r in summ["fields_compared"]["ratio_over_lit_cells"].items()) + "."],
    })


# ------------------------------------------------ refractive interface ---
def refractive():
    case = "refractive_interface"
    _clean(case)
    prov = keep(case, REFRACTIVE / "provenance.json")
    rows = []
    for region in ("mediumA", "mediumB"):
        props = REFRACTIVE / "constant" / region / "opticalRadiationProperties"
        if not props.exists():
            continue
        rows.append([
            region,
            f"{entry(props, 'nPhi')}×{entry(props, 'nTheta')}",
            f"{entry(props, 'nPixelPhi')}×{entry(props, 'nPixelTheta')}",
            (entry(REFRACTIVE / "system" / region / "fvSchemes", "div(Ji,Ii_h)") or "").replace("bounded Gauss ", ""),
            f"{entry(props, 'convergence')} / {entry(props, 'maxIter')}",
        ])
    write(case, {
        "title": "Refractive interface (slide 8)",
        "common": [
            ["Case", "of-optical-radiation `tutorials/refractiveInterface2D`, extracted from the commit with `git archive`"],
            ["Code", f"OOR {short(prov['of_optical_radiation_commit'])}; OpenFOAM {prov['openfoam_build']}, in a Docker image built from of-optical-radiation's `Dockerfile`"],
            ["Run", prov["run"]],
            ["Result", f"G_A = {prov['result_W_per_m2']['G_A']}, G_B = {prov['result_W_per_m2']['G_B']} W/m²"],
        ],
        "tables": [{"title": "Radiation settings per region",
                    "columns": ["region", "nPhi×nTheta", "pixels", "ray scheme", "conv. / max iter"],
                    "rows": rows}],
        "notes": [],
    })


# ------------------------------------------- Sozzi, prototype reactor ---
def sozzi_prototype():
    case = "sozzi_prototype"
    _clean(case)
    src = DATA / "sozzi_mean_dose.json"
    keep(case, src)
    proto = json.loads(src.read_text())["prototype"]
    write(case, {
        "title": "Sozzi & Taghipour prototype reactor (slide 10)",
        "common": [
            ["Source", "Sozzi & Taghipour (2006), Table 1 and Fig. 1c; the prototype's measured MS2 log reduction (1.51 at 25 GPM) is read off their Fig. 9"],
            ["Shared", "35 W UV output, 70 % UVT (absorption 0.357 /cm), 25 US gal/min"],
            ["Mean dose integral", f"∫G dV / Q with their multiple-point-source lamp model (200 sources, arc centred in the body): {proto['simulated_integral']:.1f} mJ/cm² for the simulated reactor, {proto['integral']:.1f} for the prototype, by `scripts/sozzi_mean_dose.py` (lamp holder and outlet reduction ring not included)"],
        ],
        "tables": [{"title": "Geometry (their Table 1)",
                    "columns": ["", "Simulated (L-shape)", "Industrial prototype"],
                    "rows": [["Reactor body diameter", "8.9 cm", "8.6 cm"],
                             ["Reactor body length", "88.9 cm", "101 cm"],
                             ["Lamp diameter", "2 cm", "2.26 cm"],
                             ["Lamp arc length", "80 cm", "88 cm"],
                             ["UV output", "35 W", "35 W"],
                             ["Inlet/outlet diameter", "1.91 cm", "2.24 cm"],
                             ["Inlet/outlet length", "85 cm", "100 cm"],
                             ["Other", "—", "lamp holder, outlet reduction ring"],
                             ["Mean dose integral [mJ/cm²]", f"{proto['simulated_integral']:.1f}", f"{proto['integral']:.1f}"]]}],
        "notes": [],
    })


COLLECTORS = (room, sozzi_slide10, sozzi_prototype, sozzi_swap, refractive)


if __name__ == "__main__":
    # One or more collector names to collect only those; none collects every record.
    chosen = sys.argv[1:]
    for f in COLLECTORS:
        if not chosen or f.__name__ in chosen:
            f()
