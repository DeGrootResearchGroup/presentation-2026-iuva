#!/usr/bin/env python3
"""Data-driven figures for the IUVA Americas 2026 talk.

Run from the deck root:   python3 scripts/make_plots.py

Every plot reads its inputs from data/ (none needs a simulation run). The first five plots are
written even when an input is missing, with a grey note inside the axes naming the file to add;
the last four are skipped instead. Each function's docstring or comment names its slide.

  refractive_bars   refractive-bars.svg   data/refractive.json {"G_A_sim", "G_B_sim"} [W/m^2]
  sozzi_radial      sozzi-radial-G.svg    data/sozzi_G_this.csv, data/sozzi_G_fluent.csv
                                          (r_m, G_W_m2 at the lamp's mid-plane)
  sozzi_cdf         sozzi-dose-cdf.svg    data/sozzi_dose_{this,fluent,analytical}.csv (radiationDose
                                          doseDistribution.csv as written), data/sozzi_fig5_digitized.csv;
                                          also writes data/sozzi_stats.json (the slide 10 table)
  scaling           scaling.svg           data/scaling.csv (cores, rep, flow_s, dom_s, dose_s, exclusive)
  absorption_222    absorption-222.svg    computed here from O2 and O3 cross-sections
  ies_polar         ies-polar.svg         data/ushio_b1_222nm.ies
  room_floor_maps   room-floor-maps.png   data/room_bunny.npz, .json (scripts/export_room_data.py)
  room_slice        room-slice-G.png      the same
  sozzi_swap        sozzi-swap.svg        data/sozzi_dose_swap.json, data/sozzi_grid.json
  sozzi_mean_dose   sozzi-mean-dose.svg   data/sozzi_mean_dose.json (scripts/sozzi_mean_dose.py)
"""

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from common import AQUA, DATA, FLUENT, GRID, INK, INK2, MUTED, SURFACE, THIS, load_doses, log_reduction
from common import FIGURES as OUT

# ---------------------------------------------------------------- style ---
plt.rcParams.update({
    # A fixed salt makes the SVGs' internal ids the same on every run, so a re-run that changes
    # nothing writes identical files.
    "svg.hashsalt": "iuva2026",
    "svg.fonttype": "none",
    "font.family": "sans-serif",
    "font.sans-serif": ["Source Sans Pro", "Source Sans 3", "Helvetica Neue",
                        "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 20,
    "axes.labelsize": 21,
    "axes.labelcolor": INK2,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 1.0,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 1.0,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
    "legend.frameon": False,
    "legend.fontsize": 18,
    "lines.linewidth": 2.5,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})

# Figure sizes in inches at 100 dpi == CSS px when shown at native width.
HALF = (5.8, 4.6)
WIDE = (11.6, 4.6)


def save(fig, name, pad=0.08):
    """``pad`` [in]: raise it for a figure with text at its edge. The SVG keeps its text as text,
    and the browser's font can set it wider than matplotlib measured, past the figure's edge."""
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    print(f"wrote figures/{name}.svg")


def missing(ax, text, loc=(0.5, 0.5)):
    """Grey 'add this data' note inside the axes."""
    ax.text(*loc, text, transform=ax.transAxes, ha="center", va="center",
            fontsize=16, color=INK2, style="italic",
            bbox=dict(boxstyle="round,pad=0.5", fc="#f4f2f7", ec=MUTED,
                      ls=(0, (4, 3)), lw=1.2))


def read_columns(path, names):
    """Read named numeric columns; header row may start with '#'."""
    with open(path, newline="") as f:
        lines = [l for l in f if l.strip()]
    header = lines[0].lstrip("#").strip().split(",")
    header = [h.strip() for h in header]
    idx = [header.index(n) for n in names]
    cols = [[] for _ in names]
    for l in lines[1:]:
        if l.startswith("#"):
            continue
        parts = l.strip().split(",")
        try:
            vals = [float(parts[i]) for i in idx]
        except (ValueError, IndexError):
            continue
        for c, v in zip(cols, vals):
            c.append(v)
    return [np.array(c) for c in cols]


def end_label(ax, x, y, text, color, dy=0, ha="left"):
    ax.annotate(text, (x, y), xytext=(6, dy), textcoords="offset points",
                color=color, fontsize=18, va="center", ha=ha,
                fontweight="semibold")


# ------------------------------------------------- refractive interface ---
def refractive_bars():
    # Analytical values from tutorials/refractiveInterface2D/README.md
    GA, GB = 8.169, 16.964
    sim = None
    f = DATA / "refractive.json"
    if f.exists():
        d = json.loads(f.read_text())
        sim = (d["G_A_sim"], d["G_B_sim"])

    fig, ax = plt.subplots(figsize=(5.6, 2.9))
    x = np.array([0, 1])
    w = 0.34
    ax.bar(x - w / 2 - 0.01, [GA, GB], w, color="#cfcbd8", label="Analytical",
           zorder=3)
    if sim:
        ax.bar(x + w / 2 + 0.01, sim, w, color=THIS, label="This work",
               zorder=3)
        for xi, a, s in zip(x, (GA, GB), sim):
            err = 100 * (s - a) / a
            ax.text(xi + w / 2 + 0.01, s + 0.4, f"{err:+.1f}%", ha="center",
                    va="bottom", fontsize=17, color=INK)
    else:
        missing(ax, "Add data/refractive.json\n(simulated G_A, G_B)",
                loc=(0.5, 0.82))
    for xi, a in zip(x, (GA, GB)):
        ax.text(xi - w / 2 - 0.01, a / 2, f"{a:.2f}", ha="center",
                va="center", fontsize=16, color=INK)
    ax.set_xticks(x, ["Air side\n$n$ = 1.0", "Glass side\n$n$ = 1.5"])
    ax.set_ylabel("Lit-region G  [W/m²]")
    ax.set_ylim(0, 22)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="x", length=0)
    ax.legend(loc="upper left", ncols=2, handlelength=1.0,
              bbox_to_anchor=(0.0, 1.14))
    save(fig, "refractive-bars")


# ------------------------------------------------------ Sozzi radial G ---
SOZZI = dict(P=35.0, Larc=0.80, rL=0.010, sigma=35.67, rBody=0.0445)


def sozzi_radial():
    s = SOZZI
    r = np.linspace(s["rL"], s["rBody"], 200)
    G = s["P"] / (2 * math.pi * s["Larc"] * r) * np.exp(-s["sigma"] * (r - s["rL"]))
    to_mW_cm2 = 0.1  # 1 W/m^2 = 0.1 mW/cm^2

    fig, ax = plt.subplots(figsize=(5.8, 3.7))
    ax.plot(r * 1000, G * to_mW_cm2, color=INK, ls=(0, (5, 4)), lw=2)
    end_label(ax, r[-1] * 1000, G[-1] * to_mW_cm2,
              "Infinite line\n(analytical)", INK, dy=24)
    have = []
    for fname, color, label in (("sozzi_G_this.csv", THIS, "This work (DOM)"),
                                ("sozzi_G_fluent.csv", FLUENT, "Fluent DO")):
        f = DATA / fname
        if f.exists():
            rr, gg = read_columns(f, ["r_m", "G_W_m2"])
            # Fluent dashed, so this work's line shows through where the two coincide.
            ax.plot(rr * 1000, gg * to_mW_cm2, color=color,
                    ls=(0, (5, 3)) if color == FLUENT else "-")
            end_label(ax, rr[-1] * 1000, gg[-1] * to_mW_cm2, label, color,
                      dy=-10 if color == THIS else -32)
            have.append(fname)
    if len(have) < 2:
        need = [n for n in ("sozzi_G_this.csv", "sozzi_G_fluent.csv")
                if n not in have]
        missing(ax, "Add " + "\n".join("data/" + n for n in need)
                + "\n(r_m, G_W_m2 at lamp mid-plane)", loc=(0.64, 0.8))
    ax.set_yscale("log")
    ax.set_xlim(8, 45)
    ax.set_xlabel("Radius from lamp axis  [mm]")
    ax.set_ylabel("Fluence rate  [mW/cm²]")
    ax.set_yticks([2, 5, 10, 20, 50, 100], ["2", "5", "10", "20", "50", "100"])
    ax.minorticks_off()
    save(fig, "sozzi-radial-G", pad=0.25)


# ---------------------------------------------------- Sozzi dose CDF ---
PAPER = dict(mean=68.0, logred=1.87, k=0.1)
# Their Fig. 5 is clipped at 150 mJ/cm2 and states "10 000 or more" particles; the digitized
# CDF assumes exactly 10,000, so it stops at 150 below 1.
PAPER_FIG5_PARTICLES = 10000


def paper_fig5_cdf():
    """(dose, cumulative fraction) at the upper edge of each digitized Fig. 5 bar, or None."""
    f = DATA / "sozzi_fig5_digitized.csv"
    if not f.exists():
        return None
    lo, hi, n = np.loadtxt(f, delimiter=",", skiprows=3, unpack=True)
    return np.r_[lo[0], hi], np.r_[0.0, np.cumsum(n)] / PAPER_FIG5_PARTICLES


def sozzi_cdf():
    fig, ax = plt.subplots(figsize=(5.8, 3.7))
    stats = {}
    for fname, color, label, y_label in (("sozzi_dose_this.csv", THIS, "This work", 0.85),
                                         ("sozzi_dose_fluent.csv", FLUENT, "Fluent", 0.70)):
        f = DATA / fname
        if f.exists():
            d = np.sort(load_doses(f))
            y = np.arange(1, len(d) + 1) / len(d)
            ax.step(d, y, where="post", color=color, ls=(0, (5, 3)) if color == FLUENT else "-")
            # Labelled on the curve's left, clear of the paper's curve to its right; at different
            # heights, since the two curves lie on top of each other.
            i = np.searchsorted(y, y_label)
            ax.annotate(label, (d[i], y[i]), xytext=(-10, 0), textcoords="offset points",
                        color=color, fontsize=18, va="center", ha="right", fontweight="semibold")
            stats[label] = (d.mean(), log_reduction(d, PAPER["k"]), len(d))
    paper = paper_fig5_cdf()
    if paper is not None:
        d, y = paper
        ax.step(d, y, where="post", color=INK, ls=(0, (2, 2)), lw=2.4)
        # Labelled in the empty lower right, pointing at the curve's upper part.
        i = np.searchsorted(y, 0.85)
        ax.annotate("Sozzi & Taghipour,\nFig. 5 (to 150)", (d[i], y[i]), xytext=(165, 0.36),
                    color=INK, fontsize=16, fontweight="semibold", va="center",
                    arrowprops=dict(arrowstyle="-", color=INK, lw=1.2))
    ax.axvline(PAPER["mean"], color=INK, ls=(0, (5, 4)), lw=1.8)
    ax.text(PAPER["mean"] + 4, 0.06, "Paper mean\n68 mJ/cm²", fontsize=16,
            color=INK, va="bottom")
    if len(stats) < 2:
        need = [n for n, l in (("sozzi_dose_this.csv", "This work"),
                               ("sozzi_dose_fluent.csv", "Fluent"))
                if l not in stats]
        missing(ax, "Add " + "\n".join("data/" + n for n in need),
                loc=(0.62, 0.55))
    ax.set_xscale("log")
    ax.set_xlim(15, 450)
    ax.set_xticks([20, 50, 100, 200, 400], ["20", "50", "100", "200", "400"])
    ax.minorticks_off()
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Particle dose  [mJ/cm²]")
    ax.set_ylabel("Cumulative fraction")
    save(fig, "sozzi-dose-cdf", pad=0.25)
    # The Sozzi table's "line source" column: the analytical-G run, same flow and tracker.
    f = DATA / "sozzi_dose_analytical.csv"
    if f.exists():
        d = load_doses(f)
        stats["Line source (analytical G)"] = (d.mean(), log_reduction(d, PAPER["k"]), len(d))
    (DATA / "sozzi_stats.json").write_text(json.dumps(
        {k: dict(mean=v[0], logred=v[1], n=v[2]) for k, v in stats.items()},
        indent=2))


# ----------------------------------------------------------- scaling ---
def scaling():
    """Strong scaling (slide 11): speed-up over 4 cores, points the median of the runs at each
    core count, bars their range."""
    f = DATA / "scaling.csv"
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    cores_ref = np.array([4, 8, 16, 32, 64, 128])
    ax.plot(cores_ref, cores_ref / cores_ref[0], color=MUTED, ls=(0, (5, 4)),
            lw=1.8)
    ax.text(cores_ref[-2] * 0.92, cores_ref[-2] / cores_ref[0] * 1.12, "Ideal",
            color=MUTED, fontsize=17, ha="right", rotation=0)
    if f.exists():
        rows = list(csv.DictReader(f.open()))
        # Exclusive-node runs are plotted alone when they cover every core count;
        # otherwise they are left out so they are never mixed with shared-node runs.
        ex = [r for r in rows if r.get("exclusive") == "1"]
        sh = [r for r in rows if r.get("exclusive") != "1"]
        if ex and {r["cores"] for r in ex} >= {r["cores"] for r in sh}:
            rows = ex
        else:
            rows = sh
        cores = sorted({int(r["cores"]) for r in rows})

        def series(key):
            return {c: np.array([float(r[key]) for r in rows
                                 if int(r["cores"]) == c and r[key] != ""])
                    for c in cores}

        for key, color, label in (("flow_s", AQUA, "Flow (RANS)"),
                                  ("dom_s", THIS, "DOM")):
            t = series(key)
            base = np.median(t[cores[0]])
            med, lo, hi = [], [], []
            for c in cores:
                sp = base / t[c] * (cores[0] / cores_ref[0])
                med.append(np.median(sp))
                lo.append(sp.min())
                hi.append(sp.max())
            med, lo, hi = map(np.array, (med, lo, hi))
            ax.errorbar(cores, med, yerr=[med - lo, hi - med], color=color,
                        marker="o", ms=8, markeredgecolor="white",
                        markeredgewidth=2, capsize=4, elinewidth=1.8)
            eff = med[-1] / (cores[-1] / cores_ref[0])
            end_label(ax, cores[-1], med[-1], f"{label}  ({eff:.0%})", color,
                      dy=11 if key == "flow_s" else -11)
        # serial dose tracker: no speed-up by construction
        end_label(ax, cores[-1], 1.0,
                  f"Dose tracker  ({cores[0] / cores[-1]:.0%})", INK)
        ax.plot(cores, np.ones(len(cores)), color=INK, marker="o", ms=8,
                markeredgecolor="white", markeredgewidth=2)
    else:
        missing(ax, "Add data/scaling.csv\n(cores, rep, flow_s, dom_s, dose_s)",
                loc=(0.7, 0.2))
    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)
    ax.set_xticks(cores_ref, [str(c) for c in cores_ref])
    ax.set_yticks([1, 2, 4, 8, 16, 32], ["1", "2", "4", "8", "16", "32"])
    ax.minorticks_off()
    ax.set_xlim(3.4, 180)
    ax.set_ylim(0.6, 45)
    ax.set_xlabel("Processor cores")
    ax.set_ylabel("Speed-up vs 4 cores")
    save(fig, "scaling")


# ------------------------------------------------ 222 nm absorption ---
def absorption_222():
    """Absorption coefficient at 222 nm from user-supplied cross-sections.

    Cross-sections are the representative values used in
    tests/molecularAbsorptionSlab2D. Air at 293.15 K, 101325 Pa.
    """
    kB = 1.380649e-23
    T, p = 293.15, 101325.0
    n_air = p / (kB * T)                 # molecules/m^3
    sig_O2, sig_O3 = 6.5e-28, 4.4e-23    # m^2/molecule
    k_O2 = 0.2095 * n_air * sig_O2
    items = [("O₂ (air)", k_O2, THIS)]
    for ppb in (10, 50, 100):
        items.append((f"O₃ {ppb} ppb", ppb * 1e-9 * n_air * sig_O3, AQUA))

    # Small figure for its font sizes: slide 12 shows it 200 px tall.
    fig, ax = plt.subplots(figsize=(2.9, 2.75))
    y = np.arange(len(items))[::-1]
    for yi, (lab, k, col) in zip(y, items):
        ax.plot([1e-6, k], [yi, yi], color=GRID, lw=2, zorder=1)
        ax.plot(k, yi, "o", color=col, ms=11, markeredgecolor="white",
                markeredgewidth=2, zorder=3)
        L = 1.0 - math.exp(-k * 3.0)
        ax.text(k * 2.2, yi, f"{100*L:.2g} %", va="center", fontsize=17,
                color=INK2)
    ax.set_yticks(y, [i[0] for i in items])
    ax.set_xscale("log")
    ax.set_xlim(1e-6, 1)
    ax.set_xticks([1e-6, 1e-3, 1])
    ax.minorticks_off()
    ax.set_xlabel("κ at 222 nm  [m⁻¹]")
    ax.set_title("Fluence lost over 3 m", fontsize=17, color=INK2,
                 loc="left")
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0, labelsize=18)
    save(fig, "absorption-222")


# ----------------------------------------------------------- IES file ---
def parse_ies(path):
    txt = Path(path).read_text().splitlines()
    i = next(k for k, l in enumerate(txt) if l.startswith("TILT"))
    nums = " ".join(txt[i + 1:]).split()
    vals = [float(v) for v in nums]
    # LM-63 header: lamps, lumens, multiplier, vertical angles, horizontal angles, photometric
    # type, units, width, length, height; then ballast factor, future use, input watts.
    _, _, mult, nv, nh = vals[:5]
    nv, nh = int(nv), int(nh)
    rest = vals[13:]
    vang = np.array(rest[:nv])
    hang = np.array(rest[nv:nv + nh])
    cd = np.array(rest[nv + nh:nv + nh + nv * nh]).reshape(nh, nv) * mult
    return vang, hang, cd


def ies_polar():
    vang, hang, I = parse_ies(DATA / "ushio_b1_222nm.ies")

    def plane(c):
        j = int(np.argmin(np.abs(hang - c)))
        return I[j]

    # Small figure for its font sizes: slide 12 shows it 200 px tall.
    fig = plt.figure(figsize=(3.6, 2.35))
    ax = fig.add_subplot(projection="polar")
    ax.set_theta_zero_location("S")   # nadir (gamma = 0) points down
    th = np.deg2rad(vang)
    for (c0, c1), color, label in (((0, 180), THIS, "C0–C180"),
                                   ((90, 270), AQUA, "C90–C270")):
        a, b = plane(c0), plane(c1)
        ax.plot(np.concatenate([-th[::-1], th]),
                np.concatenate([b[::-1], a]), color=color, lw=2.5,
                label=label)
    ax.set_thetamin(-100)
    ax.set_thetamax(100)
    ax.set_rlabel_position(95)
    ax.set_rticks([60, 120])
    ax.tick_params(axis="y", labelsize=15, colors=INK2)
    ax.tick_params(axis="x", labelsize=15, colors=INK2)
    ax.set_xticks(np.deg2rad([-90, -60, -30, 0, 30, 60, 90]),
                  ["90°", "60°", "30°", "0°", "30°", "60°", "90°"])
    ax.grid(color=GRID)
    ax.spines["polar"].set_color(MUTED)
    # Legend beside the plot, not under it: slide 12 limits this figure's height, not its width.
    ax.legend(loc="center left", bbox_to_anchor=(1.15, 0.3), ncols=1,
              handlelength=1.0, fontsize=16, frameon=False)
    ax.text(0.5, 1.02, "Radiant intensity [mW/sr]", transform=ax.transAxes,
            ha="center", fontsize=16, color=INK2)
    save(fig, "ies-polar")


# ---------------------------------------------------- ray-effects room ---
ROOM_PANELS = (  # key in room_bunny.npz, title, title colour
    ("exact", "Exact (ray traced)", INK),
    ("dom72", "DO, 72 directions", THIS),
    ("dom288", "DO, 288 directions", THIS),
    ("aquaflux", "aquaflux", AQUA),
)


def save_png(fig, name, dpi=200):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / f"{name}.png", dpi=dpi, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    print(f"wrote figures/{name}.png")


def _room():
    f = DATA / "room_bunny.npz"
    return (np.load(f), json.loads((DATA / "room_bunny.json").read_text())) if f.exists() else (None, None)


def _map_axes(ax):
    ax.set_aspect("equal")
    ax.grid(False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(True)
    ax.tick_params(labelsize=14)


def room_floor_maps():
    """Irradiance over the whole floor, four methods on one linear scale, as a 2 x 2 grid."""
    d, stats = _room()
    if d is None:
        return
    from matplotlib.colors import Normalize

    xy = d["floor_tri"].reshape(-1, 2)
    connect = np.arange(len(xy)).reshape(-1, 3)
    full = stats["floor_full"]
    top = float(d["floor_exact"].max())
    norm = Normalize(0.0, top)
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 7.3), layout="constrained")
    for ax, (key, title, colour) in zip(axes.ravel(), ROOM_PANELS):
        shown = ax.tripcolor(xy[:, 0], xy[:, 1], connect, facecolors=d[f"floor_{key}"],
                             cmap="inferno", norm=norm, edgecolors="none", rasterized=True)
        _map_axes(ax)
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        ax.set_xticks([])
        ax.set_yticks([])
        if key == "exact":
            title += "\n"
        else:
            error = full[key]["L2_of_peak"]
            title += f"\nerror {100 * error:.0f} %" if error > 1e-3 else f"\nerror {100 * error:.4f} %"
        ax.set_title(title, color=colour, fontsize=19, fontweight="semibold", linespacing=1.15)
        if key.startswith("dom"):
            ax.text(0.5, 0.5, f"peaks at\n{full[key]['max_of_exact_peak']:.1f}× exact",
                    transform=ax.transAxes, ha="center", va="center", fontsize=15, color=INK,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=MUTED, alpha=0.9))
    # Room between the rows, so each lower title reads as its own panel's, not as a caption above.
    fig.get_layout_engine().set(hspace=0.08)
    bar = fig.colorbar(shown, ax=axes, shrink=0.7, pad=0.02, extend="max")
    bar.set_label("E  [µW/cm²]", fontsize=18)
    bar.ax.tick_params(labelsize=16)
    save_png(fig, "room-floor-maps")


def room_slice():
    """Fluence rate on the vertical plane through the lamp and the bunny, log scale."""
    d, _ = _room()
    if d is None:
        return
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import LogNorm

    centre, half = d["vertical_centre"], d["vertical_half"][:, None]
    corners = np.stack([centre + half * np.array(s) for s in ((-1, -1), (1, -1), (1, 1), (-1, 1))],
                       axis=1)
    top = float(np.percentile(d["vertical_exact"], 99.5))
    norm = LogNorm(top * 1e-4, top)
    panels = [p for p in ROOM_PANELS if p[0] != "dom72"]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.5), layout="constrained")
    for ax, (key, title, colour) in zip(axes, panels):
        shown = ax.add_collection(PolyCollection(
            corners, array=np.maximum(d[f"vertical_{key}"], top * 1e-4), cmap="inferno",
            norm=norm, edgecolors="none", rasterized=True))
        _map_axes(ax)
        ax.set_xlim(-2, 2)
        ax.set_ylim(0, 3)
        ax.set_xticks([-2, 0, 2])
        ax.set_yticks([0, 1, 2, 3])
        ax.set_title(title, color=colour, fontsize=18, fontweight="semibold")
        ax.set_xlabel("x  [m]", fontsize=15)
    axes[0].set_ylabel("z  [m]", fontsize=15)
    bar = fig.colorbar(shown, ax=axes, shrink=0.9, pad=0.01)
    bar.set_label("G  [µW/cm²]", fontsize=16)
    bar.ax.tick_params(labelsize=14)
    save_png(fig, "room-slice-G")


# ------------------------------------------- radiation swap on Sozzi ---
#: The background-grid fields shown: log G, fitted to the sleeve's own value where a cell has
#: corners inside it (aquaflux validation/sozzi_radiation/background_grid.py).
GRID_VARIANT = "logG_surface"


def sozzi_swap():
    """Log reduction on the Sozzi reactor with each G, relative to aquaflux's.

    One flow and one set of particle paths (the tracker is seeded and dose does not feed back
    into the motion), so only the fluence rate differs between runs. Relative values, so the
    chart shows each DO field's error against aquaflux's at every k, and, when
    data/sozzi_grid.json is present, that of aquaflux gathered on Cartesian background grids; the mesh, flow and tracker
    are the Sozzi-validation slide's, whose absolute numbers are in its table.
    """
    f = DATA / "sozzi_dose_swap.json"
    if not f.exists():
        return
    runs = json.loads(f.read_text())["runs"]
    ks = sorted(float(k) for k in runs["aquaflux"]["log_reduction"])
    base = np.array([runs["aquaflux"]["log_reduction"][f"{k:g}"] for k in ks])
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    ax.axhline(1.0, color=AQUA, lw=3, label="aquaflux, every cell")
    for key, colour, alpha, label in (("dom288", THIS, 1.0, "DO, 288 directions"),
                                      ("dom72", THIS, 0.55, "DO, 72 directions")):
        ratio = np.array([runs[key]["log_reduction"][f"{k:g}"] for k in ks]) / base
        ax.plot(ks, ratio, color=colour, alpha=alpha, marker="o", ms=6)
        end_label(ax, ks[-1], ratio[-1], label, colour, dy=8 if key == "dom288" else -10)
    # Fluent's DO on the same mesh, put into the flow by of-mesh-converter transfer
    # (data/sozzi_fluent_swap.json, from scripts/export_fluent_swap.py)
    fl = DATA / "sozzi_fluent_swap.json"
    if fl.exists():
        fruns = json.loads(fl.read_text())["runs"]
        for key, alpha, label in (("fluent288", 1.0, "Fluent DO, 288 directions"),
                                  ("fluent72", 0.55, "Fluent DO, 72 directions")):
            ratio = np.array([fruns[key]["log_reduction"][f"{k:g}"] for k in ks]) / base
            ax.plot(ks, ratio, color=FLUENT, alpha=alpha, lw=1.8, ls=(0, (5, 2)), marker="D", ms=5,
                    label=label)
    # aquaflux on Cartesian background grids, interpolated to the cells (data/sozzi_grid.json)
    g = DATA / "sozzi_grid.json"
    if g.exists():
        grids = json.loads(g.read_text())["grids"]
        for label, style in (("h6mm", (0, (1, 1.5))), ("h4mm", (0, (4, 2))), ("h3mm", (0, (7, 2)))):
            lr = grids[label]["variants"][GRID_VARIANT]["log_reduction"]
            ratio = np.array([lr[f"{k:g}"] for k in ks]) / base
            ax.plot(ks, ratio, color=AQUA, lw=1.8, ls=style, marker="s", ms=4,
                    label=f"aquaflux, {label[1:-2]} mm grid")
    ax.legend(loc="lower left", fontsize=12, frameon=False, handlelength=2.6)
    ax.set_xscale("log")
    ax.set_ylim(0.95, 1.02)
    ax.set_xlabel("inactivation constant k  [cm²/mJ]", fontsize=16)
    ax.set_ylabel("log reduction\n÷ aquaflux's", fontsize=16)
    ax.tick_params(labelsize=14)
    save(fig, "sozzi-swap")


# ------------------------------------------- Sozzi mean dose from integral(G dV) / Q ---
def sozzi_wall_occupancy():
    """Particles near the Sozzi sleeve against a uniform distribution, for each dispersion model.

    Snapshots of the deck's tracker 1.5 to 2.5 s after injection (scripts/sozzi_wall_occupancy.py).
    One injection has not yet filled the slow water next to the wall, so the well-mixed reference
    (the random displacement walk at 0.5 ms steps) sits at or below 1 there; empty shells are not
    drawn on the log axis.
    """
    f = DATA / "sozzi_wall_occupancy.json"
    if not f.exists():
        return
    d = json.loads(f.read_text())
    e = np.array(d["edges_m"]) * 1e6
    x = np.sqrt(np.maximum(e[:-1], e[1] / 2) * e[1:])  # shell centres on a log axis, um
    fig, ax = plt.subplots(figsize=(6.2, 4.3))
    ax.axhline(1.0, color=MUTED, lw=1.5, ls=(0, (5, 4)))
    # The uncorrected walk in Fluent's colour: it is the model Fluent and OpenFOAM ship.
    series = (("drw", FLUENT, "-", "o", "Random walk (OpenFOAM, Fluent)"),
              ("drw_wm", INK2, (0, (5, 3)), "o", "Random walk, well-mixed corrections"),
              ("lgv", THIS, "-", "o", "Langevin model (this work)"),
              ("rd05", INK, (0, (1.5, 2)), "o", "Well-mixed reference"))
    for key, colour, ls, mk, label in series:
        r = np.array(d["models"][key]["sleeve"]["ratio"])
        ok = r > 0
        hollow = key == "rd05"
        ax.plot(x[ok], r[ok], color=colour, ls=ls, lw=2.6, marker=mk, ms=7 if hollow else 6,
                mfc=SURFACE if hollow else colour, mew=2, label=label)
    top = d["models"]["drw"]
    share = top["sleeve"]["counts"][0] / top["particles_in_annulus"]
    ax.annotate(f"{100 * share:.0f} % of the particles\nin 0.02 % of the volume",
                (x[0], top["sleeve"]["ratio"][0]), xytext=(40, 700), textcoords="data",
                fontsize=15, color=INK, va="center",
                arrowprops=dict(arrowstyle="-", color=INK, lw=1.2))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(7, 3000)
    ax.set_ylim(0.1, 2000)
    ax.set_xticks([10, 100, 1000], ["10", "100", "1000"])
    ax.set_yticks([0.1, 1, 10, 100, 1000], ["0.1", "1", "10", "100", "1000"])
    ax.minorticks_off()
    ax.set_xlabel("Distance from the lamp sleeve  [µm]", fontsize=17)
    ax.set_ylabel("Particles ÷ uniform share\n(1 = uniform)", fontsize=17)
    ax.tick_params(labelsize=15)
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.2), ncols=2, fontsize=13,
              frameon=False, handlelength=2.4, columnspacing=1.2)
    save(fig, "sozzi-wall-occupancy", pad=0.2)


def sozzi_mean_dose():
    """Each fluence rate's mean dose from its volume integral (hollow) against the tracked one (filled).

    In a steady flow the outflow's mean dose is integral(G dV) / Q whatever the flow pattern, so a
    tracked mean to the right of its hollow marker means the particles over-sampled bright water.
    Data from scripts/sozzi_mean_dose.py.
    """
    f = DATA / "sozzi_mean_dose.json"
    if not f.exists():
        return
    d = json.loads(f.read_text())
    snappy = d["snappy_line_source"]
    rows = [(r["label"], r["integral"], r["tracked"], INK if r["group"] == "paper"
             else AQUA if r["label"].endswith("aquaflux") else THIS) for r in d["rows"]]
    rows += [(f"Line source, {name}", snappy["integral"], mean,
              FLUENT if name.startswith("uncorrected") else MUTED)
             for name, mean in snappy["tracked"].items()]
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    # The uvmesh rows first, then the snappy-mesh rows below a gap and their heading.
    n_uvmesh = len(d["rows"])
    for i, (label, integral, tracked, colour) in enumerate(rows):
        y = len(rows) - 1 - i + (-0.6 if i >= n_uvmesh else 0)
        ax.plot([integral, tracked], [y, y], color=colour, lw=2, alpha=0.6)
        ax.plot(integral, y, "o", ms=12, mfc=SURFACE, mec=colour, mew=2)
        ax.plot(tracked, y, "o", ms=12, color=colour)
        ax.text(39, y, label, ha="right", va="center", fontsize=17, color=colour)
    ax.text(71.5, len(rows) - n_uvmesh - 0.8, "tutorial snappyHexMesh mesh, same SST flow and line source:",
            ha="right", va="center", fontsize=14, color=MUTED, style="italic")
    ax.plot([], [], "o", ms=9, mfc=SURFACE, mec=INK2, mew=2, label="∫G dV / Q: the most a passive tracer can get")
    ax.plot([], [], "o", ms=9, color=INK2, label="tracked mean dose")
    ax.legend(loc="lower right", fontsize=14, frameon=False)
    ax.set_xlim(40, 72)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("mean dose  [mJ/cm²]", fontsize=17)
    ax.tick_params(labelsize=15)
    save(fig, "sozzi-mean-dose")


if __name__ == "__main__":
    refractive_bars()
    sozzi_radial()
    sozzi_cdf()
    scaling()
    absorption_222()
    ies_polar()
    room_floor_maps()
    room_slice()
    sozzi_swap()
    sozzi_wall_occupancy()
    sozzi_mean_dose()
