#!/usr/bin/env python3
"""Hand-built SVG diagrams for the IUVA Americas 2026 talk.

Run from the deck root:   python3 scripts/make_diagrams.py

Pure diagrams only. Anything that needs a render or simulation data is a
plot (make_plots.py) or a render (the render_*.py scripts).
"""

import math
import re
from xml.sax.saxutils import escape

from common import AQUA, FLUENT, INK, INK2, MUTED, THIS
from common import FIGURES as OUT

# The series colours come from common.py; these are the diagrams' own.
PURPLE = "#4B2682"     # Western purple (brand, headings)
THIS_T = "#efe9f6"     # this-work tint
FLUENT_T = "#fdeee6"
AQUA_T = "#e8f1fb"
LINE = "#c9c6d1"
PANEL = "#f6f5f8"
GOOD = "#1f7a3f"
BAD = "#b3261e"
FONT = ("'Source Sans Pro','Source Sans 3','Helvetica Neue',Helvetica,"
        "Arial,sans-serif")


class SVG:
    def __init__(self, w, h):
        self.w, self.h, self.parts = w, h, []

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke=LINE, sw=1.5, rx=10,
             dash=None, **kw):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in kw.items())
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{extra}/>')

    def text(self, x, y, s, size=20, color=INK, weight=400, anchor="start",
             italic=False, family=FONT):
        st = ' font-style="italic"' if italic else ""
        lines = s.split("\n")
        if len(lines) == 1:
            self.add(f'<text x="{x}" y="{y}" font-family="{family}" '
                     f'font-size="{size}" fill="{color}" font-weight="{weight}" '
                     f'text-anchor="{anchor}"{st}>{escape(s)}</text>')
        else:
            lh = size * 1.22
            spans = "".join(
                f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{escape(l)}</tspan>'
                for i, l in enumerate(lines))
            self.add(f'<text x="{x}" y="{y}" font-family="{family}" '
                     f'font-size="{size}" fill="{color}" font-weight="{weight}" '
                     f'text-anchor="{anchor}"{st}>{spans}</text>')

    def line(self, x1, y1, x2, y2, color=MUTED, sw=2, dash=None, arrow=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arr)"' if arrow else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                 f'stroke="{color}" stroke-width="{sw}"{d}{m}/>')

    def path(self, d, color=MUTED, sw=2, fill="none", dash=None, arrow=False):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arr)"' if arrow else ""
        self.add(f'<path d="{d}" stroke="{color}" stroke-width="{sw}" '
                 f'fill="{fill}" stroke-linecap="round"{da}{m}/>')

    def circle(self, cx, cy, r, fill=INK, stroke="none", sw=0):
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"/>')

    def check(self, x, y, ok=True, size=22):
        """Tick or cross glyph drawn as paths (no font dependence)."""
        s = size
        if ok:
            self.path(f"M{x} {y - s*0.35} l{s*0.3} {s*0.3} l{s*0.55} {-s*0.6}",
                      color=GOOD, sw=3.5)
        else:
            self.path(f"M{x+s*0.1} {y - s*0.6} l{s*0.55} {s*0.55} "
                      f"M{x+s*0.65} {y - s*0.6} l{-s*0.55} {s*0.55}",
                      color=BAD, sw=3.5)

    def save(self, name):
        defs = (
            '<defs><marker id="arr" viewBox="0 0 10 10" refX="8.5" refY="5" '
            'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker>'
            + "".join(
                f'<marker id="arr{n}" viewBox="0 0 10 10" refX="8.5" refY="5" '
                'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
                for n, c in (("A", AQUA), ("P", THIS), ("G", GOOD)))
            + f'<marker id="arrPo" viewBox="0 0 10 10" refX="8.5" refY="5" '
              'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
              f'<path d="M1,1 L9,5 L1,9" fill="none" stroke="{THIS}" stroke-width="1.6" '
              'stroke-linecap="round" stroke-linejoin="round"/></marker>'
            + '</defs>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
               f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">{defs}'
               + "".join(self.parts) + "</svg>")
        OUT.mkdir(exist_ok=True)
        (OUT / f"{name}.svg").write_text(svg)
        print(f"wrote figures/{name}.svg")


# ------------------------------------------------ library architecture ---
def architecture():
    s = SVG(1160, 440)
    # library
    s.rect(2, 2, 700, 436, fill=THIS_T, stroke=THIS, sw=2, rx=16)
    s.text(26, 42, "libopticalRadiation", 26, PURPLE, 700)
    s.text(282, 42, "DOM with Murthy–Mathur pixelation, multi-band",
           18, INK2)
    groups = [
        ("Extinction", ["constant", "species-linear", "Rayleigh", "Mie",
                        "molecular (per band)", "composite"]),
        ("Phase function", ["isotropic", "Henyey–Greenstein", "Schlick",
                            "Rayleigh", "Mie"]),
        ("Boundaries", ["Lambertian emitter", "specular / diffuse reflector",
                        "collimated beam", "IES LM-63 luminaire",
                        "refractive interface"]),
    ]
    y = 78
    for title, chips in groups:
        s.text(26, y + 26, title, 20, INK, 600)
        x = 176
        row_y = y
        for c in chips:
            w = 16 + 9.4 * len(c)
            if x + w > 684:
                x = 176
                row_y += 44
            s.rect(x, row_y, w, 36, fill="#ffffff", stroke=LINE, rx=18)
            s.text(x + w / 2, row_y + 24, c, 17, INK, 400, "middle")
            x += w + 8
        y = row_y + 56
    # hosts
    hosts = [
        ("Standalone solver", "opticalRadiationFoam",
         "Radiation-only cases, frozen flow"),
        ("fvModel", "any OpenFOAM flow solver",
         "Radiation solved alongside flow"),
        ("Solver module", "foamMultiRun, multi-region",
         "Quartz + water regions, refraction"),
    ]
    hy = 26
    for i, (t, sub, use) in enumerate(hosts):
        s.rect(780, hy, 378, 122, fill="#ffffff", stroke=THIS, sw=2)
        s.text(800, hy + 36, t, 22, INK, 700)
        s.text(800, hy + 64, sub, 18, THIS, 600)
        s.text(800, hy + 96, use, 18, INK2)
        s.line(704, 235, 776, hy + 61, color=THIS, sw=2.5, arrow=True)
        hy += 140
    s.save("architecture")


# ---------------------------------------------------------- test suite ---
def test_taxonomy():
    s = SVG(560, 460)
    cards = [
        (12, "Radiation physics",
         "vs E₂, Schwarzschild–Milne,\nBeer–Lambert, Fresnel, Mie"),
        (8, "Code-path identity",
         "fvModel, module and standalone\nmust agree bit-for-bit"),
        (5, "Dose tracking",
         "unsteady, parallel hand-off,\ninertial settling, injection"),
        (4, "Mesh generation", "uvmesh O-grid + polyhedral\npipeline"),
    ]
    pos = [(0, 0), (284, 0), (0, 190), (284, 190)]
    for (n, title, desc), (x, y) in zip(cards, pos):
        s.rect(x + 2, y + 2, 272, 176, fill=PANEL, stroke=LINE, rx=12)
        s.text(x + 22, y + 62, str(n), 52, PURPLE, 700)
        s.text(x + 22, y + 96, title, 21, INK, 600)
        s.text(x + 22, y + 128, desc, 16, INK2)
    # CI bar
    s.rect(2, 392, 556, 60, fill="#e9f5ee", stroke=GOOD, sw=1.5, rx=12)
    s.check(26, 432, True, 24)
    s.text(62, 430, "29 tests run on every pull request (GitHub Actions)",
           19, INK, 600)
    s.save("test-taxonomy")


# --------------------------------------- field-based Lagrangian library ---
def lagrangian_fields():
    # Wide and short: slide 5 shows it under a table, 130 px tall.
    s = SVG(1600, 206)
    # left: legacy list of particle objects
    s.rect(2, 2, 580, 202, fill=PANEL, stroke=LINE, rx=14)
    s.text(22, 32, "Before: a list of particle objects", 21, INK, 700)
    for i in range(4):
        x = 24 + i * 140
        s.rect(x, 46, 110, 106, fill="#ffffff", stroke=LINE, rx=8)
        s.circle(x + 55, 62, 7, fill=MUTED)
        for j, nm in enumerate(["x", "U", "d"]):
            s.text(x + 18, 94 + j * 22, nm, 17, INK2, 600)
            s.rect(x + 42, 80 + j * 22, 50, 18, fill="#f0eff4",
                   stroke="none", rx=3)
    # The legacy particle class keeps origProc and origId from its creation.
    s.text(22, 188, "Each particle carries its own state, including a persistent ID", 16, INK2)
    # right: field-based
    x0 = 600
    s.rect(x0, 2, 996, 202, fill=THIS_T, stroke=THIS, sw=2, rx=14)
    s.text(x0 + 22, 32, "OpenFOAM 13: fields over a Lagrangian mesh", 21, INK, 700)
    top, rh, n = 80, 28, 3
    hl = 1  # highlighted particle row
    # Each element of the Lagrangian mesh is one particle and records the finite-volume cell it is
    # in, so several particles can share a cell.
    cells = [7, 7, 12]
    s.rect(x0 + 16, top + hl * rh - 2, 350, rh, fill="#ffffff",
           stroke=THIS, sw=2, rx=6)
    s.text(x0 + 52, top - 8, "row", 16, INK2, 600, "middle")
    s.text(x0 + 108, top - 8, "cell", 16, INK2, 600, "middle")
    for r in range(n):
        y = top + r * rh
        s.circle(x0 + 38, y + rh / 2 - 2, 8, fill=THIS if r == hl else MUTED)
        s.text(x0 + 60, y + rh / 2 + 3, str(r + 1), 15, INK2)
        s.text(x0 + 108, y + rh / 2 + 3, str(cells[r]), 15, INK2, 400, "middle")
    for c, nm in enumerate(["U", "d", "D"]):
        x = x0 + 150 + c * 72
        s.text(x + 29, top - 8, nm, 18, INK2, 600, "middle")
        for r in range(n):
            s.rect(x, top + r * rh + 2, 58, rh - 8,
                   fill="#ffffff" if r != hl else THIS_T,
                   stroke=LINE if r != hl else THIS, sw=1.5, rx=3)
    # Dose is not a field the shipped library computes: in this design it would be one more
    # per-particle field, written by custom code.
    xd = x0 + 150 + 2 * 72
    s.rect(xd - 7, top - 42, 72, n * rh + 40, stroke=INK2, sw=1.5, rx=6, dash="5 4")
    s.text(xd + 29, top - 26, "custom", 14, INK2, 600, "middle", italic=True)
    # LagrangianMesh::partition() re-sorts every field's rows by state as particles reach patches
    # or are removed, so a row number is a position, not an identity.
    s.text(x0 + 16, 188, "One particle = one row; several can share a mesh cell. "
           "Rows are re-sorted as particles move, so there is no particle ID", 16, INK2)
    # right-hand text
    tx = x0 + 420
    s.text(tx, 72, "Same idea as finite volume", 18, INK, 700)
    lines = ["Fields hold the state",
             "Models: injection, forces, dispersion",
             "Patches: rebound, stick, escape"]
    y = 104
    for t in lines:
        s.check(tx, y, True, 20)
        s.text(tx + 34, y - 2, t, 17, INK)
        y += 28
    s.save("lagrangian-fields")


# --------------------------------------------------- open-source cards ---
def oss_benefits():
    s = SVG(560, 440)
    cards = [
        ("1", "Inspect", "Read the physics, not just the manual.\n29 tests run on every pull request."),
        ("2", "Reproduce", "Pinned OpenFOAM 13 and a Docker image.\nThe Sozzi case and tutorials are public."),
        ("3", "Scale", "Hardware is the only limit on cores\nand concurrent runs, cloud or cluster."),
    ]
    for i, (n, title, desc) in enumerate(cards):
        y = 2 + i * 148
        s.rect(2, y, 556, 136, fill=THIS_T, stroke=THIS, sw=1.8, rx=12)
        s.text(30, y + 84, n, 58, THIS, 700)
        s.text(84, y + 44, title, 28, INK, 700)
        s.text(84, y + 80, desc, 22, INK2)
    s.save("oss-benefits")


# ------------------------------------------------------ aquaflux gather ---
def aquaflux_gather():
    """How aquaflux forms G at a point: a sum over lamp facets, each shadow-tested."""
    s = SVG(560, 390)

    # Lamp window: a row of emitting triangles; the shaded one is the facet followed below.
    xs = [150, 205, 260, 315, 370]
    for i, (a, b) in enumerate(zip(xs, xs[1:])):
        up = i % 2 == 0
        pts = f"{a},{52 if up else 30} {b},{52 if up else 30} {(a + b) / 2},{30 if up else 52}"
        fill = "#bcd6f5" if i == 2 else AQUA_T
        s.add(f'<polygon points="{pts}" fill="{fill}" stroke="{AQUA}" stroke-width="2"/>')
    rt(s, 260, 20, "lamp facets j, radiance L_j(d) from the IES file", 17, AQUA, 600, "middle")
    x, y = 300, 320
    # The exact solid angle of that facet, seen from x.
    s.add(f'<polygon points="{x},{y} 260,52 315,52" fill="{AQUA}" fill-opacity="0.18" '
          f'stroke="{AQUA}" stroke-width="1.5"/>')
    rt(s, 322, 175, "\u03a9_j(x): exact solid angle", 17, AQUA, 600)
    # Another facet's ray, blocked by a strut of the geometry lying across it.
    s.line(x, y, 177, 45, color=MUTED, sw=2, dash="6 5")
    s.add('<polygon points="208,196 256,170 264,186 216,212" fill="#cfccd6" '
          f'stroke="{MUTED}" stroke-width="2"/>')
    s.check(222, 166, ok=False, size=22)
    rt(s, 16, 250, "V_j = 0: blocked by a", 16, INK2)
    s.text(16, 271, "triangle of the STL or CAD", 16, INK2, 400)
    # A reflecting wall facet.
    s.rect(512, 110, 14, 150, fill=PANEL, stroke=MUTED, sw=2, rx=2)
    s.line(x, y, 510, 190, color=MUTED, sw=2)
    s.text(470, 290, "reflecting facets:", 16, INK2, 400, "middle")
    s.text(470, 310, "radiosity B, gathered", 16, INK2, 400, "middle")
    s.text(470, 330, "the same way", 16, INK2, 400, "middle")
    s.circle(x, y, 7, fill=INK)
    s.text(x, y + 30, "x: any point (cell, floor, sensor)", 16, INK, 600, "middle")
    rt(s, x, 382, "G(x) = \u03a3_j L_j \u03a9_j(x) V_j(x)", 22, PURPLE, 700, "middle")
    s.save("aquaflux-gather")



# ------------------------------------------- aquaflux model (backup set) ---
SUMC = AQUA     # emitted radiance term
OMEGA = THIS    # solid angle term
TRANS = GOOD    # transmittance and visibility terms


def halo(s, x, y, txt, size=22, color=INK, weight=600, anchor="start"):
    """Text with a white outline, legible over lines and fills."""
    s.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
          f'fill="{color}" font-weight="{weight}" text-anchor="{anchor}" '
          f'stroke="#ffffff" stroke-width="6" paint-order="stroke" '
          f'stroke-linejoin="round">{escape(txt)}</text>')


def rt(s, x, y, markup, size=18, color=INK, weight=400, anchor="start"):
    """Text where `_j` or `_{jk}` becomes a subscript."""
    parts, pos = [], 0
    for m in re.finditer(r"_\{([^}]*)\}|_(.)", markup):
        parts.append((markup[pos:m.start()], False))
        parts.append((m.group(1) or m.group(2), True))
        pos = m.end()
    parts.append((markup[pos:], False))
    spans = "".join(
        f'<tspan baseline-shift="sub" font-size="{size * 0.7:.0f}">{escape(t)}</tspan>'
        if sub else f"<tspan>{escape(t)}</tspan>" for t, sub in parts if t)
    s.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
          f'fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{spans}</text>')


def carrow(s, x1, y1, x2, y2, mk, color, sw=2.5, dash=None, gap=10, both=False):
    """Arrow with a coloured head, stopping `gap` px short of the end point."""
    L = math.hypot(x2 - x1, y2 - y1)
    ex, ey = x2 - (x2 - x1) / L * gap, y2 - (y2 - y1) / L * gap
    d = f' stroke-dasharray="{dash}"' if dash else ""
    st = f' marker-start="url(#arr{mk})"' if both else ""
    s.add(f'<line x1="{x1}" y1="{y1}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{color}" '
          f'stroke-width="{sw}"{d} marker-end="url(#arr{mk})"{st}/>')


def model_gather():
    """Backup: the gather sum for one facet, with each factor colour-keyed to the equation."""
    s = SVG(1180, 370)
    x, y = 520, 310
    # lamp surface split into triangles
    xs = [100, 176, 252, 328, 404, 480, 556]
    for i, (a, b) in enumerate(zip(xs, xs[1:])):
        up = i % 2 == 0
        pts = f"{a},{84 if up else 30} {b},{84 if up else 30} {(a + b) / 2},{30 if up else 84}"
        s.add(f'<polygon points="{pts}" fill="{AQUA_T}" stroke="{AQUA}" stroke-width="2"/>')
    s.text(330, 18, "lamp surface, split into triangular facets", 18, AQUA, 600, "middle")
    # cone of facet j (its solid angle seen from x)
    s.add(f'<polygon points="{x},{y} 328,30 404,30" fill="{OMEGA}" fill-opacity="0.13"/>')
    s.add(f'<polygon points="328,30 404,30 366,84" fill="{OMEGA}" fill-opacity="0.45" '
          f'stroke="{OMEGA}" stroke-width="2"/>')
    s.line(x, y, 328, 30, color=OMEGA, sw=1.5, dash="5 4")
    s.line(x, y, 404, 30, color=OMEGA, sw=1.5, dash="5 4")
    s.line(486, 158, 436, 140, color=OMEGA, sw=1.2)
    s.circle(436, 140, 3, fill=OMEGA)
    rt(s, 490, 168, "Ω_j", 24, OMEGA, 700)
    # facet j: normal, ray, angle
    cx, cy = 366, 48
    carrow(s, cx, cy, cx, 130, "A", AQUA, 2.5, gap=0)
    rt(s, cx - 8, 150, "n_j", 18, AQUA, 600, "end")
    s.line(cx, cy, x, y, color=TRANS, sw=3)
    s.path(f"M{cx} {cy + 55} A55 55 0 0 0 {cx + 55 * 0.507:.1f} {cy + 55 * 0.862:.1f}",
           color=AQUA, sw=2)
    rt(s, 382, 128, "θ_j", 20, AQUA, 600)
    s.line(580, 196, 446, 184, color=TRANS, sw=1.2)
    s.circle(446, 184, 3, fill=TRANS)
    rt(s, 584, 202, "r_j", 20, TRANS, 600)
    rt(s, 540, 250, "T_j = exp(−a r_j)", 19, TRANS, 600)
    s.text(540, 270, "medium absorbs a little", 16, INK2)
    # blocked facet k
    s.line(214, 66, x, y, color=MUTED, sw=2, dash="6 5")
    s.add(f'<polygon points="336,227 398,149 404,154 342,232" fill="#cfccd6" '
          f'stroke="{MUTED}" stroke-width="2"/>')
    s.check(292, 212, ok=False, size=26)
    rt(s, 40, 262, "V_k = 0: another surface of the", 18, BAD, 600)
    s.text(40, 284, "CAD/STL model blocks facet k", 18, BAD, 600)
    # receiver
    s.circle(x, y, 8, fill=INK)
    rt(s, x, y + 30, "x", 22, INK, 700, "middle")
    s.text(x, 358, "x: any receiver point in the medium (cell centre, probe)", 17, INK, 600, "middle")
    # cards
    cards = [
        (SUMC, "M_j g_j(cos θ_j)", "emitted toward x",
         "exitance × how bright the facet is", "at angle θ_j from its normal"),
        (OMEGA, "Ω_j(x)", "apparent size",
         "solid angle: how much of x’s surroundings", "the facet covers, nearer is bigger"),
        (TRANS, "T_j V_j", "what survives the trip",
         "transmittance (absorption, 0 to 1) ×", "visibility (0 to 1; 0 = blocked)"),
    ]
    for i, (c, big, small, l1, l2) in enumerate(cards):
        yy = 18 + i * 112
        s.rect(700, yy, 470, 98, fill="#ffffff", stroke=c, sw=2.5, rx=12)
        rt(s, 720, yy + 36, big, 26, c, 700)
        s.text(1150, yy + 36, small, 20, INK, 600, "end")
        rt(s, 720, yy + 64, l1, 18, INK2)
        rt(s, 720, yy + 86, l2, 18, INK2)
    s.save("model-gather")


def model_emission_solid_angle():
    """Backup: emission profile (left) and the solid angle of a triangle (right)."""
    s = SVG(1180, 342)
    # ---- left: polar plots of radiance for one facet
    s.text(290, 26, "Emission profile: brightness by direction", 22, INK, 700, "middle")
    ox, oy = 290, 60
    s.line(ox - 100, oy, ox + 100, oy, color=AQUA, sw=7)
    s.text(ox - 108, oy + 5, "lamp facet", 17, AQUA, 600, "end")
    carrow(s, ox, oy, ox, 245, "A", MUTED, 2, dash="5 4", gap=0)
    rt(s, ox + 8, 250, "n", 18, INK2, 600)
    s.path(f"M{ox - 55} {oy} A55 55 0 0 0 {ox + 55} {oy} Z", color=AQUA, sw=2.5,
           fill=AQUA_T)
    pts = []
    for d in range(-90, 91, 4):
        ph = math.radians(d)
        r = 165 * math.cos(ph) ** 4
        pts.append((ox + r * math.sin(ph), oy + r * math.cos(ph)))
    s.path("M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts) + " Z",
           color=OMEGA, sw=2.5)
    ph = math.radians(30)
    s.line(ox, oy, ox + 195 * math.sin(ph), oy + 195 * math.cos(ph), color=MUTED,
           sw=1.5, dash="5 4")
    for r in (55, 165 * math.cos(ph) ** 4):
        s.circle(ox + r * math.sin(ph), oy + r * math.cos(ph), 5, fill=INK)
    # normal drawn last so the Lambertian fill and lobe do not cover it
    carrow(s, ox, oy, ox, 245, "A", MUTED, 2, dash="5 4", gap=0)
    rt(s, ox + 8, 250, "n", 18, INK2, 600)
    s.path(f"M{ox} {oy + 70} A70 70 0 0 0 {ox + 70 * 0.5:.1f} {oy + 70 * 0.866:.1f}",
           color=INK2, sw=1.8)
    rt(s, ox + 24, oy + 94, "θ", 19, INK2, 600, "middle")
    s.text(372, 108, "Lambertian", 19, AQUA, 700)
    s.text(372, 128, "same radiance every way", 17, INK2)
    s.text(372, 178, "Cosine power (n = 5)", 19, OMEGA, 700)
    s.text(372, 198, "brighter along the normal", 17, INK2)
    s.text(ox, 300, "IES file: measured profile of a real lamp (also depends on azimuth)",
           17, INK2, 400, "middle")
    s.text(ox, 322, "The curve length in a direction is g(cos θ)", 17, INK2, 400, "middle")
    s.line(590, 20, 590, 320, color=LINE, sw=1.5)
    # ---- right: solid angle of a triangle
    s.text(900, 26, "Solid angle: how big a facet looks from x", 22, INK, 700, "middle")
    X, Y, R = 910, 290, 100
    A, B, C = (740, 74), (1090, 74), (930, 134)
    s.add(f'<polygon points="{A[0]},{A[1]} {B[0]},{B[1]} {C[0]},{C[1]}" fill="{AQUA_T}" '
          f'stroke="{AQUA}" stroke-width="2.5"/>')
    s.text(910, 62, "lamp facet (one triangle)", 17, AQUA, 600, "middle")
    uv = []
    for P in (A, B, C):
        dx, dy = P[0] - X, P[1] - Y
        L = math.hypot(dx, dy)
        uv.append((X + dx / L * R, Y + dy / L * R))
        s.line(X, Y, P[0], P[1], color=MUTED, sw=1.5, dash="5 4")
    a, b, c = uv
    s.path(f"M{X - R} {Y} A{R} {R} 0 0 1 {X + R} {Y}", color=MUTED, sw=1.5, dash="3 4")
    s.path(f"M{a[0]:.1f} {a[1]:.1f} A{R} {R} 0 0 1 {c[0]:.1f} {c[1]:.1f} "
           f"A{R} {R} 0 0 1 {b[0]:.1f} {b[1]:.1f} Q{X} {Y - 66} {a[0]:.1f} {a[1]:.1f} Z",
           color=OMEGA, sw=2.5, fill=OMEGA + "66")
    for P, lab, dx, dy, anc in ((a, "a", -10, 0, "end"), (b, "b", 10, 0, "start"),
                                (c, "c", 9, 4, "start")):
        carrow(s, X, Y, P[0], P[1], "Po", OMEGA, 2, gap=0)
        s.circle(P[0], P[1], 4, fill=OMEGA)
        s.text((X + P[0]) / 2 + dx, (Y + P[1]) / 2 + dy, lab, 20, OMEGA, 700, anc,
               italic=True)
    for P, lab, dx, dy in ((A, "A", -14, -6), (B, "B", 14, -6), (C, "C", 0, 22)):
        s.text(P[0] + dx, P[1] + dy, lab, 19, AQUA, 700, "middle", italic=True)
    s.circle(X, Y, 8, fill=INK)
    rt(s, X, Y + 28, "x", 22, INK, 700, "middle")
    s.text(1022, 292, "sphere of radius", 16, MUTED)
    s.text(1022, 311, "R = 1 around x", 16, MUTED)
    s.line(1024, 172, 968, 207, color=OMEGA, sw=1.5)
    rt(s, 1030, 168, "Ω = area / R²", 19, OMEGA, 700)
    s.text(1030, 190, "(R = 1, so Ω = area)", 17, OMEGA)
    s.text(630, 214, "a, b, c: unit vectors", 16, INK2)
    s.text(630, 233, "from x toward the", 16, INK2)
    s.text(630, 252, "corners A, B, C:", 16, INK2)
    s.text(630, 271, "a = (A − x)/|A − x|", 16, INK2)
    s.text(630, 300, "Far away Ω ≈ A cosθ/r²;", 16, INK2)
    s.text(630, 318, "close up that fails, so", 16, INK2)
    s.text(630, 336, "aquaflux uses exact Ω", 16, INK2)
    s.save("model-emission-solid-angle")


def model_radiosity():
    """Backup: radiosity solve (left) then gather at x (right)."""
    s = SVG(1180, 360)

    def room(dx, hi_floor=None, hi_wall=None):
        s.add(f'<g transform="translate({dx},0)">')
        s.rect(30, 60, 500, 230, fill="none", stroke=LINE, sw=1.5, rx=2)
        for k in range(10):
            col = THIS if k == hi_floor else MUTED
            s.line(33 + 50 * k, 290, 77 + 50 * k, 290, color=col, sw=7)
        for k in range(5):
            for wx in (30, 530):
                col = THIS if (wx == 530 and k == hi_wall) else MUTED
                s.line(wx, 63 + 46 * k, wx, 105 + 46 * k, color=col, sw=7)
        s.line(230, 62, 330, 62, color=AQUA, sw=9)
        s.text(280, 50, "lamp", 17, AQUA, 600, "middle")
        s.add("</g>")

    s.text(280, 24, "1. Solve for the radiosity B of every surface", 22, INK, 700, "middle")
    room(0, hi_floor=3, hi_wall=2)
    carrow(s, 280, 70, 205, 285, "A", AQUA, 2.5)
    carrow(s, 300, 70, 524, 170, "A", AQUA, 2.5)
    carrow(s, 215, 280, 520, 178, "P", THIS, 3, both=True, gap=6)
    rt(s, 170, 318, "facet i", 18, THIS, 700, "middle")
    rt(s, 548, 160, "facet j", 18, THIS, 700, "start")
    rt(s, 356, 205, "F_{ij}", 20, THIS, 700, "middle")
    s.text(280, 344, "each facet re-emits the fraction ρ of all light that reaches it",
           17, INK2, 400, "middle")
    # right panel
    s.line(590, 20, 590, 345, color=LINE, sw=1.5)
    s.text(900, 24, "2. Gather at x, adding the reflected light as lamps", 22, INK, 700, "middle")
    room(620)
    xx, yy = 620 + 280, 215
    for sx in (250, 280, 310):
        carrow(s, 620 + sx, 70, xx, yy, "A", AQUA, 2.5, gap=14)
    for fx, fy in ((620 + 130, 285), (620 + 430, 285), (620 + 32, 150), (620 + 528, 220)):
        carrow(s, fx, fy, xx, yy, "P", THIS, 2.5, gap=14)
    s.circle(xx, yy, 8, fill=INK)
    rt(s, xx, yy + 32, "x", 22, INK, 700, "middle")
    carrow(s, 640, 316, 674, 316, "A", AQUA, 2.5, gap=0)
    s.text(684, 322, "direct light from the lamp (exitance M)", 17, AQUA, 600)
    carrow(s, 640, 340, 674, 340, "P", THIS, 2.5, gap=0)
    s.text(684, 346, "reflected light from the surfaces (exitance B \u2212 M)", 17, THIS, 600)
    s.save("model-radiosity")


def model_occlusion():
    """Backup: RayCast vs Silhouette occlusion for an extended lamp and a blocker."""
    s = SVG(640, 490)
    L1, L2, B1, B2, FY = (220, 40), (400, 40), (210, 200), (410, 200), 290

    def hit(P, Q):
        return P[0] + (Q[0] - P[0]) * (FY - P[1]) / (Q[1] - P[1])

    e1, e2, e3, e4 = hit(L2, B1), hit(L1, B1), hit(L2, B2), hit(L1, B2)
    # floor bands: lit / penumbra / umbra / penumbra / lit
    bands = [(20, e1, "#fff1bf", "lit"), (e1, e2, "#cfc3e6", "penumbra"),
             (e2, e3, "#8a8894", "umbra"), (e3, e4, "#cfc3e6", "penumbra"),
             (e4, 620, "#fff1bf", "lit")]
    for a, b, col, lab in bands:
        s.add(f'<rect x="{a:.1f}" y="{FY}" width="{b - a:.1f}" height="12" fill="{col}"/>')
        s.text((a + b) / 2, FY + 34, lab, 17, INK2, 600, "middle")
    for P, Q in ((L2, B1), (L2, B2), (L1, B1), (L1, B2)):
        s.line(P[0], P[1], hit(P, Q), FY, color=LINE, sw=1.5, dash="5 4")
    s.line(20, FY, 620, FY, color=MUTED, sw=2)
    s.line(L1[0], 40, L2[0], 40, color=AQUA, sw=7)
    s.text(310, 26, "lamp facet (extended source)", 17, AQUA, 600, "middle")
    s.line(B1[0], B1[1], B2[0], B2[1], color=INK2, sw=9)
    s.text(B2[0] + 14, B2[1] + 6, "blocker", 17, INK2, 600)
    # receiver R in the left penumbra
    R = (140, FY)
    C = (310, 40)
    # silhouette: visible part of the facet as seen from R
    def proj(Bp):
        return R[0] + (Bp[0] - R[0]) * (FY - 40) / (FY - Bp[1])
    a_, b_ = sorted((proj(B1), proj(B2)))
    hid0, hid1 = max(a_, L1[0]), min(b_, L2[0])
    vis = 1 - max(0, hid1 - hid0) / (L2[0] - L1[0])
    s.line(hid0, 40, hid1, 40, color="#b5b3bd", sw=7)
    s.line(L1[0], 40, hid0, 40, color=THIS, sw=7)
    s.line(R[0], R[1], hid0, 40, color=THIS, sw=1.8, dash="6 4")
    s.line(R[0], R[1], L1[0], 40, color=THIS, sw=1.8)
    # raycast: one ray to the centroid
    s.line(R[0], R[1], C[0], C[1], color=GOOD, sw=3)
    s.circle(C[0], C[1], 5, fill=GOOD)
    s.circle(R[0], R[1], 8, fill=INK)
    s.text(R[0] - 12, R[1] - 10, "x", 20, INK, 700, "end")
    s.text(24, 90, "RayCast", 19, GOOD, 700)
    s.text(24, 111, "one ray to the", 17, INK2)
    s.text(24, 131, "facet centre: clear,", 17, INK2)
    s.text(24, 151, "so V = 1", 17, INK2)
    s.text(424, 90, "Silhouette", 19, THIS, 700)
    s.text(424, 111, "blocker hides part of", 17, INK2)
    s.text(424, 131, f"the facet: V = {vis:.2f}", 17, INK2)
    # plot of V along the floor
    y1, y0 = 360, 450
    s.line(20, y0, 620, y0, color=MUTED, sw=1.5)
    s.line(20, y1, 20, y0, color=MUTED, sw=1.5)
    s.text(14, y1 + 5, "1", 16, INK2, 400, "end")
    s.text(14, y0 + 5, "0", 16, INK2, 400, "end")
    s.text(30, y1 - 10, "visibility V along the floor", 17, INK, 600)

    def vfun(x):
        pa, pb = sorted((x + (B1[0] - x) * (FY - 40) / (FY - B1[1]),
                         x + (B2[0] - x) * (FY - 40) / (FY - B2[1])))
        ov = max(0, min(pb, L2[0]) - max(pa, L1[0]))
        return 1 - ov / (L2[0] - L1[0])
    ca, cb = hit(C, B1), hit(C, B2)
    rc = [(20, 1), (ca, 1), (ca, 0), (cb, 0), (cb, 1), (620, 1)]
    s.path("M" + " L".join(f"{x:.1f} {y0 - v * (y0 - y1):.1f}" for x, v in rc),
           color="#9fd3b0", sw=7)
    sil = [(x, vfun(x)) for x in range(20, 621, 4)]
    s.path("M" + " L".join(f"{x:.1f} {y0 - v * (y0 - y1):.1f}" for x, v in sil),
           color=THIS, sw=2.5)
    s.circle(R[0], y1, 5, fill=GOOD)
    s.circle(R[0], y0 - vis * (y0 - y1), 5, fill=THIS)
    s.line(R[0], R[1] + 14, R[0], y1 - 2, color=MUTED, sw=1, dash="2 4")
    s.add('<rect x="250" y="368" width="14" height="7" fill="#9fd3b0"/>')
    s.text(272, 376, "RayCast: steps", 16, GOOD, 600)
    s.line(250, 394, 264, 394, color=THIS, sw=2.5)
    s.text(272, 399, "Silhouette: ramps", 16, THIS, 600)
    s.save("model-occlusion")


def model_voxel():
    """Backup: a ray through a voxel grid, split at grid-plane crossings."""
    s = SVG(640, 526)
    ox, oy, cs, cols, rows = 40, 50, 90, 6, 4
    for c in range(cols):
        for r in range(rows):
            op = 0.05 + 0.5 * ((c / (cols - 1)) * 0.6 + (r / (rows - 1)) * 0.4)
            s.add(f'<rect x="{ox + c * cs}" y="{oy + r * cs}" width="{cs}" height="{cs}" '
                  f'fill="{THIS}" fill-opacity="{op:.2f}" stroke="{LINE}" stroke-width="1.5"/>')
    P0, P1 = (50, 36), (470, 405)
    dx, dy = P1[0] - P0[0], P1[1] - P0[1]
    ts = []
    for k in range(cols + 1):
        t = (ox + k * cs - P0[0]) / dx
        ts.append(t)
    for m in range(rows + 1):
        ts.append((oy + m * cs - P0[1]) / dy)
    pts = []
    for t in sorted(ts):
        x, y = P0[0] + dx * t, P0[1] + dy * t
        if 0 < t < 1 and ox <= x <= ox + cols * cs and oy <= y <= oy + rows * cs:
            pts.append(t)
    s.line(P0[0], P0[1], P1[0], P1[1], color=INK, sw=2.5)
    k = 3  # the segment that is highlighted and labelled
    s.line(P0[0] + dx * pts[k], P0[1] + dy * pts[k], P0[0] + dx * pts[k + 1],
           P0[1] + dy * pts[k + 1], color="#6fbf8a", sw=9)
    s.line(P0[0] - 22, 36, P0[0] + 22, 36, color=AQUA, sw=7)
    s.text(P0[0] + 34, 30, "lamp facet", 17, AQUA, 600)
    allp = pts + [1.0]
    for a, b in zip(allp, allp[1:]):
        m = (a + b) / 2
        mx, my = P0[0] + dx * m, P0[1] + dy * m
        s.add(f'<rect x="{mx - 5:.1f}" y="{my - 5:.1f}" width="10" height="10" '
              f'fill="{GOOD}" stroke="#ffffff" stroke-width="1.5"/>')
    for t in pts:
        s.circle(P0[0] + dx * t, P0[1] + dy * t, 6, fill="#ffffff", stroke=INK, sw=2.5)
    s.circle(P1[0], P1[1], 8, fill=INK)
    rt(s, P1[0] + 14, P1[1] + 22, "x", 22, INK, 700)
    # label that segment: s_k, s_{k+1}, midpoint
    xa, ya = P0[0] + dx * pts[k], P0[1] + dy * pts[k]
    xb, yb = P0[0] + dx * pts[k + 1], P0[1] + dy * pts[k + 1]
    rt(s, xa - 10, ya + 24, "s_k", 20, INK, 700, "end")
    rt(s, xb - 10, yb + 24, "s_{k+1}", 20, INK, 700, "end")
    xm, ym = (xa + xb) / 2, (ya + yb) / 2
    rt(s, xm + 16, ym - 12, "s_{k+½}", 20, GOOD, 700)
    # legend
    s.circle(46, 450, 6, fill="#ffffff", stroke=INK, sw=2.5)
    rt(s, 62, 456, "where the ray crosses a sample plane (s_0 … s_n)", 17, INK2)
    s.add(f'<rect x="41" y="469" width="10" height="10" fill="{GOOD}"/>')
    s.text(62, 479, "midpoint of each piece (third sample for Simpson\u2019s rule)", 17, INK2)
    rt(s, 62, 498, "\u0394s_k = s_{k+1} \u2212 s_k: length of one piece", 17, INK2)
    s.text(62, 517, "grid lines pass through the sample points (cell centres)", 17, INK2)
    s.save("model-voxel")


def model_mask():
    """Backup: the two pre-processing speed-ups behind the occlusion mask."""
    s = SVG(620, 535)
    # ---- panel A: RayCast with a uniform grid over the triangles
    s.text(10, 22, "RayCast with a grid: walk only the cells the ray crosses", 19, GOOD, 700)
    ox, oy, cs, cols, rows = 20, 44, 34, 9, 5
    S, E = (40, 50), (296, 210)
    crossed = set()
    for i in range(801):
        u = i / 800
        x, y = S[0] + (E[0] - S[0]) * u, S[1] + (E[1] - S[1]) * u
        crossed.add((int((x - ox) // cs), int((y - oy) // cs)))
    for c in range(cols):
        for r in range(rows):
            fill = "#dff1e5" if (c, r) in crossed else "#ffffff"
            s.add(f'<rect x="{ox + c * cs}" y="{oy + r * cs}" width="{cs}" height="{cs}" '
                  f'fill="{fill}" stroke="{LINE}" stroke-width="1.2"/>')
    tris = [(1, 0, 20), (2, 2, 70), (3, 1, 120), (5, 0, 30), (6, 2, 100), (7, 1, 60),
            (8, 3, 140), (1, 3, 10), (3, 4, 80), (4, 2, 150), (5, 3, 40), (7, 4, 110),
            (0, 2, 130), (2, 4, 25), (6, 4, 55), (4, 0, 95), (8, 0, 15), (0, 4, 75)]
    for c, r, deg in tris:
        cx, cy = ox + (c + 0.5) * cs, oy + (r + 0.5) * cs
        a = math.radians(deg)
        col = GOOD if (c, r) in crossed else "#b5b3bd"
        s.line(cx - 11 * math.cos(a), cy - 11 * math.sin(a), cx + 11 * math.cos(a),
               cy + 11 * math.sin(a), color=col, sw=3.5)
    s.line(S[0], S[1], E[0], E[1], color=INK, sw=2)
    s.line(S[0] - 18, S[1] - 6, S[0] + 18, S[1] - 6, color=AQUA, sw=6)
    s.circle(E[0], E[1], 7, fill=INK)
    s.text(E[0] + 12, E[1] + 20, "x", 20, INK, 700)
    s.text(336, 80, "green: the triangles tested", 17, GOOD, 600)
    s.text(336, 102, "grey: skipped", 17, INK2, 600)
    s.text(336, 134, "the walk stops at the", 17, INK2)
    s.text(336, 154, "first triangle that blocks", 17, INK2)
    s.text(336, 188, "Sozzi vessel wall: about 52", 17, INK2)
    s.text(336, 208, "triangles tested per ray, not 53,500", 17, INK2)
    s.line(10, 250, 610, 250, color=LINE, sw=1.5)
    # ---- panel B: Silhouette cone cull
    d = 250
    s.text(10, d + 28, "Silhouette: discard blockers that cannot overlap the source", 19, THIS, 700)
    X, Y = 50, d + 130
    s.add(f'<polygon points="{X},{Y} 520,{d + 90} 520,{d + 170}" fill="{AQUA}" fill-opacity="0.12"/>')
    s.line(X, Y, 520, d + 90, color=AQUA, sw=1.3, dash="5 4")
    s.line(X, Y, 520, d + 170, color=AQUA, sw=1.3, dash="5 4")
    s.line(520, d + 90, 520, d + 170, color=AQUA, sw=7)
    s.text(520, d + 82, "source facet", 17, AQUA, 600, "middle")
    s.circle(X, Y, 8, fill=INK)
    s.text(X, Y + 28, "x", 20, INK, 700, "middle")
    blockers = [(250, 372, 410, True), (380, 300, 335, False), (330, 425, 460, False),
                (450, 395, 440, True), (575, 355, 400, False)]
    for bx, y0, y1, keep in blockers:
        s.line(bx, y0, bx, y1, color=GOOD if keep else "#b5b3bd", sw=6)
    s.line(30, 492, 52, 492, color=GOOD, sw=6)
    s.text(62, 498, "cone overlaps the source: clipped exactly", 17, GOOD, 600)
    s.line(30, 516, 52, 516, color="#b5b3bd", sw=6)
    s.text(62, 522, "cannot overlap, or lies beyond the source: skipped", 17, INK2, 600)
    s.save("model-mask")


def model_overview():
    """Backup: inputs, the three steps, and outputs of the aquaflux radiation model."""
    s = SVG(1160, 450)
    GEO_T, GEO = "#eceaf1", MUTED

    def box(x, y, w, h, title, lines, fill, stroke, tcol=INK, tsize=19, lsize=16):
        s.rect(x, y, w, h, fill=fill, stroke=stroke, sw=2, rx=10)
        ty = y + 26
        if title:
            s.text(x + 14, ty, title, tsize, tcol, 700)
            ty += 24
        for ln in lines:
            s.text(x + 14, ty, ln, lsize, INK2)
            ty += 20

    def arrow(x1, y1, x2, y2, col=MUTED):
        carrow(s, x1, y1, x2, y2, "A" if col == AQUA else "P" if col == THIS else "G", col, 2.5, gap=2)

    # column titles
    s.text(180, 26, "Inputs", 23, INK, 700, "middle")
    s.text(590, 26, "What the model does", 23, INK, 700, "middle")
    s.text(990, 26, "Outputs", 23, INK, 700, "middle")
    # inputs: geometry (frozen at the build)
    s.text(10, 60, "Geometry: fixed when the model is built", 17, INK2, 700)
    box(10, 70, 340, 52, "", ["Surface triangles (STL file):", "lamps, walls, sleeves"], GEO_T, GEO)
    box(10, 128, 340, 52, "", ["Receiver points x", "(cell centres, probes)"], GEO_T, GEO)
    box(10, 186, 340, 36, "", ["Shapes of the bodies in the way"], GEO_T, GEO)
    # inputs: optics (supplied every call)
    s.text(10, 256, "Optics: supplied at every call", 17, AQUA, 700)
    box(10, 266, 340, 36, "", ["Emission M, profile g, point power P"], AQUA_T, AQUA)
    box(10, 308, 340, 36, "", ["Reflectance ρ"], AQUA_T, AQUA)
    box(10, 350, 340, 36, "", ["Absorption a (uniform or voxel grid)"], AQUA_T, AQUA)
    box(10, 392, 340, 36, "", ["Transmittance of the bodies in the way"], AQUA_T, AQUA)
    # stages
    box(420, 58, 340, 108, "1. Build once", ["Facet-to-facet geometry (N²)", "Shadow masks: facet to facet,", "facet to receiver. Reused by every call"],
        THIS_T, THIS, PURPLE)
    box(420, 196, 340, 108, "2. Solve for the radiosity B", ["(I − diag ρ F) B = s", "by matrix-free GMRES,", "once per call"],
        THIS_T, THIS, PURPLE)
    box(420, 334, 340, 108, "3. Gather the fluence rate G", ["Emitted light + reflected light (B − M)", "× absorption T × visibility V,", "summed over the facets"],
        THIS_T, THIS, PURPLE)
    carrow(s, 590, 166, 590, 196, "P", THIS, 2.5, gap=2)
    carrow(s, 590, 304, 590, 334, "P", THIS, 2.5, gap=2)
    # brackets grouping each kind of input, then one arrow per destination
    s.line(358, 70, 358, 222, color=MUTED, sw=2.5)
    s.line(358, 266, 358, 428, color=AQUA, sw=2.5)
    carrow(s, 358, 146, 420, 112, "P", MUTED, 2.5, gap=2)
    carrow(s, 358, 347, 420, 250, "A", AQUA, 2.5, gap=2)
    carrow(s, 358, 347, 420, 388, "A", AQUA, 2.5, gap=2)
    # outputs
    box(830, 196, 320, 108, "", ["B, H: radiosity and", "irradiance on every facet"], "#ffffff", GOOD, tsize=19, lsize=18)
    box(830, 334, 320, 108, "", ["G(x): fluence rate at every", "receiver, in W/m²"], "#ffffff", GOOD, tsize=19, lsize=18)
    carrow(s, 760, 250, 830, 250, "G", GOOD, 2.5, gap=2)
    carrow(s, 760, 388, 830, 388, "G", GOOD, 2.5, gap=2)
    s.save("model-overview")


def model_formfactor():
    """Backup: how one form-factor entry F_ij is evaluated."""
    s = SVG(600, 400)
    jx0, jx1, jy = 170, 430, 52
    iy = 318
    pts = [195, 233, 272, 328, 367, 405]
    P = pts[2]
    s.add(f'<polygon points="{P},{iy} {jx0},{jy} {jx1},{jy}" fill="{OMEGA}" fill-opacity="0.16"/>')
    s.line(P, iy, jx0, jy, color=OMEGA, sw=1.6, dash="5 4")
    s.line(P, iy, jx1, jy, color=OMEGA, sw=1.6, dash="5 4")
    s.line(jx0, jy, jx1, jy, color=AQUA, sw=9)
    s.text(300, 34, "sending facet j (seen edge-on)", 18, AQUA, 700, "middle")
    s.line(jx0, iy, jx1, iy, color=INK2, sw=9)
    s.text(300, 366, "receiving facet i", 18, INK2, 700, "middle")
    for x in pts:
        s.circle(x, iy, 6, fill=OMEGA if x == P else "#ffffff", stroke=OMEGA, sw=2.5)
    rt(s, 300, 392, "dots: the Q = 6 points p_{iq} on facet i", 16, OMEGA, 600, "middle")
    carrow(s, 300, iy - 14, 300, iy - 64, "A", MUTED, 2.5, gap=0)
    rt(s, 310, iy - 44, "n_i", 18, INK2, 700)
    s.line(P, iy, P, iy - 80, color=INK2, sw=1.5, dash="3 3")
    s.path(f"M{P} {iy - 62} A62 62 0 0 0 {P - 62 * math.sin(math.atan2(P - jx0, iy - jy)):.1f} {iy - 62 * math.cos(math.atan2(P - jx0, iy - jy)):.1f}", color=INK2, sw=1.8)
    s.text(P - 24, iy - 70, "\u03b8", 18, INK2, 700, "middle")
    s.line(300, jy, 300, iy, color=GOOD, sw=2, dash="3 5")
    s.circle(300, jy, 5, fill=GOOD)
    s.circle(300, iy, 5, fill=GOOD)
    s.text(312, 190, "centroid to centroid:", 16, GOOD, 600)
    s.text(312, 210, "T and V are", 16, GOOD, 600)
    s.text(312, 230, "evaluated here", 16, GOOD, 600)
    s.text(14, 150, "projected solid angle", 17, OMEGA, 700)
    rt(s, 14, 172, "Ω⊥_j(p_{iq}, n_i)", 17, OMEGA, 700)
    s.text(14, 194, "of facet j seen from", 16, INK2)
    s.text(14, 214, "one point of facet i", 16, INK2)
    s.save("model-formfactor")


# --------------------------------------------- backup: dose calculator ---
def barycentric():
    """Appendix 2: two cells cut into tets by joining the cell centre to each face
    (2-D analogue: triangles); a track crosses the face they share."""
    s = SVG(1000, 480)

    p2, p3 = (430, 80), (390, 400)
    c1, c2 = (250, 250), (660, 240)           # p1 and p4: the two cell centres
    left = [(60, 230), (190, 70), p2, p3, (170, 410)]
    right = [p2, (760, 60), (930, 230), (800, 420), p3]
    for poly, c, tri_fill in ((left, c1, PANEL), (right, c2, THIS_T)):
        pts = " ".join(f"{x},{y}" for x, y in poly)
        s.add(f'<polygon points="{pts}" fill="#ffffff" stroke="{INK}" stroke-width="2.5"/>')
        s.add(f'<polygon points="{c[0]},{c[1]} {p2[0]},{p2[1]} {p3[0]},{p3[1]}" '
              f'fill="{tri_fill}" stroke="none"/>')
        for v in poly:                           # the cut into tets
            s.line(c[0], c[1], v[0], v[1], color=LINE, sw=1.5)
        s.add(f'<polygon points="{pts}" fill="none" stroke="{INK}" stroke-width="2.5"/>')
    s.line(p2[0], p2[1], p3[0], p3[1], color=THIS, sw=5)      # the shared cell face
    for c in (c1, c2):
        s.circle(c[0], c[1], 7, INK)
    for v in (p2, p3):
        s.circle(v[0], v[1], 6, INK)
    halo(s, p2[0] + 12, p2[1] - 10, "p\u2082", 26)
    halo(s, p3[0] - 14, p3[1] + 36, "p\u2083", 26)
    halo(s, c1[0] - 44, c1[1] + 8, "p\u2081", 26)
    halo(s, c2[0] + 14, c2[1] + 10, "p\u2084", 26)
    # the track
    P, Q, R = (330, 232), (411.0, 230.0), (565, 200)
    s.circle(*P, 9, THIS, "#ffffff", 2)
    s.line(P[0] + 9, P[1], Q[0] - 8, Q[1], color=THIS, sw=3.5, arrow=True)
    s.circle(*Q, 8, "#ffffff", THIS, 3)
    s.line(Q[0] + 9, Q[1] - 1, R[0], R[1], color=THIS, sw=3, dash="7 6", arrow=True)
    halo(s, P[0] - 40, P[1] + 40, "all \u03bb > 0: inside the tet", 20, INK2, 600)
    # labels outside the cells, each with a leader line
    s.text(30, 30, "face hit:", 24, INK, 700)
    s.text(30, 58, "\u03bb\u2081 = 0 exactly", 24, INK, 700)
    s.line(215, 48, Q[0] - 8, Q[1] - 6, color=INK, sw=1.8)
    s.circle(215, 48, 3, INK)
    s.text(500, 30, "face of the original cell (p\u2082p\u2083)", 24, THIS, 700)
    s.line(560, 40, 422, 150, color=THIS, sw=1.8)
    s.text(30, 462, "p\u2081: centre of the original cell", 22, INK, 600)
    s.line(150, 440, c1[0] - 6, c1[1] + 8, color=INK, sw=1.8)
    s.text(560, 462, "p\u2084: centre of the neighbouring cell", 22, INK, 600)
    s.line(680, 440, c2[0] + 4, c2[1] + 10, color=INK, sw=1.8)
    s.save("barycentric")


def tet_exit():
    """Appendix 2: where a straight displacement leaves one tet (2-D analogue)."""
    s = SVG(840, 600)

    p1, p2, p3 = (110, 380), (520, 210), (500, 550)
    x0, X1, X3, E = (240, 380), (410.0, 250.0), (521.6, 160.0), (640, 80)
    s.add(f'<polygon points="{p1[0]},{p1[1]} {p2[0]},{p2[1]} {p3[0]},{p3[1]}" '
          f'fill="{PANEL}" stroke="{INK}" stroke-width="2.5"/>')
    # the line of side p2p3 carried on upward: where the path would reach lambda1 = 0
    s.line(p2[0], p2[1], X3[0] + 1, X3[1] - 20, color=THIS, sw=2.5, dash="6 5")
    s.line(p2[0], p2[1], p3[0], p3[1], color=THIS, sw=3.5)
    s.line(p1[0], p1[1], p2[0], p2[1], color=AQUA, sw=3.5)
    # the displacement d
    s.line(x0[0], x0[1], X1[0], X1[1], color=INK, sw=3.5)
    s.line(X1[0], X1[1], E[0] - 6, E[1] + 2, color=INK, sw=3, dash="7 6", arrow=True)
    s.circle(*x0, 8, INK)
    s.circle(*X1, 9, "#ffffff", AQUA, 4)
    s.circle(*X3, 8, "#ffffff", THIS, 3.5)
    for v, lab, dx, dy in ((p1, "p\u2081", -42, 30), (p2, "p\u2082", 14, 14),
                           (p3, "p\u2083", 12, 12)):
        s.circle(v[0], v[1], 6, INK)
        halo(s, v[0] + dx, v[1] + dy, lab, 26)
    # side names, outside the triangle
    s.text(528, 395, "\u03bb\u2081 = 0", 22, THIS, 700)
    s.text(250, 492, "\u03bb\u2082 = 0", 22, INK2, 700)
    s.text(182, 270, "\u03bb\u2083 = 0", 22, AQUA, 700, "end")
    # annotations with leader lines
    halo(s, x0[0] + 14, x0[1] + 38, "start: \u03bb = \u03bb\u2080", 21, INK, 600)
    s.text(30, 36, "\u03bc = 0.43: \u03bb\u2083 reaches 0 first,", 22, AQUA, 700)
    s.text(30, 64, "so the track leaves the tet here", 22, INK, 600)
    s.line(300, 76, X1[0] - 4, X1[1] - 10, color=AQUA, sw=1.8)
    s.text(610, 190, "\u03bc = 0.68: \u03bb\u2081 would", 21, THIS, 700)
    s.text(610, 216, "reach 0 here, but later", 21, INK, 600)
    s.line(660, 172, X3[0] + 9, X3[1] + 4, color=THIS, sw=1.8)
    halo(s, E[0] - 20, E[1] - 16, "end of d (\u03bc = 1)", 21, INK, 600)
    s.save("tet-exit")


def tet_crossing():
    """Appendix 2: one track crossing a side inside a cell, then a face of the cell
    (2-D analogue: triangles cut from the cell centre)."""
    s = SVG(1000, 510)

    s.add('<g transform="translate(0,70)">')
    p2, p3, v1 = (430, 80), (390, 400), (190, 70)
    c1, c2 = (250, 250), (660, 240)
    left = [(60, 230), v1, p2, p3, (170, 410)]
    right = [p2, (760, 60), (930, 230), (800, 420), p3]
    shade = {  # triangles the track passes through
        (c1, v1, p2): AQUA_T, (c1, p2, p3): "#e4e1ec", (c2, p2, p3): THIS_T}
    for poly, c in ((left, c1), (right, c2)):
        pts = " ".join(f"{x},{y}" for x, y in poly)
        s.add(f'<polygon points="{pts}" fill="#ffffff" stroke="none"/>')
    for (a, b2, c), fill in shade.items():
        s.add(f'<polygon points="{a[0]},{a[1]} {b2[0]},{b2[1]} {c[0]},{c[1]}" '
              f'fill="{fill}" stroke="none"/>')
    for poly, c in ((left, c1), (right, c2)):
        for v in poly:
            s.line(c[0], c[1], v[0], v[1], color=LINE, sw=1.5)
        pts = " ".join(f"{x},{y}" for x, y in poly)
        s.add(f'<polygon points="{pts}" fill="none" stroke="{INK}" stroke-width="2.5"/>')
    s.line(p2[0], p2[1], p3[0], p3[1], color=THIS, sw=5)
    s.line(c1[0], c1[1], p2[0], p2[1], color=AQUA, sw=4)
    for c in (c1, c2):
        s.circle(c[0], c[1], 7, INK)
    halo(s, c1[0] - 44, c1[1] + 30, "p\u2081", 24)
    # the track: start, side inside the cell, face of the cell, end
    S, X, Q, R = (280, 140), (330.1, 174.4), (411.0, 230.0), (520, 305)
    s.line(S[0], S[1], X[0] - 5, X[1] - 4, color=THIS, sw=3.5)
    s.line(X[0], X[1], Q[0] - 6, Q[1] - 4, color=THIS, sw=3.5)
    s.line(Q[0] + 6, Q[1] + 4, R[0], R[1], color=THIS, sw=3, dash="7 6", arrow=True)
    s.circle(*S, 8, THIS, "#ffffff", 2)
    s.circle(*X, 8, "#ffffff", AQUA, 3.5)
    s.circle(*Q, 8, "#ffffff", THIS, 3.5)
    # labels outside the cells, with leader lines
    s.text(30, -32, "another \u03bb = 0:", 23, AQUA, 700)
    s.text(30, -6, "a side inside the original cell,", 21, INK, 600)
    s.text(30, 19, "so the next tet of the same cell", 21, INK, 600)
    s.line(120, 30, X[0] - 6, X[1] - 6, color=AQUA, sw=1.8)
    s.text(560, -32, "\u03bb\u2081 = 0:", 23, THIS, 700)
    s.text(560, -6, "a face of the original cell,", 21, INK, 600)
    s.text(560, 19, "so the neighbouring cell", 21, INK, 600)
    s.line(640, 30, Q[0] + 8, Q[1] - 6, color=THIS, sw=1.8)
    s.add("</g>")
    s.save("tet-crossing")


def dose_segments():
    """Appendix 2: dose accumulates per face-to-face segment (trapezoid rule)."""
    s = SVG(1100, 420)
    xs = [90, 270, 430, 640, 800, 1010]
    G = [60, 120, 165, 115, 75, 45]
    y0, yb = 80, 360
    s.line(xs[0] - 30, y0, xs[-1] + 30, y0, color=INK, sw=2.5)
    s.text(xs[0] - 30, y0 - 34, "trajectory through the mesh", 19, INK2, 600)
    for i, x in enumerate(xs):
        s.line(x, y0 - 16, x, yb, color=LINE, sw=1.5, dash="4 5")
        s.circle(x, y0, 6, "#ffffff", THIS, 3)
    s.text(xs[0], y0 + 34, "start of", 16, INK2, anchor="middle")
    s.text(xs[0], y0 + 52, "outer step", 16, INK2, anchor="middle")
    s.text(xs[-1], y0 + 34, "end of", 16, INK2, anchor="middle")
    s.text(xs[-1], y0 + 52, "outer step", 16, INK2, anchor="middle")
    for x in xs[1:-1]:
        s.text(x, y0 + 38, "face", 16, INK2, anchor="middle")
    s.line(xs[0], y0 + 90, xs[-1], y0 + 90, color=MUTED, sw=1.5)
    # shaded trapezoids and G samples
    for i in range(len(xs) - 1):
        pts = (f"{xs[i]},{yb} {xs[i]},{yb - G[i]} "
               f"{xs[i+1]},{yb - G[i+1]} {xs[i+1]},{yb}")
        s.add(f'<polygon points="{pts}" fill="{THIS_T}" stroke="{THIS}" '
              f'stroke-width="2"/>')
        mx = (xs[i] + xs[i + 1]) / 2
        my = yb - (G[i] + G[i + 1]) / 4
        s.text(mx, my + 6, f"\u0394D{chr(0x2081 + i)}", 19, PURPLE, 700, "middle")
        s.text(mx, yb + 24, f"\u0394t{chr(0x2081 + i)}", 18, INK2, 600, "middle")
    for x, g in zip(xs, G):
        s.circle(x, yb - g, 5, THIS)
    s.line(xs[0] - 30, yb, xs[-1] + 30, yb, color=INK, sw=2)
    s.text(xs[0] - 38, yb - G[0] - 12, "G\u2080", 19, THIS, 700, "end")
    s.text(xs[1] + 4, yb - G[1] - 14, "G\u2081", 19, THIS, 700)
    s.text(xs[0] - 38, yb + 6, "0", 17, INK2, anchor="end")
    s.text(xs[-1] + 30, 200, "G along the track:", 18, THIS, 700, "end")
    s.text(xs[-1] + 30, 222, "linear within each tet", 17, INK2, 400, "end")
    s.save("dose-segments")


def dispersion_trace():
    """Appendix 2: one velocity component under the two dispersion models, on the same time axis.

    The random walk holds a value for each eddy lifetime tau_e and then redraws it; the Langevin
    model's value (an Ornstein-Uhlenbeck process, T_L = tau_e / 2) relaxes continuously with a
    small random kick every step. Fixed seeds keep the drawing reproducible.
    """
    import random

    s = SVG(1100, 330)
    x0, x1, ym = 90, 1040, 140
    s.line(x0 - 20, ym, x1 + 10, ym, color=INK, sw=2)
    s.line(x0, 24, x0, 256, color=INK, sw=2)
    s.text(x0 - 10, 18, "u\u2032 (one component)", 18, INK2, 600, "start")
    s.text(x1 + 10, ym + 26, "time", 18, INK2, 600, "end")
    amp, tl_px = 46.0, 85.0

    # Random walk: held for each eddy lifetime, then redrawn (values chosen to read clearly).
    edges = [x0, 250, 420, 540, 750, 880, x1]
    vals = [1.15, -0.85, 0.45, -1.3, 0.8, -0.35]
    held = [(edges[i], edges[i + 1], ym - amp * v) for i, v in enumerate(vals)]
    d = " ".join(f"M{a:.1f} {y:.1f} L{b:.1f} {y:.1f}" for a, b, y in held)
    s.path(d, color=FLUENT, sw=3.5)
    for (_, b, y), (_, _, y2) in zip(held, held[1:]):
        s.line(b, y, b, y2, color=FLUENT, sw=1.5, dash="3 4")

    # Langevin: exact Ornstein-Uhlenbeck samples at fine steps.
    rng = random.Random(7)
    n = 380
    dx = (x1 - x0) / n
    a = math.exp(-dx / tl_px)
    v, pts = 0.3, []
    for i in range(n + 1):
        pts.append((x0 + i * dx, ym - amp * v))
        v = a * v + math.sqrt(1 - a * a) * rng.gauss(0.0, 1.0)
    s.path("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts), color=THIS, sw=3)

    # Legend, with the time scales written with real subscripts.
    ly = 290
    s.line(x0, ly - 6, x0 + 44, ly - 6, color=FLUENT, sw=3.5)
    rt(s, x0 + 56, ly, "Random walk: held for an eddy lifetime \u03c4_{e}, then redrawn", 18, INK)
    s.line(x0, ly + 26, x0 + 44, ly + 26, color=THIS, sw=3)
    rt(s, x0 + 56, ly + 32, "Langevin: relaxes continuously over T_{L} = \u03c4_{e}/2,"
       " with a random kick every step", 18, INK)
    s.save("dispersion-trace")


def tracker_flow():
    """Appendix 2: the whole tracker on one line."""
    s = SVG(1180, 285)
    boxes = [("Fields", "U, G, k, \u03b5 or \u03c9", "read from any solver\nresults converted to\nOpenFOAM format"),
             ("Seed", "patch or point", "injection"),
             ("Outer step", "V = U(x) + u\u2032", "dt from the CFL bound"),
             ("Inner loop", "face to face", "accumulate dose"),
             ("Output", "dose per particle", "log reduction, tracks")]
    w, h, gap, y = 196, 150, 45, 55
    for i, (a, b, c) in enumerate(boxes):
        x = 10 + i * (w + gap)
        main = i in (2, 3)
        s.rect(x, y, w, h, fill=THIS_T if main else PANEL,
               stroke=THIS if main else LINE, sw=2.5 if main else 1.5, rx=14)
        s.text(x + w / 2, y + 34, a, 23, PURPLE if main else INK, 700, "middle")
        s.text(x + w / 2, y + 68, b, 18, INK, 600, "middle")
        for k, ln in enumerate(c.split("\n")):
            s.text(x + w / 2, y + 96 + k * 19, ln, 16, INK2, 400, "middle")
        if i < len(boxes) - 1:
            s.line(x + w + 5, y + h / 2, x + w + gap - 5, y + h / 2,
                   color=MUTED, sw=2.5, arrow=True)
    x2 = 10 + 2 * (w + gap) + w / 2
    x3 = 10 + 3 * (w + gap) + w / 2
    s.path(f"M{x3} {y + h + 4} L{x3} {y + h + 38} L{x2} {y + h + 38} "
           f"L{x2} {y + h + 6}", color=THIS, sw=2.5, arrow=True)
    s.text((x2 + x3) / 2, y + h + 62, "repeat until the particle escapes, times out or hits maxDose",
           16, INK2, 400, "middle")
    s.save("tracker-flow")


# ------------------------------------------------------ backup: uvmesh ---
def uvmesh_pipeline():
    """Appendix 3: what build() writes and what Allrun.mesh runs."""
    s = SVG(1180, 395)
    w, h = 240, 92

    def box(x, y, title, sub, hot=False, wide=None, tall=None):
        ww = wide or w
        s.rect(x, y, ww, tall or h, fill=THIS_T if hot else PANEL,
               stroke=THIS if hot else LINE, sw=2.5 if hot else 1.5, rx=12)
        s.text(x + ww / 2, y + 38, title, 19, PURPLE if hot else INK, 700, "middle")
        for i, ln in enumerate(sub.split("\n")):
            s.text(x + ww / 2, y + 62 + i * 19, ln, 15, INK2, 400, "middle")

    box(10, 134, "mesh.py", "Lamp, Pipe, WallLayer,\nReactorBody + STEP file", hot=True)
    # lanes
    box(305, 20, "Structured pieces", "lamp O-grid + cap, pipes,\nwall layer: blockMesh")
    box(305, 248, "Bulk", "gmsh tets from the STEP body,\nthen polyDualMesh")
    box(595, 20, "Move into place", "transformPoints\n(each piece meshed on +z)")
    box(595, 248, "Polyhedra", "gmshToFoam, polyDualMesh,\nfeature angle ~100\u00b0")
    box(885, 120, "Join", "mergeMeshes, then one\ncreateNonConformalCouples\nper seam pair", hot=True, wide=285,
        tall=120)
    s.line(250, 168, 300, 70, arrow=True)
    s.line(250, 188, 300, 292, arrow=True)
    s.line(550, 66, 590, 66, arrow=True)
    s.line(550, 294, 590, 294, arrow=True)
    s.line(840, 66, 880, 160, arrow=True)
    s.line(840, 294, 880, 196, arrow=True)
    s.text(1027, 270, "then checkMesh", 17, INK2, 600, "middle")
    s.text(10, 378, "build() writes the blockMeshDicts, the gmsh script and Allrun.mesh; "
           "Allrun.mesh runs the OpenFOAM and gmsh steps in the order shown.", 16, INK2)
    s.save("uvmesh-pipeline")


# ------------------------------------------------------------ QR code ---
def qr():
    import segno
    q = segno.make("https://github.com/DeGrootResearchGroup",
                   error="m")
    q.save(str(OUT / "qr-repo.svg"), scale=10, border=1, dark=INK,
           light="#ffffff")
    print("wrote figures/qr-repo.svg")


if __name__ == "__main__":
    architecture()
    test_taxonomy()
    lagrangian_fields()
    aquaflux_gather()
    model_gather()
    model_emission_solid_angle()
    model_radiosity()
    model_occlusion()
    model_voxel()
    model_mask()
    model_overview()
    model_formfactor()
    oss_benefits()
    barycentric()
    tet_exit()
    tet_crossing()
    dose_segments()
    dispersion_trace()
    tracker_flow()
    uvmesh_pipeline()
    qr()
