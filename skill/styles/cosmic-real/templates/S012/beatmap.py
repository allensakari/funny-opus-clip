"""音乐 → 节拍表：onset flux + Ellis (2007) 动态规划节拍跟踪（允许速度缓慢漂移），再按 4 拍分小节。
usage: python beatmap.py track.mp3 [--bpm 110]   → 打印各段速度、能量曲线；写 build/music/<name>.beats.json（beats、downbeats、rms）"""
import sys, json, subprocess, pathlib
import numpy as np

SR, HOP = 22050, 256
FPS = SR / HOP


def load(path, sr=SR):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def onset(x):
    n = len(x) // HOP; fr = x[:n * HOP].reshape(n, HOP) * np.hanning(HOP)
    sp = np.log1p(np.abs(np.fft.rfft(fr, 1024, axis=1)) * 30)
    fl = np.concatenate([[0], np.maximum(0, np.diff(sp, axis=0)).sum(1)])
    fl -= np.convolve(fl, np.ones(64) / 64, 'same'); fl = np.maximum(fl, 0)
    return fl / (fl.std() + 1e-9)


def tempo(fl, lo=60, hi=180, prior=None):
    ac = np.correlate(fl, fl, 'full')[len(fl) - 1:]; lags = np.arange(len(ac))
    bpm = 60 * FPS / np.maximum(lags, 1); m = (bpm > lo) & (bpm < hi)
    w = ac.copy()
    if prior: w = w * np.exp(-.5 * (np.log2(bpm / prior) / .4) ** 2)
    k = lags[m][np.argmax(w[m])]; return 60 * FPS / k


def track(fl, bpm, tight=120.):
    """Ellis DP: maximise onset strength at beats + penalty for deviation from the period"""
    P = 60 * FPS / bpm; n = len(fl); score = fl.copy(); back = -np.ones(n, int)
    lo, hi = int(P * .5), int(P * 2)
    for i in range(lo, n):
        prev = np.arange(max(0, i - hi), i - lo)
        if len(prev) == 0: continue
        pen = -tight * np.log((i - prev) / P) ** 2
        j = np.argmax(score[prev] + pen); score[i] = fl[i] + score[prev][j] + pen[j]; back[i] = prev[j]
    i = int(np.argmax(score[-int(P * 2):])) + n - int(P * 2); out = []
    while i >= 0: out.append(i); i = back[i]
    return np.array(out[::-1]) / FPS


if __name__ == '__main__':
    path = pathlib.Path(sys.argv[1]); prior = float(sys.argv[sys.argv.index('--bpm') + 1]) if '--bpm' in sys.argv else None
    x = load(path); fl = onset(x); dur = len(x) / SR
    bpm = tempo(fl, prior=prior)
    for a, b in ((0, 20), (20, 60), (60, 80), (80, 95), (95, 115), (115, dur)):
        s = fl[int(a * FPS):int(b * FPS)]
        if len(s) > FPS * 4: print(f'  {a:5.0f}–{b:5.0f} s  tempo ≈ {tempo(s, prior=bpm):6.1f} BPM')
    bt = track(fl, bpm)
    ib = np.diff(bt); print(f'{path.name}: {dur:.1f} s · global {bpm:.1f} BPM · {len(bt)} beats · local BPM {60 / np.median(ib):.1f} (IQR {60 / np.percentile(ib, 75):.1f}–{60 / np.percentile(ib, 25):.1f})')
    # downbeat phase: which of the 4 offsets carries the most low-frequency energy
    lowx = load(path, 4000); fr = int(.06 * 4000)
    e = np.array([np.sqrt((lowx[int(t * 4000):int(t * 4000) + fr] ** 2).mean() + 1e-12) for t in bt])
    ph = int(np.argmax([e[k::4].mean() for k in range(4)])); down = bt[ph::4]
    rms = [float(np.sqrt((x[int(t * SR):int((t + 1) * SR)] ** 2).mean())) for t in range(int(dur))]
    db = 20 * np.log10(np.array(rms) + 1e-6)
    for t in range(0, int(dur), 4): print(f'  {t:4d}s {db[t]:6.1f} dB ' + '#' * max(0, int((db[t] + 45) * 1.2)))
    json.dump(dict(beats=bt.tolist(), downbeats=down.tolist(), rms_db=db.tolist(), bpm=bpm, dur=dur), open(path.with_suffix('.beats.json'), 'w'))
