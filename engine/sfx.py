"""Soundtrack -> build/mix.wav
Music: Kevin MacLeod "All This" (CC BY 4.0).  Its bar is 3.0217 s; played 0.72 % faster so a bar is exactly 3 s and every
cut of the film sits on a bar line.  Film t = track t' - 6: strings enter at 42 s (low orbit), full orchestra at 90 s
(Starlink complete).  At 150 s the first quiet passage is swapped for its identical reprise, which leads into the track's
own finale (162 s), which ends at 177 s.  Cold open: the real Sputnik-1 beep.  SFX are synthesized."""
import os, wave, subprocess, numpy as np
from scipy.signal import butter, sosfilt
SR = 48000; T = 180.0; SPEED = 3.0217 / 3.0; LEAD = 6.0; REPRISE = 195.0
ROOT = os.path.dirname(os.path.abspath(__file__))
MUSIC = os.environ.get('MUSIC', ROOT + '/assets/music/All_This.mp3')
N = int(T * SR); rng = np.random.default_rng(57)


def load(path, t0, dur):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-t', f'{dur:.3f}', '-i', path, '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
def put(out, buf, at, gain=1.0):
    s = int(at * SR)
    if buf.ndim == 1: buf = np.stack([buf, buf], 1)
    if s < 0: buf = buf[-s:]; s = 0
    k = min(len(buf), len(out) - s)
    if k > 0: out[s:s + k] += buf[:k] * gain
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x, axis=0)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x, axis=0)
def rms(x): return float(np.sqrt((x ** 2).mean()) + 1e-9)
def whoosh(dur=.7, f0=400, f1=5000, amp=.2, power=2.5):
    n = int(dur * SR); t = np.arange(n) / SR; nz = rng.standard_normal(n + 4800); out = np.zeros(n)
    for k in range(0, n, 480):
        fc = f0 + (f1 - f0) * (k / n) ** 2
        out[k:k + 480] = sosfilt(butter(2, [fc * .6, fc * 1.5], 'band', fs=SR, output='sos'), nz[k:k + 480 + 4800])[4800:4800 + min(480, n - k)]
    out *= (t / dur) ** power * amp
    return np.stack([out, np.roll(out, 211)], 1)
def boom(amp=.5, f=46, dur=1.8):
    t = np.arange(int(dur * SR)) / SR
    x = np.sin(2 * np.pi * f * t * (1 - .12 * t)) * np.exp(-t / .45) * amp
    x[:2400] += lp(rng.standard_normal(2400), 900) * np.exp(-np.arange(2400) / 500) * amp * .8
    return x
def blip(f=1200, dur=.06, amp=.12):
    t = np.arange(int(dur * SR)) / SR; return np.sin(2 * np.pi * f * t) * np.exp(-t / (dur * .35)) * amp
def drone(dur, f=55, amp=.12):
    t = np.arange(int(dur * SR)) / SR
    x = sum(np.sin(2 * np.pi * f * h * t + i) / h for i, h in enumerate((1, 1.5, 2.01, 3.02))) * amp * (1 + .2 * np.sin(2 * np.pi * .23 * t))
    return x * np.clip(t / 1.5, 0, 1) * np.clip((dur - t) / 1.5, 0, 1)


def main():
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', MUSIC, '-vn', '-ac', '2', '-af', f'asetrate=48000*{SPEED:.6f},aresample={SR}', '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    x *= 10 ** (-13.5 / 20) / rms(x[int(96 * SR):int(144 * SR)])                 # level set on the full-orchestra section
    m = np.zeros((N, 2), np.float32); xf = int(.08 * SR); cut = int(150 * SR)
    a = x[int(LEAD * SR):int((LEAD + 150) * SR) + xf].copy(); a[-xf:] *= np.linspace(1, 0, xf)[:, None] ** .5
    b = x[int(REPRISE * SR):].copy(); b[:xf] *= np.linspace(0, 1, xf)[:, None] ** .5
    put(m, a, 0); put(m, b, 150.0)
    tt = np.arange(N) / SR
    lift = 10 ** (3.0 * np.clip((42 - tt) / 6, 0, 1) / 20)                        # sparse opening +3 dB, eased out before the strings enter
    m *= (lift * np.clip(tt / 1.5, 0, 1) * np.clip((T - .1 - tt) / .8, 0, 1))[:, None]
    fx = np.zeros((N, 2), np.float32)
    # cold open: real Sputnik beep over a low drone
    bp_ = load(ROOT + '/assets/raw/sputnik.ogg', 0, 6.2); bp_ = bp(bp_, 300, 4000); bp_ *= .13 / rms(bp_)
    e = np.clip(np.arange(len(bp_)) / (.8 * SR), 0, 1) * np.clip((len(bp_) - np.arange(len(bp_))) / (1.2 * SR), 0, 1); put(fx, bp_ * e[:, None], .3)
    put(fx, drone(6.5, 49, .06), 0); put(fx, whoosh(2.0, 200, 4000, .16), 4.0); put(fx, boom(.45), 6.0)
    # timeline: one tick per batch of catalogued objects, so the crackle thickens exactly as the orbit fills up
    cnt = np.load(ROOT + '/build/count_by_year.npy')
    def year_at(t): return 1957.8 + (2015 - 1957.8) * min(1, max(0, (t - 6) / 16)) if t < 22 else 2015 + (2026.76 - 2015) * min(1, max(0, (t - 22) / 6.5))
    acc = 0.0; prev = 0.0
    for k in range(int(22.5 * 200)):
        t = 6 + k / 200; c = float(np.interp(year_at(t), cnt[:, 0], cnt[:, 1])); acc += max(0, c - prev); prev = c
        if acc >= 60: acc = 0; put(fx, blip(1500 + 2500 * rng.random(), .02, .03 + .02 * rng.random()), t + rng.random() / 200)
    # scene cuts: riser + sub hit
    for t0, am in [(30, .5), (42, .45), (54, .25), (57, .3), (66, .35), (102, .4), (114, .4), (126, .5), (150, .4)]:
        put(fx, whoosh(1.2, 300, 6000, .2 * am / .5), t0 - 1.2); put(fx, boom(am), t0)
    put(fx, whoosh(.5, 600, 5000, .1), 36 - .5); put(fx, whoosh(.5, 600, 5000, .1), 60 - .5)
    for i in range(3): put(fx, blip(700 + 200 * i, .3, .06), 36.5 + i * .5)                      # three orbit labels
    put(fx, blip(2525, .25, .05), 57.1); put(fx, lp(rng.standard_normal(int(.4 * SR)), 3000) * .02, 57.35)   # quindar-style radio beep
    # Starlink: riser + accelerating ticks under the orchestra's own build, into the tutti at 90 s
    put(fx, whoosh(11.5, 150, 7000, .22, power=3.2), 78.5)
    t = 79.0
    while t < 89.8: put(fx, blip(900 + 60 * (t - 79) ** 1.5, .04, .045), t); t += max(.035, .5 * (1 - (t - 79) / 11) ** 1.6)
    put(fx, boom(.7, 40, 2.6), 90.0); put(fx, boom(.35, 80, .8), 90.0)
    for i in range(4): put(fx, blip(880 * 2 ** (i / 6), .3, .05), 96.3 + i * .35); put(fx, blip(660 + 110 * i, .3, .05), 104.1 + i * .4)
    # debris: two impacts
    for t0 in (138.0, 142.0):
        n = int(1.4 * SR); z = bp(rng.standard_normal(n), 200, 5000) * np.exp(-np.arange(n) / (.18 * SR)) * .3
        put(fx, np.stack([z, np.roll(z, 331)], 1), t0); put(fx, boom(.55, 52, 1.4), t0)
        for k in range(26): put(fx, blip(2500 + 5000 * rng.random(), .015, .05 * rng.random()), t0 + .05 + 1.4 * rng.random() ** 2)
    put(fx, blip(330, .5, .08), 146.1); put(fx, blip(331.5, .5, .08), 146.5)
    # finale: long riser into the last tutti, sub hits on its entry and on the final chord
    put(fx, whoosh(3.0, 200, 7000, .24, power=3.0), 159.0); put(fx, boom(.7, 40, 2.6), 162.0)
    mix = np.tanh((m + fx) * 1.5) / 1.5
    w = wave.open(ROOT + '/build/mix.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    print('mix.wav', f'music {20 * np.log10(rms(m)):.1f} dB, fx {20 * np.log10(rms(fx)):.1f} dB')
    for a0, b0 in [(0, 42), (42, 66), (66, 90), (90, 138), (138, 150), (150, 162), (162, 177.4), (177.4, 180)]:
        print(f'  film {a0:5.1f}-{b0:5.1f} s  music {20 * np.log10(rms(m[int(a0 * SR):int(b0 * SR)])):6.1f} dB')


if __name__ == '__main__':
    main()
