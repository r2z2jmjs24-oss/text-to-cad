"""Moellehaven, Aarhus - fire facader (syd, nord, oest, vest), 1:1 i mm.

Tegningen er gengivet fra en rasterskitse; maal er aflaest/estimeret.
"""
from cadgen import build123d as bd
from cadgen import dxf

FLOOR_H = 3200
TOP = 19400
RIDGE = 22000


def poly(pts):
    return bd.Face(bd.Wire.make_polygon([bd.Vector(x, y, 0) for x, y in pts], close=True))


def rect(x, y, w, h):
    return bd.Pos(x, y, 0) * bd.Face.make_rect(w, h).moved(bd.Location((w / 2, h / 2, 0)))


def hline(x0, x1, y):
    return bd.Edge.make_line(bd.Vector(x0, y, 0), bd.Vector(x1, y, 0))


def text(s, x, y, h=500):
    return bd.Pos(x, y, 0) * bd.Text(s, h, align=(bd.Align.MIN, bd.Align.MIN))


def grid(x0, x1, cols, floors, w=1000, h=1500, lo=900):
    out = []
    pitch = (x1 - x0) / cols
    for f in range(floors):
        for c in range(cols):
            out.append(rect(x0 + pitch * (c + .5) - w / 2, f * FLOOR_H + lo, w, h))
    return out


def balconies(x0, x1, floors, d=1500):
    return [rect(x0, f * FLOOR_H + FLOOR_H - 150, x1 - x0, 150) for f in range(1, floors)]


def gable(w, mirror):
    pts = [(0, 0), (w, 0), (w, TOP + 600), (9000, RIDGE), (0, 14000)]
    if mirror:
        pts = [(w - x, y) for x, y in pts]
    return pts


def clip(shapes, wall, whole):
    out = []
    for f in shapes:
        cut = f & wall
        area = sum(x.area for x in cut.faces()) if cut else 0
        if area > (f.area * 0.999 if whole else 1):
            out.append(f if whole else cut)
    return out


def elevation(ox, oy, kind, label):
    wall, win, bal, ref, txt = [], [], [], [], []
    if kind in ("syd", "nord"):
        w = 24600
        wall.append(poly([(ox + x, oy + y) for x, y in gable(w, kind == "nord")]))
        outline = wall[0]
        win += clip([f.moved(bd.Location((ox, oy, 0))) for f in grid(1500, w - 1500, 7, 6)], outline, True)
        bal += clip([f.moved(bd.Location((ox, oy, 0))) for f in balconies(0, w, 7)], outline, False)
        lvl = {19400: "19400", 22000: "22000"}
    else:
        w = 35000
        body = TOP if kind == "oest" else 16000
        wall.append(rect(ox, oy, w, body))
        if kind == "vest":
            wall.append(rect(ox + 12000, oy + body, 7000, RIDGE - body))
            win += [rect(ox + 12000 + x, oy + body + f * FLOOR_H + 900, 1000, 1500)
                    for f in range(int((RIDGE - body) // FLOOR_H)) for x in (1500, 4500)]
        win += [f.moved(bd.Location((ox, oy, 0))) for f in grid(1200, w - 1200, 14, body // FLOOR_H)]
        bal += [f.moved(bd.Location((ox, oy, 0))) for f in balconies(-600, w + 600, body // FLOOR_H)]
        lvl = {19400: "19400", 22000: "22000"}
    for z, s in lvl.items():
        ref.append(hline(ox - 3000, ox + w + 3000, oy + z))
        txt.append(text(s, ox - 6500, oy + z + 150))
    txt.append(text(label, ox, oy - 2500, 800))
    return wall, win, bal, ref, txt


@dxf
def facader():
    layers = {"VAEG": [], "VINDUER": [], "ALTANER": [], "KOTER_REF": [], "TEKST_NOTE": [], "RAMME_REF": []}
    for (ox, oy, kind, label) in [
        (0, 40000, "syd", "Facade syd"),
        (45000, 40000, "nord", "Facade nord"),
        (0, 0, "oest", "Facade oest"),
        (45000, 0, "vest", "Facade vest"),
    ]:
        for key, part in zip(layers, elevation(ox, oy, kind, label)):
            layers[key] += part
    # tegningsramme + titelfelt
    layers["RAMME_REF"] += [rect(-9000, -13000, 96000, 85000), rect(55000, -12500, 31500, 5500)]
    for i, s in enumerate(["Projekt: Moellehaven, Aarhus, 8000", "Tegningsnavn: H2_005_NRX2_2_Facader", "Maal: 1:200"]):
        layers["TEKST_NOTE"].append(text(s, 55600, -8800 - i * 1500, 600))
    return {k: bd.Compound(v) for k, v in layers.items() if v}


if __name__ == "__main__":
    facader()
