"""math-beauty v2 · 循环版「数学之美」(3:28) — the 2:10 film with four new acts, on a seamless loop of《千年以后》(loop_bed.py).
The song bed plays 0 → h(81), then jumps back 72 half-bars to h(9); the half-bar grid h(n) runs on unbroken to h(190) = 207.75 s.
  0 – h(48)        the 2:10 film unchanged (equations → sunflower → Euler → Fourier → primes)
  h(48) – h(70)    ζ: the primes become Euler's product; it pours into the curve ζ(½ + it), which passes through 0 at each zero
  h(70) – h(86)    chaos game: random halfway jumps toward three corners draw a Sierpiński triangle (quiet section + the seam)
  h(86) – h(103)   the second drum entry: the triangle bursts into a rotating tesseract (4D → 3D → 2D)
  h(103) – h(120)  Galton board: 6,032 points fall through 12 rows of pins into a bell curve, then become the grid of c values
  h(120) – h(190)  the 2:10 film from h(48) on (escape test → Mandelbrot → 10³² → Mandelbulb → Lorenz → close), 72 half-bars later —
                   which lands on exactly the same music as before
usage: python film_loop.py | --still t … | --part i n"""
import os, sys, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import skia
import film as F
from engine import *

BUILD = HERE + '/build/loop/'
os.makedirs(BUILD, exist_ok=True)
OUT = BUILD + ('en/' if EN else '')                            # EN=1: the English-only cut renders next to the bilingual one
os.makedirs(OUT, exist_ok=True)
h = F.h
JUMP = h(81) - h(9)                                             # 72 half-bars = 78.09 s
T = h(190)                                                      # 207.75 s
A0, A1 = h(48), h(120)                                          # the new block; the old film resumes at A1 (= its own h(48) + JUMP)
BEAT = 60 / 110.6444


def arc(A, B, v, seed=0, swirl=.3):
    """A → B along a sideways arc; v is each point's own progress (0…1)"""
    rr = np.random.default_rng(seed); side = rr.choice((-1, 1), len(A)) * (.5 + rr.random(len(A)))
    v = np.clip(v, 0, 1); e = v * v * (3 - 2 * v); D = B - A; nrm = np.stack([-D[:, 1], D[:, 0]], 1)
    return A + D * e[:, None] + nrm * (swirl * side * np.sin(np.pi * e))[:, None]


NONE = lambda n: (np.zeros((n, 2)), np.ones(n), np.zeros((n, 3)))

# ================================================================ act Z · Riemann ζ (h(48) – h(70))
import mpmath
TZ, NZS = 50.6, 5000
_zf = BUILD + 'zeta.npz'
if os.path.exists(_zf):
    _d = np.load(_zf); ZT, ZV, ZEROS = _d['t'], _d['v'], _d['z']
else:
    ZT = np.linspace(0, TZ, NZS); ZV = np.array([complex(mpmath.zeta(mpmath.mpc(.5, x))) for x in ZT])
    ZEROS = np.array([float(mpmath.zetazero(k).imag) for k in range(1, 11)]); np.savez(_zf, t=ZT, v=ZV, z=ZEROS)
_x0, _x1, _y0, _y1 = ZV.real.min(), ZV.real.max(), ZV.imag.min(), ZV.imag.max()
_s = min((1700 - 600) / (_x1 - _x0), (770 - 330) / (_y1 - _y0))
CAM_Z = Cam((_x0 + _x1) / 2 - (1150 - W / 2) / _s, (_y0 + _y1) / 2 - (H / 2 - 550) / _s, _s)    # curve box centred on (1150, 550)
ZSCR = CAM_Z.P(ZV)
CRIT_X = 300
def crit_y(v): return 770 - v / TZ * 440                        # the critical line Re s = ½ on the left: t = 0 at the bottom

NZ = len(F.PRIME_IDX)                                           # every prime becomes one light
ZF0, ZF1 = A0, h(50.5)                                          # primes → Euler's product
ZD0, ZD1 = h(53), h(65)                                         # the product pours into the curve
ZC0, ZC1 = h(66), h(69.5)                                       # the curve gathers into three corners
LEAD = 5.0
FORM, _ = text_pts('ζ(s) = ∏ 1/(1 − p^{−s})', 74, NZ, 31, tf=CG_I)
FORM = FORM + (960, 250)
_ordz = np.argsort(FORM[:, 0])                                   # the formula drains left to right
TAU = np.empty(NZ); TAU[_ordz] = TZ * (np.arange(NZ) + .5) / NZ
TAU_I = np.clip((TAU / TZ * (NZS - 1)).astype(int), 0, NZS - 1)
PRIME_SCR = F.cam2(F.G0).P(F.ZI[F.PRIME_IDX])


def zhead(t):
    """the walker's height t on the critical line (it starts LEAD below 0 so the first lights can fly before it sets off)"""
    return -LEAD + (TZ + LEAD) * esine((t - ZD0) / (ZD1 - ZD0))


def zero_time(v):
    u = math.acos(1 - 2 * (v + LEAD) / (TZ + LEAD)) / math.pi; return ZD0 + u * (ZD1 - ZD0)


ZERO_T = [zero_time(v) for v in ZEROS]

# the three corners of the chaos game
CORN = np.array([[960.0, 215.0], [640.0, 769.0], [1280.0, 769.0]])


def pool_zeta(t):
    if t < A0 - .02 or t > h(70.5): return NONE(NZ)
    col = GOLD_W[None] * np.ones((NZ, 1))
    if t < ZD0:
        u = clamp((t - ZF0) / (ZF1 - ZF0))
        P = morph(PRIME_SCR, FORM, u, 31, .25, .5)
        a = .38 + .1 * smooth(ZF1 - .4, ZF1, t)
        return P, np.full(NZ, 1.5), col * a
    th = zhead(t)
    v = (th - TAU + LEAD) / LEAD
    P = arc(FORM, ZSCR[TAU_I], v, 32, .22)
    landed = v >= 1
    a = np.where(landed, .4, np.where(v > 0, .6, .48)) * np.ones(NZ)
    if t > ZC0:
        tgt = CORN[np.arange(NZ) % 3] + np.random.default_rng(33).normal(0, 5, (NZ, 2))
        P = morph(ZSCR[TAU_I], tgt, clamp((t - ZC0) / (ZC1 - ZC0)), 34, .3, .45)
        a = a * (1 - smooth(h(69.4), h(70.3), t))
    return P, np.where(landed, 1.4, 1.7), col * a[:, None]


def pool_zhead(t):
    """the walker: on the critical line, and the value ζ(½ + it) on the curve"""
    th = zhead(t); k = smooth(ZD0 + .3, ZD0 + .8, t) * (1 - smooth(ZD1, ZD1 + .6, t))
    if k <= 0 or th < 0: return NONE(2)
    i = int(clamp(th / TZ) * (NZS - 1))
    return np.array([ZSCR[i], [CRIT_X, crit_y(th)]]), np.array([4.0, 3.5]), np.stack([GOLD_W * 2.2, GOLD_W * 1.6]) * k


def zeta_static(t):
    S = []
    kc = smooth(ZD0 - .6, ZD0, t) * (1 - smooth(ZC0, ZC0 + 1.2, t))
    if kc > 0:
        S.append(polyline([[CRIT_X, crit_y(0)], [CRIT_X, crit_y(TZ)]], .9, DIM * 1.1, kc))
        S.append(polyline(CAM_Z.P(np.array([_x0 - .4, _x1 + .4]) + 0j), .7, DIM * .5, kc * .8))                         # real axis
        S.append(polyline(CAM_Z.P(1j * np.array([_y0 - .25, _y1 + .25])), .7, DIM * .5, kc * .8))                       # imaginary axis
        th = zhead(t)
        if th > 0:
            i = int(clamp(th / TZ) * (NZS - 1))
            S.append(polyline(ZSCR[:i + 1:2], 1.1, GOLD_W * .55, kc))
            S.append(polyline([[CRIT_X, crit_y(0)], [CRIT_X, crit_y(min(th, TZ))]], 1.3, GOLD_W * .9, kc))
        o = CAM_Z.P(0j)
        for v, tk in zip(ZEROS, ZERO_T):
            if t >= tk:
                y = crit_y(v); S.append(polyline([[CRIT_X - 8, y], [CRIT_X + 8, y]], 1.2, GOLD_W * 1.2, kc))
                s = t - tk
                if s < 1.6:
                    uu = s / 1.6; R = 4 + 46 * eout(uu)
                    S.append(polyline(o + R * np.stack([np.cos(np.linspace(0, 6.3, 70)), np.sin(np.linspace(0, 6.3, 70))], 1), 1.3, GOLD_W * (1 - uu) ** 1.5 * 1.3, 1.0))
    kk = smooth(h(69), h(70), t) * (1 - smooth(h(85), h(86.4), t))                       # the corners of the chaos game
    if kk > 0:
        S.append(np.concatenate([CORN, CORN, np.full((3, 1), 6.0), np.tile(GOLD_W * 1.6 * kk, (3, 1))], 1))
    return S


# ================================================================ act C · the chaos game (h(70) – h(86))
NU = 32 * 940                                                   # one pool for the chaos game, the tesseract and the Galton board
_rc = np.random.default_rng(41)
CK = _rc.integers(0, 3, NU)
CPTS = np.empty((NU, 2)); _p = np.array([960.0, 560.0])
for k in range(NU): _p = (_p + CORN[CK[k]]) / 2; CPTS[k] = _p
NSLOW = 8
C0, CS1, CF1 = h(70), h(74), h(83)
APPEAR = np.empty(NU)
APPEAR[:NSLOW] = C0 + .5 + np.arange(NSLOW) * BEAT                                  # one jump per beat
APPEAR[NSLOW:] = CS1 + (CF1 - CS1) * np.log(np.arange(NSLOW, NU) / NSLOW) / math.log(NU / NSLOW)
CCOL = np.stack([GOLD_W, ROSE * 1.1, CYAN_W])[CK]


def n_jumps(t): return int(np.searchsorted(APPEAR, t, 'right'))


# ================================================================ act Q · the tesseract (h(86) – h(103))
Q0, QM, Q1 = h(86), h(87.6), h(103)
_V4 = np.array([[(i >> b & 1) * 2 - 1 for b in range(4)] for i in range(16)], float)
EDGES = [(i, i | 1 << b) for i in range(16) for b in range(4) if not i >> b & 1]           # 32 edges
_eu = (np.arange(NU) % 940) / 940 + np.random.default_rng(42).uniform(0, 1 / 940, NU)
_ea = np.array([_V4[EDGES[k // 940][0]] for k in range(NU)]); _eb = np.array([_V4[EDGES[k // 940][1]] for k in range(NU)])
QX = _ea + (_eb - _ea) * _eu[:, None]


def tess(X, t):
    """rotate in the xw and yz planes, project 4D → 3D → screen; returns (screen xy, w after rotation, 4D depth scale)"""
    s = max(0.0, t - Q0); a, b, c = .52 * s, .5 + .27 * s, .45 + .09 * s
    x, y, z, w = X[:, 0], X[:, 1], X[:, 2], X[:, 3]
    x, w = x * math.cos(a) - w * math.sin(a), x * math.sin(a) + w * math.cos(a)
    y, z = y * math.cos(b) - z * math.sin(b), y * math.sin(b) + z * math.cos(b)
    x, z = x * math.cos(c) - z * math.sin(c), x * math.sin(c) + z * math.cos(c)
    k4 = 2.4 / (3.2 - w); k3 = 6 / (6 - z * k4)
    return np.stack([960 + x * k4 * k3 * 118, 478 - y * k4 * k3 * 118], 1), w, k4


# ================================================================ act G · the Galton board (h(103) – h(120))
NB = F.NC                                                       # = the grid of c values that comes next (6,032)
ROWS, DX, DR = 12, 24, .07
G_Y = 247 + 22 * np.arange(ROWS + 1)                             # row i pin height (the last entry = the exit)
FUN = np.array([960.0, 212.0])
_rg = np.random.default_rng(43)
STEP = _rg.choice((-1, 1), (NB, ROWS)); SC_ = np.concatenate([np.zeros((NB, 1)), np.cumsum(STEP, 1)], 1)     # position after each row
GS0, GS1, GF1 = h(104) + .2, h(108), h(116)
REL = np.empty(NB); REL[:NSLOW] = GS0 + np.arange(NSLOW) * BEAT
REL[NSLOW:] = GS1 + (GF1 - GS1) * np.log(np.arange(NSLOW, NB) / NSLOW) / math.log(NB / NSLOW)
BIN = ((SC_[:, -1] + ROWS) / 2).astype(int)
SLOT = np.zeros(NB, int); _cnt = np.zeros(ROWS + 1, int)
for j in np.argsort(REL, kind='stable'): SLOT[j] = _cnt[BIN[j]]; _cnt[BIN[j]] += 1
GCOLS, GSP, FLOOR = 16, 2.6, 769
GFIN = np.stack([960 + DX * SC_[:, -1] - (GCOLS - 1) * GSP / 2 + (SLOT % GCOLS) * GSP, FLOOR - (SLOT // GCOLS) * GSP], 1)
PINS = np.array([[960 + DX * (2 * m - i), G_Y[i] + 7] for i in range(ROWS) for m in range(i + 1)])
TFALL = .3


def galton_pos(t):
    e = t - REL; P = np.repeat(FUN[None], NB, 0).copy()
    fly = (e >= -DR) & (e < 0)
    P[fly] = FUN + (np.array([960.0, G_Y[0] - 5]) - FUN) * ((e[fly] + DR) / DR)[:, None]
    on = (e >= 0) & (e < ROWS * DR)
    i = np.clip((e[on] / DR).astype(int), 0, ROWS - 1); u = e[on] / DR - i
    xa, xb = SC_[on, i], SC_[on, np.minimum(i + 1, ROWS)]
    P[on, 0] = 960 + DX * (xa + (xb - xa) * u); P[on, 1] = G_Y[i] - 5 + (G_Y[i + 1] - G_Y[i]) * u - 9 * np.sin(np.pi * u)
    fall = (e >= ROWS * DR) & (e < ROWS * DR + TFALL)
    v = (e[fall] - ROWS * DR) / TFALL
    ex = np.stack([960 + DX * SC_[fall, -1], np.full(fall.sum(), G_Y[-1] - 5)], 1)
    P[fall] = ex + (GFIN[fall] - ex) * np.stack([v, v * v], 1)
    P[e >= ROWS * DR + TFALL] = GFIN[e >= ROWS * DR + TFALL]
    return P, e


# the c-grid's lights come from the landed balls: matched by x so the morph sweeps across instead of scrambling
_home = F.CAM_M.P(F.CG_)
CG_FROM = np.empty((NB, 2)); CG_FROM[np.lexsort((_home[:, 1], _home[:, 0]))] = GFIN[np.lexsort((GFIN[:, 1], GFIN[:, 0]))]
F.CG_SRC = lambda t: CG_FROM
F.CG_MK0 = .22                                                  # the balls fly a long way to the grid: keep the streaks faint


def pool_u(t):
    """chaos game → tesseract → Galton board, one pool of 30,080 lights"""
    if t < C0 - .02 or t > A1 + .1: return NONE(NU)
    if t < Q0:
        n = n_jumps(t); a = np.clip((t - APPEAR) / .15, 0, 1)
        dens = lerp(.75, .15, clamp(math.log(max(n, 1)) / math.log(NU)))
        return CPTS, np.full(NU, lerp(2.4, 1.15, clamp(math.log(max(n, 1)) / math.log(NU)))), CCOL * (a * dens)[:, None]
    if t < h(103):
        S, w, k4 = tess(QX, t)
        P = morph(CPTS, S, clamp((t - Q0) / (QM - Q0)), 44, .35, .55) if t < QM else S
        mix = (w[:, None] + 1) / 2
        col = GOLD_W[None] * mix + CYAN_W[None] * (1 - mix)
        u = clamp((t - Q0) / (QM - Q0))
        a = (.10 + .05 * (k4 - .8)) * u + (1 - u) * .15
        a = a * (1 - .7 * np.sin(np.pi * u))                                           # 30,000 lights cross the centre at once: dim mid-flight
        col = col * u + CCOL * (1 - u)
        return P, np.full(NU, 1.3), col * a[:, None]
    S, _, _ = tess(QX, h(103))
    u = clamp((t - h(103)) / (h(104) - h(103)))
    tgt = np.repeat(FUN[None], NU, 0) + np.random.default_rng(45).normal(0, 4, (NU, 2))
    P = morph(S, tgt, u, 46, .3, .5)
    a = np.full(NU, .10) * (1 - .6 * u)
    a[NB:] *= 1 - smooth(h(104), h(105), t)
    col = np.tile(IVORY, (NU, 1))
    if t > h(104):
        G, e = galton_pos(t)
        P[:NB] = np.where((e > -DR)[:, None], G, P[:NB])
        landed = e >= ROWS * DR + TFALL
        a[:NB] = np.where(e > -DR, np.where(landed, .5, .85), .05)
        col[:NB] = np.where(landed[:, None], GOLD_W[None] * .9, IVORY[None])
    a = a * (1 - smooth(A1, A1 + .05, t))                                                # handed over to the c-grid
    return P, np.where(np.arange(NU) < NB, 1.3, 1.1), col * a[:, None]


def pool_chaos_head(t):
    """the jumping point during the slow beats, so each halfway jump is visible"""
    if not (C0 + .2 <= t <= APPEAR[NSLOW - 1] + .5): return NONE(1)
    k = int(np.searchsorted(APPEAR[:NSLOW], t))
    if k >= NSLOW: return np.array([CPTS[NSLOW - 1]]), np.array([4.0]), np.array([GOLD_W * 1.5]) * (1 - smooth(APPEAR[-1] + .1, APPEAR[-1] + .5, t))
    pa = CPTS[k - 1] if k > 0 else np.array([960.0, 560.0]); u = eio((t - (APPEAR[k] - .32)) / .32)
    return np.array([pa + (CPTS[k] - pa) * u]), np.array([4.0]), np.array([GOLD_W * 1.8]) * smooth(C0 + .2, C0 + .5, t)


def chaos_static(t):
    S = []
    if C0 + .2 <= t <= APPEAR[NSLOW - 1] + .1:                                           # the chosen corner and the halfway mark
        k = int(np.searchsorted(APPEAR[:NSLOW], t))
        if k < NSLOW:
            pa = CPTS[k - 1] if k > 0 else np.array([960.0, 560.0]); c = CORN[CK[k]]
            ka = smooth(APPEAR[k] - .5, APPEAR[k] - .4, t)
            S.append(polyline([pa, c], 1.0, IVORY * .35, ka))
            ring = c + 14 * np.stack([np.cos(np.linspace(0, 6.3, 40)), np.sin(np.linspace(0, 6.3, 40))], 1)
            S.append(polyline(ring, 1.2, GOLD_W * .9, ka, closed=True))
    kq = smooth(QM - .3, QM + .3, t) * (1 - smooth(h(102.6), h(103.2), t))                # the tesseract's 16 vertices
    if kq > 0:
        V, w, k4 = tess(_V4, t); mix = (w[:, None] + 1) / 2
        S.append(np.concatenate([V, V, (2.2 + 1.6 * (k4 - .8))[:, None], (GOLD_W[None] * mix + CYAN_W[None] * (1 - mix)) * 1.4 * kq], 1))
    kg = smooth(h(103), h(104), t) * (1 - smooth(A1 - .3, A1 + .2, t))                    # pins and bins
    if kg > 0:
        S.append(np.concatenate([PINS, PINS, np.full((len(PINS), 1), 1.7), np.tile(DIM * 1.4 * kg, (len(PINS), 1))], 1))
        for m in range(ROWS + 2):
            x = 960 + DX * (2 * m - ROWS) - DX
            S.append(polyline([[x, 525], [x, FLOOR + 3]], .7, DIM * .8, kg))
        S.append(polyline([[960 - DX * (ROWS + 1), FLOOR + 3], [960 + DX * (ROWS + 1), FLOOR + 3]], .8, DIM * .9, kg))
        kb = smooth(h(113), h(114.5), t) * (1 - smooth(A1 - .3, A1 + .2, t))           # the normal curve over the stacks
        if kb > 0:
            sig = DX * math.sqrt(ROWS); x = np.linspace(-4 * sig, 4 * sig, 200)
            y = NB * (2 * DX) / (sig * math.sqrt(2 * math.pi)) * np.exp(-x * x / (2 * sig * sig)) / GCOLS * GSP
            S.append(polyline(np.stack([960 + x, FLOOR - y - 4], 1), 1.6, GOLD_W * 1.1, kb))
    return S


# ================================================================ captions and readouts of the new block
CAPS = [
    (A0 + .1, h(50.5) - .2, '质数看似杂乱……', 'The primes look scattered…'),
    (h(50.5), h(53) - .2, '……却都藏在欧拉的乘积里', '…yet every one of them hides in Euler’s product.'),
    (h(53), h(57) - .2, '让 s 沿直线 ½ + it 往上走，画出 ζ(s)', 'Let s climb the line ½ + it, and trace the zeta function.'),
    (h(57), h(61) - .2, '它一次次穿过原点：每次就是一个零点', 'Again and again it passes through 0 — each pass is a zero.'),
    (h(61), h(65) - .2, '黎曼猜想：所有非平凡零点都在这条线上？', 'The Riemann hypothesis: do all the nontrivial zeros lie on this line?'),
    (h(65), h(70) - .25, '1859 年至今，还没有人能证明', 'Since 1859, no one has proved it.'),
    (h(70), h(74) - .2, '随机挑一个角，朝它跳一半', 'Pick a corner at random, and jump halfway to it.'),
    (h(74), h(78) - .2, '再挑，再跳……一遍又一遍', 'Pick again, jump again… over and over.'),
    (h(78), h(82) - .2, '乱跳出来的，竟是谢尔宾斯基三角形', 'The random jumps draw a Sierpiński triangle.'),
    (h(82), h(86) - .2, '它是 1.585 维：比线多，比面少', 'It is 1.585-dimensional: more than a line, less than a plane.'),
    (h(86), h(90) - .2, '维度可以是分数，也可以是四', 'A dimension can be a fraction — or four.'),
    (h(90), h(95) - .2, '四维超立方体：16 个顶点，32 条棱', 'The tesseract: 16 vertices, 32 edges.'),
    (h(95), h(99) - .2, '我们看到的，只是它投到三维的影子', 'What we see is only its shadow in three dimensions.'),
    (h(99), h(103) - .2, '它正在第四个维度里翻转', 'It is turning through the fourth dimension.'),
    (h(103), h(107) - .2, '每个点穿过钉板：向左还是向右，全凭运气', 'Each point falls through the pins: left or right is pure chance.'),
    (h(107), h(111) - .2, '单独一个点，完全无法预测', 'No single point can be predicted.'),
    (h(111), h(115) - .2, '六千个点，却堆出一条钟形曲线', 'Yet six thousand of them pile into a bell curve.'),
    (h(115), A1 - .2, '随机也有形状：正态分布', 'Randomness has a shape: the normal distribution.'),
]


def overlay_new(cv, t):
    for t0, t1, zh, en in CAPS: caption(cv, zh, en, t, t0, t1)
    F.ro_primes(cv, t, 1 - smooth(A0, A0 + .4, t))                                 # the primes readout hands over
    kz = fade(t, ZD0 - .4, ZC0 + .6, .5, .6)
    if kz > 0:
        math_tx(cv, [('ζ', 1, 0, 1), ('(½ + ', 1, 0, 0), ('it', 1, 0, 1), (')', 1, 0, 0)], SXT, SY, 40, T_IVORY, kz)
        th = clamp(zhead(t), 0, TZ)
        tx(cv, f't = {th:.3f}', SXT + 2, SY + 46, 26, T_SUB, kz, lf=CG_SB)
        tx(cv, 'Re s = ½', CRIT_X, crit_y(TZ) - 16, 20, T_SUB, kz, 'c', glow=0)
        for v, tk in zip(ZEROS, ZERO_T):
            if t >= tk: tx(cv, f'{v:.2f}', CRIT_X + 16, crit_y(v) + 6, 17, T_GOLD, kz * smooth(tk, tk + .3, t), lf=CG_SB, glow=0)
        o = CAM_Z.P(0j); tx(cv, '0', o[0] - 14, o[1] + 22, 20, T_SUB, kz, 'c', lf=CG_SB, glow=0)
    kc = fade(t, C0 + .4, Q0 + .2, .5, .4)
    if kc > 0:
        n = n_jumps(t)
        tx(cv, lang(f'跳了 {n:,} 次 · {n:,} jumps', f'{n:,} jumps'), SXT, SY, 26, T_IVORY, kc)
        kd = fade(t, h(82), Q0 + .2, .6, .4)
        tx(cv, 'log 3 / log 2 = 1.585', SXR, SY, 30, T_GOLD, kd, lf=CG_SB)
        tx(cv, lang('维数 · dimension', 'dimension'), SXR, SY + 36, 20, T_SUB, kd, glow=0)
    kq = fade(t, QM, h(103) + .2, .6, .4)
    if kq > 0:
        tx(cv, '(x, y, z, w)', SXT, SY, 34, T_IVORY, kq, lf=CG_SBI)
        tx(cv, lang('在 xw、yz 平面里旋转 · rotating in xw, yz', 'rotating in xw, yz'), SXT + 2, SY + 42, 21, T_SUB, kq, glow=0)
        tx(cv, lang('w > 0  金 · gold', 'w > 0  gold'), SXR, SY, 22, T_GOLD, kq, glow=0)
        tx(cv, lang('w < 0  青 · cyan', 'w < 0  cyan'), SXR, SY + 32, 22, T_CYAN, kq, glow=0)
    kg = fade(t, h(103.5), A1 + .2, .5, .4)
    if kg > 0:
        n = int((REL <= t).sum())
        tx(cv, lang(f'{n:,} / {NB:,} 个点 · points', f'{n:,} / {NB:,} points'), SXT, SY, 26, T_IVORY, kg)
        tx(cv, lang(f'{ROWS} 排钉子 · {ROWS} rows of pins', f'{ROWS} rows of pins'), SXT + 2, SY + 36, 20, T_SUB, kg, glow=0)
        kb = fade(t, h(113), A1 + .2, .6, .4)
        math_tx(cv, [('1', 1, 0, 0), ('/√2π', 1, 0, 0), (' e', 1, 0, 1), ('−x²/2', .6, .48, 1)], SXR, SY, 34, T_GOLD, kb)


SXT, SXR, SY = F.SX, 1440, F.SY

# ================================================================ frame
NEW_POOLS = [
    (pool_zeta, (A0, h(70.6)), lambda t: .18 if ZD0 < t < ZC0 else .1, 6),
    (pool_zhead, (ZD0, ZD1 + .7), lambda t: .35, 10),
    (pool_u, (C0 - .05, A1 + .12), lambda t: .02 if t < Q0 else .07 if t < QM else .1 if t < h(103) else .07, 6),
    (pool_chaos_head, (C0, APPEAR[NSLOW - 1] + .6), lambda t: .25, 10),
]
GLX = None


def frame(i):
    global GLX
    t = i / FPS
    if GLX is None: GLX = GL()
    S = []; layers = []; extra = {}; km = kb = 0.0
    new = A0 <= t < A1
    if not new:
        to = t if t < A0 else t - JUMP
        for fn, (a, b), L, k in F.POOLS:
            if fn is F.pool_primes and t >= A1: continue
            if fn is F.pool_cgrid: L = lambda x: .05 if x < F.G1 else .3                # short streaks while they regroup
            if a <= to <= b: S.append(trail_segs(fn, to, L(to), k))
        S += F.static_segs(to)
        km = smooth(F.SETTLE + .1, F.SETTLE + 1.3, to) * (1 - smooth(F.B0, F.B0 + 2.2, to))
        if km > 0 and to < F.B0 + 2.3:
            layers.append((F.mandel_tex(to), km * 1.05, 2.0)); extra['L'] = F._MAND.last_L if to > F.DZ0 else None
        kb = smooth(F.B0, F.B0 + 2.2, to) * (1 - smooth(F.L0, F.LS + .3, to))
        if kb > 0:
            tex, pw = F.bulb_tex(to); layers.append((tex, kb * .5, 2.2)); extra['power'] = pw
        layers += F.hook_layers(t)
    for fn, (a, b), L, k in NEW_POOLS:
        if a <= t <= b: S.append(trail_segs(fn, t, L(t), k))
    if new: S += zeta_static(t) + chaos_static(t)
    S.append(dust(F.cam1(t) if t < F.P0 else Cam(0, 0, 200 * (1 + .02 * t)), t, 1.0 - .6 * max(km, kb)))
    S = cull(np.concatenate([s for s in S if len(s)]))
    k = (1.0 if F.HOOK else smooth(0, .8, t)) * (1 - smooth(T - .6, T, t))
    S[:, 5:8] *= k
    rgb = GLX.run(S, t, bgK=k, layers=[(tx_, kk * k, g) for tx_, kk, g in layers])
    buf = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)]).copy(); surf = skia.Surface(buf); cv = surf.getCanvas()   # buf must outlive surf (skia draws into its memory)
    if not os.environ.get('NOTEXT'):
        if new: overlay_new(cv, t)
        else:
            F.RO_PRIMES = 0.0 if t >= A1 else 1.0
            F.overlay(cv, t if t < A0 else t - JUMP, extra)
    if k < 1: cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 1 - k))
    if not os.environ.get('NOTEXT'): F.BR.watermark(cv, t, T, expand_at=9.2, hold=2.0, end_len=1.9)
    return surf.makeImageSnapshot().toarray()


if __name__ == '__main__':
    os.makedirs(OUT + 'stills', exist_ok=True); NF = int(round(T * FPS))
    if len(sys.argv) > 1 and sys.argv[1] == '--still':
        for a in sys.argv[2:]: skia.Image.fromarray(frame(int(float(a) * FPS))).save(f'{OUT}stills/f_{float(a):06.2f}.jpg', skia.kJPEG, 90); print('still', a, flush=True)
    elif len(sys.argv) > 1 and sys.argv[1] == '--part':
        i, n = int(sys.argv[2]), int(sys.argv[3]); a, b = NF * i // n, NF * (i + 1) // n
        if len(sys.argv) > 5: a, b = int(sys.argv[4]), int(sys.argv[5])
        w = Writer(f'{OUT}part_{i:02d}.mp4' if len(sys.argv) <= 6 else sys.argv[6])
        for f in range(a, b):
            w.write(frame(f))
            if (f - a) % 300 == 0: print(f'part {i}: {f - a}/{b - a}', flush=True)
        w.close()
    else:
        F.lz_hist()
        n = int(os.environ.get('JOBS', 4))
        ps = [subprocess.Popen([sys.executable, __file__, '--part', str(i), str(n)]) for i in range(n)]
        if any(p.wait() for p in ps): raise SystemExit('render failed')
        open(OUT + 'concat.txt', 'w').write(''.join(f"file 'part_{i:02d}.mp4'\n" for i in range(n)))
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', OUT + 'concat.txt', '-c', 'copy', OUT + 'video.mp4'])
        print('ok', OUT + 'video.mp4', f'{T:.2f} s')
