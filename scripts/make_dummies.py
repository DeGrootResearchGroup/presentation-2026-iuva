#!/usr/bin/env python3
"""Generate the room-simulation dummies with Anny, an Apache-2.0 parametric human model.

    pip install anny trimesh
    python3 scripts/make_dummies.py [outdir]

Writes one arms-down STL per person (metres, feet on z = 0, +z up, facing +y) plus a
summary of height and watertightness. Anny is parametric, not a scan.
"""
import math
import sys
from pathlib import Path

import anny
import torch
import trimesh

# phenotype values are 0..1; age 0.5 is a young adult
PEOPLE = {
    "adult_female": dict(gender=1.0, age=0.5, muscle=0.4, weight=0.45, height=0.5, proportions=0.5),
    "adult_male": dict(gender=0.0, age=0.5, muscle=0.6, weight=0.55, height=0.6, proportions=0.5),
    "elder_female": dict(gender=1.0, age=1.0, muscle=0.3, weight=0.5, height=0.3, proportions=0.5),
    "child": dict(gender=0.5, age=0.25, muscle=0.5, weight=0.5, height=0.5, proportions=0.5),
}


ARM_DEG = 35  # rotate the upper arms down from the T-pose


def arms_down(model, dtype):
    labels = list(model.bone_labels)
    pose = torch.eye(4, dtype=dtype).repeat(1, len(labels), 1, 1)
    for side, sign in (("L", 1), ("R", -1)):
        a = math.radians(sign * ARM_DEG)
        c, s = math.cos(a), math.sin(a)
        pose[0, labels.index(f"upperarm01.{side}"), :3, :3] = torch.tensor(
            [[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=dtype)
    return pose


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    model = anny.Anny()
    faces = model.get_triangular_faces().cpu().numpy()
    for name, ph in PEOPLE.items():
        with torch.no_grad():
            o = model(phenotype_kwargs={k: torch.tensor([v]) for k, v in ph.items()})
            o = model(pose_parameters=arms_down(model, o["vertices"].dtype),
                      phenotype_kwargs={k: torch.tensor([v]) for k, v in ph.items()})
        v = o["vertices"][0].cpu().numpy()
        m = trimesh.Trimesh(v, faces, process=False)
        m.apply_translation([-(m.bounds[0, 0] + m.bounds[1, 0]) / 2, -(m.bounds[0, 1] + m.bounds[1, 1]) / 2,
                             -m.bounds[0, 2]])
        print(f"{name}: height {m.extents[2]:.2f} m, width {m.extents[0]:.2f} m, watertight {m.is_watertight}")
        m.export(out / f"{name}.stl")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/dummies"))
