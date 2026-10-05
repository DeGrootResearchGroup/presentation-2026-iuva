#!/usr/bin/env python3
"""uvmesh slide images from a mesh built by uvmesh (needs pyvista and Pillow).

    python3 scripts/render_uvmesh.py /path/to/uvmesh/case

The case is the one `data/uvmesh/mesh.py` builds (`python3 mesh.py`, then `./Allrun.mesh`), with
a `<case>.foam` file beside `constant/` (any name ending in .foam). Writes, all 900x900:

- figures/renders/uvmesh-pipe.png: the inlet pipe's O-grid, seen on its open end;
- figures/renders/uvmesh-tip.png: the sleeve surface at the lamp's hemispherical tip, the
  cubed-sphere cap joined to the cylinder's O-grid;
- figures/renders/uvmesh-slice.png: the plane y = 0 around the lamp tip, cutting the structured
  layer on the lamp and the polyhedral bulk around it.
"""

import argparse
from pathlib import Path

import numpy as np
import pyvista as pv
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "renders"
W, H = 900, 900  # output size of every image (square, three side by side on the slide)
SCALE = 2  # render at twice the output size, then downsample
FILL = "#efe9f7"  # light purple, as the inlet-seeding image
EDGE = "#1e1d24"  # near-black, so the lines survive projection
STRUCT = "#d9cdee"  # structured blocks in the slice
POLY = "#f6f4f0"  # polyhedral bulk in the slice

# The lamp runs along x from 0 to 0.8 m with its hemispherical tip at x = 0.8 m; the sleeve radius
# is 10 mm. The inlet pipe runs along x from 0.889 m (the body) to 1.739 m (its open end).
TIP_X = 0.80  # centre of the tip hemisphere (the sleeve ends at x = 0.81 m)
SLEEVE_R = 0.010
SLICE_VIEW = ((0.768, 0.838), (-0.035, 0.035))  # axial, transverse extent of the slice image (m)
SLICE_TURN_DEG = 360 / 64 / 2  # half of one of the lamp O-grid's 64 azimuthal cells


def plotter():
    p = pv.Plotter(off_screen=True, window_size=(W * SCALE, H * SCALE))
    p.set_background("white")
    p.enable_anti_aliasing("ssaa")
    return p


def save(p, name):
    path = OUT / name
    p.screenshot(str(path))
    p.close()
    im = Image.open(path).convert("RGB")
    bbox = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    im = im.crop(bbox)
    w, h = im.size
    pad = 1.04
    cw = max(w * pad, h * pad * W / H)
    canvas = Image.new("RGB", (round(cw), round(cw * H / W)), "white")
    canvas.paste(im, ((canvas.width - w) // 2, (canvas.height - h) // 2))
    canvas.resize((W, H), Image.LANCZOS).save(path)
    print(f"wrote {path}")


def read(case, internal):
    foam = next(case.glob("*.foam"))
    reader = pv.OpenFOAMReader(str(foam))
    reader.enable_all_patch_arrays()
    if not internal:
        reader.disable_patch_array("internalMesh")
    return reader.read()


def surface(blocks, patch):
    return blocks["boundary"][patch].extract_surface(algorithm="dataset_surface")


def pipe_image(blocks):
    inlet = surface(blocks, "inlet")
    c = np.array(inlet.center)
    p = plotter()
    p.add_mesh(inlet, color=FILL, show_edges=True, edge_color=EDGE, line_width=3.0, lighting=False)
    p.camera_position = [tuple(c + np.array([1.0, 0.0, 0.0])), tuple(c), (0, 0, 1)]
    p.camera.parallel_projection = True
    p.reset_camera()
    save(p, "uvmesh-pipe.png")


def tip_image(blocks):
    tip = surface(blocks, "lamp0_tip_B")
    wall = surface(blocks, "lamp0_wall").clip(normal="-x", origin=(TIP_X - 0.02, 0, 0))
    print(f"tip faces {tip.n_cells}, sleeve faces near the tip {wall.n_cells}")
    p = plotter()
    shade = dict(show_edges=True, edge_color=EDGE, line_width=2.4, ambient=0.35, diffuse=0.7)
    p.add_mesh(tip, color=STRUCT, **shade)
    p.add_mesh(wall, color="#e4e1e8", **shade)
    c = np.array([TIP_X, 0.0, 0.0])
    d = np.array([1.0, -0.65, 0.5])
    p.camera_position = [tuple(c + 0.2 * d / np.linalg.norm(d)), tuple(c), (0, 0, 1)]
    p.camera.parallel_projection = True
    p.reset_camera()
    save(p, "uvmesh-tip.png")


def slice_image(blocks):
    mesh = blocks["internalMesh"]
    (x0, x1), (z0, z1) = SLICE_VIEW
    box = mesh.extract_cells(
        np.flatnonzero(
            _cells_in_box(mesh, (x0 - 0.01, x1 + 0.01), (-0.04, 0.04), (z0 - 0.01, z1 + 0.01))
        )
    )
    # Structured blocks are hexahedra; the dual of the tetrahedral bulk is polyhedra.
    box.cell_data["structured"] = (box.celltypes == pv.CellType.HEXAHEDRON).astype(float)
    # A plane through the lamp axis at y = 0 lies on a layer of the O-grid's radial faces, which
    # leaves slivers in the cut; turning it half an azimuthal cell about the axis cuts mid-cell.
    a = np.radians(SLICE_TURN_DEG)
    up = np.array([0.0, np.sin(a), np.cos(a)])
    normal = np.array([0.0, np.cos(a), -np.sin(a)])
    cut = box.slice(normal=normal, origin=(0, 0, 0))
    print(f"slice polygons {cut.n_cells}, structured {int(cut.cell_data['structured'].sum())}")
    p = plotter()
    p.add_mesh(
        cut,
        scalars="structured",
        cmap=[POLY, STRUCT],
        clim=(0, 1),
        show_scalar_bar=False,
        show_edges=True,
        edge_color=EDGE,
        line_width=2.6,
        lighting=False,
    )
    p.camera.parallel_projection = True
    focal = np.array([(x0 + x1) / 2, 0.0, 0.0]) + up * (z0 + z1) / 2
    cam = p.camera
    cam.focal_point = focal
    cam.position = focal - normal
    cam.up = tuple(up)
    cam.parallel_scale = max((z1 - z0) / 2, (x1 - x0) / 2 * H / W)
    save(p, "uvmesh-slice.png")


def _cells_in_box(mesh, xr, yr, zr):
    c = mesh.cell_centers().points
    return (
        (c[:, 0] > xr[0]) & (c[:, 0] < xr[1])
        & (c[:, 1] > yr[0]) & (c[:, 1] < yr[1])
        & (c[:, 2] > zr[0]) & (c[:, 2] < zr[1])
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case", type=Path)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    blocks = read(a.case, internal=False)
    pipe_image(blocks)
    tip_image(blocks)
    slice_image(read(a.case, internal=True))


if __name__ == "__main__":
    main()
