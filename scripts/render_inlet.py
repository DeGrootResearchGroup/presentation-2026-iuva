#!/usr/bin/env python3
"""Dose-tracker slide image: seeded particles on the Sozzi inlet face (needs pyvista and Pillow).

    python3 scripts/render_inlet.py <case> [--time 2060]

The case is the one render_sozzi.py renders (the slide 10 DO run, traced with writeVtk on, time
2060). Reads the inlet patch through the case's out.foam and the first point of every track in
postProcessing/radiationDose/<time>/trajectories.vtk; the seed points do not depend on G.
Writes figures/renders/inlet-seeding.png (5:4).
"""

import argparse
from pathlib import Path

import numpy as np
import pyvista as pv
from common import THIS
from common import RENDERS as OUT
from PIL import Image, ImageChops

W, H = 1560, 1260


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("case", type=Path, help="the traced DO case (see the module docstring)")
    ap.add_argument("--time", type=float, default=2060, help="its time directory (default 2060)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    reader = pv.OpenFOAMReader(str(a.case / "out.foam"))
    reader.set_active_time_value(a.time)
    reader.enable_all_patch_arrays()
    blocks = reader.read()
    bnd = blocks["boundary"]
    inlet = bnd["inlet"].extract_surface(algorithm="dataset_surface")

    tr = pv.read(a.case / "postProcessing" / "radiationDose" / f"{a.time:g}" / "trajectories.vtk")
    lines = tr.lines
    starts, i = [], 0
    while i < len(lines):
        n = lines[i]
        starts.append(lines[i + 1])
        i += n + 1
    seeds = pv.PolyData(tr.points[starts])
    print(f"inlet faces {inlet.n_cells}, seeds {seeds.n_points}, x range {seeds.bounds[:2]}")

    x_in = float(np.mean(inlet.points[:, 0]))

    p = pv.Plotter(off_screen=True, window_size=(W, H))
    p.set_background("white")
    p.enable_anti_aliasing("ssaa")
    p.add_mesh(inlet, color="#efe9f7", show_edges=True, edge_color="#8a8894", line_width=1.2, lighting=False)
    p.add_mesh(
        seeds, color=THIS, point_size=2.6, render_points_as_spheres=True, lighting=False
    )
    c = np.array([x_in, 0.0, 0.0])
    # View the face from outside the pipe with a slight tilt
    d = np.array([1.0, 0.18, 0.12])
    p.camera_position = [tuple(c + d * 1.0), tuple(c), (0, 0, 1)]
    p.camera.parallel_projection = True
    p.camera.parallel_scale = 0.05
    tmp = OUT / "inlet-seeding.png"
    p.screenshot(tmp)
    p.close()

    im = Image.open(tmp).convert("RGB")
    bbox = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    im = im.crop(bbox)
    w, h = im.size
    pad = 0.05
    cw = max(w * (1 + 2 * pad), h * (1 + 2 * pad) * 5 / 4)
    canvas = Image.new("RGB", (round(cw), round(cw * 4 / 5)), "white")
    canvas.paste(im, ((canvas.width - w) // 2, (canvas.height - h) // 2))
    canvas.resize((1040, 832), Image.LANCZOS).save(tmp)


if __name__ == "__main__":
    main()
