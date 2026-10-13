"""Moellehaven, Aarhus - 3D-volumen af bygningen i facader.py, i mm.

X = vest->oest (gavlbredde), Y = syd->nord (langside), Z = op.
Profilet er facade syd/nord fra facader.py; maal er estimeret fra skitse.
"""
from cadgen import build123d as bd
from cadgen import glb, step

DEPTH = 24600          # oest-vest, facade syd/nord bredde
LENGTH = 35000         # syd-nord, facade oest/vest bredde
FLOOR_H = 3200
FLOORS = 6
EAVE_E = 20000
EAVE_W = 14000
RIDGE = 22000
RIDGE_X = 9000
WIN_W, WIN_H, WIN_SILL, WIN_D = 1000, 1500, 900, 250
BAL_D, BAL_T = 1500, 200


def profile_prism(y0, y1):
    pts = [(0, 0), (DEPTH, 0), (DEPTH, EAVE_E), (RIDGE_X, RIDGE), (0, EAVE_W)]
    face = bd.Plane.XZ.offset(-y0) * bd.Face(bd.Wire.make_polygon([bd.Vector(x, z, 0) for x, z in pts], close=True))
    return bd.extrude(face, amount=y1 - y0, dir=(0, 1, 0))


def box(x, y, z, dx, dy, dz):
    return bd.Pos(x + dx / 2, y + dy / 2, z + dz / 2) * bd.Box(dx, dy, dz)


def roof_z(x):
    """Tagfladens hoejde over gavlprofilet ved x."""
    if x <= RIDGE_X:
        return EAVE_W + (RIDGE - EAVE_W) * x / RIDGE_X
    return RIDGE + (EAVE_E - RIDGE) * (x - RIDGE_X) / (DEPTH - RIDGE_X)


def window_cuts():
    cuts = []
    for f in range(FLOORS):
        z = f * FLOOR_H + WIN_SILL
        pitch = (LENGTH - 2400) / 14
        for c in range(14):
            y = 1200 + pitch * (c + .5) - WIN_W / 2
            cuts.append(box(DEPTH - WIN_D, y, z, WIN_D + 10, WIN_W, WIN_H))       # oest
            if z + WIN_H < EAVE_W - 300:
                cuts.append(box(-10, y, z, WIN_D + 10, WIN_W, WIN_H))             # vest
        pitch = (DEPTH - 3000) / 7
        for c in range(7):
            x = 1500 + pitch * (c + .5) - WIN_W / 2
            if z + WIN_H + 300 > min(roof_z(x), roof_z(x + WIN_W)):
                continue
            for y in (-10, LENGTH - WIN_D):                                       # syd, nord
                cuts.append(box(x, y, z, WIN_W, WIN_D + 10, WIN_H))
    return cuts


def glass():
    """Ruder, sat 120 mm inde i hvert vindueshul."""
    panes = []
    for c in window_cuts():
        bb = c.bounding_box()
        if bb.size.X < bb.size.Y:      # oest/vest: hullet gaar i X
            x = DEPTH - 130 if bb.min.X > 0 else 110
            panes.append(box(x, bb.min.Y, bb.min.Z, 20, bb.size.Y, bb.size.Z))
        else:                          # syd/nord: hullet gaar i Y
            y = LENGTH - 130 if bb.min.Y > 0 else 110
            panes.append(box(bb.min.X, y, bb.min.Z, bb.size.X, 20, bb.size.Z))
    return panes


def balconies():
    slabs = []
    for f in range(1, FLOORS):
        z = f * FLOOR_H - BAL_T
        slabs.append(box(0, -BAL_D, z, DEPTH, BAL_D, BAL_T))
        slabs.append(box(0, LENGTH, z, DEPTH, BAL_D, BAL_T))
    return bd.Compound(slabs) & profile_prism(-BAL_D - 10, LENGTH + BAL_D + 10)


@step(out="../STEP/bygning.step")
@glb(out="../GLB/bygning.glb")
def bygning():
    body = profile_prism(0, LENGTH) - bd.Compound(window_cuts())
    body.label = "bygning"
    body.color = bd.Color(0.62, 0.62, 0.64)
    bal = balconies()
    bal = bd.Compound(bal.solids()) if hasattr(bal, "solids") else bal
    bal.label = "altaner"
    bal.color = bd.Color(0.25, 0.25, 0.27)
    win = bd.Compound(glass())
    win.label = "vinduer"
    win.color = bd.Color(0.16, 0.22, 0.30)
    return bd.Compound(children=[body, bal, win], label="moellehaven")


if __name__ == "__main__":
    bygning()
