"""S005 soundtrack -> build/mix<SUFFIX>.wav
Music from music.py (Kevin MacLeod, CC BY 4.0), started on a downbeat so every cut sits on the half-bar grid; the chosen moment of the track (align)
lands on the chosen spot of the film.  Voice: Gemini 设计音色 A.  SFX synthesized: engine/sfx.py + engine/uisfx.py (full UI sound design)."""
import os, sys, wave, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE + '/../../engine'); sys.path.insert(0, HERE)
import numpy as np
import sfx as A
from uisfx import pop, swish, swell, rumble, sweep, ticks
from script import SEGMENTS
from timeline import build
from music import M, BEAT, SUFFIX

SR = A.SR; BAR = 4 * BEAT; DOWN0 = M['down0']
TL = build(SEGMENTS, HERE + '/build/' + os.environ.get('VOICE_DIR', 'voice'), beat=BEAT, unit=2, gap=.35, tail=2.6); T, SEG, when = TL.T, TL.SEG, TL.when
MUSIC = HERE + '/../../assets/music/' + M['file']
PEAK, (_seg, _sub) = M['align']
AT = when(_seg, _sub) if _sub else SEG[_seg]['t0']
MUSIC_FROM = DOWN0 + round((PEAK - AT - DOWN0) / BAR) * BAR
N = int(T * SR)


def music():
    x = A.load(MUSIC, MUSIC_FROM, T + 1)[:N]; x = np.pad(x, ((0, N - len(x)), (0, 0)))
    x *= 10 ** (-15 / 20) / A.rms(x)
    tt = np.arange(N) / SR
    x *= (np.clip(tt / .3, 0, 1) * np.clip((T - .05 - tt) / 2.2, 0, 1))[:, None]
    return x


def voice():
    v = np.zeros(N, np.float32)
    for s in TL.SEGS:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', s['audio'], '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
        a = np.frombuffer(raw, np.float32); i = int(s['voice_at'] * SR); v[i:i + len(a)] += a[:N - i]
    return v * (10 ** (-16 / 20) / A.rms(v[np.abs(v) > 1e-3]))


def cues():
    w, S_ = when, SEG; c = []
    SEC = 365 * 24 * 3600 / 1293e4
    c += ticks(.05, w('hook', '四千八百九十七万', 'b'), 14, .035)
    t = .3                                                                     # one soft pop per plate, at the real 2.44 s cadence, while the cards are up
    while t < w('speed', '而二零一九') - .3: c.append((pop(.08, 1180), t)); t += SEC
    c += [(pop(.12, 700), w('speed', '一千二百九十三万')), (pop(.10, 880), w('speed', '三万五千'))]
    tb = w('speed', '而二零一九') - .3
    c += [(swish(1.0, .06, 1), tb), (sweep(1.0, 220, 660, .05), tb + .3), (pop(.12, 640), w('speed', '一百二十万'))]
    # road: plates fly back to the car tails
    c += [(swish(1.0, .07, 2), S_['road']['t0'] - .1), (swell(.8, .05, 3), S_['road']['t0'] + .4), (pop(.10, 760), w('road', '八辆')), (pop(.14, 980), w('road', '一辆'))]
    # total: zoom out into the 100-grid
    c += [(swish(1.0, .06, 4), S_['total']['t0'] + .2), (pop(.12, 620), w('total', '三点七一亿'))]
    # new: second grid, then the line
    c += [(swish(.9, .06, 5), w('new', '差不多') - .1), (pop(.13, 880), w('new', '一辆是')), (swish(1.0, .06, 6), w('new', '路上的绿牌') - .2),
          (sweep(1.4, 260, 700, .05), w('new', '路上的绿牌') + .3), (pop(.10, 700), w('new', '百分之三')), (pop(.14, 940), w('new', '百分之十三'))]
    # twist: stacked bars
    c += [(swish(1.0, .06, 7), S_['twist']['t0'] + .2), (sweep(.8, 300, 600, .04), S_['twist']['t0'] + .6), (pop(.12, 820), w('twist', '八十一')),
          (pop(.12, 620), w('twist', '六十九')), (pop(.14, 980), w('twist', '插电混动'))]
    # charge: icons
    c += [(swish(1.0, .06, 8), S_['charge']['t0'] + .2), (pop(.12, 700), w('charge', '两千三百零六万')), (pop(.09, 820), w('charge', '平均每')),
          (pop(.10, 560), w('charge', '自家车位')), (pop(.13, 940), w('charge', '五百零一万'))]
    # world: ring
    c += [(swish(1.0, .07, 9), S_['world']['t0'] + .1), (swell(1.2, .07, 10), S_['world']['t0'] + .4), (pop(.12, 700), w('world', '两千万')), (pop(.15, 980), w('world', '百分之六十'))]
    # end: back to the red light; question
    c += [(swish(1.2, .07, 11), S_['end']['t0'] + .1), (swell(1.0, .06, 12), S_['end']['t0'] + .5), (pop(.12, 760), w('end', '再想想'))]
    return c


def main():
    m, v = music(), voice()
    hop = int(.01 * SR); e = np.sqrt(np.convolve(v ** 2, np.ones(hop) / hop, 'same'))[::hop]
    act = (e > 10 ** (-45 / 20)).astype(float); g = np.zeros_like(act); s = 0.0
    for i, a in enumerate(act): s += (a - s) * (.35 if a > s else .03); g[i] = s
    duck = 10 ** (-8 * np.interp(np.arange(N) / hop, np.arange(len(g)), g) / 20); m *= duck[:, None]
    fx = np.zeros((N, 2), np.float32)
    # no whoosh + boom on cuts: this film has no hard cuts — the morphs carry their own swishes (cues)
    for wd, amp in [(('hook', '四千八百九十七万'), .4), (('speed', '一千二百九十三万'), .35), (('road', '一辆'), .3), (('new', '一辆是'), .35),
                    (('new', '百分之十三'), .3), (('twist', '插电混动'), .3), (('charge', '五百零一万'), .3), (('world', '百分之六十'), .45)]:
        A.put(fx, A.boom(amp, 44, 1.8), when(*wd))
    for buf, at in cues(): A.put(fx, buf, at)
    fx *= duck[:, None] ** .5
    mix = np.tanh((m + fx + v[:, None]) * 1.25) / 1.25
    w = wave.open(HERE + f'/build/mix{SUFFIX}.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    print(f'mix{SUFFIX}.wav {T:.2f} s · {M["title"]} from {MUSIC_FROM:.2f} s')


if __name__ == '__main__':
    main()
