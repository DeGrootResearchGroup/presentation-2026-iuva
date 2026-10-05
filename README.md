# IUVA Americas 2026: An Open-Source OpenFOAM Framework for UV Reactor Design

Slides, figure scripts and simulation records for the talk by Christopher T. DeGroot (Department of
Mechanical and Materials Engineering, Western University) at IUVA Americas 2026, on October 6,
2026. The slides are a
[Quarto](https://quarto.org) reveal.js deck in the assertion-evidence style; they are published at
<https://degrootresearchgroup.github.io/presentation-2026-iuva/> by `.github/workflows/publish.yml` on every push
to `main`. Press `S` in the published deck for the speaker notes.

The talk presents two open-source codes:

- **of-optical-radiation** (<https://github.com/DeGrootResearchGroup/of-optical-radiation>): an
  OpenFOAM 13 library for ultraviolet radiation transport by the discrete-ordinates method, and the
  `radiationDose` Lagrangian tracker that integrates each particle's dose.
- **aquaflux** (<https://github.com/DeGrootResearchGroup/aquaflux>, alpha): a JAX solver whose
  radiation module computes the fluence rate by summing each emitting surface facet's exact
  contribution, with no angular discretization.

## Terms used in these files

| term | meaning |
|---|---|
| G | fluence rate, W/m² (µW/cm² on the room slides) |
| E | irradiance on a surface |
| D = ∫G dt | the UV dose a particle accumulates along its path |
| LR, RED | log reduction, −log₁₀ of the surviving fraction; reduction-equivalent dose |
| DO, DOM | the discrete-ordinates method; "DO" on the slides, "DOM" in of-optical-radiation's names |
| OOR | of-optical-radiation, in commit tables |
| directions, pixels | a DOM run's angular bins (`2 × nPhi × nTheta`) and their Murthy–Mathur subdivision (`nPixelPhi × nPixelTheta`) |
| ray scheme | the convection scheme for each direction's radiance, `div(Ji,Ii_h)`: `bounded Gauss upwind` (first order) or `bounded Gauss linearUpwind` (second order) |
| iesEmitter, diffuseEmitter | of-optical-radiation boundary conditions: a lamp from a measured IES (LM-63) file, and a Lambertian emitter |
| setFluenceRate | an of-optical-radiation utility writing the analytical infinite-line-source G |
| exact field | the ray-effects room's reference: each floor point ray-traced to 17,920 points on the lamp window (numpy and Embree), valid for black walls only |

## Build the slides

The figures are committed, so the deck needs only Quarto (built with 1.10):

```bash
quarto preview slides.qmd      # or: quarto render slides.qmd
```

## Regenerate the figures

```bash
python3 -m pip install -r requirements.txt
```

The data in `data/` is exported from simulation runs, which are not in this repository (they are
tens of gigabytes). Every plot and diagram can be redrawn from `data/` alone (steps 2 and 4 below);
the exports and renders need the runs. The scripts find the runs through environment variables,
with defaults under the author's run archive (`scripts/common.py`):

| variable | what | default |
|---|---|---|
| `IUVA_RUNS` | the folder holding the run directories | `~/aquaflux-runs` |
| `IUVA_SOZZI` | the Sozzi run directory: uvmesh mesh, flow, DO and tracker cases, the slide 15 swap set and background grids | `$IUVA_RUNS/sozzi_sst_dose_2026-10-01` |
| `IUVA_SOZZI_FLOW`, `IUVA_ROOM_CASE`, `IUVA_REFRACTIVE`, `IUVA_BUNNY_STL` | read by `collect_records.py` only (its docstring) | under `$IUVA_RUNS` |
| `AQUAFLUX_ROOT` | an aquaflux checkout, for `run_dummy_room.py` | `~/cfd` |

Run every script from the deck root, as `python3 scripts/<name>.py`. To rebuild everything from the
runs, in this order:

1. **Export the data** from each run (the table below).
2. **Draw the figures:** `python3 scripts/make_diagrams.py` (the hand-drawn SVG diagrams, and the QR
   code, which needs `segno`) and `python3 scripts/make_plots.py` (every data plot, from `data/`).
3. **Render the 3-D images** (the `render_*.py` rows below; they need pyvista).
4. **Rebuild the run records** (below): `python3 scripts/collect_records.py`, then
   `python3 scripts/make_case_tables.py`.

| script | reads | writes |
|---|---|---|
| `common.py` | — | nothing: the colours, paths and dose helpers the other scripts import |
| `make_diagrams.py` | nothing (drawn) | every hand-drawn `figures/*.svg` and `qr-repo.svg` |
| `make_plots.py` | `data/` only (its docstring lists each plot's inputs) | the data plots in `figures/`, and `data/sozzi_stats.json` |
| `export_sozzi_data.py <case> --time 2060` | the traced slide 10 DO case (`case/slide10_dom6_lu_B` under `IUVA_SOZZI`); with `--series fluent --time 2059`, the Fluent case (`swap/fluent33`) | `data/sozzi_G_{this,fluent}.csv`, `data/sozzi_dose_{this,fluent}.csv` |
| `sozzi_mean_dose.py` | `data/sozzi_dose_swap.json`, `data/sozzi_dose_analytical.csv`, and the snappy-mesh line-source runs under `IUVA_SOZZI` | `data/sozzi_mean_dose.json` (each fluence rate's ∫G dV / Q against the tracked mean dose, including Sozzi & Taghipour's own lamp models) |
| `digitize_sozzi_fig5.py <image>` | a screen capture of Sozzi & Taghipour (2006) Fig. 5, axes included (not kept here) | `data/sozzi_fig5_digitized.csv` |
| `export_room_data.py <aquaflux>/validation/ray_effects_room` | the aquaflux ray-effects case after its pipeline has run; needs that checkout's aquaflux | `data/room_bunny.{npz,json}`, `data/bunny_surface.npz` |
| `render_room.py` | `data/room_bunny.npz`, `data/bunny_surface.npz` | `figures/room-scene.png`, `figures/bunny-closeup.png` |
| `render_sozzi.py <case> [--time 2060]`, `render_inlet.py <case> [--time 2060]` | the same traced slide 10 DO case, with its trajectories (`writeVtk` on) | `figures/renders/pipe-*.png`, `figures/renders/inlet-seeding.png` |
| `render_tip_compare.py [<Sozzi run>]` | G from the slide 15 swap set (`swap/{dom72,dom288,aquaflux}` under `IUVA_SOZZI`) and from aquaflux's background grids (`grid/h{6,4,3}mm/logG_surface`), `data/sozzi_tip_timing.json` (the uncontended timings, written by hand from the runs it describes), and the log reductions in `data/sozzi_dose_swap.json` and `data/sozzi_grid.json` | `figures/renders/tip-G-*.png`, `figures/sozzi-tip-compare.png` |
| `render_refractive.py <refractiveInterface2D case>` | a finished run of that tutorial | `data/refractive.json`, `figures/renders/refractive-render.png` |
| `render_uvmesh.py <uvmesh case>` | a mesh built by `data/uvmesh/mesh.py` (copy it and OOR's `tutorials/uvReactorSozzi2006/SozziTaghipour.step` into an empty directory, run `python3 mesh.py`, then `./Allrun.mesh` in the of-optical-radiation Docker image), with a `*.foam` file beside `constant/` | `figures/renders/uvmesh-{pipe,tip,slice}.png` |
| `make_dummy_room.sh` (runs the next three) | — | slide 12's occupant figures |
| `make_dummies.py` | the Anny body model (needs `anny`, `torch`, `trimesh`) | `data/dummies/*.stl` |
| `run_dummy_room.py` | `data/dummies/*.stl`, `data/ushio_b1_222nm.ies`; aquaflux at `AQUAFLUX_ROOT` | `data/dummy_room.{npz,json}` |
| `render_dummy_room.py` | `data/dummy_room.npz` | `figures/dummy-room-{E,G}.png` |
| `parse_scaling.py [results dirs] [--all]` | the strong-scaling runs' logs under `scripts/cluster/results*`, kept on the author's machine only (the job scripts carry a personal cluster account); runs listed in its `exclude.txt` are left out | `data/scaling.csv` |
| `collect_records.py`, `make_case_tables.py` | the runs' own records (below) | `data/records/`, `backup_cases.qmd` |

`data/sozzi_dose_analytical.csv` (the line source on the lamp arc only) is copied as its run wrote
it; `data/sozzi_dose_swap.json` is aquaflux `validation/sozzi_radiation/uvmesh_swap.py`'s
`swap/summary.json`. `data/sozzi_grid.json` is `validation/sozzi_radiation/background_grid.py`'s
`grid/summary.json` (aquaflux gathered on Cartesian background grids and interpolated to the cells).

## Run records: what every simulation ran with

`REPRODUCIBILITY.md` maps every figure to its script, its data file, the run behind it and the code
commits that run used. The backup slides show the same settings and commits, one slide per case,
generated from `data/records/` by `scripts/collect_records.py` and `scripts/make_case_tables.py`
(`backup_cases.qmd` is generated; do not edit it). `data/records/raw/` holds a copy of every run's
own record, with local paths replaced by placeholders (`<aquaflux>`, `<of-optical-radiation>`,
`<runs>`). `collect_records.py` reads the runs from paths set by the `IUVA_*` environment variables
listed in its docstring.

To repeat a run, check out the commit its record names, e.g.

```bash
git clone https://github.com/DeGrootResearchGroup/of-optical-radiation && cd of-optical-radiation
git checkout 4f95835
```

and run the case named in the record: of-optical-radiation's `tutorials/refractiveInterface2D`,
`tutorials/uvReactorSozzi2006` and `tutorials/uvReactorSozzi2006-DOM`, or aquaflux's
`validation/ray_effects_room` (its `README.md` gives the pipeline) and
`validation/sozzi_radiation/uvmesh_swap.py`. The Sozzi runs of slides 2, 3, 9, 10 and 15 share one
mesh (the slide 6 uvmesh) and one k-ω SST flow; no committed script writes that flow's case, so its
dictionaries and logs are kept in `data/records/raw/sozzi_slide10/`.

## Licence

The slides, figures and data are licensed under CC BY 4.0 (`LICENSE-CONTENT.md`) and the code under
the MIT License (`LICENSE`). Third-party files keep their own terms, listed in `LICENSE-CONTENT.md`.

## Sources

- `data/ushio_b1_222nm.ies`: the Ushio B1 (Care222) far-UVC module, measured by OSLUV (Dec 2023),
  from the guv-calcs package (<https://github.com/jvbelenky/guv-calcs>), MIT licence; its notice is
  `data/ushio_b1_222nm.ies.LICENSE`. Intensities are radiometric (mW/sr).
- The Voronoi bunny (`data/bunny_surface.npz`, and the room data) is built by aquaflux's
  `validation/ray_effects_room/voronoi_bunny.py` from the Stanford Bunny of the Stanford 3D Scanning
  Repository (Stanford University Computer Graphics Laboratory).
- The validation reactor: Sozzi, D. A., and Taghipour, F. (2006), "UV reactor performance modeling
  by Eulerian and Lagrangian methods", *Environmental Science & Technology* 40(5), 1609–1615.
