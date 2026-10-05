#!/usr/bin/env python3
"""Renders of the dummy room (needs pyvista, matplotlib; reads data/dummy_room.npz).

    python3 scripts/render_dummy_room.py

Writes figures/dummy-room-E.png (irradiance on the four bodies) and figures/dummy-room-G.png
(fluence rate on two vertical planes through the fixtures, bodies in grey).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from common import INK
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures"
NAMES = ["adult_male", "adult_female", "child", "elder_female"]
LAMP = "#2a78d6"
GREY = "#d9d6de"
SLICE_OPACITY = 0.55  # the slices let the scene behind show through
CAMERA = dict(position=(7.2, -8.0, 5.2), focal_point=(0.0, 0.0, 1.35), viewup=(0, 0, 1))


def polydata(v, f):
    return pv.PolyData(v, np.hstack([np.full((len(f), 1), 3), f]).ravel())


def room_frame(p, lo, hi):
    box = pv.Box(bounds=(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    p.add_mesh(box, style="wireframe", color="#8a8894", line_width=1.5)
    floor = pv.Plane(center=((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0), i_size=hi[0] - lo[0],
                     j_size=hi[1] - lo[1])
    p.add_mesh(floor, color="#f1eff4", lighting=False)


def lamps(p, xy, z):
    for x, y in xy:
        p.add_mesh(pv.Box(bounds=(x - 0.1, x + 0.1, y - 0.07, y + 0.07, z - 0.03, z)), color=LAMP)


def scene():
    p = pv.Plotter(off_screen=True, window_size=(2600, 2200))
    p.set_background("white")
    p.enable_anti_aliasing("ssaa")
    return p


def add_bar(path, clim, title):
    """Append a log colour bar in a white strip under the render."""
    im = np.asarray(Image.open(path).convert("RGB"))
    h, w = im.shape[:2]
    # px at 200 dpi: the bar, its tick labels and its title, sized to the font rather than the image.
    # The renders are drawn about 0.22 of full size on the slide, so 24-26 pt reads as 15-16 px.
    strip = 360
    fig = plt.figure(figsize=(w / 200, (h + strip) / 200), dpi=200)
    ax = fig.add_axes([0, strip / (h + strip), 1, h / (h + strip)])
    ax.imshow(im)
    ax.axis("off")
    cax = fig.add_axes([0.2, 200 / (h + strip), 0.6, 60 / (h + strip)])
    cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=matplotlib.colors.LogNorm(*clim), cmap="inferno"),
                      cax=cax, orientation="horizontal")
    cb.set_label(title, fontsize=26, color=INK, labelpad=4)
    cb.ax.tick_params(labelsize=24, colors=INK, length=3)
    cb.outline.set_edgecolor("#8a8894")
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)


def trim(path, pad=12):
    """Crop the white margin off a render."""
    im = Image.open(path).convert("RGB")
    box = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    box = (max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, im.width), min(box[3] + pad, im.height))
    im.crop(box).save(path)


def main():
    d = np.load(ROOT / "data" / "dummy_room.npz")
    lo, hi, xy = d["room_low"], d["room_high"], d["lamp_xy"]

    # E on the bodies, log colour scale in mW/m^2
    allE = np.concatenate([d[f"{n}_E"] for n in NAMES]) * 1e3
    clim = (0.5, float(np.percentile(allE, 99.9)))
    p = scene()
    room_frame(p, lo, hi)
    lamps(p, xy, hi[2])
    for n in NAMES:
        m = polydata(d[f"{n}_vertices"], d[f"{n}_faces"])
        m.cell_data["E"] = np.maximum(d[f"{n}_E"] * 1e3, clim[0])
        p.add_mesh(m, scalars="E", cmap="inferno", clim=clim, log_scale=True, smooth_shading=False,
                   show_scalar_bar=False)
    p.camera_position = [CAMERA["position"], CAMERA["focal_point"], CAMERA["viewup"]]
    p.reset_camera()  # fit every actor, so nothing is clipped; trim() then removes the spare margin
    p.screenshot(OUT / "dummy-room-E.png")
    p.close()
    trim(OUT / "dummy-room-E.png")
    add_bar(OUT / "dummy-room-E.png", clim, "Irradiance E on the body (mW/m²)")
    print("E colour range mW/m2", clim)

    # G on the two vertical planes that hold the fixtures (y = -1 and 1), bodies grey
    ax, ay, az = d["grid_axes_x"], d["grid_axes_y"], d["grid_axes_z"]
    G = d["G"] * 1e3  # mW/m^2; grid points inside a body are shadowed, and the grey body hides them
    gpos = G[(G > 0) & ~d["inside"]]
    glim = (float(np.percentile(gpos, 2)), float(np.percentile(gpos, 99.9)))
    grid = pv.ImageData(dimensions=(len(ax), len(ay), len(az)), spacing=(ax[1] - ax[0],) * 3,
                        origin=(ax[0], ay[0], az[0]))
    grid.point_data["G"] = G.flatten(order="F")
    p = scene()
    room_frame(p, lo, hi)
    lamps(p, xy, hi[2])
    for y in sorted({round(float(v), 3) for v in xy[:, 1]}):
        p.add_mesh(grid.slice(normal="y", origin=(0, y, 0)), scalars="G", cmap="inferno", clim=glim,
                   log_scale=True, opacity=SLICE_OPACITY, show_scalar_bar=False)
    for n in NAMES:
        p.add_mesh(polydata(d[f"{n}_vertices"], d[f"{n}_faces"]), color=GREY, smooth_shading=True)
    p.camera_position = [CAMERA["position"], CAMERA["focal_point"], CAMERA["viewup"]]
    p.reset_camera()  # fit every actor, so nothing is clipped; trim() then removes the spare margin
    p.screenshot(OUT / "dummy-room-G.png")
    p.close()
    trim(OUT / "dummy-room-G.png")
    add_bar(OUT / "dummy-room-G.png", glim, "Fluence rate G in the air (mW/m²)")
    print("G colour range mW/m2", glim)


if __name__ == "__main__":
    main()
