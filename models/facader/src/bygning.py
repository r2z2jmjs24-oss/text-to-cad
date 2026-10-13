"""Moellehaven, Aarhus - 3D-model af bygningen, i mm.

Kilder: Tagplan (K01_A13_H3_Etag_N600), Snit A (K01_A13_H3_Etag_SA_N400) og
detaljerne N701-N707. X = modullinje 1 -> 5 (vest -> oest), Y = A -> I
(syd -> nord), Z = op, terraen i Z = 0.

- Oestfloej (linje 2-5): 15 graders pulttag i alu, kote 22039 ved linje 2
  ned til 19000 ved linje 5.
- Vestfloej (linje 1-2): fladt tag med tagpap (kote ca. 19700) i midten
  (felt C-F), 60 graders tag i alu i gavlfelterne A-C og F-I.
- Ydervaegge: 108 mm formur af tegl.

Farver og altanplacering er fra projektets situationsplan og 3D-visning
(K01_A13_H1_SIT_902): sandfarvet tegl, terrakottafarvede skraatage, altaner
mod Moellevejen (vest), mod oest og paa sydgavlen.

Modullinjeafstande er aflaest fra tagplanen; felternes laengder (A-C, C-F,
F-I), etagehoejden, vinduer og altaner er estimeret fra tegningerne.
"""
from cadgen import build123d as bd
from cadgen import glb, step

# Modullinjer (X) fra tagplanen: 1-2 ca. 9300, 2-3 1482, 3-4 2612, 4-5 7177
GRID_1 = 0
GRID_2 = 9300
GRID_5 = GRID_2 + 1482 + 2612 + 7177       # 20571
LENGTH = 30000                             # A-I
BAND_S = 9500                              # A-C: 60 graders tag, syd
BAND_N = 19700                             # F-I: 60 graders tag, nord

RIDGE = 22039          # Snit A, linje 2
EAVE_E = 19000         # Snit A, linje 5
FLAT = 19700           # fladt tag (19727 -> 19555)
STEEP_ANGLE = 60       # (27)02 tag 60 grader
STEEP_SLOPE_LEN = 9122 # (27)02 elementlaengde
FLOOR_H = 3100
FLOORS = 6

WIN_W, WIN_H, WIN_SILL, WIN_D = 1200, 1600, 800, 250
ROOF_T = 250           # alu-beklaedning + overkant, vist som en plade
BAL_D, BAL_T, RAIL_H = 1500, 200, 1100

BRICK = (0.82, 0.69, 0.50)     # sandfarvet tegl
ROOF = (0.72, 0.36, 0.21)      # terrakottafarvet tagbeklaedning
FELT = (0.13, 0.13, 0.14)
GLASS = (0.16, 0.22, 0.30)
CONCRETE = (0.80, 0.79, 0.76)
RAIL = (0.62, 0.76, 0.82)


def steep_rise():
    """60-graders taget: (vandret laengde, stigning) af elementet."""
    import math
    a = math.radians(STEEP_ANGLE)
    return STEEP_SLOPE_LEN * math.cos(a), STEEP_SLOPE_LEN * math.sin(a)


def roof_z(x, y):
    """Tagfladens kote over punktet (x, y)."""
    if x >= GRID_2:
        return RIDGE + (EAVE_E - RIDGE) * (x - GRID_2) / (GRID_5 - GRID_2)
    if BAND_S <= y <= BAND_N:
        return FLAT
    run, rise = steep_rise()
    x0 = GRID_2 - run
    return RIDGE - rise if x <= x0 else RIDGE - rise * (GRID_2 - x) / run


def prism(pts, y0, y1):
    """Polygon i XZ-planet (x, z), ekstruderet fra y0 til y1."""
    wire = bd.Wire.make_polygon([bd.Vector(x, y0, z) for x, z in pts], close=True)
    return bd.extrude(bd.Face(wire), amount=y1 - y0, dir=(0, 1, 0))


def box(x, y, z, dx, dy, dz):
    return bd.Pos(x + dx / 2, y + dy / 2, z + dz / 2) * bd.Box(dx, dy, dz)


def west_end_profile():
    run, rise = steep_rise()
    x0 = GRID_2 - run
    return [(GRID_1, 0), (GRID_2, 0), (GRID_2, RIDGE), (x0, RIDGE - rise), (GRID_1, RIDGE - rise)]


def shell():
    east = prism([(GRID_2, 0), (GRID_5, 0), (GRID_5, EAVE_E), (GRID_2, RIDGE)], 0, LENGTH)
    south = prism(west_end_profile(), 0, BAND_S)
    north = prism(west_end_profile(), BAND_N, LENGTH)
    middle = box(GRID_1, BAND_S, 0, GRID_2 - GRID_1, BAND_N - BAND_S, FLAT)
    return east + south + north + middle


def roofs():
    """Tagbeklaedning som plader oven paa skallen: alu-tage og tagpap."""
    run, rise = steep_rise()
    x0 = GRID_2 - run
    over = 300
    k = (EAVE_E - RIDGE) / (GRID_5 - GRID_2)
    east = prism([(GRID_2, RIDGE), (GRID_5 + over, EAVE_E + k * over),
                  (GRID_5 + over, EAVE_E + k * over + ROOF_T), (GRID_2, RIDGE + ROOF_T)], -over, LENGTH + over)
    steep_pts = [(x0, RIDGE - rise), (GRID_2, RIDGE), (GRID_2, RIDGE + ROOF_T),
                 (x0 - 150, RIDGE - rise + ROOF_T / 2)]
    flat_pts = [(GRID_1 - over, RIDGE - rise), (x0, RIDGE - rise),
                (x0, RIDGE - rise + ROOF_T), (GRID_1 - over, RIDGE - rise + ROOF_T)]
    alu = [east,
           prism(steep_pts, -over, BAND_S), prism(steep_pts, BAND_N, LENGTH + over),
           prism(flat_pts, -over, BAND_S), prism(flat_pts, BAND_N, LENGTH + over)]
    felt = box(GRID_1 - over, BAND_S, FLAT, GRID_2 - GRID_1 + over, BAND_N - BAND_S, ROOF_T / 2)
    return alu, [felt]


def windows():
    """(hul, rude) par paa alle fire facader, under tagfladen."""
    out = []
    for f in range(FLOORS):
        z = f * FLOOR_H + WIN_SILL
        top = z + WIN_H + 400
        # oest (x = GRID_5) og vest (x = GRID_1): 12 fag a 2400 langs Y
        for c in range(12):
            y = 600 + 2400 * c + (2400 - WIN_W) / 2
            if top < roof_z(GRID_5, y):
                out.append((box(GRID_5 - WIN_D, y, z, WIN_D + 10, WIN_W, WIN_H),
                            box(GRID_5 - 130, y, z, 20, WIN_W, WIN_H)))
            if top < roof_z(GRID_1, y) and top < roof_z(GRID_1, y + WIN_W):
                out.append((box(GRID_1 - 10, y, z, WIN_D + 10, WIN_W, WIN_H),
                            box(GRID_1 + 110, y, z, 20, WIN_W, WIN_H)))
        # syd (y = 0) og nord (y = LENGTH): fag langs X
        for x in (900, 3600, 6300, 10400, 12900, 15400, 17900):
            if top > min(roof_z(x, 0), roof_z(x + WIN_W, 0)):
                continue
            out.append((box(x, -10, z, WIN_W, WIN_D + 10, WIN_H), box(x, 110, z, WIN_W, 20, WIN_H)))
            out.append((box(x, LENGTH - WIN_D, z, WIN_W, WIN_D + 10, WIN_H),
                        box(x, LENGTH - 130, z, WIN_W, 20, WIN_H)))
    return out


def balcony_stack(face, a0, a1):
    """Altaner paa etage 1-5 foran en facade; a0-a1 er udstraekningen langs facaden."""
    slabs, rails = [], []
    for f in range(1, FLOORS):
        z = f * FLOOR_H - BAL_T
        w = a1 - a0
        if face == "vest":
            slabs.append(box(GRID_1 - BAL_D, a0, z, BAL_D, w, BAL_T))
            rails.append(box(GRID_1 - BAL_D, a0, z + BAL_T, 60, w, RAIL_H))
        elif face == "oest":
            slabs.append(box(GRID_5, a0, z, BAL_D, w, BAL_T))
            rails.append(box(GRID_5 + BAL_D - 60, a0, z + BAL_T, 60, w, RAIL_H))
        else:  # syd
            slabs.append(box(a0, -BAL_D, z, w, BAL_D, BAL_T))
            rails.append(box(a0, -BAL_D, z + BAL_T, w, 60, RAIL_H))
    return slabs, rails


def balconies():
    """Altaner mod Moellevejen (vest), mod oest og paa sydgavlen."""
    slabs, rails = [], []
    for face, a0, a1 in (("vest", 10300, 13700), ("vest", 15500, 18900),
                         ("oest", 13100, 16500), ("syd", 10200, 14300)):
        s_, r_ = balcony_stack(face, a0, a1)
        slabs += s_
        rails += r_
    return slabs, rails


def part(shapes, label, rgb):
    c = bd.Compound(shapes) if isinstance(shapes, list) else shapes
    c.label = label
    c.color = bd.Color(*rgb)
    return c


@step(out="../STEP/bygning.step")
@glb(out="../GLB/bygning.glb")
def bygning():
    wins = windows()
    walls = shell() - bd.Compound([hole for hole, _ in wins])
    alu, felt = roofs()
    slabs, rails = balconies()
    return bd.Compound(children=[
        part(walls, "tegl", BRICK),
        part(alu, "tag", ROOF),
        part(felt, "tag_pap", FELT),
        part([pane for _, pane in wins], "vinduer", GLASS),
        part(slabs, "altaner", CONCRETE),
        part(rails, "altanvaern", RAIL),
    ], label="moellehaven")


if __name__ == "__main__":
    bygning()
