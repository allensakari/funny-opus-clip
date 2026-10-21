"""S012 3 分钟版配乐：把 lyria_a_1（131 s，110 BPM）在强拍上剪接延长到约 3 分钟（用户 2026-10-15：「剪接延长原曲」）。
做法：按小节（4 拍）切；在三个段落（绝望 / 人类的努力 / 屏息）里各找一段整 4 或 8 小节的「重复区间」[a, b)：
播放到 b 之后跳回 a 再播一遍。跳转点要求 b 小节和 a 小节的和声（12 维音级）、响度、频谱都最像，前一小节也像，接缝 30 ms 等功率交叉淡化。
输出 build/music/lyria_a_1_3min.wav、.beats.json（新时间轴上的拍点 + 段落锚点）、splice.txt（剪接记录）。usage: python extend_music.py"""
import os, sys, json, subprocess, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); EP = os.path.dirname(HERE)
SR = 48000
SRC = EP + '/build/music/lyria_a_1.mp3'
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', SRC, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
X = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
BT = np.array(json.load(open(EP + '/build/music/lyria_a_1.beats.json'))['beats'])
i0 = int(np.argmin(abs(BT - 17.90)))                       # a downbeat (drums enter)
bars = [BT[k] for k in range(i0 % 4, len(BT), 4)]          # every downbeat
bars = np.array(bars)


def feat(t0, t1):
    x = X[int(t0 * SR):int(t1 * SR)].mean(1); n = 8192; F = np.zeros(12); S = np.zeros(48)
    for s in range(0, len(x) - n, n // 2):
        sp = np.abs(np.fft.rfft(x[s:s + n] * np.hanning(n))); f = np.fft.rfftfreq(n, 1 / SR)
        m = (f > 60) & (f < 2000); pc = (np.round(12 * np.log2(f[m] / 440)) % 12).astype(int)
        np.add.at(F, pc, sp[m] ** 2)
        S += np.interp(np.geomspace(60, 12000, 48), f, sp)
    rms = 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    return F / (np.linalg.norm(F) + 1e-9), np.log1p(S) / (np.linalg.norm(np.log1p(S)) + 1e-9), rms


FE = [feat(bars[k], bars[k + 1]) for k in range(len(bars) - 1)]
def sim(i, j):
    (ca, sa, ra), (cb, sb, rb) = FE[i], FE[j]; return float(ca @ cb + sa @ sb - abs(ra - rb) / 6)
def score(a, b):                                            # jump from the end of bar b-1 back to bar a: bar b ~ bar a, bar b-1 ~ bar a-1
    return sim(b, a) + sim(b - 1, a - 1)

bar_of = lambda t: int(np.argmin(abs(bars - t)))
SECTIONS = [('绝望', 17.90, 57.20, 8), ('人类的努力', 57.20, 76.83, 8), ('屏息', 76.83, 92.11, 6)]
plan = []
for name, t0, t1, want in SECTIONS:
    b0, b1 = bar_of(t0), bar_of(t1); best = None
    for L, reps in ((8, 1), (4, 2), (4, 1)) if want >= 8 else ((4, 1),):
        if L * reps > want + 1: continue
        for a in range(b0 + 1, b1):
            b = a + L
            if b > b1 - 1: continue                       # never touch the section's last bar (it winds into the next section)
            sc = score(a, b) + .15 * L * reps            # prefer the longer extension when seams are comparably clean
            if best is None or sc > best[0]: best = (sc, a, b, reps)
    plan.append((name, *best))

# build the new timeline: original bars in order, each chosen span [a, b) replayed `reps` more times
spans = {b: (a, reps) for _, _, a, b, reps in plan}
out_bars = []
for k in range(0, len(bars) - 1):
    out_bars.append(k)
    if (k + 1) in spans:
        a, reps = spans[k + 1]
        for _ in range(reps): out_bars.extend(range(a, k + 1))
# pieces: lead-in before the first downbeat, then bars, then the tail after the last downbeat
pieces = [(0.0, bars[0])] + [(bars[k], bars[k + 1]) for k in out_bars] + [(bars[-1], len(X) / SR)]
XF = int(.03 * SR); y = []
for j, (t0, t1) in enumerate(pieces):
    seg = X[int(t0 * SR):int(t1 * SR) + XF].copy()
    y.append(seg)
outx = y[0][:-XF] if len(y[0]) > XF else y[0]
w = np.sin(np.linspace(0, np.pi / 2, XF)) ** 2
tl = []                                                     # (new time, original time) at each piece start
for seg in y[1:]:
    tl.append(len(outx) / SR)
    tail = outx[-XF:].copy(); outx = outx[:-XF] if len(outx) > XF else outx
    head = seg[:XF] * w[:, None] + tail * w[::-1, None]
    outx = np.concatenate([outx, head, seg[XF:]])
outx = outx[:int((sum(t1 - t0 for t0, t1 in pieces)) * SR)]
dur = len(outx) / SR
# new beat list: map each original beat inside each piece onto the new timeline
nbt = []
for (t0, t1), ts in zip(pieces[1:], tl):
    for b_ in BT[(BT >= t0 - 1e-6) & (BT < t1 - 1e-6)]: nbt.append(ts + (b_ - t0))
nbt = np.array(sorted(set(np.round(nbt, 4))))
# section anchors on the new timeline: the first occurrence of each original anchor's bar
starts = [0.0] + tl                                           # new start time of each piece (piece 0 = lead-in)
def new_t(orig):
    kb = bar_of(orig); j = out_bars.index(kb) + 1                 # first occurrence of that bar
    return starts[j] + orig - bars[kb]
anchors = {nm: new_t(t) for nm, t in (('groove', 17.90), ('loud', 57.20), ('breath', 76.83), ('fate', 92.11), ('climax', 109.57), ('slow', 116.12))}
peak = np.abs(outx).max()
wf = wave.open(EP + '/build/music/lyria_a_1_3min.wav', 'wb'); wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
wf.writeframes((np.clip(outx / max(peak, 1), -1, 1) * 32767).astype(np.int16).tobytes()); wf.close()
json.dump(dict(beats=nbt.tolist(), anchors=anchors, dur=dur), open(EP + '/build/music/lyria_a_1_3min.beats.json', 'w'), ensure_ascii=False, indent=0)
with open(EP + '/build/music/splice.txt', 'w') as f:
    for name, sc, a, b, reps in plan:
        f.write(f'{name}: 第 {a}–{b - 1} 小节（原曲 {bars[a]:.2f}–{bars[b]:.2f} s，{b - a} 小节）多播 {reps} 遍，接缝相似度 {score(a, b):.3f}\n')
    f.write(f'总长 {dur:.2f} s；新段落锚点 ' + ' · '.join(f'{k} {v:.2f}' for k, v in anchors.items()) + '\n')
print(open(EP + '/build/music/splice.txt').read())
