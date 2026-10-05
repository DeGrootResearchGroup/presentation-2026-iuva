# Fluent DO fluence rate at 288 directions on the uvmesh SST flow (2026-10-03)

Same as `../dom288` except for `2059/G`, which is the Fluent DO solution in the IUVA 2026 deck's
`fluent_results/sozzi_fluent_6_6.cgns` (`Incident_Radiation`; 6 x 6 per octant = 288 directions) on
the same 1,232,629-cell uvmesh mesh. The 72-direction counterpart is `../fluent33`.

1. `foamPostProcess -func writeCellCentres -time 2059` here (in `lgv-runner`), writing `2059/C`.
2. `of-mesh-converter transfer <cgns> . --time 2059 --fields G`, of-mesh-converter `b654443`
   (branch `add-polyhedral-cgns`, PR #2): 1,232,629 cells matched one to one, largest distance
   1.3e-15 m. No G existed, so the tool wrote zeroGradient on ordinary patches and their own types on
   the non-conformal couplings: the same boundaryField as `../dom288/2059/G`, checked. See
   `transfer_report.txt`.
3. Traced with OOR `b23582b` (`/work/lib_b23582b`), one OpenMP thread, `-time 2059`, in
   `lgv-runner`: 186 s, 9,987 escaped, 0 stuck, 127,033 outer steps (as every swap run).

Mean dose 49.42 mJ/cm2 (OpenFOAM DO 288: 49.50); log reduction 1.490 at
k = 0.1 (49.50 / 1.491 for DO 288), 5.365 at k = 0.5. Volume-averaged G
134.00 W/m2 (DO 288: 134.22). Summary of both Fluent runs: the deck's data/sozzi_fluent_swap.json.
