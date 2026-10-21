"""print-cartoon 配乐 / 音效工具包（numpy 合成，48 kHz 立体声）—— 源自 S015 score.py。
两条配乐路线（用户 2026-10-18：这个风格适合电子乐和 Lyria，不适合《千年以后》）：
  ① 合成电子乐：120 BPM、I–vi–IV–V，hi-hat 用收银扫码的「嘀」，每次结账一声同调的铃（Synth 类 + 乐器函数）
  ② Lyria 3.5：提示词按片子段落写，固定 120 BPM；拿到后测拍、按小节剪接对齐段落（bar_edit）
音效由画面登记的事件（print_cartoon.EV）驱动；剪辑版用 remap_music() 让每段保留自己的小节。"""
import math, subprocess, wave
import numpy as np
from scipy.signal import lfilter, butter

SR = 48000
rng = np.random.default_rng(15)


class Mix:
    """一条立体声缓冲；add(t, 信号, 增益, 声像)"""
    def __init__(self, dur): self.N = int((dur + .5) * SR); self.L = np.zeros(self.N); self.R = np.zeros(self.N)

    def add(self, t, sig, g=1., pan=0.):
        i = int(t * SR)
        if i >= self.N or i + len(sig) <= 0: return
        if i < 0: sig, i = sig[-i:], 0
        sig = sig[:self.N - i]
        self.L[i:i + len(sig)] += sig * g * math.sqrt((1 - pan) / 2) * 1.414
        self.R[i:i + len(sig)] += sig * g * math.sqrt((1 + pan) / 2) * 1.414

    def stereo(self): return np.stack([self.L, self.R], 1)


def mf(m): return 440 * 2 ** ((m - 69) / 12)


def tt(d): return np.arange(int(d * SR)) / SR


def env(d, a=.005, dec=.3):
    x = tt(d); e = np.minimum(1, x / a) * np.exp(-x / dec)
    e[-int(.01 * SR):] *= np.linspace(1, 0, int(.01 * SR)); return e


def lp(x, fc, o=2): b, a = butter(o, fc / (SR / 2)); return lfilter(b, a, x)


def bp(x, lo, hi, o=2): b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)


def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), 'high'); return lfilter(b, a, x)


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


def swoosh(rise=True, d=.42):
    """章节卡进 / 出的气声（移动低通的噪声）"""
    x = tt(d); n = noise(d); fc = 600 + 5000 * (x / d if rise else 1 - x / d)
    y = np.zeros_like(n); a_ = 0.
    for i in range(0, len(n), 256):
        al = 1 - math.exp(-2 * math.pi * fc[i] / SR)
        y[i:i + 256] = lfilter([al], [1, al - 1], n[i:i + 256], zi=[a_ * (1 - al)])[0]; a_ = y[min(i + 255, len(n) - 1)]
    return y * np.sin(np.pi * x / d) ** 1.5


def pop(d=.07):
    x = tt(d); return np.sin(2 * np.pi * np.cumsum(500 + 900 * x / d) / SR) * env(d, .001, .02)


def boing(d=.7):
    x = tt(d); return np.sin(2 * np.pi * np.cumsum(220 + 380 * (x / d) + 60 * np.sin(2 * np.pi * 14 * x)) / SR) * env(d, .005, .3)


def womp():
    out = []
    for j, (f0, f1) in enumerate(((330, 300), (300, 270), (270, 190))):
        d = .32 if j < 2 else .8; x = tt(d); f = np.linspace(f0, f1, len(x))
        out.append((j * .36, lp(np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR)), 1200) * env(d, .01, .3 if j < 2 else .6)))
    return out                                                          # [(偏移秒, 信号)]


def load(path, dur=None):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)
    return x if dur is None else np.concatenate([x, np.zeros((max(0, int(dur * SR) - len(x)), 2))])[:int(dur * SR)]


def bar_edit(src, edits, xf=.03):
    """按小节剪接：edits = [(原曲起, 原曲止), …]（秒，都落在原曲强拍上；先用 S011 的 show/beatmap.py 测拍）。片段之间 30 ms 交叉淡化。"""
    k = int(xf * SR); out = np.zeros((sum(int((b - a) * SR) for a, b in edits) + k, 2)); pos = 0
    for a, b in edits:
        s = src[int(a * SR):int(b * SR) + k].copy(); s[:k] *= np.linspace(0, 1, k)[:, None]; s[-k:] *= np.linspace(1, 0, k)[:, None]
        out[pos:pos + len(s)] += s; pos += len(s) - k
    return out[:pos + k]


def match_rms(x, ref, upto=100.):
    n = int(upto * SR); return x * np.sqrt((ref[:n] ** 2).mean()) / np.sqrt((x[:n] ** 2).mean() + 1e-12)


def remap_music(mus, seg):
    """剪辑版：每个保留段从它自己的起点按 1× 播放原配乐（2× 段只用前一半小节），片段 20 ms 交叉淡化"""
    import print_cartoon as PC
    tab, tot = PC.seg_table(seg); no = int(tot * SR); out = np.zeros((no, 2)); k = int(.02 * SR)
    for a, b, sp, o in tab:
        n = int((b - a) / sp * SR); ch = mus[int(a * SR):int(a * SR) + n + k].copy()
        ch[:k] *= np.linspace(0, 1, k)[:, None]; ch[-k:] *= np.linspace(1, 0, k)[:, None]
        i = int(o * SR); m = min(len(ch), no - i); out[i:i + m] += ch[:m]
    return out


def save(x, path):
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
