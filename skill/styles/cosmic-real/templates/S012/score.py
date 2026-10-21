"""S012 声音：Google Lyria 3.5 配乐（build/music/lyria_a_1.mp3）+ 程序合成音效，音效压在配乐下面约 7 dB。
  build/show/nobgm.wav — 只有音效；build/show/mix.wav — 配乐 + 音效。usage: python score.py
音效（这一期新做，跟着情绪线）：
  希望：城市灯光的细碎亮起声 · 宇宙日历的钟　绝望：熄灭的「咔」、大灭绝的低频重击、小行星呼啸 + 撞击、加速的钟表滴答
  努力：倒数无线电「哔」、火箭轰鸣（低频噪声 + 噼啪）、阿波罗通话的 Quindar 双音（2525 / 2475 Hz）、遥测哔声、光速扫频
  屏息：旅行者号的载波音、心跳　宿命：越走越快的钟、蒸汽嘶声、龟裂噼啪、膨胀的低频　吞没：巨大的低频轰鸣　熄灭：星星熄灭的轻响，最后心跳停止
转场：熄灯 = 开关闷响；红移 = 下滑扫频；时间流逝 = 磁带拉伸；引力透镜 = 低频起伏；尘埃 = 沙粒沙沙；曲速 = 上扬呼啸；日食 = 低沉嗡鸣；光柱 = 空气般的微光"""
import os, sys, wave, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
os.environ.pop('DRAFT', None)
CUT = os.environ.get('CUT', '')                                  # CUT=3min / 3m30 → the 3-minute / 3:30 versions (they patch film's grid, shots and music)
import film as F
if CUT == '3min': import film_3min
if CUT == '3m30': import film_3m30
if CUT == '3m30v5': import film_3m30_v5                            # the 3:31 v5 cut (卡点校正), restored for the YouTube English version
LONG = CUT in ('3min', '3m30', '3m30v5')

SR = 48000; T = F.T; N = int(T * SR); tt = np.arange(N) / SR; SH = F.SH; BEAT = F.BEAT
rng = np.random.default_rng(12)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x, axis=0)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x, axis=0)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, min(hi, SR / 2 - 100)], 'band', fs=SR, output='sos'), x, axis=0)
def st(x, pan=0.0): return np.stack([x * math.sqrt((1 - pan) / 2) * 1.414, x * math.sqrt((1 + pan) / 2) * 1.414], 1)
def put(out, x, t0, g=1.0):
    if x.ndim == 1: x = st(x)
    i = int(t0 * SR)
    if i < 0: x = x[-i:]; i = 0
    j = min(len(out), i + len(x))
    if j > i: out[i:j] += x[:j - i] * g
def env(n, a=.01, r=.2):
    t = np.arange(n) / SR; d = n / SR; return np.minimum(1, t / max(a, 1e-4)) * np.clip((d - t) / max(r, 1e-4), 0, 1)
def norm(x): return x / (np.abs(x).max() + 1e-9)


# ---------------------------------------------------------------- the sounds
def tick(f=3200, amp=.05):
    n = int(.04 * SR); t = np.arange(n) / SR; return (np.sin(2 * np.pi * f * t) * np.exp(-t * 180) + hp(rng.standard_normal(n), 4000) * np.exp(-t * 400) * .4) * amp
def clock(t0, dur, rate0, rate1, amp=.04, out=None):
    t, k = 0.0, 0
    while t < dur:
        put(out, st(tick(3200 if k % 2 else 2700, amp), (-.3 if k % 2 else .3)), t0 + t); k += 1
        r = rate0 * (rate1 / rate0) ** (t / dur); t += 1 / r
def chime(f, amp=.02, d=1.6):
    n = int(d * SR); t = np.arange(n) / SR; return (np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4)) * np.exp(-t * 3) * np.minimum(1, t / .003) * amp
def click_out(amp=.04):
    n = int(.12 * SR); t = np.arange(n) / SR; return (lp(rng.standard_normal(n), 1800) * np.exp(-t * 90) + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 40) * .6) * amp
def boom(amp=.15, f=38, d=3.5):
    n = int(d * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + 1.5 * np.exp(-t * 6))) / SR) * np.exp(-t * 1.1) + lp(rng.standard_normal(n), 180) * np.exp(-t * 1.6) * .6
    return st(x * np.minimum(1, t / .01) * amp)
def rumble(dur, amp=.1, f=120, swell=True):
    n = int(dur * SR); u = np.arange(n) / n; x = lp(rng.standard_normal(n), f)
    e = np.sin(np.pi * np.minimum(1, u * (1.6 if swell else 1))) ** 1.2 if swell else np.minimum(1, u / .05) * (1 - u) ** .8
    return np.stack([norm(x), norm(np.roll(x, 700))], 1) * e[:, None] * amp
def roar(dur, amp=.14):
    """rocket: low roar + crackle (randomly clipped impulses), swelling then fading as it climbs away"""
    n = int(dur * SR); u = np.arange(n) / n; x = norm(lp(rng.standard_normal(n), 400)) * .8
    cr = np.zeros(n); idx = rng.integers(0, n, int(dur * 900)); cr[idx] = rng.uniform(-1, 1, len(idx)); cr = bp(cr, 600, 5000) * 3
    e = np.minimum(1, u / .08) * (1 - u) ** 1.3
    y = (x + norm(cr) * .35) * e; return np.stack([y, np.roll(y, 400)], 1) * amp
def quindar(amp=.03):
    out = np.zeros(int(.6 * SR))
    for k, f in enumerate((2525, 2475)):
        n = int(.25 * SR); t = np.arange(n) / SR; out[k * int(.3 * SR):k * int(.3 * SR) + n] += np.sin(2 * np.pi * f * t) * env(n, .005, .01)
    return lp(out, 3500) * amp
def beeps(n_, f=1000, amp=.02, gap=.5):
    out = np.zeros(int((n_ * gap + .3) * SR))
    for k in range(n_):
        m = int(.12 * SR); t = np.arange(m) / SR; i = int(k * gap * SR); out[i:i + m] += np.sin(2 * np.pi * f * t) * env(m, .004, .02)
    return out * amp
def sweep(f0, f1, dur, amp=.04):
    n = int(dur * SR); t = np.arange(n) / SR; f = f0 * (f1 / f0) ** (t / dur); return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .05, .2) * amp
def noise_sweep(dur, f0, f1, amp=.05, q=1.3):
    n = int(dur * SR); u = np.arange(n) / n; x = rng.standard_normal(n); out = np.zeros(n)
    for k in range(20):
        a, b = k * n // 20, (k + 1) * n // 20; fc = f0 * (f1 / f0) ** ((k + .5) / 20); out[a:b] = bp(x, fc / q, fc * q)[a:b]
    return np.stack([out, np.roll(out, 300)], 1) / (np.abs(out).max() + 1e-9) * (np.sin(np.pi * u) ** 1.3)[:, None] * amp
def heartbeat(amp=.08):
    out = np.zeros(int(.8 * SR))
    for dt, g in ((0, 1), (.2, .7)):
        n = int(.25 * SR); t = np.arange(n) / SR; i = int(dt * SR)
        out[i:i + n] += np.sin(2 * np.pi * np.cumsum(48 * (1 + .6 * np.exp(-t * 30))) / SR) * np.exp(-t * 16) * g
    return lp(out, 200) * amp
def heartbeat_clear(amp=1.0):
    """the ending heartbeat (user 2026-10-15: louder, clearly audible): lub-dub with a low thump, a chest resonance (~110–180 Hz,
    audible on phone speakers) and a soft valve click; dry, not sent to the reverb"""
    out = np.zeros(int(1.0 * SR))
    for dt, g, f in ((0, 1, 52), (.24, .72, 60)):
        n = int(.3 * SR); t = np.arange(n) / SR; i = int(dt * SR)
        thump = np.sin(2 * np.pi * np.cumsum(f * (1 + .7 * np.exp(-t * 28))) / SR) * np.exp(-t * 13)
        chest = bp(rng.standard_normal(n), 90, 220) * np.exp(-t * 22) * 2.2 + np.sin(2 * np.pi * 2.6 * f * t) * np.exp(-t * 24) * .55
        click = bp(rng.standard_normal(n), 900, 2600) * np.exp(-t * 160) * .25
        out[i:i + n] += (thump + chest + click) * g
    return out / (np.abs(out).max() + 1e-9) * amp


def carrier(dur, amp=.012):
    n = int(dur * SR); t = np.arange(n) / SR; f = 1400 * (1 + .002 * np.sin(2 * np.pi * .2 * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + .3 * np.sin(2 * np.pi * 3 * t)) + bp(rng.standard_normal(n), 800, 3000) * .5
    return x * env(n, .8, 1.2) * amp
def sand(dur, amp=.03):
    n = int(dur * SR); u = np.arange(n) / n; x = hp(rng.standard_normal(n), 3000) * (rng.uniform(0, 1, n) > .7)
    return np.stack([x, np.roll(x, 200)], 1) / (np.abs(x).max() + 1e-9) * (np.sin(np.pi * u) ** .8)[:, None] * amp
def crackle(dur, amp=.03, rate=60):
    n = int(dur * SR); x = np.zeros(n); idx = rng.integers(0, n, int(dur * rate)); x[idx] = rng.uniform(-1, 1, len(idx))
    return bp(x, 900, 6000) * 4 * amp
def shimmer(dur, amp=.02):
    n = int(dur * SR); u = np.arange(n) / n; t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + k) for k, f in enumerate((2093, 2637, 3136, 4186))) * (.6 + .4 * np.sin(2 * np.pi * 7 * t))
    return x * np.sin(np.pi * u) ** 1.5 * amp


TRANS = {0: lambda d: st(click_out(.05)) + 0, 1: lambda d: st(sweep(900, 180, d * 1.1, .03)), 2: lambda d: noise_sweep(d, 3000, 400, .04, 1.15),
         3: lambda d: st(lp(sweep(70, 45, d * 1.2, .08), 200)), 4: lambda d: sand(d * 1.2, .035), 5: lambda d: noise_sweep(d, 300, 5000, .05),
         6: lambda d: st(lp(sweep(55, 50, d * 1.3, .07), 160)), 7: lambda d: st(shimmer(d * 1.1, .018)),
         8: lambda d: st(lp(sweep(90, 60, d * 1.3, .07), 250) * (1 + .5 * np.sin(2 * np.pi * 6 * np.arange(int(d * 1.3 * SR)) / SR))),     # ripple: a low warble
         9: lambda d: st(crackle(d * 1.1, .04, 160)) + rumble(d * 1.1, .03, 200)}                                                                # burn: crackling edge + low roar


def _sh(name):
    try: return F.C(name)
    except KeyError: return None                                          # a shot this cut doesn't have: its sounds are skipped
def at(name, u=0.0): sh = _sh(name); return sh['t0'] + u * (sh['t1'] - sh['t0']) if sh else -1e6
def dur(name): sh = _sh(name); return sh['t1'] - sh['t0'] if sh else 1.0


def effects():
    fx = np.zeros((N, 2))
    for sh in SH[1:]:
        if sh['td'] < .05:                                               # a hard cut on beat 1: the band's own kick is the hit (v6: no extra boom), except a light one on the two big moments
            if sh['draw'].__name__ in ('d_launch', 'd_engulf'): put(fx, boom(.035, 42, 1.0), sh['t0'])
        else: put(fx, TRANS[sh['mode']](sh['td']), sh['t0'] - sh['td'] / 2)
    # 希望
    for k in range(14): put(fx, st(chime(rng.choice([1568, 1760, 2093, 2349, 2637]), .008), rng.uniform(-.7, .7)), (at('hook') if CUT == '3m30' else 0) + rng.uniform(.4, 4.2))   # city lights appear
    for k in range(4): put(fx, st(tick(2900, .03)), at('calendar', .55) + k * .3)
    for k in range(18): put(fx, st(chime(rng.choice([1319, 1568, 1760, 2093]), .006), rng.uniform(-.8, .8)), at('lights') + rng.uniform(0, dur('lights') * .9))
    put(fx, st(shimmer(dur('sunrise'), .012)), at('sunrise'))
    # 绝望
    for k in range(40): put(fx, st(click_out(.012), rng.uniform(-.8, .8)), at('species', .25 + .6 * k / 40))
    for j, (e, _) in enumerate(F.EXT): put(fx, boom(.08, 42 - j * 2, 2.0), at('extinct', .9 * (1 - e / 540) + .02))      # each extinction as the line reaches it
    if CUT == '3m30':                                                     # the bigger impact: a long descending roar, a deep slam, then rumble and falling debris
        put(fx, noise_sweep(dur('impact2') * .42, 400, 4000, .07), at('impact2')); put(fx, boom(.26, 28, 6.0), at('impact2', .42))
        put(fx, rumble(dur('impact2') * .7, .1, 90, swell=False), at('impact2', .43)); put(fx, st(crackle(dur('impact2') * .5, .03, 90)), at('impact2', .55))
    else:
        put(fx, noise_sweep(dur('impact') * .55, 600, 3500, .05), at('impact')); put(fx, boom(.18, 34, 4.0), at('impact', .55))
    clock(at('dayclock'), dur('dayclock') * .8, 4, 18, .03, fx); put(fx, st(tick(2200, .06)), at('dayclock', .82))
    for k in range(109): put(fx, st(click_out(.01), rng.uniform(-.8, .8)), at('people', .2 + .65 * k / 109))
    put(fx, st(carrier(dur('dot'), .006)), at('dot'))
    put(fx, rumble(dur('sun'), .06, 90), at('sun'))
    for k in range(10): put(fx, st(click_out(.03), rng.uniform(-.6, .6)), at('off', .15 + .08 * k))
    if CUT != '3m30': put(fx, st(beeps(4, 880, .02, 1.0)), at('pad', .1))          # (the 3:30 cut has no separate pad shot)
    for k in range(10): put(fx, st(beeps(1, 1200 if k < 9 else 1600, .022)), at('ignite') + k * dur('ignite') / 10.5)
    put(fx, rumble(dur('ignite') * 1.1, .07, 140), at('ignite'))
    # 人类的努力
    put(fx, roar(dur('launch') * 1.6, .16), at('launch') - .02); put(fx, boom(.12, 40, 2.5), at('launch'))
    put(fx, st(quindar(.03), .4), at('earthrise', .25)); put(fx, st(quindar(.025), -.4), at('earthrise', .7))
    put(fx, st(beeps(3, 1500, .015, .25), .5), at('artemis_photo' if LONG else 'artemis', .3))
    put(fx, st(sweep(400, 3200, 1.36, .025)), at('artemis_photo' if LONG else 'artemis', .38))                                   # light crossing the distance
    put(fx, noise_sweep(dur('vgr_photo' if LONG else 'vgr_launch'), 200, 1800, .05), at('vgr_photo' if LONG else 'vgr_launch'))
    put(fx, noise_sweep(dur('helio'), 5000, 900, .03, 1.1), at('helio'))
    # 屏息
    put(fx, st(carrier(dur('alone') + dur('scalebar'), .012)), at('alone'))
    for k in range(int((at('bright') - at('alone')) / 1.1)): put(fx, st(heartbeat(.07)), at('alone') + .5 + k * 1.1)
    clock(at('drift'), dur('drift'), 1.0, 1.0, .02, fx)
    # 宿命
    clock(at('bright'), at('engulf') - at('bright'), 2, 16, .025, fx)
    put(fx, rumble(at('engulf') - at('bright'), .05, 70), at('bright'))
    put(fx, noise_sweep(dur('dry'), 2000, 6000, .03, 1.5), at('dry'))
    if not LONG: put(fx, st(crackle(dur('scorch'), .04, 120)), at('scorch'))           # (the 3-min cut folds the scorched Earth into its neighbours)
    put(fx, st(lp(sweep(80, 40, dur('swell') + dur('giant'), .1), 160)), at('swell'))
    # 吞没
    put(fx, boom(.3, 30, 5.0), at('engulf')); put(fx, rumble(dur('engulf') + dur('dwarf'), .14, 110, swell=False), at('engulf'))
    put(fx, st(sweep(600, 3000, dur('dwarf'), .02)), at('dwarf'))
    # 熄灭
    for k in range(26): put(fx, st(chime(rng.choice([523, 659, 784, 1047]) * .5, .006, 2.5), rng.uniform(-.8, .8)), at('stars_c' if CUT == '3m30' else 'stars') + rng.uniform(0, dur('stars_c' if CUT == '3m30' else 'stars') + dur('last_c' if CUT == '3m30' else 'last') * .6))
    if LONG:                                                              # the 3-min cut's ten new shots (also in the 3:30 cut)
        MAM = 'pyr_mammoth' if CUT == '3m30' else 'mammoth'
        put(fx, rumble(dur(MAM), .03, 300), at(MAM))                       # wind over the snow
        put(fx, rumble(dur(MAM) * .5, .025, 140), at(MAM, .45))                  # the herd fades: a low sigh, no footsteps
        for k in range(7): put(fx, st(tick(1800 + 200 * (k % 3), .03)), at('writing', .5 + k * .03))       # wedge taps
        put(fx, st(lp(sweep(110, 90, dur('moon'), .05), 400)), at('moon'))
        put(fx, st(bp(rng.standard_normal(int(dur('iss') * SR)), 1500, 4000) * .006), at('iss')); put(fx, st(quindar(.02), .3), at('iss', .4))
        put(fx, st(shimmer(dur('jwst'), .016)), at('jwst'))
        put(fx, st(crackle(dur('record'), .025, 40)), at('record')); put(fx, st(chime(784, .02, 3)), at('record', .15))
        put(fx, noise_sweep(dur('speed'), 400, 6000, .05), at('speed'))
        for k in range(6): put(fx, st(beeps(1, 1400, .02 * (1 - k / 7))), at('silence') + k * (.3 + .25 * k))      # the beacon slows, then stops
        put(fx, st(lp(rng.standard_normal(int(dur('plants') * SR)), 900) * .008), at('plants')); put(fx, st(crackle(dur('plants'), .015, 30)), at('plants', .3))
    if CUT == '3m30':                                                     # the cold open: the ending first, a low drone under the piano
        put(fx, rumble(dur('cold') + .6, .07, 90, swell=False), 0.0); put(fx, boom(.08, 34, 3.0), 0.02)
    if CUT == '3m30':                                                     # 第一幕 / 第二幕 new shots
        for k in range(5): put(fx, st(beeps(1, 1000, .02)), at('medicine', .1) + k * .8)                       # a heart monitor, steady
        put(fx, rumble(dur('seeds'), .03, 400), at('seeds')); put(fx, clunk_door(), at('seeds', .55))
        put(fx, st(sweep(200, 2400, dur('fusion') * .55, .03)), at('fusion')); put(fx, rumble(dur('fusion') * .5, .06, 160), at('fusion', .5))
        put(fx, noise_sweep(dur('dart') * .95, 300, 3000, .05), at('dart')); put(fx, boom(.12, 40, 2.0), at('dart', .97))
        put(fx, rumble(dur('parker'), .07, 600), at('parker'))
        put(fx, st(rotor(dur('ingenuity'), .025)), at('ingenuity'))
        put(fx, st(shimmer(dur('pluto'), .012)), at('pluto')); put(fx, st(lp(sweep(50, 45, dur('eht'), .07), 150)), at('eht'))
        put(fx, st(chirp(dur('ligo') * .8, .06)), at('ligo'))
        for k in range(10): put(fx, st(beeps(1, 2380 / 2, .015)), at('arecibo', .05) + k * .2)
    return fx


def clunk_door(amp=.06):
    n = int(1.2 * SR); t = np.arange(n) / SR
    return st((lp(rng.standard_normal(n), 500) * np.exp(-t * 9) + np.sin(2 * np.pi * 70 * t) * np.exp(-t * 7) * .8) * amp)
def rotor(dur, amp=.02):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.sign(np.sin(2 * np.pi * 84 * t)) * .5 + bp(rng.standard_normal(n), 100, 900) * .6
    return lp(x, 900) * np.sin(np.pi * np.minimum(1, t / dur)) * amp
def chirp(dur, amp=.06):
    """the gravitational-wave 'chirp' made audible: frequency and loudness sweep up, then ring down"""
    n = int(dur * SR); t = np.arange(n) / SR; tau = np.maximum(1e-3, 1.0 - t / dur)
    f = 35 + 220 * (1 - tau) ** 3; a = (.15 + .85 * (1 - tau) ** 2)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * a * amp


def reverb(x, d=3.0, mix=.28):
    ir = rng.normal(0, 1, int(d * SR)) * np.exp(-np.arange(int(d * SR)) / SR * 1.6); ir = bp(ir, 150, 9000); ir /= np.abs(ir).sum() ** .5 * 6
    return x + mix * np.stack([fftconvolve(x[:, 0], ir)[:len(x)], fftconvolve(x[:, 1], np.roll(ir, 331))[:len(x)]], 1)


def load_music(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64); out = np.zeros((N, 2)); out[:min(N, len(x))] = x[:N]; return out


def save(x, path):
    x = x * (.6 / np.abs(x).max()); w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    fade = (np.clip(tt / .05, 0, 1) * np.clip((T - tt) / .3, 0, 1))[:, None]
    fx = reverb(effects()); mu = load_music(F.MUSIC)
    g = .4 * np.sqrt((mu ** 2).mean()) / (np.sqrt((fx ** 2).mean()) + 1e-9)
    out = F.BUILD; os.makedirs(out, exist_ok=True)
    hb = np.zeros((N, 2))                                                   # the last heartbeats, then silence: their own dry layer, not ducked
    if not LONG:                                                          # 3 分钟版 / 3:30 版：用户要求去掉结尾心跳（2:11 版保留）
        for k in range(4): put(hb, st(heartbeat_clear(1 - k * .16)), at('black') + .4 + k * 1.35)
    peak = np.abs(mu).max(); hb *= .55 * peak
    save((fx + hb / max(g, 1e-6)) * fade, out + 'nobgm.wav'); save((mu + fx * g + hb) * fade, out + 'mix.wav'); print('ok', f'fx gain {g:.2f}', out)
