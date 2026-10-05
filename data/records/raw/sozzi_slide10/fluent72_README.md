# Fluent DO fluence rate on the uvmesh SST flow (2026-10-02)

Same as `../dom72` except for `2059/G`, which is the Fluent DO solution in the IUVA 2026 deck's
`fluent_results/sozzi_fluent_3_3.cgns` (`Incident_Radiation`; 3 x 3 per octant = 72 directions) on the same 1,232,629-cell uvmesh mesh.

How G got here (re-done with the released tool on 2026-10-02; the first, hand-made run is kept in
`hand_made/`, its G file was overwritten; every particle's dose agrees with it to 2e-8):

1. `foamPostProcess -func writeCellCentres -time 2059` here (in `lgv-runner`), writing `2059/C`.
2. `of-mesh-converter transfer <cgns> . --time 2059 --fields G --overwrite`, of-mesh-converter
   `b654443` (branch `add-polyhedral-cgns`, PR #2): 1,232,629 cells matched one to one, largest
   distance 1.3e-15 m; the `boundaryField` of the G it replaced (`../dom72/2059/G`'s) was kept.
   See `transfer_report.txt`. The converted Fluent mesh alone passes `checkMesh` (max
   non-orthogonality 52.81, total volume 0.00575851 m3).
3. Traced with OOR `b23582b` (`/work/lib_b23582b`), one OpenMP thread, `-time 2059`, in
   `lgv-runner`: 415 s, 9,987 escaped, 0 stuck, 127,033 outer steps (as every swap run).

| G | mean dose | p5 | p50 | p95 | LR k=0.02 | LR k=0.05 | LR k=0.1 |
|---|---|---|---|---|---|---|---|
| Fluent DO, 72 directions | 49.09 | 21.10 | 40.43 | 103.74 | 0.373 | 0.830 | 1.474 |
| OpenFOAM DO, 72 (`dom72`) | 49.16 | 21.09 | 40.54 | 103.92 | 0.373 | 0.831 | 1.475 |
| OpenFOAM DO, 288 (`dom288`) | 49.50 | 21.41 | 40.92 | 104.01 | 0.376 | 0.839 | 1.491 |
| aquaflux | 49.33 | 21.43 | 40.79 | 103.37 | 0.376 | 0.838 | 1.490 |

Volume-averaged G: Fluent 133.08 W/m2, `dom72` 133.29. Fluent's G is positive everywhere
(minimum 4.3e-8); `dom72` is negative in 71,948 cells (linearUpwind rays).
