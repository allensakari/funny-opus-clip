"""math-beauty v2「数学之美」· one unbroken camera through mathematics — 16:9, Chinese / English captions.
Timed to the beat grid of《千年以后》(110.64 BPM, h(n) = half-bars; the 抖音 cut carries no music, the song is attached on the platform);
the full cut uses an original score written on the same grid (score.py). Every transition is the mathematics itself changing shape:
  equations dissolve into seeds → seeds at √k·e^{2πikθ} fall onto the unit circle → one point walks to e^{iπ} = −1 →
  that arm is the largest epicycle of 数学's Fourier series → the drawn line shatters into the integers at polar (n, n) → only primes remain →
  the primes become a grid of c values that iterate z → z² + c; escapers fly away, the rest are the Mandelbrot set → deep zoom to 10³² →
  the minibrot rises into the Mandelbulb → its dust collapses to one point → 3,000 Lorenz trajectories 0.0001 apart split →
  every light converges into 数学 → back to the drifting equations.
usage: python film.py | --still t … | --part i n"""
import os, sys, math, cmath, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import numpy as np
import skia
from engine import *
import proto as PR                                            # sunflower / Fourier data from the approved prototype
def _root(p):                                                  # the skill root = the first parent that has engine/channel.py
    while not os.path.exists(os.path.join(p, 'engine', 'channel.py')) and os.path.dirname(p) != p: p = os.path.dirname(p)
    return p
sys.path.append(_root(HERE) + '/engine')                      # the channel's brand mark (dot anchor)
import brand as BR
BR.set_canvas(W, H)
if EN: BR.LANG = 'en'                                         # English corner mark and end card

BUILD = HERE + '/build/film/'
os.makedirs(BUILD, exist_ok=True)


def h(n): return 1.6811 + 1.0846 * n                         # n-th half-bar of《千年以后》(film 0 s = the vocal onset)


T = h(118)                                                    # 129.66 s, a phrase boundary

CAPS = [
    (.6, 4.7, '如果宇宙有源代码，', 'If the universe has source code,'),
    (h(3), 8.9, '它一定是用数学写成的。', 'it must be written in mathematics.'),
    (h(7), h(12) - .2, '每长出一颗种子，就转一个固定的角度', 'Each new seed turns by the same fixed angle.'),
    (h(12), h(14) - .2, '转 137.5°，黄金角：种子排得最密', 'At 137.5°, the golden angle, the seeds pack the tightest.'),
    (h(14), h(16) - .2, '每一颗种子，都是单位圆上的一个点', 'Every seed is a point on the unit circle.'),
    (h(16), h(22) - .25, '让其中一点，沿着单位圆转……', 'Let one point travel around the circle…'),
    (h(22), h(24) - .2, '转过 π，正好落在 −1', 'Turn by π, and it lands exactly on −1.'),
    (h(24), h(27) - .2, '五个最基本的常数，被一个等式连在一起', 'Five fundamental constants, joined in a single equation.'),
    (h(27), h(31) - .2, '很多个圆首尾相连，各自匀速旋转……', 'Chain hundreds of circles, each spinning at its own pace…'),
    (h(31), h(35) - .2, '……就能画出任何形状', '…and they can draw any shape.'),
    (h(35), h(38) - .2, '傅里叶：声音、图像、Wi-Fi，都离不开它', 'Fourier: sound, images and Wi-Fi all rely on it.'),
    (h(38), h(41) - .2, '把每个整数 n，放在极坐标 (n, n) 上', 'Place every whole number n at polar coordinates (n, n).'),
    (h(41), h(44) - .2, '只留下质数', 'Keep only the primes.'),
    (h(44), h(48) - .2, '看似毫无规律的质数，排成了一条条射线', 'The primes, which look random, line up into rays.'),
    (h(48), h(52) - .2, '复平面上的每一个点 c，都重复同一步', 'Every point c on the plane repeats one step.'),
    (h(52), h(55) - .2, '跑掉的点消失，留下来的点……', 'The points that escape vanish; the ones that stay…'),
    (h(55), h(60) - .2, '……就是曼德博集合', '…form the Mandelbrot set.'),
    (h(60), h(68) - .2, '它的边界无限复杂，越放大，细节越多', 'Its boundary is infinitely complex: the closer you look, the more you see.'),
    (h(68), h(70) - .2, '放大 10³² 倍，它又出现了', 'Magnified 10³² times, it appears again.'),
    (h(70), h(76) - .2, '把它推向三维', 'Push it into three dimensions.'),
    (h(76), h(84) - .2, '无限的细节，藏在一个方程里', 'Infinite detail, hidden in a single equation.'),
    (h(84), h(89) - .2, '3,000 个起点，彼此只差 0.0001', '3,000 starting points, just 0.0001 apart.'),
    (h(89), h(96) - .2, '几秒之后，它们分道扬镳', 'Seconds later, they go their separate ways.'),
    (h(96), h(102) - .2, '微小的差别，会长成完全不同的未来', 'A tiny difference grows into an entirely different future.'),
    (h(104), h(110) - .2, '自然之书，是用数学的语言写成的。', 'The book of nature is written in the language of mathematics. — Galileo'),
]

# ================================================================ the first 3 seconds (HOOK=A: the deep zoom rushing in · HOOK=B: z → z² + c in light)
HOOK = os.environ.get('HOOK', 'A')                            # 用户 2026-10-13 选定 A（开场就是深度放大 + 问句）；HOOK= 关掉
HK0, HK1 = 2.7, 4.3                                           # the hook breaks into the drifting equations
if HOOK:
    CAPS = [(3.4, 8.9, '如果宇宙有源代码，它一定是用数学写成的。', 'If the universe has source code, it must be written in mathematics.')] + CAPS[2:]


def hook_mandel_tl(t):
    """deep-zoom shader time for the hook: A rushes from the whole set to ×10¹⁰ (about 3 decades a second); B holds the whole set"""
    return lerp(3.0, 9.5, eio(t / 3.4) * .3 + .7 * t / 3.4) if HOOK == 'A' else 2.6 + .25 * t


def hook_overlay(cv, t):
    k = 1 - smooth(2.9, 3.35, t)
    if k <= 0: return
    cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), .0))
    sc = skia.Paint(AntiAlias=True); sc.setShader(skia.GradientShader.MakeRadial((W / 2, 520), 760, [skia.Color4f(0, 0, 0, .62 * k).toColor(), skia.Color4f(0, 0, 0, 0).toColor()]))
    if HOOK == 'A':
        cv.drawRect(skia.Rect.MakeWH(W, H), sc)
        math_tx(cv, [('z', 1, 0, 1), (' → ', 1, 0, 0), ('z', 1, 0, 1), ('2', .6, .45, 0), (' + ', 1, 0, 0), ('c', 1, 0, 1)], W / 2, 455, 64, T_GOLD, k, 'c', glow=.6)
        tx(cv, lang('一个公式，放大 10³² 倍，会看到什么？', 'One formula, magnified 10³² times — what will you see?'), W / 2, 575, lang(72, 60), T_IVORY, k, 'c', glow=.5)
        if _MAND is not None:
            L = _MAND.last_L; e = int(L); m = 10 ** (L - e)
            wd = tx(cv, f'ZOOM  × {m:.2f} × 10', SXR, SY, 30, T_IVORY, k, lf=CG_SB, glow=.2)
            tx(cv, f'{e}', SXR + wd + 3, SY - 18, 19, T_IVORY, k, lf=CG_SB, glow=0)
    else:
        tx(cv, lang('一行公式，能画出多复杂的东西？', 'How complex can a single line of math get?'), W / 2, 700, lang(72, 60), T_IVORY, k, 'c', glow=.5)


# ================================================================ act 0 · equations drifting in the dark (0 – 8.9 s, and the closing)
EQS = ['E = mc^2', 'e^{iπ} + 1 = 0', 'a^2 + b^2 = c^2', 'φ = (1 + √5) / 2', 'V − E + F = 2', 'z → z^2 + c', 'π = 3.14159265…',
       'iħ ∂ψ/∂t = Ĥψ', '∇ · E = ρ / ε_0', 'ζ(s) = ∑ 1/n^s', '∫ e^{−x²} dx = √π', 'f(t) = ∑ c_n e^{2πint}', 'G_{μν} + Λg_{μν} = 8πG T_{μν}', 'dx/dt = σ(y − x)']
_re = np.random.default_rng(21)
EQ_LAY = []                                                     # (string, x, y, depth, size)
_slots = [(420, 215), (980, 240), (1500, 205), (620, 340), (1420, 320), (400, 450), (900, 430), (1400, 460),
          (600, 560), (1080, 545), (1520, 575), (470, 690), (1000, 675), (1460, 700)]     # on-screen centres at the widest point of the push-in
_order = [0, 1, 2, 12, 11, 3, 4, 13, 5, 6, 10, 7, 8, 9]                                  # which equation sits in which slot
TAU_MAX = 9.2                                                                            # the push-in never takes them out of x 200–1720, y 170–780
for i, s in enumerate(EQS):                                                              # (safe area for the platforms' UI; captions live below 780)
    d = _re.uniform(.05, 1.0); _re.uniform(-1, 1); _re.uniform(-1, 1); sz = 46 + 40 * (1 - d)
    p, _ = text_pts(s, sz, int(15 * len(s.replace('{', '').replace('}', '').replace('^', '').replace('_', '')) * sz / 46), seed=i, tf=CG_I)
    sx, sy = _slots[_order.index(i)]; g = 1 + .022 * TAU_MAX * (1.25 - d)
    EQ_LAY.append((s, 960 + (sx - 960) / g - (p[:, 0].min() + p[:, 0].max()) / 2, 540 + (sy - 540) / g - (p[:, 1].min() + p[:, 1].max()) / 2, d, sz))
EQ_PTS, EQ_ID = [], []
for i, (s, x, y, d, sz) in enumerate(EQ_LAY):
    p, _ = text_pts(s, sz, int(15 * len(s.replace('{', '').replace('}', '').replace('^', '').replace('_', '')) * sz / 46), seed=i, tf=CG_I)
    EQ_PTS.append(p); EQ_ID.append(np.full(len(p), i))
EQ_PTS = np.concatenate(EQ_PTS); EQ_ID = np.concatenate(EQ_ID); NE = len(EQ_PTS)
EQ_X = np.array([EQ_LAY[i][1] for i in EQ_ID]); EQ_Y = np.array([EQ_LAY[i][2] for i in EQ_ID]); EQ_D = np.array([EQ_LAY[i][3] for i in EQ_ID])
EQ_PH = _re.uniform(0, 6.28, NE)


def eq_pos(tau):
    """drifting equations: a slow push-in, nearer ones faster; depth sets blur (depth of field, focus at d≈.55)"""
    g = 1 + .022 * tau * (1.25 - EQ_D)
    x = 960 + (EQ_X + EQ_PTS[:, 0] + 6 * np.sin(tau * .3 + EQ_D * 9) - 960) * g
    y = 540 + (EQ_Y + EQ_PTS[:, 1] + 5 * np.cos(tau * .25 + EQ_D * 7) - 540) * g
    blur = np.abs(EQ_D - .55) ** 1.4 * 7
    r = 1.0 + blur
    b = .95 / (1 + .35 * blur * blur) * (.85 + .15 * np.sin(tau * 1.3 + EQ_PH))
    return np.stack([x, y], 1), r, b


# ================================================================ act 1 · sunflower → unit circle → Euler → Fourier (8.9 – 42.9 s)
N, KS = PR.N, PR.KS
HOLD = [8.9, h(8), h(9), h(10), h(11)]
TG = h(12)
COLLAPSE = h(14)                                             # the drums enter: seeds fall onto the circle


def turn(t):
    pts = [(HOLD[i], PR.CONV[i][0] / PR.CONV[i][1]) for i in range(5)] + [(TG, PR.PHI2)]
    if t <= pts[0][0]: return pts[0][1]
    for (ta, fa), (tb, fb) in zip(pts, pts[1:]):
        if t < tb: return lerp(fa, fb, eio((t - (tb - .5)) / .5))
    return PR.PHI2


def seeds_z(t):
    ang = 2 * math.pi * KS * turn(t)
    u = np.clip((t - COLLAPSE - .5 * (1 - KS / N)) / 1.3, 0, 1); u = u * u * (3 - 2 * u)
    return (PR.C0 * np.sqrt(KS) * (1 - u) + u) * np.exp(1j * ang), u


TE0, TE1 = h(17), h(22)
def theta(t): return math.pi * esine((t - TE0) / (TE1 - TE0))


CF, FQ, RECON, PEN, NK = PR.CF, PR.FQ, PR.RECON, PR.PEN, PR.NK
GROW0, GROW1, TF0, TF1 = h(26), h(27) - .1, h(27), h(35)
TAU0 = PR.TAU0
def tau(t): return TAU0 + eio((t - TF0) / (TF1 - TF0))


def grow(t):
    j = np.arange(NK); a = GROW0 + (GROW1 - GROW0) * (j / NK) ** .6
    g = np.clip((t - a) / .35, 0, 1); g[0] = 1.0; return g * g * (3 - 2 * g)


CAM_SUN = Cam(0, 0, 108); CAM_UNIT = Cam(0, .05, 300)
_sf = PR.CAM_FOUR.s * .84; CAM_FOUR = Cam(PR.GC.real, PR.GC.imag - 75 / _sf, _sf)      # smaller and higher: clear of the captions


def cam1(t):
    if t < COLLAPSE: return Cam(0, 0, 108 * (1 + .012 * max(0, t - 8.9)))
    s0 = Cam(0, 0, 108 * (1 + .012 * (COLLAPSE - 8.9)))
    if t < GROW0: return cam_mix(s0, CAM_UNIT, esine((t - COLLAPSE) / 2.0))
    return cam_mix(CAM_UNIT, CAM_FOUR, esine((t - GROW0) / 1.9))


# ================================================================ act 2 · integers at polar (n, n), then primes (42.9 – 53.7 s)
NI = 40000
_isp = np.ones(NI + 1, bool); _isp[:2] = False
for p in range(2, int(NI ** .5) + 1):
    if _isp[p]: _isp[p * p::p] = False
INTS = np.arange(1, NI + 1); ISP = _isp[1:]
ZI = INTS * np.exp(1j * INTS.astype(float))
P0, P1 = h(38), h(40)
ZOUT0, ZOUT1 = h(40) + .4, h(47) + .4


def cam2(t):
    s = math.exp(lerp(math.log(3.6), math.log(400 / NI), esine((t - ZOUT0) / (ZOUT1 - ZOUT0))))
    return Cam(0, 0, s)


_src = np.nonzero(PEN)[0]
PR_SRC = RECON[_src[np.arange(NI) * len(_src) // NI]]           # the drawn line, resampled onto 40,000 lights


# ================================================================ act 3 · every c iterates z → z² + c (53.7 – 61.3 s), then the deep zoom
CAM_M = Cam(-0.62, 0.0, (H / 2) / 1.22)                          # = the deep-zoom shader's opening view
GX, GY = 104, 58
_gx, _gy = np.meshgrid(np.linspace(-2.75, 1.5, GX), np.linspace(-1.18, 1.18, GY))
CG_ = (_gx + 1j * _gy).ravel(); NC = len(CG_)
NIT = 24
ZIT = np.zeros((NIT + 1, NC), complex); _z = np.zeros(NC, complex); ESC = np.full(NC, 999)
for k in range(1, NIT + 1):
    _z = np.where(np.abs(_z) < 1e3, _z * _z + CG_, _z); ZIT[k] = _z
    ESC = np.where((np.abs(_z) > 2) & (ESC == 999), k, ESC)
INSIDE = ESC == 999
_zz = c_ = CG_.copy(); _w = np.zeros(NC, complex)
for _ in range(400): _w = np.where(np.abs(_w) < 1e3, _w * _w + c_, _w)
INSIDE = INSIDE & (np.abs(_w) < 2)                                 # the set (to 400 iterations), so the particles match the shader
G0, G1 = h(48), h(49.5)
IT0, ITD = h(50), .19
SETTLE = h(54)
DZ0, DZ1 = h(55) + .1, h(69)


def it_pos(t):
    """orbit position of every c at fractional iteration (straight jumps; escapers keep flying outward)"""
    x = clamp((t - IT0) / ITD, 0, NIT); k = int(x); f = eio(x - k)
    za = ZIT[k]; zb = ZIT[min(NIT, k + 1)]; z = za + (zb - za) * f
    esc = ESC <= x
    ang = np.angle(np.where(esc, ZIT[np.clip(ESC, 0, NIT), np.arange(NC)], 1)); fly = np.maximum(0, x - ESC) ** 1.6 * .9 + 2.2
    z = np.where(esc & ~INSIDE, fly * np.exp(1j * ang), z)
    z = np.where(np.abs(z) > 30, 30 * z / np.abs(z), z)
    return z


# ================================================================ act 4 · the Mandelbulb (77.6 – 94 s) · act 5 · Lorenz (92.8 – 114 s)
B0, BP0, BP1, B1 = h(70), h(71), h(79), h(84)
L0, LS = h(84), h(85.1)                                         # dust collapses; the simulation starts
NP = 3000
SIG, RHO, BETA = 10.0, 28.0, 8.0 / 3.0


def _f(p):
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    return np.stack([SIG * (y - x), x * (RHO - z) - y, x * y - BETA * z], -1)


def _rk4(p, hh):
    k1 = _f(p); k2 = _f(p + hh / 2 * k1); k3 = _f(p + hh / 2 * k2); k4 = _f(p + hh * k3)
    return p + hh / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


_LZ = None
LZ_FPS, LZ_DT = 60, .021                                       # sim time per frame (= the old film)


def lz_hist():
    global _LZ
    if _LZ is not None: return _LZ
    f = BUILD + 'lorenz.npy'
    if os.path.exists(f): _LZ = np.load(f); return _LZ
    p = np.array([1.0, 1.0, 1.0])
    for _ in range(3000): p = _rk4(p, .005)
    rr = np.random.default_rng(7); off = rr.normal(0, 1, (NP, 3)); off *= 1e-4 / np.linalg.norm(off, axis=1, keepdims=True) * rr.uniform(.2, 1, (NP, 1))
    P = p + off; nfr = int((T - LS) * LZ_FPS) + 4; out = np.zeros((nfr, NP, 3), np.float32)
    for i in range(nfr):
        out[i] = P
        for _ in range(6): P = _rk4(P, LZ_DT / 6)
    np.save(f, out); _LZ = out; return out


GHOST = None


def lz_ghost():
    global GHOST
    if GHOST is None:
        p = np.array([1.0, 1.0, 1.0]); out = []
        for i in range(24000):
            p = _rk4(p, .004)
            if i > 2000: out.append(p)
        GHOST = np.array(out)
    return GHOST


def lz_proj(P, t):
    a = .5 + .13 * (t - L0)
    x = P[..., 0] * math.cos(a) - P[..., 1] * math.sin(a); dep = P[..., 0] * math.sin(a) + P[..., 1] * math.cos(a)
    g = 1 / (1 + dep * .006)
    return np.stack([960 + x * 19 * g, 560 - (P[..., 2] - 25) * 16.5 * g], -1)


LZ_COL = None
FIN0, FIN1 = h(102), h(104)                                    # second climax: everything converges into 数学
CLOSE0, CLOSE1 = h(110), h(112.5)
FIN_PTS, _ = text_pts(lang('数学', 'MATH'), lang(380, 300), NP, 3, tf=CG_SB if EN else None)
FIN_XY = FIN_PTS + (960, 470)


# ================================================================ light pools (each keeps a fixed size so trails can follow every light)
def pool_eq(t):
    """equations; at 7.1 s the first 1,500 lights become the seeds; at the close they come back"""
    if t < 9.2:
        P, r, b = eq_pos(t)
        u = clamp((t - 7.1) / 1.8)
        a = smooth(0, 1.2, t) * np.ones(NE)
        if HOOK:
            uh = clamp((t - HK0) / (HK1 - HK0))
            if uh < 1:
                P = morph(HOOK_SRC, P, uh, 2, .3, .5); r = lerp(1.6, 1.0, uh) + r * uh
                b = lerp(HOOK_B, b, uh) * (1 - .65 * math.sin(math.pi * uh))      # thousands of lights in flight at once: keep them dim
            a = (smooth(2.5, 3.1, t) if HOOK == 'A' else 1.0) * np.ones(NE)
        if u > 0:
            tgt = PR_seed_screen(t)
            P = P.copy(); P[EQ2SEED] = morph(P[EQ2SEED], tgt, u, 1, .12, .5)
            rest = np.ones(NE, bool); rest[EQ2SEED] = False
            a = a * np.where(rest, 1 - smooth(0, .7, u), 1.0)
            r = np.where(rest, r, lerp(1.0, 2.0, u) * np.ones(NE)); b = np.where(rest, b, lerp(b, .75, u))
            a = a * np.where(rest, 1, 1 - smooth(.97, 1.0, u))
        col = IVORY[None] * b[:, None]
        return P, r, col * a[:, None]
    if t > CLOSE0 - .05:
        tau_ = max(0.0, t - CLOSE0)
        P, r, b = eq_pos(tau_ * .6)
        a = smooth(CLOSE0 + .6, CLOSE1, t) * (1 - smooth(T - 2.4, T - .4, t))
        a = np.where(np.arange(NE) < NP, smooth(CLOSE1 - .05, CLOSE1 + .05, t) * (1 - smooth(T - 2.4, T - .4, t)), a)
        return P, r, IVORY[None] * (b * a)[:, None]
    return np.zeros((NE, 2)), np.ones(NE), np.zeros((NE, 3))


if HOOK == 'A':                                                  # the fractal shatters into lights that become the equations
    _rh = np.random.default_rng(22); _a = _rh.uniform(0, 6.283, NE); _r = 40 * np.sqrt(_rh.uniform(0, 1, NE))
    HOOK_SRC = np.stack([W / 2 + _r * np.cos(_a), 540 + _r * np.sin(_a)], 1); HOOK_B = .3        # the zoom's vanishing point blooms into the equations
elif HOOK == 'B':                                                # every light of the equations first spells z → z² + c
    HOOK_SRC = text_pts('z → z^2 + c', 230, NE, 23, tf=CG_I)[0] + (W / 2, 430); HOOK_B = .55


def PR_seed_screen(t):
    z, _ = seeds_z(max(t, 8.9))
    return cam1(t).P(z)


_ang_e = np.arctan2(EQ_Y + EQ_PTS[:, 1] - 540, EQ_X + EQ_PTS[:, 0] - 960)
_pick = np.sort(np.random.default_rng(4).choice(NE, N, replace=False))
_ord_src = _pick[np.argsort(_ang_e[_pick])]
_z0, _ = seeds_z(8.9); _ang_s = np.angle(_z0)
EQ2SEED = np.empty(N, int); EQ2SEED[np.argsort(_ang_s)] = _ord_src      # matched by angle: the swirl stays coherent


def pool_seeds(t):
    c = cam1(t)
    if t < 9.0 - .02 or t > GROW0 + 1.2: return np.zeros((N, 2)), np.ones(N), np.zeros((N, 3))
    z, u = seeds_z(t)
    ring = smooth(COLLAPSE + .7, COLLAPSE + 1.9, t)
    col = PR.SEED_COL * (1 - ring) + CYAN_W[None] * ring * .9
    a = smooth(8.98, 9.02, t) * (1 - .72 * smooth(TE0 + .2, TE0 + 1.4, t)) * (1 - smooth(GROW0 + .2, GROW0 + 1.0, t))
    return c.P(z), 2.0 + .4 * (1 - u), col * .75 * a


def pool_euler(t):
    c = cam1(t); th = theta(t); kp = smooth(TE0 - .3, TE0 + .1, t) * (1 - smooth(GROW0 + .2, GROW0 + .25, t))
    p = c.P(np.array([np.exp(1j * th)] * 2))
    return p, np.array([5.0, 16]), np.stack([GOLD_W * 2.0 * kp, GOLD * .35 * kp])


_vis_end = np.abs(ZI) * 3.6 < 640                                  # integers on screen when the morph lands
PR_SRC = RECON[_src[(np.cumsum(_vis_end) * len(_src) // max(1, _vis_end.sum())) % len(_src)]]   # the visible ones come from evenly spaced points of the line


def pool_primes(t):
    if t < P0 - .02 or t > G1 + .1: return np.zeros((NI, 2)), np.ones(NI), np.zeros((NI, 3))
    c = cam2(t); B = c.P(ZI)
    u = clamp((t - P0) / (P1 - P0))
    if u < 1: P = morph(CAM_FOUR.P(PR_SRC), B, u, 5, .2, .55)
    else: P = B
    comp = 1 - smooth(h(41), h(41) + 1.0, t)
    dens = clamp((c.s / 3.6) ** .3, .3, 1)
    a = np.where(ISP, 1.0, comp * .7) * dens
    a = a * np.where(_vis_end, 1.0, smooth(P1 - .2, P1 + .6, t))     # the far ones appear as the camera pulls back
    col = np.where(ISP[:, None], GOLD_W[None] * .8, IVORY[None] * .5)
    hand = 1 - smooth(G0, G0 + .05, t)                                   # handed over to the c-grid
    r = np.where(ISP, 1.5, 1.2)
    return P, r, col * (a * hand)[:, None]


_rp = np.random.default_rng(9).permutation(NC)
PRIME_IDX = np.nonzero(ISP)[0]
CG_SRC = None                                                       # loop cut: where the grid's lights come from (default: the primes)
CG_MK0 = .45                                                        # brightness of the lights while they regroup into the grid


def pool_cgrid(t):
    """every c is tested: wave after wave, the points that escape fly outward (cyan); the ones that stay are the set (gold)"""
    if t < G0 - .02 or t > SETTLE + 2.0: return np.zeros((NC, 2)), np.ones(NC), np.zeros((NC, 3))
    home = CAM_M.P(CG_)
    x = clamp((t - IT0) / ITD, 0, NIT)
    if t < G1:
        src = CG_SRC(t) if CG_SRC else cam2(t).P(ZI[PRIME_IDX[_rp % len(PRIME_IDX)]])
        P = morph(src, home, clamp((t - G0) / (G1 - G0)), 6, .15, .5)
        mk = CG_MK0 + (1 - CG_MK0) * smooth(G1 - .3, G1, t)
    else:
        go = np.maximum(0, x - ESC) * ITD                                  # seconds since this point escaped
        dirn = CG_ + .35 - 0j; dirn = dirn / np.maximum(np.abs(dirn), 1e-3)
        z = CG_ + dirn * (go ** 1.8) * 2.2 * (~INSIDE)
        P = CAM_M.P(z)
    esc = (ESC <= x) & ~INSIDE
    kesc = np.clip(1 - np.maximum(0, x - ESC) * ITD / 1.4, 0, 1)
    glow = smooth(SETTLE - 1.5, SETTLE, t)
    col = np.where(INSIDE[:, None], GOLD_W[None] * (.45 + .5 * glow), np.where(esc[:, None], CYAN_W[None] * .55, IVORY[None] * .35))
    a = np.where(esc, kesc, 1.0) * (1 - smooth(SETTLE + .6, SETTLE + 1.6, t)) * (mk if t < G1 else 1.0)
    return P, np.where(INSIDE, 1.7, 1.3), col * a[:, None]


_rl = np.random.default_rng(11)
DUST_SRC = np.stack([960 + _rl.normal(0, 1, NP) * 210, 540 + _rl.normal(0, 1, NP) * 170], 1)


def lz_col():
    global LZ_COL
    if LZ_COL is None:
        Hh = lz_hist(); d = np.linalg.norm(Hh[0] - Hh[0].mean(0), axis=1); o = np.argsort(np.argsort(d)) / NP
        LZ_COL = (GOLD_W[None] * (1 - o)[:, None] ** 2 + ROSE[None] * (2 * o * (1 - o))[:, None] * 2 + CYAN_W[None] * (o ** 2)[:, None])
    return LZ_COL


def lz_at(t):
    Hh = lz_hist(); x = clamp((t - LS) * LZ_FPS, 0, len(Hh) - 1.001); i = int(x); f = x - i
    return Hh[i] * (1 - f) + Hh[i + 1] * f


def pool_lorenz(t):
    if t < L0 - .02: return np.zeros((NP, 2)), np.ones(NP), np.zeros((NP, 3))
    col = lz_col()
    if t < LS:
        start = lz_proj(lz_at(LS), LS)[0]
        P = morph(DUST_SRC, np.repeat(start[None], NP, 0), clamp((t - L0) / (LS - L0)), 12, .5, .5)
        a = smooth(L0, L0 + .4, t) * .16
        return P, 1.3 * np.ones(NP), IVORY[None] * a * np.ones((NP, 1))
    P = lz_proj(lz_at(min(t, FIN0)), min(t, FIN0))
    if t > FIN0: P = morph(P, FIN_XY, clamp((t - FIN0) / (FIN1 - FIN0)), 13, .45, .5)
    if t > CLOSE0:
        tgt, _, _ = eq_pos(0.0); P = morph(FIN_XY, tgt[:NP], clamp((t - CLOSE0) / (CLOSE1 - CLOSE0)), 14, .35, .5)
    spread = float(np.linalg.norm(lz_at(t) - lz_at(t).mean(0), axis=1).mean()) if t < FIN0 else 10
    a = clamp(.035 + .008 * spread, .035, .1) * np.ones(NP)              # dense at first (one bright point), then fine threads
    a = a + (1 - a) * smooth(FIN0 + .6, FIN1, t) * .55
    a = a * (1 - smooth(CLOSE1 - .05, CLOSE1 + .05, t))
    fin = smooth(FIN0 + 1.0, FIN1 + .4, t)
    c = col * (1 - fin) + GOLD_W[None] * fin
    return P, (1.6 + .4 * fin) * np.ones(NP), c * a[:, None]


POOLS = [  # (fn, active window, trail length(t), trail steps)
    (pool_eq, (0, 9.3), lambda t: .05 + .1 * math.sin(math.pi * clamp((t - 7.1) / 1.8)) + (.05 * math.sin(math.pi * clamp((t - HK0) / (HK1 - HK0))) if HOOK else 0), 8),
    (pool_eq, (CLOSE0 - .1, T), lambda t: .05 + .2 * math.sin(math.pi * clamp((t - CLOSE0) / 2.5)), 6),
    (pool_seeds, (8.9, GROW0 + 1.3), lambda t: (.025 if t < TG + .3 else .1) + .3 * math.sin(math.pi * clamp((t - COLLAPSE) / 2.0)), 10),
    (pool_euler, (TE0 - .4, GROW0 + .4), lambda t: .3, 10),
    (pool_primes, (P0 - .05, G1 + .2), lambda t: .2 * math.sin(math.pi * clamp((t - P0) / (P1 - P0))) + .001, 5),
    (pool_cgrid, (G0 - .05, SETTLE + 2.1), lambda t: .14 if t < G1 else .3, 8),
    (pool_lorenz, (L0 - .05, CLOSE1 + .2), lambda t: .6 if t < FIN0 else .12, 18),
]


# ================================================================ fractal layers (the old engine's deep-zoom and ray-marching shaders)
_MAND = _BULB = None


def mandel_tex(t):
    global _MAND
    if _MAND is None:
        sys.path.insert(0, ROOT); import scene_mandel
        _MAND = scene_mandel.Mandel()
    tl = clamp((t - DZ0) / (DZ1 - DZ0)) * 19.5
    return _MAND.render(tl)


def bulb_tex(t):
    global _BULB
    if _BULB is None:
        sys.path.insert(0, ROOT); import scene_bulb, core, moderngl
        _BULB = scene_bulb.Scene(); _BULB.core, _BULB.mgl = core, moderngl
    sc, core, mg = _BULB, _BULB.core, _BULB.mgl
    c = core.ctx(); s = t - B0
    power = 3.0 + 5.0 * eio((t - BP0) / (BP1 - BP0))
    tilt = eio((t - B0) / 6.5)                                         # from straight above to an orbit
    a = .4 + .05 * s; r = lerp(3.6, 3.05, eio(s / 14)); zc = lerp(r, .9, tilt)
    rh = math.sqrt(max(1e-4, r * r - zc * zc)) + .02
    ro = (rh * math.cos(a), rh * math.sin(a), zc); ta = (0.0, 0.0, 0.0)
    sc.fb.use(); c.viewport = (0, 0, W, H); sc.fb.clear(0, 0, 0, 0)
    c.enable(mg.BLEND); c.blend_func = mg.ONE, mg.ONE
    jit = [(-0.25, -0.25), (0.25, 0.25), (0.25, -0.25), (-0.25, 0.25)]; n = int(os.environ.get('BSS', 4))
    for j in range(n):
        core.setu(sc.prog, res=(float(W), float(H)), jitter=jit[j], time=t, power=power, wgt=1.0 / n, ro=ro, ta=ta, fov=1.35)
        for k in range(4):
            sc.fb.scissor = (0, H * k // 4, W, H * (k + 1) // 4 - H * k // 4); sc.vao.render(mg.TRIANGLE_STRIP); c.finish()
    sc.fb.scissor = None; c.disable(mg.BLEND)
    return sc.tex, power


def hook_layers(t):
    """A: the deep zoom fills the frame and fades as it shatters · B: the whole set, faint, behind the formula"""
    if not HOOK or t > 3.7: return []
    global _MAND
    if _MAND is None:
        sys.path.insert(0, ROOT); import scene_mandel
        _MAND = scene_mandel.Mandel()
    g = (1.05 if HOOK == 'A' else .28) * (1 - smooth(2.8, 3.6, t))
    return [(_MAND.render(hook_mandel_tl(t)), g, 2.0)]


# ================================================================ static light (lines that do not need trails)
def static_segs(t):
    S = []
    c = cam1(t)
    ke = smooth(TE0 - .6, TE0 + .2, t) * (1 - smooth(GROW0 + .4, GROW0 + 1.2, t))
    if ke > 0:
        S.append(polyline(c.P(np.array([-1.7, 1.7]) + 0j), .9, DIM * .9, ke)); S.append(polyline(c.P(1j * np.array([-1.7, 1.7])), .9, DIM * .9, ke))
        th = theta(t); arc = np.exp(1j * np.linspace(0, th, max(2, int(th * 60))))
        S.append(polyline(c.P(arc), 1.6, CYAN_W * 1.2, ke * smooth(TE0 - .1, TE0 + .1, t)))
        S.append(polyline(c.P(np.array([0, np.exp(1j * th)])), 1.1, IVORY * .8, ke * smooth(TE0 - .1, TE0 + .2, t)))
        S.append(polyline(c.P(np.exp(1j * np.linspace(0, th, 40)) * .22), 1.0, IVORY * .5, ke * smooth(TE0, TE0 + .4, t)))
        s = t - TE1
        if s > 0:
            for d in (0, .3):
                uu = clamp((s - d) / 1.6); R = .02 + .5 * eout(uu)
                S.append(polyline(c.P(-1 + R * np.exp(1j * np.linspace(0, 2 * np.pi, 90))), 1.3, GOLD_W * (1 - uu) ** 1.5 * 1.2, 1.0, closed=True))
    kf = smooth(GROW0 - .05, GROW0 + .2, t) * (1 - smooth(P0 - .1, P0 + .5, t))
    if kf > 0:
        g = grow(t); tt = tau(t)
        terms = CF * g * np.exp(2j * np.pi * FQ * tt); centres = np.concatenate([[0j], np.cumsum(terms)])
        ring = np.exp(1j * np.linspace(0, 2 * np.pi, 48)); R = np.abs(CF) * g
        circles_k = kf * (1 - smooth(TF1, TF1 + 1.5, t) * .7)
        vis = np.nonzero(R * c.s > 1.5)[0]
        for k_, row in zip(vis, c.P(centres[vis][:, None] + R[vis][:, None] * ring[None])):
            S.append(polyline(row, .8, IVORY * (.10 + .2 * (k_ == 0)), circles_k, closed=True))
        S.append(polyline(c.P(centres), 1.0, IVORY * .45, circles_k))
        tip = c.P(centres[-1:])
        S.append(np.concatenate([tip, tip, [[4.0]], [GOLD_W * 2.2 * kf]], 1)); S.append(np.concatenate([tip, tip, [[14.0]], [GOLD * .4 * kf]], 1))
        if t > TF0:
            n = int((tt - TAU0) * len(RECON)); i0 = int(TAU0 * len(RECON)); idx = np.arange(i0, i0 + n + 1) % len(RECON)
            if len(idx) > 1:
                age = (n - np.arange(len(idx))) / len(RECON)
                S.append(polyline(c.P(RECON[idx]), 1.7, GOLD_W * 1.1, PEN[idx] * (.55 + .45 * np.exp(-age * 20)) * kf))
    kg = smooth(LS + 1.5, LS + 4, t) * (1 - smooth(FIN0, FIN0 + 1, t))
    if kg > 0: S.append(polyline(lz_proj(lz_ghost()[::3], t), .8, CYAN * .06, kg))
    return S


# ================================================================ words on screen (beyond the captions)
SX, SY, SXR = 200, 230, 1400                                  # formula readouts: inside the 16:9 safe area, below / right of the brand mark


RO_PRIMES = 1.0                                                # the loop cut switches the primes readout off once the grid takes over


def ro_primes(cv, t, kp):
    if kp > 0:
        math_tx(cv, [('(', 1, 0, 0), ('r', 1, 0, 1), (', θ) = (', 1, 0, 0), ('n', 1, 0, 1), (', ', 1, 0, 0), ('n', 1, 0, 1), (')', 1, 0, 0)], SX, SY, 44, T_IVORY, kp)
        nmax = int(min(NI, (W / 2) / cam2(t).s))
        tx(cv, f'n ≤ {nmax:,}', SX + 2, SY + 52, 26, T_SUB, kp, lf=CG_SB)
        tx(cv, lang('金色 = 质数 · gold = primes', 'gold = primes'), SX + 2, SY + 92, 22, T_GOLD, kp * smooth(h(41), h(41) + .6, t), glow=0)


def overlay(cv, t, extra):
    if HOOK: hook_overlay(cv, t)
    for t0, t1, zh, en in CAPS: caption(cv, zh, en, t, t0, t1)
    k = fade(t, 9.0, COLLAPSE + .2, .4, .5); x = 1480
    if k > 0:
        f = turn(t)
        tx(cv, lang('TURN ANGLE · 每次转过的角度', 'TURN ANGLE'), x, 330, 20, T_SUB, k, glow=0)
        tx(cv, f'θ = {f * 360:.3f}°', x, 380, 40, T_IVORY, k)
        locked = [i for i in range(5) if HOLD[i] <= t < (HOLD[i + 1] if i + 1 < 5 else TG)]
        if t >= TG:
            kg = smooth(TG, TG + .4, t); tx(cv, '= 360° / φ²', x, 435, 34, T_GOLD, k * kg, lf=CG_SBI)
            tx(cv, lang('黄金角 · the golden angle', 'the golden angle'), x, 485, 26, T_GOLD, k * kg)
        elif locked:
            p, q = PR.CONV[locked[0]]
            tx(cv, f'≈ 360° × {p}/{q}', x, 435, 34, T_GOLD, k, lf=CG_SBI); tx(cv, lang(f'{q} 条旋臂 · {q} spiral arms', f'{q} spiral arms'), x, 485, 26, T_GOLD, k)
    c = cam1(t)
    ke = fade(t, TE0 - .6, GROW0 + .8, .5, .5)
    if ke > 0:
        for z, s_ in ((1, '1'), (-1, '−1'), (1j, 'i'), (-1j, '−i')):
            p = c.P(np.array([z * 1.12]))[0]; tx(cv, s_, p[0], p[1] + 12, 30, T_SUB, ke, 'c', lf=CG_SBI if 'i' in s_ else CG_SB, glow=0)
        th = theta(t); p = c.P(np.array([.34 * np.exp(1j * th / 2)]))[0]
        tx(cv, 'θ', p[0], p[1] + 10, 26, T_IVORY, ke * smooth(TE0, TE0 + .4, t), 'c', lf=CG_SBI, glow=0)
        math_tx(cv, [('e', 1, 0, 1), ('iθ', .6, .48, 1), ('  = cos θ + ', 1, 0, 0), ('i', 1, 0, 1), (' sin θ', 1, 0, 0)], W / 2, SY + 20, 52, T_IVORY, ke * smooth(TE0 - .2, TE0 + .3, t) * (1 - smooth(TE1 - .1, TE1 + .2, t)), 'c')
        math_tx(cv, [('e', 1, 0, 1), ('iπ', .6, .48, 1), (' + 1 = 0', 1, 0, 0)], W / 2, SY + 30, 86, T_GOLD, ke * smooth(TE1, TE1 + .5, t), 'c', glow=.6)
    kf = fade(t, TF0 - .2, P0 + .6, .6, .5)
    if kf > 0:
        math_tx(cv, [('f', 1, 0, 1), ('(', 1, 0, 0), ('t', 1, 0, 1), (') = ∑ ', 1, 0, 0), ('c', 1, 0, 1), ('n', .6, -.2, 1), (' e', 1, 0, 1), ('2πint', .6, .48, 1)], SX, SY, 44, T_IVORY, kf)
        tx(cv, lang(f'{NK} 个圆 · {NK} circles', f'{NK} circles'), SX + 2, SY + 50, 24, T_SUB, kf)
    ro_primes(cv, t, fade(t, P0 + .3, G0 + .3, .5, .5) * RO_PRIMES)
    km = fade(t, G0 + .3, DZ0 + 3.0, .5, .6)
    if km > 0:
        big = 1 - smooth(G1 + 1.5, G1 + 2.5, t)
        y = lerp(SY, 470, big); sz = lerp(50, 110, big); x = lerp(SX, W / 2, big)
        math_tx(cv, [('z', 1, 0, 1), (' → ', 1, 0, 0), ('z', 1, 0, 1), ('2', .6, .45, 0), (' + ', 1, 0, 0), ('c', 1, 0, 1)], x, y, sz, T_IVORY, km * smooth(G0 + .6, G0 + 1.2, t), 'c' if big > .5 else 'l', glow=.5)
    if extra.get('L') is not None:
        L = extra['L']; kz = fade(t, DZ0 + .8, DZ1 + .9, .5, .5)
        e = int(L); m = 10 ** (L - e)
        wd = tx(cv, f'ZOOM  × {m:.2f} × 10', SXR, SY, 30, T_IVORY, kz, lf=CG_SB, glow=.2)
        tx(cv, f'{e}', SXR + wd + 3, SY - 18, 19, T_IVORY, kz, lf=CG_SB, glow=0)
    if extra.get('power') is not None:
        kb = fade(t, B0 + .6, B1 + .4, .6, .5)
        math_tx(cv, [('z', 1, 0, 1), (' → ', 1, 0, 0), ('z', 1, 0, 1), ('n', .6, .45, 1), (' + ', 1, 0, 0), ('c', 1, 0, 1)], SX, SY, 50, T_IVORY, kb)
        tx(cv, f'n = {extra["power"]:.2f}', SX + 2, SY + 52, 28, T_SUB, kb, lf=CG_SB)
    kl = fade(t, L0 + .5, FIN0 + .3, .6, .5)
    if kl > 0:
        for j, ln in enumerate([[('dx/dt', 1, 0, 1), (' = σ(', 1, 0, 0), ('y', 1, 0, 1), (' − ', 1, 0, 0), ('x', 1, 0, 1), (')', 1, 0, 0)],
                                [('dy/dt', 1, 0, 1), (' = ', 1, 0, 0), ('x', 1, 0, 1), ('(ρ − ', 1, 0, 0), ('z', 1, 0, 1), (') − ', 1, 0, 0), ('y', 1, 0, 1)],
                                [('dz/dt', 1, 0, 1), (' = ', 1, 0, 0), ('xy', 1, 0, 1), (' − β', 1, 0, 0), ('z', 1, 0, 1)]]):
            math_tx(cv, ln, SX, SY + 48 * j, 36, T_IVORY, kl, glow=.3)
        if t > LS:
            P = lz_at(t); sp = float(np.linalg.norm(P - P.mean(0), axis=1).mean())
            tx(cv, f'Δ = {sp:.4f}' if sp < 1 else f'Δ = {sp:.1f}', SXR, SY, 30, T_GOLD, kl, lf=NOTO)
            tx(cv, lang('起点间的平均距离 · mean spread', 'mean spread'), SXR, SY + 36, 20, T_SUB, kl, glow=0)


# ================================================================ frame
GLX = None


def frame(i):
    global GLX
    t = i / FPS
    if GLX is None: GLX = GL()
    S = []
    for fn, (a, b), L, k in POOLS:
        if a <= t <= b: S.append(trail_segs(fn, t, L(t), k))
    S += static_segs(t)
    layers = []; extra = {}
    km = smooth(SETTLE + .1, SETTLE + 1.3, t) * (1 - smooth(B0, B0 + 2.2, t))
    if km > 0 and t < B0 + 2.3:
        tex = mandel_tex(t); layers.append((tex, km * 1.05, 2.0)); extra['L'] = _MAND.last_L if t > DZ0 else None
    kb = smooth(B0, B0 + 2.2, t) * (1 - smooth(L0, LS + .3, t))
    if kb > 0:
        tex, pw = bulb_tex(t); layers.append((tex, kb * .5, 2.2)); extra['power'] = pw
    layers += hook_layers(t)
    S.append(dust(cam1(t) if t < P0 else Cam(0, 0, 200 * (1 + .02 * t)), t, 1.0 - .6 * max(km, kb)))
    S = cull(np.concatenate([s for s in S if len(s)]))
    k = (1.0 if HOOK else smooth(0, .8, t)) * (1 - smooth(T - .6, T, t))
    S[:, 5:8] *= k
    rgb = GLX.run(S, t, bgK=k, layers=[(tx_, kk * k, g) for tx_, kk, g in layers])
    buf = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)]).copy(); surf = skia.Surface(buf); cv = surf.getCanvas()   # buf must outlive surf (skia draws into its memory)
    if not os.environ.get('NOTEXT'): overlay(cv, t, extra)
    if k < 1: cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 1 - k))   # the brand mark is drawn after this, so the end logo stays lit
    if not os.environ.get('NOTEXT'): BR.watermark(cv, t, T, expand_at=9.2, hold=2.0, end_len=1.9)   # mark unfolds after the opening line
    return surf.makeImageSnapshot().toarray()


if __name__ == '__main__':
    os.makedirs(BUILD + 'stills', exist_ok=True); NF = int(round(T * FPS))
    if len(sys.argv) > 1 and sys.argv[1] == '--still':
        for a in sys.argv[2:]: skia.Image.fromarray(frame(int(float(a) * FPS))).save(f'{BUILD}stills/f_{float(a):06.2f}.jpg', skia.kJPEG, 90); print('still', a, flush=True)
    elif len(sys.argv) > 1 and sys.argv[1] == '--part':
        i, n = int(sys.argv[2]), int(sys.argv[3]); a, b = NF * i // n, NF * (i + 1) // n
        if len(sys.argv) > 5: a, b = int(sys.argv[4]), int(sys.argv[5])
        w = Writer(f'{BUILD}part_{i:02d}.mp4')
        for f in range(a, b):
            w.write(frame(f))
            if (f - a) % 300 == 0: print(f'part {i}: {f - a}/{b - a}', flush=True)
        w.close()
    else:
        lz_hist()
        n = int(os.environ.get('JOBS', 4))
        ps = [subprocess.Popen([sys.executable, __file__, '--part', str(i), str(n)]) for i in range(n)]
        if any(p.wait() for p in ps): raise SystemExit('render failed')
        open(BUILD + 'concat.txt', 'w').write(''.join(f"file 'part_{i:02d}.mp4'\n" for i in range(n)))
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', BUILD + 'concat.txt', '-c', 'copy', BUILD + 'video.mp4'])
        print('ok', BUILD + 'video.mp4', f'{T:.2f} s')
