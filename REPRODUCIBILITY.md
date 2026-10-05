# Where every figure comes from

Each figure in `slides.qmd`: the script that draws it, the data file it reads, the simulation run
behind that data, and the code commits the run used. Slide numbers are as rendered (title = 1).
The backup slides list every run's settings and commits too (generated into `backup_cases.qmd` from
`data/records/`; see `README.md`).

**Status:** ✔ reproducible from the named commits and settings; ◻ placeholder, no data yet;
△ reproducible, with the limitation noted below.

## Code

| repository | commit | what it is |
|---|---|---|
| [of-optical-radiation](https://github.com/DeGrootResearchGroup/of-optical-radiation) (OOR) | `726714d` | `main`, 2026-05-29 to 2026-09-29 |
| OOR | `4f95835` | PR #81 (merged 2026-09-29, merge commit `10f48d8`): adds the incident-flux output `qin`, makes `iesEmitter` emit exactly its stated power, and holds no per-ray snapshot without scattering. Fields not using `iesEmitter` are unchanged from `726714d`. |
| OOR | `b634a20` | branch `radiation-dose-particle-tracking`, where the Sozzi flow and analytical G were solved (2026-05-05) |
| OOR | `96e51ee` | PR #81's first commit; the ray-effects room's meshes were built with it (meshing uses only OpenFOAM's own tools) |
| OOR | `276d992` | uvmesh 0.12.0 (`tools/uvMesh`), PR #84, merged 2026-10-01 as `d30e089`; the slide 6 mesh was built from its working tree on 2026-09-30, before the commit; Appendix 3 describes this version |
| OOR | `8923b21` | `setFluenceRate -xStart/-xEnd` (the line source on the lamp arc only) and the tutorial's use of it, PR #85, merged 2026-10-01 as `629ac09` |
| OOR | `659ec4a` | `main` after PR #85; the Sozzi DO and line-source fields (slides 10 and 15) were solved with it |
| OOR | `b23582b` | PR #90 (open): the `langevin` dispersion model -- one integrator for every step length with a continuous step (defaults `maxStepFraction` 0.02, `minLagrangianTime` 10 ms) -- on `main` with PRs #88 (well-mixed random walks) and #89 (reflection at uncovered non-conformal faces and at the inlet), and the last step cut to end at `maxTime`. Every Sozzi dose in the talk was traced with it (2026-10-02) |
| OOR | `ebadf6e` | PR #90's first version, whose Langevin model switched to a diffusion step near the walls; the deck's Sozzi doses were first traced with it and re-traced with `b23582b`. Only the snappy-mesh rows of the Appendix 2 mean-dose figure still use it, and are labelled so |
| [aquaflux](https://github.com/DeGrootResearchGroup/aquaflux) | `2ba97418` | `validation/sozzi_radiation/uvmesh_swap.py`, the slide 15 harness (PR #598, open) |
| aquaflux | `2f243441` | `validation/sozzi_radiation/uvmesh_swap.py` on uniform DO grids (PR #600, open) |
| aquaflux | `4aa0293d` | `validation/sozzi_radiation/background_grid.py`, aquaflux on Cartesian background grids (PR #601, open, stacked on #600) |
| aquaflux | `8dd4caae` | the ray-effects room case (PR #597, open), the first commit whose records name their own commit |
| [of-mesh-converter](https://github.com/DeGrootResearchGroup/of-mesh-converter) | `b654443` | branch `add-polyhedral-cgns` (PR #2, open): reads Fluent's polyhedral CGNS export and adds `transfer`, which put Fluent's G on the slide 10 mesh |

OpenFOAM is version 13 throughout, in a Docker image built from of-optical-radiation's `Dockerfile`;
each record gives the OpenFOAM build.

## Figures drawn from no simulation (✔)

| slide | figure | script | input |
|---|---|---|---|
| 5 | `lagrangian-fields.svg` | `make_diagrams.py` | drawn |
| 7 | `architecture.svg` | `make_diagrams.py` | drawn |
| 8 | `test-taxonomy.svg` | `make_diagrams.py` | the 29 test cases of OOR `main` after PR #81 |
| 11 | `oss-benefits.svg` | `make_diagrams.py` | drawn |
| 12 | `ies-polar.svg` | `make_plots.py` | `data/ushio_b1_222nm.ies` |
| 12 | `dummy-room-E.png`, `dummy-room-G.png` | `make_dummies.py` → `run_dummy_room.py` → `render_dummy_room.py` (`make_dummy_room.sh` runs all three) | `data/dummies/*.stl` (Anny 0.6.1), `data/dummy_room.npz` (aquaflux, direct gather, black walls, 4 × Ushio B1, no mesh) |
| 12 | `absorption-222.svg` | `make_plots.py` | O₂ and O₃ cross-sections as in OOR's `tests/molecularAbsorptionSlab2D` |
| 14 | `aquaflux-gather.svg` | `make_diagrams.py` | drawn |
| 16 | `qr-repo.svg` | `make_diagrams.py` (needs `segno`) | github.com/DeGrootResearchGroup |
| backup | `model-overview.svg`, `model-gather.svg`, `model-emission-solid-angle.svg`, `model-radiosity.svg`, `model-formfactor.svg`, `model-occlusion.svg`, `model-mask.svg`, `model-voxel.svg` (Appendix 1); `tracker-flow.svg`, `barycentric.svg`, `tet-exit.svg`, `tet-crossing.svg`, `dose-segments.svg`, `dispersion-trace.svg` (Appendix 2); `uvmesh-pipeline.svg` (Appendix 3) | `make_diagrams.py` | drawn; Appendix 1 follows aquaflux's `aquaflux/radiation`, Appendix 2 OOR `b23582b` `src/radiationDose` (PR #90) |

## Figures from simulations

| slide | figure or number | script | data | run | code | DO settings | status |
|---|---|---|---|---|---|---|---|
| 8 | `renders/refractive-render.png`, `refractive-bars.svg` | `render_refractive.py`, `make_plots.py` | `data/refractive.json` | OOR `tutorials/refractiveInterface2D`, 2026-09-29 | OOR `4f95835` | the tutorial's | ✔ |
| 6 | `renders/uvmesh-pipe.png`, `renders/uvmesh-tip.png`, `renders/uvmesh-slice.png`, the slide's cell count and non-orthogonality | `render_uvmesh.py` | — (rendered from the mesh) | `data/uvmesh/mesh.py` with OOR's `tutorials/uvReactorSozzi2006/SozziTaghipour.step` beside it, built 2026-09-30: 1,232,629 cells, maximum non-orthogonality 52.8° (checkMesh, OpenFOAM build 13-18870c24d21c) | uvmesh: OOR `276d992`; bulk tetrahedra by gmsh 4.15.2 with Netgen (PyPI, macOS) | — | △ 3 |
| 2, 3, 15 | `renders/pipe-*.png` | `render_sozzi.py --time 2060` | — | the 72-direction DO run (`case/slide10_dom6_lu_B`; slide 10 reported it until 2026-10-03), which writes its tracks (`writeVtk` on, `trajectoryStride 10`) | as slide 10 | as slide 10 | ✔ |
| 15 | `sozzi-tip-compare.png` (G at the lamp tip; the time to G and LR at k = 0.1) | `render_tip_compare.py` | `data/sozzi_tip_timing.json`, `data/sozzi_dose_swap.json`, `data/sozzi_grid.json` | left column the slide 15 swap fields, right column aquaflux on 6, 4 and 3 mm Cartesian background grids (`background_grid.py`, variant `logG_surface`: log G, fitted to the sleeve's value 2M where a cell has corners inside it), cut on y = 0 around the tip, cell values on one log scale; timings 2026-10-02, one at a time with nothing else on the machine (Apple M3 Pro, 11 cores, 18 GB): DO 72 258 s and DO 288 1055 s (opticalRadiationFoam clock time, 8 MPI ranks in Docker), aquaflux every cell 757 s (mesh read 24 s, coarsening 18 s, gather 714 s), grids 67, 96 and 145 s (mesh read, coarsening, grid set-up, gather and interpolation; the 6 and 4 mm gathers ran past the launcher's free-memory check) | DO: OOR `659ec4a`; aquaflux `2ba97418` (every cell) and `4aa0293d` (grids, PR #601, open), jax 0.10.2 | — | ✔ |
| 9 | `renders/inlet-seeding.png` | `render_inlet.py --time 2060` | — | the same run; the seed points do not depend on G | as slide 10 | — | ✔ |
| 10 | `sozzi-radial-G.svg`, `sozzi-dose-cdf.svg`, the table's "DOM" column | `export_sozzi_data.py swap/dom288_native --time 2059`, `make_plots.py` | `data/sozzi_G_this.csv`, `data/sozzi_dose_this.csv`, `data/sozzi_stats.json` | the slide 6 mesh (uvmesh, 1,232,629 cells); k-ω SST flow converged by its residual controls in 2059 iterations (OpenFOAM 13-18870c24d21c, 8 ranks); DO from OOR's `uvReactorSozzi2006-DOM` dictionaries on the mesh's own lamp patches at 288 directions (the slide 15 set's `dom288_native`: its own patch values); dose traced with the `langevin` dispersion model, 9,987 particles, seed 42, one thread. The 72-direction run (`case/slide10_dom6_lu_B`, 49.2 mJ/cm² and 1.475) is in the record too: 288 directions raise the mean dose by 0.3 mJ/cm² and the log reduction by 0.016 at k = 0.1, 2 % at k = 0.5, so the slide reports 288. Every setting is in `data/records/sozzi_slide10.json` and `raw/sozzi_slide10/` | mesh: OOR `276d992`; flow dictionaries: OOR `659ec4a` with SST (case set up by hand, its dictionaries kept in the records); DO: OOR `659ec4a`; tracker: OOR `b23582b` | 288 directions on a uniform grid (nPhi = nTheta = 12; Fluent 6 × 6 per octant), 1×1 pixels, **linearUpwind** rays, convergence 1e-5 | △ 1 |
| 10 | the table's "line source" column | `make_plots.py` | `data/sozzi_dose_analytical.csv` → `data/sozzi_stats.json` | the same mesh, flow, particles and tracker, with G from `setFluenceRate -xStart 0 -xEnd 0.80` (the lamp arc only; zero in the inlet pipe and past the tip) | setFluenceRate: OOR `659ec4a`; tracker: OOR `b23582b` | — | ✔ |
| backup (Appendix 2) | `sozzi-wall-occupancy.svg` | `sozzi_wall_occupancy.py`, `make_plots.py` | `data/sozzi_wall_occupancy.json` | `wallsnap/` in the Sozzi run folder, 2026-10-05: the slide 10 mesh, flow, seeding and seed, one tracker per dispersion model (uncorrected discrete random walk; the walk with `wellMixed`; `langevin` at its defaults; `randomDisplacement` with dtMax 0.5 ms as the well-mixed reference), each with three instances stopped at maxTime 1.5, 2 and 2.5 s; the end points of the tracks still inside are snapshots. Particles between the sleeve and the chamber wall, 0.1 < x < 0.7 m, about 20,000 per model, counted in shells by distance from the sleeve over each shell's share of the annulus volume. No particle stuck in any run | tracker: OOR `b23582b` | — | ✔ |
| backup (Appendix 2) | `sozzi-mean-dose.svg`, the slide 10 takeaway line | `sozzi_mean_dose.py`, `make_plots.py` | `data/sozzi_mean_dose.json`, from `data/sozzi_dose_swap.json`, `data/sozzi_dose_analytical.csv` and the snappy-mesh runs' `summary.dat` | Sozzi & Taghipour's radial (eq. 3, closed form) and MPSS (eq. 5, 200 point sources, arc centred in the body, which they do not state) lamp models integrated over their Table 1 reactor at their 15.8e-4 m³/s; this work's integrals from the slide 15 harness; the snappy-mesh line-source runs with the uncorrected walk, the corrected walk and the Langevin model (3 threads) | as slides 10 and 15; snappy runs: tracker OOR `659ec4a` (uncorrected), `7f11000` plus the drift correction later merged as PR #88 (corrected), `ebadf6e` (Langevin) | — | ✔ |
| 10 | the dotted "Sozzi & Taghipour, Fig. 5" curve in `sozzi-dose-cdf.svg` | `digitize_sozzi_fig5.py` (from a screen capture of the figure, not kept here), `make_plots.py` | `data/sozzi_fig5_digitized.csv` | their Lagrangian dose histogram, L-shape reactor, 25 GPM, MPSS lamp model; clipped by the paper at 150 mJ/cm²; the CDF assumes 10,000 particles. The digitized bars give a log reduction of 1.81 against the paper's 1.87 | — | — | ✔ |
| 10 | the table's grey "Measured, prototype reactor" column, log reduction 1.51 | — | — | MS2 biodosimetry on the commercial prototype (a different reactor: Sozzi & Taghipour 2006, Fig. 1c and Table 1), 25 GPM, 70 % UVT; read off their Fig. 9 with WebPlotDigitizer | — | — | ✔ |
| 10 | the table's "Fluent DO" column and the Fluent curves in `sozzi-radial-G.svg` and `sozzi-dose-cdf.svg` | `export_sozzi_data.py --series fluent --time 2059`, `make_plots.py` | `data/sozzi_G_fluent.csv`, `data/sozzi_dose_fluent.csv` → `data/sozzi_stats.json` | ANSYS Fluent DO on the slide 6 mesh, exported to CGNS (`fluent_results/sozzi_fluent_6_6.cgns`, `Incident_Radiation` only; about 1 GB with the 3 × 3 export, so kept locally and not in the repository); `of-mesh-converter transfer` matched its 1,232,629 cells one to one by centre (largest distance 1.3e-15 m) and wrote G into a copy of the slide 15 swap set's flow (`swap/fluent66`, zeroGradient patch values, as the slide 15 fields); the same particles and tracker, traced at 2059, 2026-10-03. The 3 × 3 export went the same way into `swap/fluent33` (2026-10-02). Record: `data/records/sozzi_slide10.json` | of-mesh-converter `b654443`; tracker: OOR `b23582b` | 6 × 6 θ × φ divisions per octant (288 directions; 3 × 3 = 72 in the record); the exports do not record the Fluent version, pixelation or scheme | △ 5 |
| 11 | `scaling.svg` | `parse_scaling.py` (from `scripts/cluster/results*`), `make_plots.py` | `data/scaling.csv` | OOR `tutorials/uvChannelChiu1999-3d` (about 7 M cells) on Nibi, 4 to 128 MPI ranks, 2026-09-29 to 10-02, by `scripts/cluster/` (Apptainer image of OOR's CI, OpenFOAM build 13-441953dfbb42): 200 flow iterations and 6 DO steps of at most 5 sweeps each, timed per iteration and per sweep with start-up and the first step excluded. The plot uses the runs on whole nodes (the `results0*_excl` sets: three runs at 4 and 8 cores, two from 16 up), median and range; `data/scaling.csv` also holds the shared-node runs, which the plot leaves out, less six that shared a node with another job of the same set (results01/np4, np8, np64; results02/np4, np8, np16). The job scripts and logs (`scripts/cluster/`) are kept on the author's machine only: they carry a personal cluster account | OOR: not recorded (△ 6) | 256 directions (nPhi 16 × nTheta 8, not uniform; timing only), 1×1 pixels | △ 6 |
| 2, 13, 14 | `room-scene.png` (also on slide 2), `bunny-closeup.png`, `room-floor-maps.png`, `room-slice-G.png`, the slide 14 table | `export_room_data.py`, `render_room.py`, `make_plots.py` | `data/room_bunny.{npz,json}`, `data/bunny_surface.npz` | aquaflux `validation/ray_effects_room`; the earlier 8 × 4 and 16 × 8 runs are in its `work/runs_nonuniform/` | DO: OOR `4f95835`; aquaflux and the exact field: aquaflux `8dd4caae` | 72 directions (6×6, 3×3 pixels; 1×1 also run) and 288 (12×12, 1×1: 3×3 swaps at this size), uniform grids (Fluent 3 × 3 and 6 × 6 per octant), **linearUpwind** rays; runs of 2026-10-02/03, one at a time (the reflecting-walls run shared its first few minutes with the Sozzi renders) | ✔ |
| 15 | `sozzi-swap.svg` | `make_plots.py` (Fluent lines: `export_fluent_swap.py`) | `data/sozzi_dose_swap.json` (= the harness's `swap/summary.json`), `data/sozzi_grid.json` (the background-grid curves, variant `logG_surface`), `data/sozzi_fluent_swap.json` (the Fluent lines) | aquaflux `validation/sozzi_radiation/uvmesh_swap.py` (stages `gather`, `write`, `compare`) on the slide 10 mesh and flow, 2026-10-02 (the DO fields; aquaflux's gather 2026-10-01): aquaflux's G from the mesh's own lamp patches (16,878 facets), the 72-direction DO run, and a 288-direction DO run; the tracker once per G with the slide 10 settings, all 9,987 particles on identical paths. The Fluent lines: Fluent DO at 3 × 3 and 6 × 6 per octant, put in the same flow by `of-mesh-converter transfer` (`swap/fluent33`, `swap/fluent66`) and traced the same way (2026-10-02/03) | DO: OOR `659ec4a`; tracker: OOR `b23582b`; aquaflux `2ba97418` (the gather) and `2f243441` (write and compare, PR #600, open); of-mesh-converter `b654443` | 72 (6×6) and 288 (12×12) directions, uniform grids (Fluent 3 × 3 and 6 × 6 per octant), 1×1 pixels, **linearUpwind** rays, convergence 1e-5 | △ 2 |

The backup slides on aquaflux quote results from aquaflux's `validation/sozzi_radiation/README.md`.

## Known limitations

1. **linearUpwind rays dip below zero.** The Sozzi DO fields use bounded linearUpwind rays, the
   tutorial's scheme; G is negative in 5.8 % of cells at 72 directions and 6.5 % at 288 and the tracker counts it as zero. On the earlier snappyHexMesh mesh first-order
   upwind rays moved the log reduction at k = 0.1 by about 0.02 (1.54 to 1.56, with the old random
   walk); upwind was not re-run on the uvmesh set.
2. **The Sozzi flow's case has no committed script.** It is set up by hand from OOR's tutorial
   dictionaries with SST; its dictionaries and logs are in `data/records/raw/sozzi_slide10/`.
3. **The slide 6 mesh is reproducible in kind, not bit for bit.** Its bulk was meshed on the host by
   gmsh 4.15.2 from PyPI (macOS) with Netgen. OOR's Docker image at `276d992` builds the same gmsh
   version from source with Netgen, but different OpenCASCADE builds give slightly different
   tetrahedra: on the same bulk, 96,833 cells in the container against 96,373 on the host, both Mesh
   OK. A rebuild therefore gives a mesh like this one, not the same one.
4. **The tracker uses one OpenMP thread on the uvmesh mesh.** With three threads it aborts building
   the non-conformal coupling's point normals; the particle paths depend on the thread count, so the
   records name it.
5. **The Fluent DO runs' settings beyond their angular grids are not recorded.** The CGNS exports
   carry only the incident radiation: not the Fluent version, the pixelation or the
   discretization scheme. Their G also traces with zeroGradient patch values, as the slide 15 fields
   do, rather than Fluent's own wall values; on the OpenFOAM DO field at 72 directions that choice
   moves the mean dose by 0.002 mJ/cm² (49.161 with zeroGradient against 49.159 with the solver's
   own, the same particles).
6. **The scaling runs' of-optical-radiation commit is not recorded.** They were built on Nibi from a
   clone of `main` taken between 2026-09-29 and 10-02 (`scripts/cluster/build.sbatch`), and the logs
   keep only the OpenFOAM build. Their DO grid, nPhi 16 × nTheta 8, has polar bins twice as wide as
   its azimuthal ones; the slide uses only their timings, which depend on the number of directions,
   not on the bins' shape.
