"""数说世界 界面音效（全账号默认，用户 2026-10-10）：文字 / 数字落定、滑入滑出、计数嘀嗒、条形生长、场景出现、下沉。
全部程序合成，返回 (n, 2) 立体声数组；用 sfx.put(buf, cue, at) 放到时间线上。首次用于 S003（A2 版）。"""
import numpy as np
import sfx as A
SR = A.SR


def env_noise(dur, lo, hi, attack, amp, seed, rev=False):
    r = np.random.default_rng(seed); n = int(dur * SR); t = np.arange(n) / SR
    x = A.bp(r.standard_normal(n), lo, hi); e = np.minimum(1, t / attack) * np.exp(-np.maximum(0, t - attack) / (dur * .35))
    if rev: e = e[::-1]
    x = x * e; x *= amp / (np.abs(x).max() + 1e-9)
    return np.stack([x, np.roll(x, 70)], 1)


def pop(amp=.12, f=900):
    """text / number lands: soft tick + short tonal body"""
    n = int(.18 * SR); t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t / .03) * .6 + np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t / .015) * .3) * amp
    x[:300] += A.bp(np.random.default_rng(int(f)).standard_normal(300), 2000, 8000) * np.exp(-np.arange(300) / 60) * amp * .8
    return np.stack([x, x], 1)


def swish(dur=.35, amp=.06, seed=0, rev=False): return env_noise(dur, 1500, 9000, dur * .7, amp, seed, rev)       # text slides in / out
def swell(dur=1.2, amp=.07, seed=0): return env_noise(dur, 200, 2500, dur * .85, amp, seed)                      # scene / map reveal
def rumble(dur=2.0, amp=.08, seed=0): return env_noise(dur, 50, 400, dur * .8, amp, seed)                         # descent / heavy fill


def sweep(dur=.6, f0=220, f1=660, amp=.06):
    """rising glide under a growing bar"""
    n = int(dur * SR); t = np.arange(n) / SR; f = f0 * (f1 / f0) ** (t / dur)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / .05) * np.exp(-np.maximum(0, t - dur * .7) / .08) * amp
    return np.stack([x, x], 1)


def ticks(t0, t1, n, amp=.05, f=2200):
    """counter rolling: n blips spread over t0..t1 → [(buf, at), ...]"""
    return [(np.stack([A.blip(f + 7 * j, .03, amp)] * 2, 1), t0 + (t1 - t0) * j / max(1, n - 1)) for j in range(n)]
