#!/usr/bin/env python3
"""Export the ray-effects room results from the aquaflux case into data/.

Run once, from the deck root, pointing at the case directory of the aquaflux
repository (validation/ray_effects_room, after its pipeline has run):

    python3 scripts/export_room_data.py /path/to/aquaflux/validation/ray_effects_room

Writes
  data/room_bunny.npz   floor triangles and irradiance, the vertical slice's
                        cells and fluence rate,
                        each for exact / DOM 72 / DOM 288 / aquaflux
  data/room_bunny.json  errors and wall times, with their configuration
  data/bunny_surface.npz  the bunny's triangles (for render_room.py)

make_plots.py reads only these files, so the deck needs neither aquaflux nor
the case's work/ directory to rebuild its figures.
"""

import json
import sys
from pathlib import Path

import numpy as np
from common import DATA

# The case's own modules are imported from the case directory, so it is read before anything else.
if len(sys.argv) != 2 or not (Path(sys.argv[1]) / "figures.py").exists():
    sys.exit("usage: python3 scripts/export_room_data.py <aquaflux>/validation/ray_effects_room\n"
             "(an aquaflux checkout's case directory, after its pipeline has run)")
CASE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(CASE))
import figures  # noqa: E402  (the case's own loaders)
import room  # noqa: E402

KEYS = {  # deck name: case name
    "exact": "reference",
    # Uniform angular grids, nPhi = nTheta (of-optical-radiation's nTheta spans the whole sphere, so
    # its bins are square only then): 72 directions with 3 x 3 Murthy-Mathur pixels, and 288 with
    # 1 x 1, since a 3 x 3 run at that size swaps on this machine (the 64- and 256-direction runs
    # gave the same floor error at 1 x 1 and 3 x 3 to four figures; 72 is checked below).
    "dom72": "bunny_nphi6_ntheta6_px3x3",
    "dom288": "bunny_nphi12_ntheta12",
    "aquaflux": "aquaflux",
}
TO_UW_CM2 = 1e6 / 1e4


def floor_arrays(case):
    floor = case["floor"]
    face = floor["triangle_face"]
    # The whole 4 x 4 m floor: DO's light lands in rings, most of them outside the central window.
    out = {"floor_tri": floor["triangles"][:, :, :2].astype(np.float32)}
    for key, name in KEYS.items():
        out[f"floor_{key}"] = (case["fields"][name]["E"][face] * TO_UW_CM2).astype(np.float32)
    return out


def full_floor_errors(case):
    """Area-weighted RMS difference from the exact field over the whole floor, and the share of
    the lamp's power each method puts on the floor, in the central 2 x 2 m, and as negative
    irradiance."""
    floor, fields = case["floor"], case["fields"]
    area, exact = floor["area"], fields["reference"]["E"]
    window = figures._window(floor)
    power = room.lamp_power()
    out = {}
    for key, name in KEYS.items():
        values = fields[name]["E"]
        out[key] = {
            "L2_of_peak": float(np.sqrt(np.sum(area * (values - exact) ** 2) / area.sum())
                                / exact.max()),
            "floor_share_of_lamp": float(np.sum(area * values) / power),
            "window_share_of_lamp": float(np.sum((area * values)[window]) / power),
            "negative_share_of_lamp": float(np.sum(area * np.minimum(values, 0.0)) / power),
            "max_of_exact_peak": float(values.max() / exact.max()),
        }
    return out


def slice_arrays(volume, name="vertical"):
    piece = volume["slices"][name]
    axis, _ = room.SLICES[name]
    across = [i for i in range(3) if i != axis]
    centre = volume["centre"][piece["cells"]][:, across]
    half = 0.5 * np.cbrt(volume["volume"][piece["cells"]])
    out = {
        f"{name}_centre": centre.astype(np.float32),
        f"{name}_half": half.astype(np.float32),
    }
    for key, case_name in KEYS.items():
        out[f"{name}_{key}"] = (piece["fields"][case_name]["G"] * TO_UW_CM2).astype(np.float32)
    return out


def main():
    case = figures.load("bunny")
    volume = figures.load_volume("bunny")
    arrays = {**floor_arrays(case), **slice_arrays(volume, "vertical")}
    np.savez_compressed(DATA / "room_bunny.npz", **arrays)

    errors = figures.errors(case)
    slice_errors = figures.volume_errors(volume)["slices"]["vertical"]
    work = CASE / "work"
    ours_floor = json.loads((work / "aquaflux" / "bunny.json").read_text())
    ours_volume = json.loads((work / "aquaflux" / "bunny_volume.json").read_text())
    reflecting = json.loads((work / "aquaflux" / "bunny_reflecting.json").read_text())
    stats = {
        "floor_full": full_floor_errors(case),
        "floor_L2_of_peak": {},
        "slice_L2_of_p99": {},
        "wall_s": {},
    }
    for key, name in KEYS.items():
        if key == "exact":
            continue
        stats["floor_L2_of_peak"][key] = errors[name]["L2_of_peak"]
        stats["slice_L2_of_p99"][key] = slice_errors[name]["L2_of_p99"]
        if key.startswith("dom"):
            record = case["fields"][name]["record"]
            stats["wall_s"][key] = record["wall_seconds"]
    # The 72-direction run at 1 x 1 pixels, to check the pixels change nothing here.
    one_by_one = case["fields"]["bunny_nphi6_ntheta6"]
    stats["wall_s"]["dom72_1x1"] = one_by_one["record"]["wall_seconds"]
    stats["floor_full_1x1"] = {"dom72_1x1": float(
        np.sqrt(np.sum(case["floor"]["area"]
                       * (one_by_one["E"] - case["fields"]["reference"]["E"]) ** 2)
                / case["floor"]["area"].sum()) / case["fields"]["reference"]["E"].max())}
    stats["wall_s_notes"] = {
        key: case["fields"][name]["record"].get("wall_seconds_note")
        for key, name in KEYS.items() if key.startswith("dom")
    }
    reflecting_dom = json.loads((work / "runs" / "bunny_reflecting_nphi6_ntheta6" / "record.json").read_text())
    stats["wall_s"]["dom72_reflecting"] = reflecting_dom["wall_seconds"]
    stats["reflecting_dom"] = {key: reflecting_dom[key] for key in (
        "wall_reflectance", "directions", "n_pixel_phi", "n_pixel_theta", "outer_iterations", "wall_seconds")}
    stats["wall_s"]["aquaflux_floor"] = ours_floor["total_s"]
    stats["wall_s"]["aquaflux_volume"] = ours_volume["total_s"]
    stats["wall_s"]["aquaflux_reflecting"] = reflecting["timing_s"]["total"]
    stats["cells"] = int(case["n_cells"])
    stats["configuration"] = {
        "room_m": [4.0, 4.0, 3.0],
        "wavelength_nm": 222,
        "lamp": "Ushio B1 (OSLUV IES), window 60 x 45 mm on the ceiling centre, 118.8 mW",
        "bunny_base_m": room.BUNNY_BASE,
        "walls": "black (reflectance 0)",
        "medium": "transparent air",
        "dom": "of-optical-radiation opticalRadiationFoam, 8 MPI ranks, converged to 1e-5",
        "aquaflux": "CPU, 11 cores, jax " + ours_floor["jax"],
        "aquaflux_lamp_facets": {"floor": ours_floor["refined_lamp_facets"],
                                 "volume": ours_volume["lamp_facets"]},
        "exact": "per-point ray-traced sum over 17,920 window samples (numpy + Embree)",
    }
    (DATA / "room_bunny.json").write_text(json.dumps(stats, indent=2) + "\n")

    from aquaflux.radiation import read_stl

    stl = CASE / "work" / "bunny" / "case" / "constant" / "triSurface" / "bunny.stl"
    np.savez_compressed(
        DATA / "bunny_surface.npz",
        triangles=np.asarray(read_stl(stl).vertices).astype(np.float32),
    )
    print("wrote data/room_bunny.npz, data/room_bunny.json, data/bunny_surface.npz")


if __name__ == "__main__":
    main()
