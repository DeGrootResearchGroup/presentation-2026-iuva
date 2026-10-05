#!/usr/bin/env python3
"""3-D renders of the ray-effects room and the bunny (needs pyvista).

Run from the deck root after export_room_data.py:

    python3 scripts/render_room.py

Writes figures/room-scene.png (the room, the lamp's window drawn at twice its
60 x 45 mm so it shows, the bunny, and aquaflux's floor irradiance under it)
and figures/bunny-closeup.png, each cropped to its content (needs Pillow too).
"""

from pathlib import Path

import numpy as np
import pyvista as pv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "figures"

BUNNY = "#d9d6de"
EDGE = "#8a8894"
LAMP = "#2a78d6"


def triangles_mesh(triangles):
    points = triangles.reshape(-1, 3)
    faces = np.hstack([np.full((len(triangles), 1), 3), np.arange(len(points)).reshape(-1, 3)])
    return pv.PolyData(points, faces.ravel()).clean()


def floor_mesh(room):
    tri = room["floor_tri"]
    points = np.concatenate([tri.reshape(-1, 2), np.zeros((tri.size // 2, 1))], axis=1)
    faces = np.hstack([np.full((len(tri), 1), 3), np.arange(len(points)).reshape(-1, 3)])
    mesh = pv.PolyData(points, faces.ravel())
    mesh.cell_data["E"] = room["floor_aquaflux"]
    return mesh


def scene(room, bunny):
    plotter = pv.Plotter(off_screen=True, window_size=(1500, 1100))
    plotter.set_background("white")
    # The rest of the floor, outside the mapped window, and the room's edges -- all but the three
    # meeting at the corner nearest the camera, which would cut across the bunny.
    plotter.add_mesh(pv.Plane(center=(0, 0, -0.002), direction=(0, 0, 1), i_size=4, j_size=4),
                     color="#eeecf2", lighting=False)
    corners = [(-2, -2), (2, -2), (2, 2), (-2, 2)]
    for z in (0.0, 3.0):
        for a, b in zip(corners, corners[1:] + corners[:1]):
            if z == 3.0 and (2, -2) in (a, b):
                continue
            plotter.add_mesh(pv.Line((*a, z), (*b, z)), color=EDGE, line_width=2)
    for c in corners:
        if c != (2, -2):
            plotter.add_mesh(pv.Line((*c, 0.0), (*c, 3.0)), color=EDGE, line_width=2)
    plotter.add_mesh(
        floor_mesh(room),
        scalars="E",
        cmap="inferno",
        clim=(0, float(np.percentile(room["floor_exact"], 99.9))),
        show_scalar_bar=False,
        lighting=False,  # unshaded, so the colours read against the slide's colour bar
    )
    plotter.add_mesh(bunny, color=BUNNY, smooth_shading=True, specular=0.3)
    plotter.add_mesh(pv.Box((-0.06, 0.06, -0.045, 0.045, 2.97, 3.0)), color=LAMP)
    plotter.camera_position = [(4.6, -9.6, 4.6), (0.0, 0.0, 1.4), (0, 0, 1)]
    plotter.enable_anti_aliasing("ssaa")
    return plotter.screenshot(None, return_img=True)


def closeup(bunny):
    plotter = pv.Plotter(off_screen=True, window_size=(1200, 1000))
    plotter.set_background("white")
    plotter.add_mesh(bunny, color=BUNNY, smooth_shading=True, specular=0.3)
    plotter.camera_position = [(0.9, -1.1, 1.85), (0.0, 0.0, 1.47), (0, 0, 1)]
    plotter.enable_anti_aliasing("ssaa")
    return plotter.screenshot(None, return_img=True)


def trimmed(image, name, margin=12):
    """Save a render cropped to what it holds, with a small white margin."""
    from PIL import Image, ImageChops, ImageOps

    image = Image.fromarray(image).convert("RGB")
    box = ImageChops.difference(image, Image.new("RGB", image.size, "white")).getbbox()
    ImageOps.expand(image.crop(box), border=margin, fill="white").save(OUT / f"{name}.png")
    print(f"wrote figures/{name}.png")


if __name__ == "__main__":
    room = np.load(DATA / "room_bunny.npz")
    bunny = triangles_mesh(np.load(DATA / "bunny_surface.npz")["triangles"])
    trimmed(scene(room, bunny), "room-scene")
    trimmed(closeup(bunny), "bunny-closeup")
