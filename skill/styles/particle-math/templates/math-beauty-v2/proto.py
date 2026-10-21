"""math-beauty v2 · 15 s prototype: sunflower → unit circle → Euler → Fourier, in one unbroken camera move over the complex plane.
The links are real mathematics:
  seed k of a sunflower sits at √k · e^{2πik·θ}; pull every radius to 1 and the seeds become points e^{2πik·θ} on the unit circle;
  one point walks the circle to e^{iπ} = −1; that arm is the biggest epicycle of 数学's Fourier series, and the other 239 grow from its tip.
usage: python proto.py | --still t …"""
import os, sys, math, cmath
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import skia
from engine import *

T = 15.0
BUILD = HERE + '/build/'

# ---------------------------------------------------------------- act 1 · sunflower (0 – 5 s)
N = 1500
KS = np.arange(1, N + 1)
C0 = 4.0 / math.sqrt(N)                         # outer seed at radius 4
PHI2 = (3 - math.sqrt(5)) / 2                   # 1/φ² of a turn = 137.507…°
CONV = [(1, 3), (3, 8), (8, 21), (21, 55), (55, 144)]
HOLD = [.0, 1.25, 1.8, 2.3, 2.75]               # when each convergent locks in
TG_LOCK = 3.25


def turn(t):
    """fraction of a turn per seed: steps through the Fibonacci convergents, then settles on 1/φ²"""
    pts = [(HOLD[i], CONV[i][0] / CONV[i][1]) for i in range(len(CONV))] + [(TG_LOCK, PHI2)]
    if t <= pts[0][0]: return pts[0][1]
    for (ta, fa), (tb, fb) in zip(pts, pts[1:]):
        if t < tb: return lerp(fa, fb, eio((t - (tb - .5)) / .5))          # hold each convergent, slide in the last half second
    return PHI2


def seeds_z(t):
    f = turn(t)
    ang = 2 * math.pi * KS * f
    u = np.clip((t - 4.9 - .5 * (1 - KS / N)) / 1.3, 0, 1); u = u * u * (3 - 2 * u)   # radii collapse onto the unit circle (outer seeds first)
    r = C0 * np.sqrt(KS) * (1 - u) + 1.0 * u
    return r * np.exp(1j * ang), u


SEED_COL = ROSE[None] * (1 - KS / N)[:, None] ** 1.5 + GOLD[None] * (1 - (1 - KS / N) ** 1.5)[:, None]

# ---------------------------------------------------------------- act 2 · Euler (6.6 – 10 s)
TE0, TE1 = 7.0, 9.6
def theta(t): return math.pi * esine((t - TE0) / (TE1 - TE0))


# ---------------------------------------------------------------- act 3 · Fourier (10 – 15 s)
def glyph_path(text=lang('数学', 'MATH'), size=600):
    f = skia.Font(CG_SB if EN else WK, size); x = 0; cons = []
    for ch in text:
        p = f.getPath(f.textToGlyphs(ch)[0]); p.offset(x, 0)
        pm = skia.PathMeasure(p, False)
        while True:
            L = pm.getLength()
            if L > 1:
                n = max(8, int(L / 1.2)); pts = []
                for i in range(n):
                    pt, _ = pm.getPosTan(L * i / n); pts.append(complex(pt.x(), -pt.y()))
                cons.append(np.array(pts))
            if not pm.nextContour(): break
        x += f.measureText(ch)
    left = list(range(len(cons))); pos = min((c[np.argmin(c.real)] for c in cons), key=lambda z: z.real)
    seq, pen = [], []
    while left:
        b = min(left, key=lambda i: np.abs(cons[i] - pos).min()); c = cons[b]; j = int(np.argmin(np.abs(c - pos)))
        c = np.append(np.roll(c, -j), np.roll(c, -j)[0])
        if seq:
            jump = np.linspace(seq[-1][-1], c[0], 24)[1:-1]; seq.append(jump); pen.append(np.zeros(len(jump), bool))
        seq.append(c); pen.append(np.ones(len(c), bool)); pos = c[-1]; left.remove(b)
    jump = np.linspace(seq[-1][-1], seq[0][0], 24)[1:-1]; seq.append(jump); pen.append(np.zeros(len(jump), bool))
    z = np.concatenate(seq); pd = np.concatenate(pen)
    d = np.abs(np.diff(np.append(z, z[0]))); s = np.concatenate([[0], np.cumsum(d)])[:-1]
    M = 4096; u = np.linspace(0, s[-1] + d[-1], M, endpoint=False)
    zz = np.interp(u, s, z.real) + 1j * np.interp(u, s, z.imag); pp = np.interp(u, s, pd.astype(float)) > .5
    return zz, pp


NK = 240
_z, PEN = glyph_path()
_z = _z - _z.mean()
_c = np.fft.fft(_z) / len(_z); _f = np.fft.fftfreq(len(_z), 1 / len(_z)).astype(int)
_o = np.argsort(-np.abs(_c))[:NK + 1]; _o = _o[_f[_o] != 0][:NK]
SC = 1.0 / np.abs(_c[_o[0]])                     # biggest epicycle = the unit circle
CF, FQ = _c[_o] * SC, _f[_o]
TAU0 = ((math.pi - cmath.phase(CF[0])) / (2 * math.pi * FQ[0])) % (1 / abs(FQ[0]))   # start where the big arm points at −1
TF0, TF1 = 11.0, 14.6                            # one full turn of the drawing
GROW0, GROW1 = 10.0, 10.9
_tt = np.arange(len(_z)) / len(_z)
RECON = (CF[None, :] * np.exp(2j * np.pi * FQ[None, :] * _tt[:, None])).sum(1)          # the truncated series, drawn by the tip
GW = (RECON.real.max() - RECON.real.min()); GH = RECON.imag.max() - RECON.imag.min(); GC = complex((RECON.real.max() + RECON.real.min()) / 2, (RECON.imag.max() + RECON.imag.min()) / 2)


def tau(t): return TAU0 + eio((t - TF0) / (TF1 - TF0)) * 1.0 if t < TF1 else TAU0 + 1.0 + (t - TF1) * 0.0


def grow(t):
    j = np.arange(NK); a = GROW0 + (GROW1 - GROW0) * (j / NK) ** .6
    g = np.clip((t - a) / .35, 0, 1); g[0] = 1.0
    return g * g * (3 - 2 * g)


# ---------------------------------------------------------------- camera: one continuous move
CAM_SUN = Cam(0, 0, 108)
CAM_UNIT = Cam(0, .05, 300)
CAM_FOUR = Cam(GC.real, GC.imag, min(1250 / GW, 640 / GH))


def cam(t):
    if t < 4.9: return Cam(0, 0, CAM_SUN.s * (1 + .015 * t))
    if t < 10.0: return cam_mix(Cam(0, 0, CAM_SUN.s * (1 + .015 * 4.9)), CAM_UNIT, esine((t - 4.9) / 1.9))
    return cam_mix(CAM_UNIT, CAM_FOUR, esine((t - 10.0) / 1.8))


# ---------------------------------------------------------------- the moving lights (trail-able)
def lights(t):
    c = cam(t); ps = PS()
    z, u = seeds_z(t)
    appear = np.clip((t + .05 - KS / N * 1.1) / .25, 0, 1)                    # seeds sprout from the centre outward
    ring = smooth(5.6, 6.8, t)
    col = SEED_COL * (1 - ring) + CYAN_W[None] * ring * .9
    a = appear * (1 - .72 * smooth(7.2, 8.4, t)) * (1 - smooth(10.2, 11.0, t))
    ps.add(c.P(z), 2.0 + .4 * (1 - u), col * .75, a)
    th = theta(t); kp = smooth(6.7, 7.1, t) * (1 - smooth(10.2, 10.25, t))
    p = c.P(np.exp(1j * th))
    ps.add(p[None], 5.0, GOLD_W * 2.0, kp); ps.add(p[None], 16, GOLD * .35, kp)
    return ps.arrays()


def frame_segs(t):
    c = cam(t); S = []
    L = (.025 if t < 3.6 else .1) + .3 * math.sin(math.pi * clamp((t - 4.9) / 1.9))
    S.append(trail_segs(lights, t, L, 10, .85 if t > 3.6 else .45))
    # Euler: axes, travelled arc, arm, the landing ring at −1
    ke = smooth(6.4, 7.2, t) * (1 - smooth(10.4, 11.2, t))
    if ke > 0:
        for a_, b_ in ((-1.7, 1.7), ):
            S.append(polyline(c.P(np.array([a_, b_]) + 0j), .9, DIM * .9, ke))
            S.append(polyline(c.P(1j * np.array([a_, b_])), .9, DIM * .9, ke))
        th = theta(t)
        arc = np.exp(1j * np.linspace(0, th, max(2, int(th * 60))))
        S.append(polyline(c.P(arc), 1.6, CYAN_W * 1.2, ke * smooth(6.9, 7.1, t)))
        S.append(polyline(c.P(np.array([0, np.exp(1j * th)])), 1.1, IVORY * .8, ke * smooth(6.9, 7.2, t)))
        sa = np.exp(1j * np.linspace(0, th, 40)) * .22
        S.append(polyline(c.P(sa), 1.0, IVORY * .5, ke * smooth(7.0, 7.4, t)))
        s = t - TE1
        if s > 0:
            for d in (0, .3):
                uu = clamp((s - d) / 1.6); R = .02 + .5 * eout(uu)
                S.append(polyline(c.P(-1 + R * np.exp(1j * np.linspace(0, 2 * np.pi, 90))), 1.3, GOLD_W * (1 - uu) ** 1.5 * 1.2, 1.0, closed=True))
    # Fourier: epicycles and the drawing
    if t >= GROW0 - .05:
        g = grow(t); tt = tau(t)
        terms = CF * g * np.exp(2j * np.pi * FQ * tt)
        centres = np.concatenate([[0j], np.cumsum(terms)])
        kf = smooth(GROW0 - .05, GROW0 + .2, t)
        ring = np.exp(1j * np.linspace(0, 2 * np.pi, 48))
        R = np.abs(CF) * g
        vis = np.nonzero((R * c.s > 1.5))[0]
        circ = centres[vis][:, None] + R[vis][:, None] * ring[None]
        P = c.P(circ)
        for k_, row in zip(vis, P):
            S.append(polyline(row, .8, IVORY * (.10 + .2 * (k_ == 0)), kf, closed=True))
        S.append(polyline(c.P(centres), 1.0, IVORY * .45, kf))
        tip = c.P(centres[-1:])
        S.append(np.concatenate([tip, tip, [[4.0]], [GOLD_W * 2.2]], 1)); S.append(np.concatenate([tip, tip, [[14.0]], [GOLD * .4]], 1))
        if t > TF0:
            n = int((tt - TAU0) * len(RECON)); i0 = int(TAU0 * len(RECON))
            idx = (np.arange(i0, i0 + n + 1)) % len(RECON)
            if len(idx) > 1:
                pts = c.P(RECON[idx]); pen = PEN[idx].astype(float)
                age = (n - np.arange(len(idx))) / len(RECON)
                S.append(polyline(pts, 1.7, GOLD_W * 1.1, pen * (.55 + .45 * np.exp(-age * 20))))
    S.append(dust(c, t, 1.0))
    return cull(np.concatenate([s for s in S if len(s)]))


# ---------------------------------------------------------------- words
def overlay(cv, t):
    c = cam(t)
    caption(cv, '每长出一颗种子，就转一个固定的角度', t, .3, 3.0)
    caption(cv, '转 137.5°，黄金角：种子排得最密', t, 3.2, 4.8)
    caption(cv, '把它们都拉到同一个半径：单位圆', t, 5.0, 6.9)
    caption(cv, '让其中一点，沿着单位圆转……', t, 7.1, 9.5)
    caption(cv, '转过 π，正好落在 −1', t, 9.7, 11.0)
    caption(cv, '很多个圆首尾相连地转，就能画出任何形状', t, 11.2, 14.8)
    k = fade(t, .3, 4.9, .4, .5); x = 1480
    if k > 0:
        f = turn(t); deg = f * 360
        tx(cv, 'TURN ANGLE', x, 330, 20, T_SUB, k, lf=CG_SB, glow=0)
        tx(cv, f'θ = {deg:.3f}°', x, 380, 40, T_IVORY, k, lf=CG_SB)
        locked = [i for i in range(len(CONV)) if HOLD[i] <= t < (HOLD[i + 1] if i + 1 < len(CONV) else TG_LOCK)]
        if t >= TG_LOCK:
            kg = smooth(TG_LOCK, TG_LOCK + .4, t)
            tx(cv, '= 360° / φ²', x, 435, 34, T_GOLD, k * kg, lf=CG_SBI)
            tx(cv, '黄金角', x, 485, 28, T_GOLD, k * kg)
        elif locked:
            p, q = CONV[locked[0]]
            tx(cv, f'≈ 360° × {p}/{q}', x, 435, 34, T_GOLD, k, lf=CG_SBI)
            tx(cv, f'{q} 条旋臂', x, 485, 28, T_GOLD, k)
    ke = fade(t, 6.6, 10.8, .5, .5)
    if ke > 0:
        for z, s_ in ((1, '1'), (-1, '−1'), (1j, 'i'), (-1j, '−i')):
            p = c.P(np.array([z * 1.12]))[0]
            tx(cv, s_, p[0], p[1] + 12, 30, T_SUB, ke, 'c', lf=CG_SBI if 'i' in s_ else CG_SB, glow=0)
        th = theta(t); p = c.P(np.array([.34 * np.exp(1j * th / 2)]))[0]
        tx(cv, 'θ', p[0], p[1] + 10, 26, T_IVORY, ke * smooth(7.1, 7.5, t), 'c', lf=CG_SBI, glow=0)
        k1 = ke * (1 - smooth(TE1 - .1, TE1 + .2, t))
        math_tx(cv, [('e', 1, 0, 1), ('iθ', .6, .48, 1), ('  = cos θ + ', 1, 0, 0), ('i', 1, 0, 1), (' sin θ', 1, 0, 0)], W / 2, 150, 52, T_IVORY, k1 * smooth(7.0, 7.5, t), 'c')
        k2 = ke * smooth(TE1, TE1 + .5, t)
        math_tx(cv, [('e', 1, 0, 1), ('iπ', .6, .48, 1), (' + 1 = 0', 1, 0, 0)], W / 2, 160, 86, T_GOLD, k2, 'c', glow=.6)
    kf = fade(t, 11.0, 15.2, .6, .3)
    if kf > 0:
        math_tx(cv, [('f', 1, 0, 1), ('(', 1, 0, 0), ('t', 1, 0, 1), (') = ∑ ', 1, 0, 0), ('c', 1, 0, 1), ('n', .6, -.2, 1), (' e', 1, 0, 1), ('2πint', .6, .48, 1)], 110, 130, 44, T_IVORY, kf, 'l')
        tx(cv, f'{NK} 个圆', 112, 180, 26, T_SUB, kf)


GLX = None


def frame(i):
    global GLX
    t = i / FPS
    if GLX is None: GLX = GL()
    S = frame_segs(t)
    k = smooth(0, .6, t) * (1 - smooth(T - .5, T, t))
    S[:, 5:8] *= k
    rgb = GLX.run(S, t, bgK=k)
    surf = skia.Surface(np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)]).copy()); cv = surf.getCanvas()
    overlay(cv, t)
    if k < 1: cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 1 - k))
    return surf.makeImageSnapshot().toarray()


if __name__ == '__main__':
    os.makedirs(BUILD + 'stills', exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == '--still':
        for a in sys.argv[2:]: skia.Image.fromarray(frame(int(float(a) * FPS))).save(f'{BUILD}stills/p_{float(a):05.2f}.jpg', skia.kJPEG, 90); print('still', a)
    else:
        n = int(os.environ.get('JOBS', 4)); NF = int(T * FPS)
        if len(sys.argv) > 1 and sys.argv[1] == '--part':
            i, n = int(sys.argv[2]), int(sys.argv[3]); w = Writer(f'{BUILD}proto_{i}.mp4')
            for f in range(NF * i // n, NF * (i + 1) // n): w.write(frame(f))
            w.close()
        else:
            import subprocess
            ps = [subprocess.Popen([sys.executable, __file__, '--part', str(i), str(n)]) for i in range(n)]
            if any(p.wait() for p in ps): raise SystemExit('render failed')
            open(BUILD + 'proto_concat.txt', 'w').write(''.join(f"file 'proto_{i}.mp4'\n" for i in range(n)))
            subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', BUILD + 'proto_concat.txt', '-c', 'copy', BUILD + 'proto_video.mp4'])
            print('ok', BUILD + 'proto_video.mp4')
