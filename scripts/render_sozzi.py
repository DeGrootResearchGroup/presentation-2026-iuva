#!/usr/bin/env python3
"""Pipeline images from a finished Sozzi run (needs pyvista, Pillow, matplotlib).

    python3 scripts/render_sozzi.py <case> [--time 2060]

The deck's images come from the slide 10 DO run (72 directions), traced with writeVtk on: the case
case/slide10_dom6_lu_B under the Sozzi run directory, time 2060.

The case needs the flow and G at the given time, readable by pyvista through a file named out.foam
beside constant/, and postProcessing/radiationDose/<time>/{trajectories.vtk,doseDistribution.csv}.
Writes figures/renders/pipe-{flow,G,tracks,dose,response}.png, all 1200x550.
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from common import INK, THIS, load_doses, log_reduction
from common import RENDERS as OUT
from PIL import Image, ImageChops

W, H = 1200, 550  # output size of every pipeline image
WIN_H = 900  # 4:3 render window; view_midplane is framed for it
N_TRACKS = 100
LEG_TRIM = 0.315  # fraction of the content height cut from the top (shortens the outlet leg)
CROP = ((-0.02, 0.95), (-0.055, 0.17))  # x, z extent of the view (m)


_CROP = {}


def fit_canvas(path, pad=0.04):
    """Crop to content, trim the top of the outlet leg, then place on a white W:H canvas.

    The content sits at the top of the canvas; the space below is left for the colour bar.
    """
    im = Image.open(path).convert("RGB")
    # The first image sets the crop; the rest reuse it so all three line up.
    if "bbox" not in _CROP:
        _CROP["bbox"] = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    x0, y0, x1, y1 = _CROP["bbox"]
    im = im.crop((x0, y0 + round(LEG_TRIM * (y1 - y0)), x1, y1))
    w, h = im.size
    cw = max(w * (1 + 2 * pad), h * (1 + 2 * pad) * W / H)
    ch = cw * H / W
    canvas = Image.new("RGB", (round(cw), round(ch)), "white")
    canvas.paste(im, ((canvas.width - w) // 2, round(0.005 * w)))
    canvas.resize((W, H), Image.LANCZOS).save(path)


def plotter():
    p = pv.Plotter(off_screen=True, window_size=(W * 2, WIN_H * 2))
    p.set_background("white")
    p.enable_anti_aliasing("ssaa")
    return p


def view_midplane(p):
    # Long axis (x) horizontal, outlet leg (z) up; look down -y at the y = 0 plane.
    p.camera_position = "xz"
    p.camera.parallel_projection = True
    p.reset_camera()
    # Crop to the lamp section plus a stub of each leg (the legs are ~1 m long and thin).
    (x0, x1), (z0, z1) = CROP
    cam = p.camera
    d = np.array(cam.position) - np.array(cam.focal_point)
    focal = np.array([(x0 + x1) / 2, 0.0, (z0 + z1) / 2])
    cam.focal_point = focal
    cam.position = focal + d
    cam.parallel_scale = max((z1 - z0) / 2, (x1 - x0) / 2 * 3 / 4)


def field_image(slice_, name, scalars, cmap, clim, log, wall):
    p = plotter()
    p.add_mesh(wall, color="#d9d6de", opacity=0.10, smooth_shading=True)
    p.add_mesh(
        slice_, scalars=scalars, cmap=cmap, clim=clim, log_scale=log,
        show_scalar_bar=False, lighting=False,
    )
    view_midplane(p)
    tmp = OUT / f"{name}.png"
    p.screenshot(tmp, transparent_background=False)
    p.close()
    fit_canvas(tmp)
    return tmp


def add_bar(path, cmap, clim, log, title):
    """Thin horizontal colour bar under the image (rendered by matplotlib for crisp text)."""
    im = Image.open(path).convert("RGB")
    fig = plt.figure(figsize=(W / 200, H / 200), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(np.asarray(im), aspect="auto")
    ax.axis("off")
    norm = matplotlib.colors.LogNorm(*clim) if log else matplotlib.colors.Normalize(*clim)
    cax = fig.add_axes([0.22, 0.213, 0.56, 0.05])
    cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    cb.set_label(title, fontsize=10, color=INK, labelpad=2)
    cb.ax.tick_params(labelsize=9, colors=INK, length=2)
    cb.outline.set_edgecolor("#8a8894")
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS).save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("case", type=Path, help="the traced DO case (see the module docstring)")
    ap.add_argument("--time", type=float, default=2060, help="its time directory (default 2060)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    post = a.case / "postProcessing" / "radiationDose" / f"{a.time:g}"

    reader = pv.OpenFOAMReader(str(a.case / "out.foam"))
    reader.set_active_time_value(a.time)
    reader.cell_to_point_creation = True
    blocks = reader.read()
    mesh = blocks["internalMesh"]
    mesh["Umag"] = np.linalg.norm(mesh.point_data["U"], axis=1)
    mid = mesh.slice(normal="y", origin=(0, 0, 0))
    wall = mesh.extract_surface(algorithm="dataset_surface")

    # 1. Flow: |U| on the mid-plane
    umax = float(np.percentile(mid["Umag"], 99.5))
    f = field_image(mid, "pipe-flow", "Umag", "viridis", (0, umax), False, wall)
    add_bar(f, "viridis", (0, umax), False, "|U| (m/s)")

    # 2. Fluence rate G on the mid-plane (log scale: it spans decades away from the lamp)
    g = mid["G"]
    ghi = float(np.percentile(g, 99.5))
    glo = ghi * 1e-3
    f = field_image(mid, "pipe-G", "G", "inferno", (glo, ghi), True, wall)
    add_bar(f, "inferno", (glo, ghi), True, "G (W/m²)")

    # 3. Tracks coloured by final dose (a random subset, thinned already by trajectoryStride)
    tr = pv.read(post / "trajectories.vtk")
    dose = np.asarray(tr.cell_data["finalDose_mJcm2"])
    rng = np.random.default_rng(1)
    pick = np.sort(rng.choice(tr.n_cells, N_TRACKS, replace=False))
    sub = tr.extract_cells(pick).extract_surface(algorithm="dataset_surface")
    lo, hi = float(np.percentile(dose, 1)), float(np.percentile(dose, 99))
    p = plotter()
    p.add_mesh(wall, color="#d9d6de", opacity=0.10, smooth_shading=True)
    p.add_mesh(
        sub, scalars="finalDose_mJcm2", preference="cell", cmap="viridis", clim=(lo, hi),
        line_width=3, render_lines_as_tubes=True, show_scalar_bar=False, lighting=False,
    )
    view_midplane(p)
    tmp = OUT / "pipe-tracks.png"
    p.screenshot(tmp)
    p.close()
    fit_canvas(tmp)
    add_bar(tmp, "viridis", (lo, hi), False, "dose (mJ/cm²)")

    # 4. Dose histogram
    d = load_doses(post / "doseDistribution.csv")
    fig, ax = plt.subplots(figsize=(W / 200, H / 200), dpi=200)
    ax.hist(d, bins=60, range=(0, np.percentile(d, 99.8)), color=THIS, edgecolor="white", linewidth=0.4)
    ax.axvline(d.mean(), color=INK, lw=1.4, ls="--")
    ax.text(d.mean(), ax.get_ylim()[1] * 0.96, f" mean {d.mean():.0f}", color=INK, fontsize=16, va="top")
    ax.set_xlabel("Dose (mJ/cm²)", fontsize=17, color=INK)
    ax.set_ylabel("Particles", fontsize=17, color=INK)
    ax.tick_params(labelsize=14, colors=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "pipe-dose.png", dpi=200, facecolor="white")
    plt.close(fig)
    Image.open(OUT / "pipe-dose.png").convert("RGB").resize((W, H), Image.LANCZOS).save(OUT / "pipe-dose.png")
    # 5. Log reduction and RED: first-order (MS2-like) dose response at the run's k
    k = 0.1  # cm2/mJ, matches kInact in postProcess.dict
    lr = log_reduction(d, k)
    red = lr * np.log(10) / k
    x = np.linspace(0, 120, 200)
    fig, ax = plt.subplots(figsize=(W / 200, H / 200), dpi=200)
    ax.plot(x, k * x / np.log(10), color=THIS, lw=3)
    ax.plot([0, red, red], [lr, lr, 0], color=INK, lw=1.4, ls="--")
    ax.plot([red], [lr], "o", color=THIS, ms=9)
    ax.text(2, lr + 0.1, f"{lr:.1f}-log", color=INK, fontsize=17, va="bottom")
    ax.text(red + 2, 0.08, f"RED {red:.0f}", color=INK, fontsize=17, va="bottom")
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 5.2)
    ax.set_xlabel("Dose (mJ/cm²)", fontsize=17, color=INK)
    ax.set_ylabel("Log reduction", fontsize=17, color=INK)
    ax.tick_params(labelsize=14, colors=INK)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "pipe-response.png", dpi=200, facecolor="white")
    plt.close(fig)
    Image.open(OUT / "pipe-response.png").convert("RGB").resize((W, H), Image.LANCZOS).save(OUT / "pipe-response.png")
    print(f"log reduction {lr:.2f}, RED {red:.1f} mJ/cm2")
    print(f"mean dose {d.mean():.1f} mJ/cm2, N = {len(d)}")


if __name__ == "__main__":
    main()
