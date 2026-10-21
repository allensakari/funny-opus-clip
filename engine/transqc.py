"""数说世界 转场质检（借鉴 Anatomy skill 的「慢放连续帧」检查，2026-10-16）
直接读视频文件，逐帧（每一帧，不抽样）检查转场里肉眼在正常速度下看不出、但观众会感到「跳了一下」的问题。
任何画面引擎都能用（render.py / show/film.py / GLSL），因为它只看成片。
在期目录运行：  python ../../engine/transqc.py [视频，默认 build/video.mp4] [--ignore 12.0-14.5,30-31] [--out build/transqc]
检查：
  ① 单帧闪烁：某一帧和前后两帧都差很多，但前后两帧彼此很像、再往外一帧也平稳 → 有一帧「闪」了（整幅或某一块区域）；
     逐帧滚动的计数器、粒子之类每帧都在变的画面不算
  ② 淡出时亮度回升：整体亮度在 ±8 帧内一路往下走（≥ 75% 的帧在变暗），中间却有一帧明显变亮
  ③ 硬切（只列出，不算问题）：一帧之内整幅画面突变；每个硬切也出连续帧拼图，节点 ③ 里人工看一眼
结果：<out>.txt + <out>/<序号>_<类型>_<时间>.jpg（13 帧慢放拼图，中间一帧红框）。① ② 有问题时退出码 1；
确实有意为之的（S002 的闪电本身就是单帧闪光）用 --ignore 跳过，并在节点 ③ 里逐条说明。"""
import os, sys, json, subprocess
import numpy as np
import skia

args = sys.argv[1:]
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
pos = [a for i, a in enumerate(args) if not a.startswith('--') and (i == 0 or args[i - 1] not in ('--ignore', '--out'))]
SRC = pos[0] if pos else 'build/video.mp4'
OUT = opt('--out', os.path.join(os.path.dirname(SRC) or '.', 'transqc'))
IGN = [tuple(float(x) for x in r.split('-')) for r in opt('--ignore', '').split(',') if r]

info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                           'stream=width,height,r_frame_rate', '-of', 'json', SRC]))['streams'][0]
SW, SH = info['width'], info['height']; num, den = map(int, info['r_frame_rate'].split('/')); FPS = num / den
S = 4 if max(SW, SH) >= 1600 else 2                     # analyse at 1/4 size: averages out grain and encoder noise
W, H = SW // S // 2 * 2, SH // S // 2 * 2
GX, GY = (16, 9) if W > H else (9, 16)                  # tiles for local flashes
FLASH_ALL, FLASH_TILE, RATIO, SAME = 3.0, 12.0, .4, .15            # mean |Δ| on 0–255
CUT = 18.0
FADE, RISE, K = 4.0, 1.0, 8


def frames():
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-vf', f'scale={W}:{H}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE)
    n = W * H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.wait()


def tiles(d):                                           # (H, W) → (GY, GX) tile means
    h, w = H // GY * GY, W // GX * GX
    return d[:h, :w].reshape(GY, h // GY, GX, w // GX).mean((1, 3))


def diff(a, b): return np.abs(a.astype(np.int16) - b.astype(np.int16)).mean(2)


# pass 1: per-frame numbers
L, DA, DT, FL = [], [], [], []                          # luma, |f[i]-f[i-1]| whole frame, per tile, flash score at i
win = []
for f in frames():
    L.append(float((f[..., 0] * .2126 + f[..., 1] * .7152 + f[..., 2] * .0722).mean()))
    win = (win + [f])[-5:]
    if len(win) >= 2:
        d = diff(win[-1], win[-2]); DA.append(float(d.mean())); DT.append(tiles(d))
    else: DA.append(0.0); DT.append(np.zeros((GY, GX)))
    if len(win) == 5:                                   # judge frame m = win[2]: it differs from both neighbours, the neighbours
        m = len(L) - 3                                  # match each other, and the scene around them is steady (a rolling counter isn't)
        cc = diff(win[3], win[1]); c = tiles(cc)
        a, b, pa, pb = DT[m], DT[m + 1], DT[m - 1], DT[m + 2]
        lo = np.minimum(a, b); hit = (lo > FLASH_TILE) & (c < SAME * lo) & (np.maximum(pa, pb) < RATIO * lo)
        ga, gb, gc = DA[m], DA[m + 1], float(cc.mean()); glo = min(ga, gb)
        whole = glo > FLASH_ALL and gc < SAME * glo and max(DA[m - 1], DA[m + 2]) < RATIO * glo
        FL.append((m, whole, gc, int(hit.sum()), np.argwhere(hit)))
N = len(L); L = np.array(L); DA = np.array(DA); T = N / FPS
tc = lambda i: i / FPS
ignored = lambda i: any(a <= tc(i) <= b for a, b in IGN)

events = []                                             # (frame, kind, desc, is_problem)
for i, whole, gc, nt, where in FL:
    if not (whole or nt) or ignored(i): continue
    if whole: events.append((i, 'flash', f'单帧闪烁（整幅）：Δ前 {DA[i]:.1f} / Δ后 {DA[i + 1]:.1f}，前后两帧彼此只差 {gc:.1f}', True))
    else:
        y, x = where[0]; region = ('上' if y < GY / 3 else '下' if y >= GY * 2 / 3 else '中') + ('左' if x < GX / 3 else '右' if x >= GX * 2 / 3 else '中')
        events.append((i, 'flash', f'单帧闪烁（局部，{nt} 块，{region}部）', True))
for i in range(K, N - K - 1):
    if ignored(i): continue
    st = np.diff(L[i - K:i + K + 2])                    # a real fade falls steadily; a boiling shader only wobbles
    if (L[i + 1] - L[i] > max(RISE, 3 * np.median(np.abs(st))) and L[i - K] - L[i] > FADE and L[i + 1] - L[i + 1 + K] > FADE
            and (st < 0).mean() >= .75):
        events.append((i + 1, 'fade', f'淡出中亮度回升：{L[i]:.1f} → {L[i + 1]:.1f}（前 {K} 帧 {L[i - K]:.1f}，后 {K} 帧 {L[i + 1 + K]:.1f}）', True))
for i in range(1, N):
    if DA[i] > CUT and not ignored(i):
        events.append((i, 'cut', f'硬切：Δ {DA[i]:.1f}，亮度 {L[i - 1]:.1f} → {L[i]:.1f}', False))

ev, last = [], {}                                       # one entry per run of neighbouring frames of the same kind
for e in sorted(events):
    if e[1] in last and e[0] - last[e[1]][0] <= (FPS if e[3] else 3):              # problems within 1 s = one entry
        it = last[e[1]][1]; it['n'] += 1; it['end'] = e[0]; last[e[1]][0] = e[0]; continue
    it = dict(i=e[0], end=e[0], kind=e[1], desc=e[2], bad=e[3], n=1); ev.append(it); last[e[1]] = [e[0], it]

# pass 2: contact sheets, 13 frames centred on each event
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith('.jpg'): os.remove(os.path.join(OUT, f))
need = {}
for k, it in enumerate(ev):
    for j in range(it['i'] - 6, it['i'] + 7):
        if 0 <= j < N: need.setdefault(j, []).append(k)
grab = {}
for j, f in enumerate(frames()):
    if j in need: grab[j] = f.copy()
TW = 240 if W > H else 135; TH = round(TW * H / W); COLS = 13 if W > H else 7
font = skia.Font(skia.Typeface('Helvetica'), 13)
NAME = dict(flash='闪烁', fade='亮度回升', cut='硬切')
for k, it in enumerate(ev):
    js = [j for j in range(it['i'] - 6, it['i'] + 7) if j in grab]
    rows = -(-len(js) // COLS); surf = skia.Surface(COLS * (TW + 4) + 4, rows * (TH + 22) + 4); cv = surf.getCanvas(); cv.clear(skia.ColorBLACK)
    for n, j in enumerate(js):
        x, y = 4 + n % COLS * (TW + 4), 4 + n // COLS * (TH + 22)
        img = skia.Image.fromarray(np.dstack([grab[j], np.full((H, W), 255, np.uint8)]).copy(), colorType=skia.kRGBA_8888_ColorType)
        cv.drawImageRect(img, skia.Rect.MakeXYWH(x, y, TW, TH), skia.SamplingOptions(skia.FilterMode.kLinear))
        if j == it['i']: cv.drawRect(skia.Rect.MakeXYWH(x - 2, y - 2, TW + 4, TH + 4), skia.Paint(Color=skia.ColorRED, Style=skia.Paint.kStroke_Style, StrokeWidth=3))
        cv.drawString(f'{tc(j):.2f}s  #{j}  L{L[j]:.0f}', x, y + TH + 15, font, skia.Paint(Color=skia.ColorWHITE, AntiAlias=True))
    it['shot'] = f"{k + 1:03d}_{NAME[it['kind']]}_{tc(it['i']):07.2f}.jpg"
    surf.makeImageSnapshot().save(os.path.join(OUT, it['shot']), skia.kJPEG, 85)

bad = [e for e in ev if e['bad']]; cuts = [e for e in ev if not e['bad']]
lines = [f'转场 QC {SRC}: {N} 帧 @ {FPS:g} fps（{T:.1f} s，逐帧），{len(bad)} 个问题，{len(cuts)} 个硬切（只列出）'
         + (f"；跳过 {', '.join(f'{a:g}–{b:g}s' for a, b in IGN)}" if IGN else '')]
for e in bad + cuts:
    lines.append(f"{'⚠' if e['bad'] else '·'} {tc(e['i']):7.2f}s  #{e['i']:<5d} {e['desc']}" + (f"（到 {tc(e['end']):.2f}s 共 {e['n']} 处）" if e['n'] > 1 else '') + f"  → {e['shot']}")
open(OUT + '.txt', 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
sys.exit(1 if bad else 0)
