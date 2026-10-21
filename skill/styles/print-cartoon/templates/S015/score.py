"""S015 original score + sound design, all synthesised here (numpy). 120 BPM, F major, I–vi–IV–V.
The hi-hat is the checkout scanner beep; every person who pays rings a small bell in key; the film's events (film.EV) drive the effects.
MUSIC=lyria: same effects over the Lyria 3.5 track (show/lyria.py, take lyria_a_1), re-edited on bar lines to fit the acts.
→ build/mix.wav | build/mix_lyria.wav (48 kHz stereo)"""
import os, math
import numpy as np
from scipy.signal import lfilter, butter
from timeline import *
import film

SR = 48000
TEND = film.warp(DUR) if film.WARP else DUR                       # WARP=qnyh: effects on the 《千年以后》 grid
WT = film.warp if film.WARP else film.film2out if film.CUT else (lambda x: x)   # CUT=90: None = the event fell in a cut
TOUT = film.seg_table(film.SEG90)[1] if film.CUT else TEND
N = int((TEND + .5) * SR)
L, R = np.zeros(N), np.zeros(N)
rng = np.random.default_rng(15)


def mf(m): return 440 * 2 ** ((m - 69) / 12)
def tt(d): return np.arange(int(d * SR)) / SR


def add(t, sig, g=1., pan=0.):
    i = int(t * SR)
    if i >= N or i + len(sig) <= 0: return
    if i < 0: sig, i = sig[-i:], 0
    sig = sig[:N - i]
    L[i:i + len(sig)] += sig * g * math.sqrt((1 - pan) / 2) * 1.414
    R[i:i + len(sig)] += sig * g * math.sqrt((1 + pan) / 2) * 1.414


def env(d, a=.005, dec=.3):
    x = tt(d); e = np.minimum(1, x / a) * np.exp(-x / dec)
    e[-int(.01 * SR):] *= np.linspace(1, 0, int(.01 * SR)); return e


def lp(x, fc, o=2): b, a = butter(o, fc / (SR / 2)); return lfilter(b, a, x)
def bp(x, lo, hi, o=2): b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), 'high'); return lfilter(b, a, x)


# ---------------------------------------------------------------- instruments
def marimba(f, d=.45):
    x = tt(d); e = env(d, .002, .16)
    return (np.sin(2 * np.pi * f * x + 1.2 * np.exp(-x / .03) * np.sin(2 * np.pi * 4 * f * x)) * e + .25 * np.sin(2 * np.pi * 4 * f * x) * env(d, .001, .03))


def epiano(f, d=.6):
    x = tt(d); e = env(d, .004, .35)
    return np.sin(2 * np.pi * f * x + 1.6 * np.exp(-x / .25) * np.sin(2 * np.pi * f * x)) * e


def bell(f, d=1.2, dec=.5):
    x = tt(d)
    return (np.sin(2 * np.pi * f * x + 2.2 * np.exp(-x / .2) * np.sin(2 * np.pi * 3.5 * f * x)) * env(d, .001, dec))


def musicbox(f, d=1.5):
    x = tt(d)
    return (np.sin(2 * np.pi * f * x) + .3 * np.sin(2 * np.pi * 2 * f * x) * np.exp(-x / .2) + .15 * np.sin(2 * np.pi * 5.4 * f * x) * np.exp(-x / .05)) * env(d, .001, .6)


def bass(f, d=.4):
    x = tt(d); s = np.sin(2 * np.pi * f * x); s = np.tanh(1.8 * (s + .3 * np.sin(4 * np.pi * f * x)))
    return lp(s * env(d, .006, .22), 900)


def pad(fs, d):
    x = tt(d); s = np.zeros_like(x)
    for f in fs:
        for det in (-.004, 0, .005):
            ph = 2 * np.pi * f * (1 + det) * x + rng.random() * 6
            s += sum(np.sin(ph * k) / k for k in range(1, 9))
    s = lp(s, 1400)
    a = np.minimum(1, x / .5) * np.minimum(1, (d - x) / .6)
    return s * a / (len(fs) * 6)


def kick():
    x = tt(.35); f = 45 + 75 * np.exp(-x / .04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(.35, .001, .14)


def clap():
    x = tt(.25); n = bp(rng.standard_normal(len(x)), 900, 2600)
    e = np.zeros_like(x)
    for o in (0, .011, .022): e += (x >= o) * np.exp(-np.maximum(0, x - o) / (.008 if o < .02 else .08))
    return n * e * .6


def scanner(d=.045):                                      # the checkout beep (≈ 2.7 kHz)
    x = tt(d); return (np.sin(2 * np.pi * 2730 * x) + .2 * np.sin(2 * np.pi * 8190 * x)) * env(d, .002, .03)


def wood(f=1700):
    x = tt(.08); return (np.sin(2 * np.pi * f * x) + .5 * np.sin(2 * np.pi * f * 2.7 * x)) * env(.08, .001, .018)


def noise(d): return rng.standard_normal(int(d * SR))


# ---------------------------------------------------------------- harmony & form
CH = {'F': (41, [65, 69, 72]), 'Dm': (38, [62, 65, 69]), 'Bb': (34, [58, 62, 65]), 'C': (36, [60, 64, 67]),
      'A': (33, [57, 61, 64]), 'Gm': (43, [55, 58, 62])}
MAIN = ['F', 'Dm', 'Bb', 'C']


def chord(b):
    if 17 <= b <= 21: return ['Dm', 'Dm', 'Bb', 'A', 'Dm'][b - 17]
    if 50 <= b <= 57: return ['Bb', 'C', 'Dm', 'F'][(b - 50) % 4]
    if b >= 58: return 'F'
    return MAIN[b % 4]


def sec(t):
    if t < 8: return 'intro'
    if t < 34: return 'A'
    if t < 44.6: return 'stuck'
    if t < 53.8: return 'build'
    if t < 58: return 'memory'
    if t < 72: return 'switch'
    if t < 100: return 'B'
    if t < 117: return 'end'
    return 'out'


MEL = [(0, 72, .5), (.5, 74, .5), (1, 72, .5), (1.5, 69, .5), (2, 65, 1), (3, 69, .5), (3.5, 72, .5),
       (4, 74, .5), (4.5, 72, .5), (5, 69, 1), (6, 65, .5), (6.5, 67, .5), (7, 69, 1),
       (8, 70, .5), (8.5, 69, .5), (9, 67, .5), (9.5, 65, .5), (10, 67, 1), (11, 70, .5), (11.5, 74, .5),
       (12, 72, 1.5), (13.5, 70, .5), (14, 67, 1), (15, 72, 1)]

NB = int(DUR / BEAT)
for b in range(int(DUR / 2)):                                     # bars
    t0 = b * 2.0; s = sec(t0 + .01); root, tones = CH[chord(b)]
    if s in ('intro', 'A', 'stuck', 'build', 'memory', 'switch', 'B', 'end'):
        g = {'stuck': .55, 'memory': .9, 'end': 1.1, 'intro': .9}.get(s, .45)
        add(t0, pad([mf(m) for m in tones], 2.15), g * .55, 0)
    for k in range(8):                                              # 8th notes
        t = t0 + k * BEAT / 2
        if t >= DUR - 3: break
        s = sec(t); beat = k / 2
        # mute window: "womp" bar and the breath before the finale
        if 63.6 <= t < 66.0 or 116.0 <= t < 117.0: continue
        drums = s in ('A', 'build', 'switch', 'B') and not (s == 'switch' and t < 62.5)
        if drums or (s == 'stuck' and k % 4 == 0):
            if k in (0, 4) or (s == 'B' and k == 7): add(t, kick(), .9)
        if drums and k in (2, 6) and s != 'build': add(t, clap(), .5, .1)
        if s == 'build' and t > 49.6 and k % 2 == 0: add(t, clap(), .18 + .3 * (t - 49.6) / 4.2, .1)
        if s in ('intro', 'A', 'build', 'switch', 'B') and not (s == 'switch' and t < 62.5):  # scanner beeps as hats
            add(t, scanner(), .10 if k % 2 else .05, .35)
        if s == 'stuck': add(t, wood(1700 if k % 2 == 0 else 1250), .16, -.3)   # the stopwatch
        if s in ('A', 'build', 'B', 'switch', 'intro'):
            bp_ = {0: 0, 3: 0, 4: 0, 6: 12, 7: 0}
            if k in bp_: add(t, bass(mf(root + 12 + bp_[k])), .5 if t >= 4 else .38)
        if s == 'stuck' and k in (0, 3, 6): add(t, bass(mf(CH['Dm'][0] + 12)), .45)
        if s in ('A', 'B') and k % 2 == 1:                          # marimba offbeat stabs
            for m in tones: add(t, marimba(mf(m + 12)), .07, -.2)
        if s == 'switch' and t >= 66 and k % 2 == 1:
            for m in tones: add(t, marimba(mf(m + 12)), .06, -.2)

# melody: act 1 from bar 6, act 4 full (an octave up the second time), then the finale on a music box
for start, end, inst, oct_, g in ((12.0, 34.0, epiano, 0, .22), (74.0, 92.0, epiano, 0, .22), (84.0, 100.0, marimba, 12, .14)):
    c0 = start
    while c0 < end - .1:
        for bt, m, d in MEL:
            t = c0 + bt * BEAT
            if start <= t < end: add(t, inst(mf(m + oct_), d * BEAT + .3), g, .15)
        c0 += 16 * BEAT
for bt, m, d in MEL[:-1]:
    t = 100.6 + bt * BEAT * 2                                        # half-speed music box
    if t < 116: add(t, musicbox(mf(m + 12)), .34, .2)
# the build: rising arpeggio under the bar chart
for k in range(int((53.8 - 44.6) / (BEAT / 2))):
    t = 44.6 + k * BEAT / 2; b = int(t // 2); root, tones = CH[chord(b)]
    m = tones[k % 3] + 12 * (1 + (k // 6) % 2)
    add(t, marimba(mf(m)), .10 + .08 * k / 36, .25)
# finale resolve: the three fronts pay together (117) → big F chord
for m in (53, 65, 69, 72, 77, 81):
    add(117.0, epiano(mf(m), 3.5), .14)
add(117.0, pad([mf(m) for m in (65, 69, 72, 77)], 4.0), .8)
for i, m in enumerate((77, 81, 84, 89)):
    add(121.0 + i * .12, bell(mf(m), 2.5, .9), .12, -.3 + .2 * i)
MUS = np.stack([L, R], 1).copy(); L[:] = 0; R[:] = 0                   # music bed / effects kept apart

LYRIA = os.environ.get('MUSIC') == 'lyria'
# Lyria take a_1 is 120.0 BPM with its downbeats on even seconds, like the film. Cuts on bar lines (orig seconds → film time):
EDIT = [(0, 42), (36, 38), (42, 66), (68, 108), (100, 108), (140, 151)]
if LYRIA:
    import subprocess
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', film.HERE + '/build/music/lyria_a_1.mp3', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    src = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)
    xf = int(.03 * SR); out = np.zeros((N, 2)); pos = 0
    for a_, b_ in EDIT:
        seg = src[int(a_ * SR):int(b_ * SR) + xf].copy()
        seg[:xf] *= np.linspace(0, 1, xf)[:, None]; seg[-xf:] *= np.linspace(1, 0, xf)[:, None]
        n = min(len(seg), N - pos)
        if n <= 0: break
        out[pos:pos + n] += seg[:n]; pos += len(seg) - xf
    ref = np.sqrt((MUS[:int(100 * SR)] ** 2).mean()); out *= ref / np.sqrt((out[:int(100 * SR)] ** 2).mean())
    MUS = out
    for i, m in enumerate((77, 81, 84, 89)):                            # keep the end-card chime
        add(WT(121.0) + i * .12, bell(mf(m), 2.5, .9), .10, -.3 + .2 * i)

# ---------------------------------------------------------------- effects from the film
DING = [mf(84), mf(81), mf(88), mf(79)]
for i, e in enumerate(sorted(film.EV, key=lambda e: e['t'])):
    t0_, k = e['t'], e['kind']; t = WT(t0_)
    if t is None: continue
    pan = {480: -.4, 700: 0, 920: .4}.get(e.get('lane'), 0)
    if k == 'ding': add(t, bell(DING[i % 4], .8, .25), .07, pan)
    elif k == 'ding2': add(t, bell(mf(84 + [0, 2, 4, 5][int(t0_ - 62.5)]), .9, .3), .12, 0)
    elif k == 'step': add(t, np.sin(2 * np.pi * np.cumsum(260 * np.exp(-tt(.07) / .03) + 120) / SR) * env(.07, .002, .02), .12, .3)
    elif k == 'pop' or k == 'pop2':
        x = tt(.07); f = 500 + 900 * x / .07
        add(t, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(.07, .001, .02), .16 if k == 'pop' else .3, (i % 5 - 2) * .15)
    elif k == 'tick': add(t, wood(1500 + e['n'] * 1.2), .07, (e['n'] % 3 - 1) * .3)
    elif k == 'bar': add(t, marimba(mf(72 + e['k'] // 6)), .05, .2)
    elif k == 'coin':
        for j in range(2):
            x = tt(.12); f = 3200 + 900 * rng.random()
            add(t + j * .06, np.sin(2 * np.pi * f * x + 2 * np.sin(2 * np.pi * f * 1.41 * x)) * env(.12, .001, .04), .07, .1 * j)
    elif k == 'whoosh':
        n = bp(noise(.9), 500, 4000); x = tt(.9)
        add(t, n * np.sin(np.pi * x / .9) ** 2, .12, 0)
    elif k == 'wipe' or k == 'tear':                                   # chapter panel: air swoosh in (rising) / out (falling) + a soft thump when it covers
        d = .42; x = tt(d); n = noise(d)
        fc = 600 + 5000 * (x / d if k == 'wipe' else 1 - x / d)
        y_ = np.zeros_like(n); a_ = 0.
        for i_ in range(0, len(n), 256):                                 # block-wise moving low-pass
            al = 1 - math.exp(-2 * math.pi * fc[i_] / SR)
            y_[i_:i_ + 256] = lfilter([al], [1, al - 1], n[i_:i_ + 256], zi=[a_ * (1 - al)])[0]; a_ = y_[min(i_ + 255, len(n) - 1)]
        add(t, y_ * np.sin(np.pi * x / d) ** 1.5, .5, .5 if k == 'wipe' else -.5)
        if k == 'wipe': add(t + .35, kick(), .45)
    elif k == 'type': add(t, wood(1300 + 90 * (e['k'] % 5)), .05, (e['k'] % 3 - 1) * .3)
    elif k == 'pick': add(t, bell(mf(88), .8, .25), .16); add(t, kick(), .3)
    elif k == 'theme': add(t, bell(mf(77), 3.0, 1.2), .12); add(t + .02, bell(mf(84), 3.0, 1.2), .08)
    elif k == 'go': add(t, bell(mf(84), 1, .3), .2); add(t + .25, bell(mf(89), 1.2, .4), .2)
    elif k == 'stamp': add(t, kick(), .7); add(t, clap(), .35)
    elif k == 'boing':
        x = tt(.7); f = 220 + 380 * (x / .7) + 60 * np.sin(2 * np.pi * 14 * x)
        add(t, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(.7, .005, .3), .22)
    elif k == 'womp':
        for j, (f0, f1) in enumerate(((330, 300), (300, 270), (270, 190))):
            d = .32 if j < 2 else .8; x = tt(d); f = np.linspace(f0, f1, len(x))
            s = np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR)); add(t + j * .36, lp(s, 1200) * env(d, .01, .3 if j < 2 else .6), .2)
    elif k == 'laser':                                                 # scanner sweep: fast beeps rising in pitch
        for j in range(16): add(t + j * .125, np.sin(2 * np.pi * (2400 + j * 40) * tt(.05)) * env(.05, .002, .025), .05, -.6 + j * .08)
    elif k == 'next': add(t, bell(mf(81), .6, .2), .07, -.2); add(t + .18, bell(mf(77), .7, .25), .07, -.2)

import wave


def save(x, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


if film.WARP:                                                          # the synth score's resolve + end chime, kept as effects
    for m in (65, 69, 72, 77): add(WT(117.0), bell(mf(m), 2.5, .8), .06)
    for i, m in enumerate((77, 81, 84, 89)): add(WT(121.0) + i * .12, bell(mf(m), 2.5, .9), .10, -.3 + .2 * i)
FX = np.stack([L, R], 1)
if film.WARP:
    # music on the song grid: the 《千年以后》 recording (preview only; on Douyin the song is attached in-app) or a Gemini track aligned to it
    src_ = os.environ.get('QMUSIC', film.ROOT + '/episodes/S006_什么叫天赋/build/ref_qnyh/song.wav')
    raw = __import__('subprocess').run(['ffmpeg', '-v', 'error', '-i', src_, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    song = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)[:N]
    song = np.concatenate([song, np.zeros((N - len(song), 2))])
    nz = song[:int(100 * SR)]
    song *= np.sqrt((MUS[:int(100 * SR)] ** 2).mean()) / np.sqrt((nz ** 2).mean())
    end = int(min(TEND, len(raw) / 8 / SR) * SR)                       # the recording stops at 129 s: fade its last 2 s
    song[max(0, end - 2 * SR):end] *= np.linspace(1, 0, min(end, 2 * SR))[:, None]
    mix = song + FX
    g = .9 / np.abs(mix).max(); tag = os.environ.get('QTAG', 'qnyh')
    save(mix * g, film.BUILD + f'/mix_{tag}.wav'); save(FX * g, film.BUILD + '/nobgm.wav')
else:
    if film.CUT:                                                       # the music follows the edit list: each kept span plays its own bars at 1×
        no = int(TOUT * SR); out = np.zeros((no, 2)); xf = int(.02 * SR)
        for a_, b_, sp_, o_ in film.seg_table(film.SEG90)[0]:
            n_ = int((b_ - a_) / sp_ * SR); ch = MUS[int(a_ * SR):int(a_ * SR) + n_ + xf].copy()
            ch[:xf] *= np.linspace(0, 1, xf)[:, None]; ch[-xf:] *= np.linspace(1, 0, xf)[:, None]
            i_ = int(o_ * SR); m_ = min(len(ch), no - i_); out[i_:i_ + m_] += ch[:m_]
        MUS, FX = out, FX[:no]
    mix = MUS + FX
    mix[-int(3 * SR):] *= np.linspace(1, 0, int(3 * SR))[:, None]
    mix /= np.abs(mix).max() / .9
    save(mix, film.BUILD + ('/mix_lyria.wav' if LYRIA else '/mix.wav') if film.CUT else film.HERE + ('/build/mix_lyria.wav' if LYRIA else '/build/mix.wav'))
print('mix', len(mix) / SR, 's, events', len(film.EV))
