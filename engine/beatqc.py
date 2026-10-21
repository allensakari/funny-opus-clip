"""卡点质检（硬性：必须 0 个问题才能进节点 ③ 和出成片）：画面的每个切点 / 转场 / 关键动作都要落在配乐的拍点网格上。
在期目录运行：  python ../../engine/beatqc.py [视频，默认 build/video.mp4] [--music 配乐] [--events build/events.json]
                                            [--grid 8] [--tol 0.035] [--ignore 12.0-14.5,30-31] [--out build/beatqc.txt]
  拍点网格：engine/beats.py 的 grid() 测 --music（对齐到成片时间轴的纯配乐，例如 build/music.wav；默认用视频自己的音轨）。
  画面事件：
    ① events（必给，默认 build/events.json）：本期时间轴导出的设计时间，[{"t": 秒, "name": "…", "dur": 转场长度}] 或秒的列表——
       镜头 / 场景切换、转场中心、数字砸下、关键动作。旁白驱动的字幕出现时间不算。这是判定的依据。
    ② 视频里的单帧硬切（整幅画面一帧内突变，同 transqc.py）：按实际帧时间判定。
    ③ 视频里的多帧突变（相隔 ≤ 3 帧的连续突变 = 一个快速转场 / 闪动）：必须落在某个 ① 事件的窗口里（±max(0.6 s, dur)），
       否则算「未登记的画面跳变」——把它的设计时间加进 events（会按网格判定），或者改成卡拍。
  判定：① ② 离最近的网格点不超过 --tol 秒（默认 max(35 ms, 1 帧)）。--grid = 每小节几格：4 = 每拍，8 = 8 分音符（默认），2 = 半小节。
  结果：<out> 逐条列出；有问题退出码 1。有意不卡拍的（例如黑场里的一句话）用 --ignore 跳过并在节点 ③ 说明。"""
import os, sys, json, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beats

args = sys.argv[1:]
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
VALS = ('--music', '--events', '--grid', '--tol', '--ignore', '--out')
pos = [a for i, a in enumerate(args) if not a.startswith('--') and (i == 0 or args[i - 1] not in VALS)]
SRC = pos[0] if pos else 'build/video.mp4'
MUSIC = opt('--music', SRC)
SUB = int(opt('--grid', '8'))
IGN = [tuple(float(x) for x in r.split('-')) for r in opt('--ignore', '').split(',') if r]
OUT = opt('--out', 'build/beatqc.txt')
EVF = opt('--events', 'build/events.json')

info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate',
                                           '-of', 'json', SRC]))['streams'][0]
num, den = map(int, info['r_frame_rate'].split('/')); FPS = num / den
TOL = float(opt('--tol', max(.035, 1 / FPS)))
CUT = 18.0                                               # mean |Δ| on 0–255 at 1/4 size: same threshold as transqc.py


def jumps():
    """runs of frames that change abruptly → [(peak time, frames in the run)]"""
    W, H = info['width'] // 4 // 2 * 2, info['height'] // 4 // 2 * 2
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-vf', f'scale={W}:{H}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    prev, i, hit = None, 0, []
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        f = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.int16)
        if prev is not None:
            d = np.abs(f - prev).mean()
            if d > CUT: hit.append((i, d))
        prev, i = f, i + 1
    p.wait()
    runs = []
    for fr, d in hit:
        if runs and fr - runs[-1][-1][0] <= 3: runs[-1].append((fr, d))
        else: runs.append([(fr, d)])
    return [(max(r, key=lambda x: x[1])[0] / FPS, len(r)) for r in runs]


def events():
    if not os.path.exists(EVF): return None
    return [dict(t=float(e)) if not isinstance(e, dict) else dict(e, t=float(e['t'])) for e in json.load(open(EVF))]


g = beats.grid(MUSIC)
step = g['beat'] * 4 / SUB; t0 = g['first_downbeat']
EV = events(); J = jumps()
rows = [(e['t'], e.get('name', 'event'), True) for e in EV or []]
for t, n in J:
    if n == 1: rows.append((t, 'hard cut', True))
    elif not any(abs(t - e['t']) <= max(.6, e.get('dur', 0)) for e in EV or []): rows.append((t, f'未登记的跳变 ×{n} 帧', False))
lines, bad = [], 0
for t, name, judged in sorted(rows):
    k = round((t - t0) / step); gt = t0 + k * step; d = t - gt
    ignored = any(a <= t <= b for a, b in IGN)
    ok = ignored or (judged and abs(d) <= TOL)
    bad += not ok
    lines.append(f'{"  " if ok else "✗ "}{t:7.3f}s  {name:<22} 网格 {gt:7.3f}s（第 {k // SUB + 1} 小节第 {k % SUB + 1}/{SUB} 格）  偏差 {d * 1000:+6.0f} ms'
                 + ('  [ignore]' if ignored else ''))
bad += EV is None
head = [f'卡点质检 {SRC}',
        f'配乐 {MUSIC}：{g["bpm"]:.2f} BPM，拍长 {g["beat"]:.4f} s，第一个强拍 {t0:.3f} s；网格 = 每小节 {SUB} 格（{step:.4f} s），容差 ±{TOL * 1000:.0f} ms',
        f'登记事件 {len(EV or [])} 个 · 视频单帧硬切 {sum(n == 1 for _, n in J)} 个 · 多帧突变 {sum(n > 1 for _, n in J)} 段；问题 {bad} 个', '']
if EV is None: head.append(f'✗ 没有 {EVF}：从本期时间轴导出镜头切换、转场中心、数字砸下的时间（见 SKILL.md 第 4 步）')
os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
open(OUT, 'w').write('\n'.join(head + lines) + '\n'); print('\n'.join(head[:3] + head[4:])); print('→', OUT)
sys.exit(1 if bad else 0)
