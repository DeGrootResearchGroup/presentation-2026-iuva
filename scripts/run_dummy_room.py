#!/usr/bin/env python3
"""Irradiance on four dummies and fluence rate in a far-UVC room, from aquaflux.

    AQUAFLUX_ROOT=~/cfd python3 scripts/run_dummy_room.py

A 5 x 4 x 3 m room of clear air at 222 nm with black walls and four Ushio B1 fixtures on the
ceiling facing down. Four Anny dummies (data/dummies, made by make_dummies.py) stand in it:
three the same distance from a fixture and one at the centre. aquaflux's direct gather gives

  * the irradiance E (a cosine-weighted receiver) at every triangle of every dummy, which is what
    an exposure limit is written for, gated by the dummies' own shadows, and
  * the fluence rate G on a regular grid through the room (no receiver cosine).

Needs the aquaflux checkout of PR #596/#597 or later on AQUAFLUX_ROOT (jax, numpy, equinox), and
trimesh. No mesh or OpenFOAM run is involved. Writes data/dummy_room.npz and data/dummy_room.json.
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.expanduser(os.environ.get("AQUAFLUX_ROOT", "~/cfd")))

import aquaflux  # noqa: E402,F401  (enables x64)
import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from aquaflux.radiation import (  # noqa: E402
    NoOcclusion,
    Surfaces,
    TriangleBody,
    build_visibility,
    direct_fluence_rate,
    direct_irradiance,
    read_ies,
)

IES = ROOT / "data" / "ushio_b1_222nm.ies"
DUMMIES = ROOT / "data" / "dummies"
ROOM_LOW, ROOM_HIGH = np.array([-2.5, -2.0, 0.0]), np.array([2.5, 2.0, 3.0])
LAMP_XY = [(-1.25, -1.0), (1.25, -1.0), (-1.25, 1.0), (1.25, 1.0)]
WINDOW = (0.0625, 0.04375)  # m, long side along x as in the deck's bunny room
LAMP_UP = (1.0, 0.0, 0.0)
GRID = 0.1  # m, fluence-rate grid spacing
CHUNK = 20_000  # receivers per shadow mask
OFFSET = 0.002  # m, receivers sit this far off the skin so a body does not shadow its own point

# name: (x, y, yaw in degrees about z; 0 faces -y, the way Anny's front faces)
PLACEMENT = {
    "adult_male": (-1.25, -1.0, 0.0),  # under a fixture
    "adult_female": (1.25, 1.0, 90.0),  # under a fixture, facing away from the wall
    "child": (1.25, -1.0, 180.0),  # under a fixture
    "elder_female": (0.0, 0.0, 45.0),  # centre of the four
}
# ACGIH 2022 TLVs at 222 nm, mJ/cm2 per 8 h
TLV_EYE, TLV_SKIN = 23.0, 479.0


def say(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def lamps():
    """Four windows on the ceiling, each cut into 10 x 7 squares of two triangles, facing down."""
    nx, ny = 10, 7
    xs = np.linspace(-WINDOW[0] / 2, WINDOW[0] / 2, nx + 1)
    ys = np.linspace(-WINDOW[1] / 2, WINDOW[1] / 2, ny + 1)
    tris = []
    for cx, cy in LAMP_XY:
        for i in range(nx):
            for j in range(ny):
                p = [(cx + xs[i], cy + ys[j]), (cx + xs[i + 1], cy + ys[j]),
                     (cx + xs[i + 1], cy + ys[j + 1]), (cx + xs[i], cy + ys[j + 1])]
                p = np.array([[a, b, ROOM_HIGH[2]] for a, b in p])
                tris += [p[[0, 2, 1]], p[[0, 3, 2]]]  # counter-clockwise seen from below: normal -z
    tris = np.array(tris)
    area = 0.5 * np.linalg.norm(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1)
    photometry = read_ies(IES)
    assert photometry.keywords.get("_INTENSITYUNITS") == "mW/sr"
    power = photometry.flux * 1e-3  # W per fixture
    surfaces = Surfaces.from_triangles(
        tris, emission=power / (area.sum() / len(LAMP_XY)),
        profiles=(photometry.profile(up=LAMP_UP),))
    assert np.allclose(np.asarray(surfaces.normal), (0, 0, -1), atol=1e-9), "lamps face the wrong way"
    return surfaces, power


def place(name):
    x, y, yaw = PLACEMENT[name]
    mesh = trimesh.load(DUMMIES / f"{name}.stl", process=False)
    a = np.radians(yaw)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(a, (0, 0, 1)))
    mesh.apply_translation([x, y, 0])
    assert mesh.volume > 0, f"{name}: normals point inward"
    return mesh


def gather(kind, lamp, points, normals, body, label):
    out = np.empty(len(points))
    for s in range(0, len(points), CHUNK):
        p = points[s:s + CHUNK]
        vis = build_visibility([body], lamp, p, self_occlusion=NoOcclusion())
        if kind == "E":
            v = direct_irradiance(lamp, jnp.asarray(p), jnp.asarray(normals[s:s + CHUNK]), visibility=vis)
        else:
            v = direct_fluence_rate(lamp, jnp.asarray(p), visibility=vis)
        out[s:s + len(p)] = np.asarray(jax.block_until_ready(v))
        say(f"  {label}: {min(s + CHUNK, len(points))}/{len(points)}")
    return out


def main():
    lamp, power = lamps()
    meshes = {n: place(n) for n in PLACEMENT}
    tris = np.concatenate([m.triangles for m in meshes.values()])
    body = TriangleBody.build(tris, sheet=True)
    say(f"{lamp.n_facets} lamp facets, {len(tris)} body triangles, {power * 1e3:.1f} mW per fixture")

    record = {"lamp_power_W_each": power, "tlv_eye_mJ_cm2": TLV_EYE, "tlv_skin_mJ_cm2": TLV_SKIN,
              "dummies": {}}
    arrays = {"lamp_xy": np.array(LAMP_XY), "room_low": ROOM_LOW, "room_high": ROOM_HIGH}
    for name, m in meshes.items():
        pts = m.triangles_center + OFFSET * m.face_normals
        E = gather("E", lamp, pts, m.face_normals, body, f"E {name}")
        height = m.bounds[1, 2]
        # the eye: front-facing triangles within a few cm of eye height (0.115 m below the crown),
        # so the cornea's worst-case direction is the way the person looks, not up at the lamp
        yaw = np.radians(PLACEMENT[name][2])
        front = np.array([np.sin(yaw), -np.cos(yaw), 0.0])  # rotated (0, -1, 0)
        c = m.triangles_center[:, 2]
        face = (np.abs(c - (height - 0.115)) < 0.04) & ((m.face_normals @ front > 0.85) & (np.abs(m.face_normals[:, 2]) < 0.5))
        assert face.sum() > 20, f"{name}: no eye patch found"
        e_eye, e_skin = E[face].max(), E.max()
        record["dummies"][name] = {
            "height_m": round(float(height), 3),
            "peak_E_head_W_m2": float(e_eye), "peak_E_body_W_m2": float(e_skin),
            "hours_to_eye_TLV": TLV_EYE * 10 / e_eye / 3600,
            "hours_to_skin_TLV": TLV_SKIN * 10 / e_skin / 3600,
            "position_yaw": PLACEMENT[name],
        }
        arrays[f"{name}_vertices"], arrays[f"{name}_faces"] = np.asarray(m.vertices), np.asarray(m.faces)
        arrays[f"{name}_E"] = E
        say(f"{name}: eye {e_eye * 1e3:.2f} mW/m2 -> {record['dummies'][name]['hours_to_eye_TLV']:.1f} h")

    axes = [np.arange(l + GRID / 2, h, GRID) for l, h in zip(ROOM_LOW, ROOM_HIGH)]
    grid = np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, 3)
    G = gather("G", lamp, grid, None, body, "G grid")
    inside = np.zeros(len(grid), bool)
    for m in meshes.values():
        inside |= m.contains(grid)
    arrays.update(grid_axes_x=axes[0], grid_axes_y=axes[1], grid_axes_z=axes[2],
                  G=G.reshape(len(axes[0]), len(axes[1]), len(axes[2])),
                  inside=inside.reshape(len(axes[0]), len(axes[1]), len(axes[2])))
    np.savez_compressed(ROOT / "data" / "dummy_room.npz", **arrays)
    record["backend"] = jax.default_backend()
    record["jax"] = jax.__version__
    (ROOT / "data" / "dummy_room.json").write_text(json.dumps(record, indent=2) + "\n")
    say("done")


if __name__ == "__main__":
    main()
