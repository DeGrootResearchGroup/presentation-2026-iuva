#!/usr/bin/env python3
"""As prod_lowre4_mesh.py, plus: the bulk refined along the inlet jet's path, from the lamp tip
region (x = 0.79 m) to the inlet pipe's exit (0.889 m), radius 12 mm, at the pipe's 1.25 mm spacing
grading out to the 4 mm bulk (the jet crossed 4 mm cells, ~5 across its 19 mm); and the bulk's tets
optimised harder (gmsh OptimizeThreshold 0.5, which cleared prod_lowre4's 3 bad dual faces, and
Netgen, meshed on the host, whose gmsh has it).

prod_lowre4_mesh.py: as prod_lowre3_mesh.py (lamp and chamber cylinder at y+ ~ 1, pipes in the log-law region,
uniform pipe cells) but with a thicker lamp layer whose outer cells match the bulk beside it.

On prod_lowre3 the flow would not settle over x ~ 0.58-0.79 m, where the wall jet coming off the
lamp's tip runs back along the sleeve: it still carries 1-3 m/s at the 15 mm seam, so its outer
part crossed from the structured layer into the bulk where it decays fastest, and the structured
layers there changed 100x more per iteration than the bulk beside them.

- lamp: the structured layer to r = 22 mm (12 mm thick), 26 radial cells from 20 um at the sleeve
  growing ~1.20 per cell to ~2.0 mm at the seam (grading 100); 64 around (2.16 mm at the seam),
  2.5 mm along.
- bulk next to the lamp: gmsh size 1.5 mm (its polyhedra come out ~1.4x the gmsh size, so ~2.1 mm,
  to match the layer's outer cells), growing to 4 mm.
- chamber cylinder: 0.1 mm first cell, an 8 mm layer of 16 cells (grading 13.6), 96 around, 4 mm.
- pipes: 12 per quadrant, 8 radial graded 4 (y+ ~31-38), uniform ~4 mm axial cells graded over the
  last 30 mm to 1.25 mm at the junction.
"""
import os

from uvmesh import Lamp, Pipe, ReactorBody, Refinement, WallLayer, build

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE_CELLS = dict(radius=0.00955, n_azimuth_per_quadrant=12, n_radial=8, radial_grading=4.0,
                  n_axial=205, junction_length=0.03, junction_cell_size=0.00125)
build(
    case_dir=HERE,
    lamps=[Lamp(
        axis_start=(0.0, 0.0, 0.0), axis_end=(0.8, 0.0, 0.0),
        sleeve_radius=0.01, annulus_outer_radius=0.022,
        n_radial=26, radial_grading=100.0,
        n_azimuth_per_quadrant=16, n_axial=320,
        endcap_a_shape="flat", endcap_b_shape="hemisphere",
    )],
    body=ReactorBody(
        step_path=os.path.join(HERE, "SozziTaghipour.step"),
        step_scale=1e-3,
        step_rotate=((0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
        wall_patch_name="bodyWall",
        bulk_cell_size=0.004,
        near_lamp_cell_size=0.0015,
        bulk_cells="polyhedral",
        dual_feature_angle=100,
        refinements=[Refinement(axis_start=(0.79, 0.0, 0.0), axis_end=(0.889, 0.0, 0.0),
                                radius=0.012, cell_size=0.00125)],
        optimize_threshold=0.5,
        optimize_netgen=True,
    ),
    pipes=[
        Pipe(axis_start=(0.889, 0.0, 0.0), axis_end=(1.739, 0.0, 0.0),
             open_patch_name="inlet", **PIPE_CELLS),
        Pipe(axis_start=(0.04765, 0.0, 0.0445), axis_end=(0.04765, 0.0, 0.8945),
             open_patch_name="outlet", **PIPE_CELLS),
    ],
    wall_layers=[
        WallLayer(axis_start=(0.0, 0.0, 0.0), axis_end=(0.889, 0.0, 0.0), radius=0.0445,
                  thickness=0.008, n_layers=16, wall_grading=13.6, n_azimuth_per_quadrant=24,
                  axial_cell_size=0.004),
    ],
)
