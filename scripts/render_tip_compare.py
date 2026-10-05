#!/usr/bin/env python3
"""G around the Sozzi lamp's tip from the slide 15 fields, with each one's time and log reduction.

    python3 scripts/render_tip_compare.py [/path/to/sozzi/run]

Needs pyvista. Two columns. Left, the swap set (swap/dom72, swap/dom288 and swap/aquaflux under
IUVA_SOZZI or the argument), the fields slide 15's chart is traced through on the uvmesh mesh.
Right, aquaflux gathered on Cartesian background grids of 6, 4 and 3 mm and taken to the cells as
log G fitted to the sleeve's own value (grid/h<mm>/logG_surface, from aquaflux's
validation/sozzi_radiation/background_grid.py). Each is cut on the plane y = 0 around the lamp's
hemispherical tip (the sleeve ends at x = 0.81 m; the chamber at x = 0.889 m, where the inlet pipe
opens on the axis) and coloured by log G on one shared scale, cell by cell with no smoothing, so
the discrete-ordinates rays show as they are in the field.

The timings are data/sozzi_tip_timing.json, written by hand from the uncontended runs described
there; the log reductions at k = 0.1 cm^2/mJ are data/sozzi_dose_swap.json's and
data/sozzi_grid.json's. Writes figures/renders/tip-G-<name>.png and figures/sozzi-tip-compare.png.
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from common import AQUA, DATA, INK, SOZZI, THIS
from common import FIGURES as OUT
from PIL import Image

VIEW = ((0.745, 0.905), (-0.0445, 0.0445))  # x, z extent of the cut (m)
#: (name, case under the run directory, label), by column.
COLUMNS = (
    (("dom72", "swap/dom72", "DO, 72 directions"),
     ("dom288", "swap/dom288", "DO, 288 directions"),
     ("aquaflux", "swap/aquaflux", "aquaflux, every cell")),
    (("grid_h6mm", "grid/h6mm/logG_surface", "aquaflux, 6 mm grid"),
     ("grid_h4mm", "grid/h4mm/logG_surface", "aquaflux, 4 mm grid"),
     ("grid_h3mm", "grid/h3mm/logG_surface", "aquaflux, 3 mm grid")),
)
SOURCES = [source for column in COLUMNS for source in column]
K = "0.1"  # the inactivation rate constant whose log reduction is printed, cm^2/mJ
PX = 1400  # render width in pixels


def cut(run, case):
    """The plane y = 0 through the G of the case at ``case`` under the run directory ``run``,
    clipped to VIEW, as cell data."""
    reader = pv.OpenFOAMReader(str(run / case / "out.foam"))
    reader.set_active_time_value(2059)
    reader.cell_to_point_creation = False
    reader.disable_all_patch_arrays()
    reader.enable_patch_array("internalMesh")
    reader.disable_all_cell_arrays()
    reader.enable_cell_array("G")
    mesh = reader.read()["internalMesh"]
    (x0, x1), (z0, z1) = VIEW
    box = mesh.clip_box((x0 - 0.01, x1 + 0.01, -0.06, 0.06, z0 - 0.01, z1 + 0.01), invert=False)
    return box.slice(normal="y", origin=(0, 0, 0))


def render(slice_, path, clim):
    (x0, x1), (z0, z1) = VIEW
    h = round(PX * (z1 - z0) / (x1 - x0))
    p = pv.Plotter(off_screen=True, window_size=(PX, h))
    p.set_background("white")
    p.add_mesh(slice_, scalars="G", preference="cell", cmap="inferno", clim=clim, log_scale=True,
               show_scalar_bar=False, lighting=False)
    p.camera_position = "xz"
    p.camera.parallel_projection = True
    cam = p.camera
    d = np.array(cam.position) - np.array(cam.focal_point)
    focal = np.array([(x0 + x1) / 2, 0.0, (z0 + z1) / 2])
    cam.focal_point = focal
    cam.position = focal + d
    cam.parallel_scale = (z1 - z0) / 2
    p.screenshot(str(path))
    p.close()


def log_reductions():
    """Each source's log reduction at K."""
    swap = json.loads((DATA / "sozzi_dose_swap.json").read_text())["runs"]
    grid = json.loads((DATA / "sozzi_grid.json").read_text())["grids"]
    out = {name: swap[name]["log_reduction"][K] for name in ("dom72", "dom288", "aquaflux")}
    for label, g in grid.items():
        out[f"grid_{label}"] = g["variants"]["logG_surface"]["log_reduction"][K]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run", type=Path, nargs="?", default=SOZZI,
                    help="the Sozzi run directory (default: IUVA_SOZZI, see common.py)")
    run = ap.parse_args().run
    timing = json.loads((DATA / "sozzi_tip_timing.json").read_text())["runs"]
    lr = log_reductions()
    slices = {name: cut(run, case) for name, case, _ in SOURCES}
    ghi = float(np.percentile(slices["aquaflux"]["G"], 99.5))
    clim = (ghi * 1e-3, ghi)
    for name, _, _ in SOURCES:
        render(slices[name], OUT / "renders" / f"tip-G-{name}.png", clim)

    # Two columns of three rows, each image with its label, time and log reduction beside it; one
    # shared colour bar underneath.
    (x0, x1), (z0, z1) = VIEW
    fig_w, fig_h, row_h = 8.4, 2.75, 0.265
    img_w = row_h * fig_h * (x1 - x0) / (z1 - z0) / fig_w
    col_w = 0.5
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    for c, column in enumerate(COLUMNS):
        left = c * col_w
        for i, (name, _, label) in enumerate(column):
            bottom = 1 - (i + 1) * (row_h + 0.02)
            ax = fig.add_axes([left, bottom, img_w, row_h])
            ax.imshow(np.asarray(Image.open(OUT / "renders" / f"tip-G-{name}.png").convert("RGB")))
            ax.axis("off")
            t = timing[name]["seconds"]
            when = f"{t / 60:.1f} min" if t >= 120 else f"{t:.0f} s"
            x_text = left + img_w + 0.02
            colour = THIS if name.startswith("dom") else AQUA
            fig.text(x_text, bottom + 0.64 * row_h, label, fontsize=12.5, fontweight="bold",
                     color=colour, va="center")
            fig.text(x_text, bottom + 0.28 * row_h,
                     f"{when}, {timing[name]['cores']} cores · LR {lr[name]:.3f}",
                     fontsize=12.5, color=INK, va="center")
    norm = matplotlib.colors.LogNorm(*clim)
    cax = fig.add_axes([0.02, 0.085, img_w - 0.04, 0.03])
    cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap="inferno"), cax=cax,
                      orientation="horizontal")
    cb.ax.tick_params(labelsize=8, colors=INK, length=2, pad=1)
    cb.outline.set_edgecolor("#8a8894")
    fig.text(img_w + 0.02, 0.10, "G (W/m²)", fontsize=9, color=INK, va="center")
    fig.savefig(OUT / "sozzi-tip-compare.png", dpi=300, facecolor="white", bbox_inches="tight",
                pad_inches=0.03)
    plt.close(fig)
    print(f"wrote {OUT / 'sozzi-tip-compare.png'}; G scale {clim[0]:.3g} to {clim[1]:.3g} W/m^2")


if __name__ == "__main__":
    main()
