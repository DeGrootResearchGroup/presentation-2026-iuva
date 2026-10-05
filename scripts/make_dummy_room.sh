#!/usr/bin/env bash
# Rebuild slide 12's occupant figures: dummies -> aquaflux run -> renders.
#
#   AQUAFLUX_ROOT=~/cfd scripts/make_dummy_room.sh
#
# Needs a Python with `anny trimesh` (make_dummies.py), one with jax + aquaflux's dependencies and
# `trimesh rtree` (run_dummy_room.py), and one with `pyvista matplotlib pillow` (render_dummy_room.py).
# Set DUMMY_PY, RUN_PY and RENDER_PY to point at them; each defaults to python3.
set -euo pipefail
cd "$(dirname "$0")/.."
"${DUMMY_PY:-python3}" scripts/make_dummies.py data/dummies
"${RUN_PY:-python3}" scripts/run_dummy_room.py
"${RENDER_PY:-python3}" scripts/render_dummy_room.py
