"""Beat grid of a music file: python engine/beats.py track.mp3 [t0 t1]
Onset envelope (100 Hz) → tempo by autocorrelation (60–180 BPM, folded to 70–140) → phase by comb sum → bar phase by
the strongest of 4 offsets.  Prints BPM, beat period, first beat, first downbeat, and an energy envelope per bar."""
import sys, subprocess, json
import numpy as np

SR, HOP = 22050, 220


def load(path, sr=SR):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def grid(path, t0=0.0, t1=None):
    x = load(path); x = x[int(t0 * SR):int(t1 * SR) if t1 else None]
    n = len(x) // HOP; fr = x[:n * HOP].reshape(n, HOP)
    spec = np.abs(np.fft.rfft(fr * np.hanning(HOP), axis=1)); flux = np.maximum(0, np.diff(np.log1p(spec * 20), axis=0)).sum(1)
    flux = np.concatenate([[0], flux]); flux -= np.convolve(flux, np.ones(50) / 50, 'same'); flux = np.maximum(flux, 0)
    fps = SR / HOP
    ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]
    lag = np.arange(len(ac)) / fps; m = (lag > 60 / 180) & (lag < 60 / 60)
    best = lag[m][np.argmax(ac[m])]
    period = best
    while 60 / period < 70: period /= 2
    while 60 / period > 140: period *= 2
    # refine period: maximise comb energy around the estimate
    def comb(p, ph): idx = (np.arange(ph, len(flux) / fps, p) * fps).astype(int); idx = idx[idx < len(flux)]; return flux[idx].mean()
    ps = np.linspace(period * .985, period * 1.015, 61)
    period = max(ps, key=lambda p: max(comb(p, ph) for ph in np.linspace(0, p, 40, endpoint=False)))
    phs = np.linspace(0, period, 200, endpoint=False); ph = phs[np.argmax([comb(period, q) for q in phs])]
    # downbeat: which of 4 beat offsets has the most energy (bars of 4)
    db = max(range(4), key=lambda k: comb(period * 4, ph + k * period))
    first_down = ph + db * period
    return dict(bpm=60 / period, beat=period, first_beat=t0 + ph, first_downbeat=t0 + first_down, dur=len(x) / SR + t0)


def envelope(path, g, bars=40):
    x = load(path, 8000); out = []
    for k in range(bars):
        a = g['first_downbeat'] + k * 4 * g['beat']; s = x[int(a * 8000):int((a + 4 * g['beat']) * 8000)]
        if len(s) == 0: break
        out.append((round(a, 2), round(20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9), 1)))
    return out


if __name__ == '__main__':
    p = sys.argv[1]; t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0; t1 = float(sys.argv[3]) if len(sys.argv) > 3 else None
    g = grid(p, t0, t1); print(json.dumps({k: round(v, 4) for k, v in g.items()}))
    for a, db in envelope(p, g): print(f'  bar @ {a:7.2f}s  {db:6.1f} dB  ' + '#' * int(max(0, db + 40)))
