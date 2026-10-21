"""math-beauty v2 soundtrack, synthesised in numpy on the《千年以后》grid (110.64 BPM, film 0 s = the song's vocal onset).
  build/film/nobgm.wav — 抖音 upload: sound effects only, mostly unpitched (the platform song plays over it, so nothing should clash with its key)
  build/film/score.wav — full cut: an original score in D minor that follows the same song form + the same effects
     intro pad (0–16.9) → pulse enters with the seeds falling onto the circle (16.9) → quiet section for the Mandelbulb (77.6–92.8) →
     build through Lorenz with a held breath at 105.8–110.1 → full chords at the second climax (112.3) → decay to the end (129.7)
usage: python score.py"""
import os, sys, wave
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
import film as F

SR = 48000; T = F.T; N = int(T * SR); tt = np.arange(N) / SR
BEAT = 60 / 110.6444; B0 = 1.6811
rng = np.random.default_rng(3)


def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)


def put(out, x, t0, g=1.0):
    i = int(t0 * SR); j = min(N, i + len(x))
    if 0 <= i < N and j > i: out[i:j] += x[:j - i] * g


def env(n, a=.01, d=1.0): x = np.arange(n) / SR; return np.minimum(1, x / a) * np.exp(-x / d)


def bell(f, d=2.5, amp=.2):
    n = int(d * 1.6 * SR); x = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * x) + .35 * np.sin(2 * np.pi * f * 2.0 * x) * np.exp(-x * 2) + .18 * np.sin(2 * np.pi * f * 3.01 * x) * np.exp(-x * 4)
    return s * env(n, .004, d) * amp


def pluck(f, amp=.06, d=.15):
    n = int(.8 * SR); x = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * x) + .3 * np.sin(4 * np.pi * f * x)) * np.exp(-x / d) * np.minimum(1, x / .002) * amp


def whoosh(dur, amp=.06, lo=500, hi=7000, seed=0, rev=False):
    n = int(dur * SR); x = np.arange(n) / SR; r = np.random.default_rng(seed)
    e = np.sin(np.pi * x / dur) ** 2
    if rev: e = (x / dur) ** 2.5 * (x < dur)
    return bp(r.normal(0, 1, n), lo, hi) * e * amp


def thump(amp=.18, f=48, d=.9):
    n = int(d * 1.8 * SR); x = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(f * (1 + .8 * np.exp(-x * 30))) / SR) * np.exp(-x / d * 2) * np.minimum(1, x / .004) * amp


def tick(amp=.03, seed=0):
    n = int(.04 * SR); r = np.random.default_rng(seed)
    return hp(r.normal(0, 1, n), 2500) * np.exp(-np.arange(n) / SR * 120) * amp


def shimmer(dur, amp=.03, seed=0):
    n = int(dur * SR); x = np.arange(n) / SR; r = np.random.default_rng(seed)
    return hp(r.normal(0, 1, n), 6000) * np.sin(np.pi * x / dur) ** 2 * (.6 + .4 * np.sin(2 * np.pi * 9 * x)) * amp


def stereo(x, pan=0.0): return np.stack([x * np.sqrt((1 - pan) / 2) * 1.414, x * np.sqrt((1 + pan) / 2) * 1.414], 1)


def reverb(x, dur=2.4, mix=.25):
    ir = rng.normal(0, 1, int(dur * SR)) * np.exp(-np.arange(int(dur * SR)) / SR * 2.4); ir = bp(ir, 200, 9000); ir /= np.abs(ir).sum() ** .5 * 6
    wl = fftconvolve(x[:, 0], ir)[:N]; wr = fftconvolve(x[:, 1], np.roll(ir, 331))[:N]
    return x + mix * np.stack([wl, wr], 1)


# ---------------------------------------------------------------- effects (both cuts)
def effects(pitched):
    fx = np.zeros(N)
    put(fx, whoosh(3.0, .03, 200, 2000, 1), 0.0)
    put(fx, whoosh(2.2, .05, 600, 8000, 2), 6.6)                                   # equations dissolve into seeds
    for i, tc in enumerate(F.HOLD[1:] + [F.TG]):                                   # each Fibonacci convergent locks in
        put(fx, bell(hz([69, 72, 74, 76, 81][i]), 1.8, .05) if pitched else tick(.05, i), tc)
    put(fx, shimmer(2.2, .03, 3), F.TG)
    put(fx, whoosh(2.2, .06, 400, 6000, 4), F.COLLAPSE - .4)                        # seeds fall onto the circle
    put(fx, thump(.16, 42, 1.4), F.TE1); put(fx, shimmer(1.6, .03, 5), F.TE1)       # e^{iπ} lands on −1
    if pitched: put(fx, bell(hz(62), 3.5, .09), F.TE1)
    for j in range(40):                                                              # epicycles grow
        tj = F.GROW0 + (F.GROW1 - F.GROW0) * (j / 40) ** .6
        put(fx, pluck(hz(74 + [0, 3, 5, 7, 10][j % 5] + 12 * (j // 20)), .018) if pitched else tick(.02, 10 + j), tj)
    put(fx, shimmer(2.5, .03, 6), F.TF1)
    put(fx, whoosh(2.4, .07, 300, 9000, 7), F.P0 - .2)                             # the line shatters into the integers
    put(fx, whoosh(1.2, .03, 1500, 9000, 8), 46.15)                                  # composites vanish
    put(fx, whoosh(2.0, .06, 300, 7000, 9), F.G0 - .1)                              # primes regroup as the c-grid
    for k in range(F.NIT):                                                           # waves of escaping points
        n = int(((F.ESC == k + 1) & ~F.INSIDE).sum())
        if n: put(fx, whoosh(.5, .012 * min(4, n / 300) ** .7, 2000, 10000, 20 + k), F.IT0 + k * F.ITD)
    put(fx, thump(.14, 45, 1.2), F.SETTLE)
    put(fx, whoosh(15.0, .025, 120, 1800, 30), F.DZ0)                               # the deep dive
    put(fx, shimmer(3.0, .035, 31), h(68)); put(fx, thump(.12, 40, 1.6), h(68))
    if pitched: put(fx, bell(hz(57), 4, .08), h(68))
    put(fx, whoosh(3.0, .04, 150, 3000, 32), F.B0 - .3)                             # into three dimensions
    put(fx, whoosh(1.4, .07, 400, 9000, 33, rev=True), F.L0)                        # the dust collapses to one point
    put(fx, thump(.12, 60, .6), F.LS)
    put(fx, shimmer(3.0, .03, 34), h(89))
    put(fx, whoosh(2.2, .07, 300, 8000, 35), F.FIN0 - .2)                           # everything converges into 数学
    put(fx, thump(.16, 44, 1.6), F.FIN1); put(fx, shimmer(3.0, .035, 36), F.FIN1)
    if pitched: put(fx, bell(hz(62), 5, .07), F.FIN1); put(fx, bell(hz(69), 5, .05), F.FIN1)
    put(fx, whoosh(2.6, .05, 400, 7000, 37), F.CLOSE0)                              # back to the equations
    return fx


def h(n): return F.h(n)


# ---------------------------------------------------------------- the score (full cut only)
def score():
    m = np.zeros(N)
    prog = [(50, 53, 57), (46, 50, 53), (48, 52, 55), (45, 49, 52)]                 # Dm · B♭ · C · A
    bar = 4 * BEAT
    lvl = np.interp(tt, [0, 16.87, 17.5, 77.6, 79, 92.8, 105.8, 110.1, 112.3, 125, T],
                        [.55, .7, 1.0, 1.0, .5, .5, 1.0, .35, 1.0, .8, 0])
    pad = np.zeros(N)
    for b in range(int(T / bar) + 2):
        t0 = B0 + (b - 1) * bar; ch = prog[b % 4]
        i0, i1 = max(0, int(t0 * SR)), min(N, int((t0 + bar + .3) * SR))
        if i1 <= i0: continue
        x = tt[i0:i1]; e = np.clip((x - t0) / .4, 0, 1) * np.clip((t0 + bar + .3 - x) / .5, 0, 1)
        for mm in ch + (ch[0] - 12,):
            for det in (-.07, .07): pad[i0:i1] += np.sin(2 * np.pi * hz(mm + det) * x + rng.uniform(0, 6)) * e * .22
    m += lp(pad, 2200) * lvl * .07
    pulse = (tt > 16.87) & ~((tt > 77.6) & (tt < 92.8)) & ~((tt > 105.8) & (tt < 112.3)) & (tt < 125)
    for b in range(int((T - B0) / BEAT) + 1):                                       # soft kick on the beat, hats on the off-beats
        t0 = B0 + b * BEAT
        if t0 < N / SR and pulse[min(N - 1, int(t0 * SR))]:
            put(m, thump(.11 if b % 4 == 0 else .07, 52, .25), t0)
            put(m, tick(.012, b), t0 + BEAT / 2)
    arp = [62, 65, 69, 72, 74, 72, 69, 65]                                           # sixteenth-note arpeggio through Fourier, Lorenz and the climax
    for a, b in ((F.TF0, F.P0 + 2), (F.LS, 105.8), (112.3, 124)):
        k = 0; t0 = a
        while t0 < b:
            put(m, pluck(hz(arp[k % 8] + 12), .028, .12), t0); t0 += BEAT / 2; k += 1
    for t0, mm in ((F.TG, 74), (F.TE1, 62), (h(68), 69), (F.FIN1, 74), (F.FIN1 + bar, 77)):
        put(m, bell(hz(mm), 4.5, .05), t0)
    sw = whoosh(4.3, .05, 300, 5000, 50, rev=True); put(m, sw, 105.8)                # the held breath before the second climax
    return m


def save(x, path):
    x = x * (.6 / np.abs(x).max())
    w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    fade = (np.clip(tt / .3, 0, 1) * np.clip((T - tt) / 1.0, 0, 1))[:, None]
    dy = reverb(stereo(effects(False)), mix=.2) * fade
    save(dy, F.BUILD + 'nobgm.wav')
    full = reverb(stereo(effects(True) + score()), mix=.3) * fade
    save(full, F.BUILD + 'score.wav')
    print('ok', F.BUILD + 'nobgm.wav', F.BUILD + 'score.wav', f'{T:.2f} s')
