"""Style test C · 等距微缩世界 (chosen 2026-10-21 → skill/styles/iso-diorama): a cut-away block of earth with a pump jack, tank,
barrels and trees on top; the shallow reservoir drains, the bore goes deeper and four new reservoirs pop out on the cut faces."""
import os, sys, math
os.environ['VERT'] = '1'
import numpy as np, skia
from common import *
sys.path.insert(0, ROOT + '/skill/styles/iso-diorama')
import iso_diorama as D
from iso_diorama import PAL, BOX, CYL, SPH, Scene, rot

HB = 2.3                                   # block half-width
LAYERS = [(0, -.55, 'sand'), (-.55, -1.25, 'shale'), (-1.25, -1.8, 'oil'), (-1.8, -2.3, 'cap'), (-2.3, -3.5, 'deep'), (-3.5, -4.6, 'base')]
POCK = [('z', -1.0, -2.85, .55, .32), ('x', .6, -2.9, .6, .3), ('z', .8, -4.0, .62, .3), ('x', -1.0, -4.05, .55, .3)]   # face, along, y, rx, ry
WELL = (-.2, 1.95)                         # x, z of the well (near the +z face)


def deep_u(t): return eio((t - TWIST) / 1.0)
def bottom(t): return lerp(-2.3, -4.6, deep_u(t))
def camera(t): d = deep_u(t); return D.iso_vp((0, lerp(.1, -.9, d), 0), lerp(6.4, 7.3, d))


def build(t):
    S = Scene(); bot = bottom(t)
    for y0, y1, k in LAYERS:
        y1c = max(y1, bot)
        if y1c >= y0: continue
        if k == 'oil':                                                         # the shallow reservoir drains: its top drops
            lv = 1 - .78 * drained(t); top = y1 + (y0 - y1) * lv
            S.add(BOX, (0, (y0 + top) / 2, 0), (2 * HB, y0 - top, 2 * HB), PAL['shale'] * .93)
            S.add(BOX, (0, (top + y1) / 2, 0), (2 * HB + .002, top - y1, 2 * HB + .002), PAL['oil'], gloss=1.)
        else: S.add(BOX, (0, (y0 + y1c) / 2, 0), (2 * HB, y0 - y1c, 2 * HB), PAL[k])
    S.add(BOX, (0, .06, 0), (2 * HB + .06, .12, 2 * HB + .06), PAL['grass'])  # grass lid
    for i, (x, z, s) in enumerate(((-1.85, .9, .9), (-1.9, -1.8, 1), (1.85, -1.85, .9), (.2, -1.9, .7), (1.95, .8, .65))):
        S.tree(x, z, s, PAL['tree'] if i % 2 else PAL['grass2'] * .85)
    # pump jack: the beam lies along x and rocks about z, once every two beats
    wx, wz = WELL; ang = 9 * math.sin(2 * math.pi * t / 1.0); px, py = wx + .75, 1.45
    for sx in (-1, 1):
        for dz in (-.18, .18): S.add(BOX, (px + sx * .28, .78, wz + dz), (.08, 1.4, .08), PAL['teal'], R=rot('z', sx * 11))
    S.add(BOX, (px, .16, wz), (1.9, .08, .6), PAL['steel'])
    R = rot('z', ang); piv = np.array([px, py, wz])
    S.add(BOX, (px + .15, py, wz), (2.2, .14, .16), PAL['teal'], R=R, pivot=piv)
    S.add(BOX, (px - 1.0, py - .14, wz), (.26, .46, .2), PAL['red'], R=R, pivot=piv)
    S.add(CYL, (px + 1.15, .55, wz), (.42, .06, .42), PAL['red'], R=rot('x', 90))       # counterweight disc
    S.add(BOX, (wx, .2, wz), (.22, .2, .22), PAL['steel'])
    S.add(BOX, (wx, -1.0, HB + .012), (.1, 2.2, .02), PAL['steel'])                     # the bore, seen on the cut face
    d = deep_u(t)
    if d > 0:                                                                           # deeper, then sideways
        y2 = lerp(-2.1, -3.45, eio(d * 1.6)); S.add(BOX, (wx, (-2.1 + y2) / 2, HB + .012), (.1, -2.1 - y2 + .05, .02), PAL['steel'])
        if d > .6:
            xl = lerp(wx, -1.5, eio((d - .6) / .4)); S.add(BOX, ((wx + xl) / 2, -3.45, HB + .012), (abs(wx - xl) + .1, .1, .02), PAL['steel'])
    if t < PUMP[1] + .5:                                                                # oil rising up the bore
        for k in range(6): S.add(SPH, (wx, -1.75 + ((t * 2.2 + k * .3) % 1.75), HB + .03), (.09, .09, .05), PAL['oil'], gloss=1.)
    # tank + barrels (the burned oil piles up as barrels)
    S.add(CYL, (-1.2, .65, -.5), (1.1, .55, 1.1), PAL['cream'])
    S.add(CYL, (-1.2, .75, -.5), (1.11, .08, 1.11), PAL['red'])
    nb = int(drained(t) * 10 + .001)
    spots = [(x, 0, z) for z in (.2, .55) for x in (1.0, 1.32, 1.64)] + [(1.16, 1, .38), (1.48, 1, .38), (1.32, 2, .38), (1.32, 1, .2)]
    for i in range(nb):
        x, lvl, z = spots[i]; age = clamp((drained(t) * 10 - i) / .6); sc = eback(age) if age < 1 else 1
        S.add(CYL, (x + .1, .32 + lvl * .36 + (1 - sc) * .3, z - 1.4), (.3 * sc, .17 * sc, .3 * sc), PAL['red'] if i % 3 else PAL['teal'])
    # new reservoirs pop out of the cut faces as glossy lenses
    for i, (face, a, y, rx, ry) in enumerate(POCK):
        u = found(t, i)
        if u <= 0 or y < bot + .2: continue
        s = eback(u)
        pos = (a, y, HB) if face == 'z' else (HB, y, a)
        size = (rx * 2 * s, ry * 2 * s, .7 * s) if face == 'z' else (.7 * s, ry * 2 * s, rx * 2 * s)
        S.add(SPH, pos, size, PAL['oil'], gloss=1.)
    return S


SURF = skia.Surface(W, H)


def frame(t):
    VP = camera(t); img = D.render(build(t), VP); c = SURF.getCanvas()
    bx, by = D.project(VP, (0, bottom(t), 0))
    D.composite(c, img, lerp(1180, 1200, deep_u(t)), contact=(bx, by, 660))
    for i, (face, a, y, rx, ry) in enumerate(POCK):                                    # labels ride on the projected reservoirs
        u = found(t, i)
        if u <= 0: continue
        x, yy = D.project(VP, (a, y + ry + .05, HB + .05) if face == 'z' else (HB + .05, y + ry + .05, a))
        D.pill_label(c, '+' + FIND_LABELS[i][0], x, yy - 26 - (1 - eout(u)) * 14, u)
    for k, (lab, v, yr, col) in enumerate((('已烧掉', used(t), year_pump(t), D.TOMATO),
                                           ('探明储量', reserves(t) if t >= RES[0] else R80, year_res(t) if t >= RES[0] else 1980, D.INK))):
        D.counter_card(c, 70 + k * 480, 452, 460, f'{lab} · {yr}', num(v), '亿桶', col)
    D.stamp_pill(c, '×2.5', 880, 452, t - STAMP)
    D.captions(c, t, CAPS)
    D.text(c, '样片 · 数字待核实', W - 40, 1640, D.ZH_B, 24, D.INK, .45, 'r')
    return SURF.toarray(colorType=skia.kRGBA_8888_ColorType)


if __name__ == '__main__': run('C_等距微缩', frame)
