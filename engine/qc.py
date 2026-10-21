"""数说世界 自动质检（用户 2026-10-11：字幕互相覆盖要作为 QC 项目）
在期目录运行：  python ../../engine/qc.py [--step 0.2] [--land]        （横版加 --land，等于 FILM_W=1920 FILM_H=1080）
逐帧（默认每 0.2 s）调用期目录 render.frame()，收集 brand.QC 里每段文字的框，检查：
  ① 重叠：两个可见（不透明度 ≥ 0.35）的文字 / 数字 / 来源标签 / 字幕框相交（收缩 3 px 容差）；
     期内用 brand.qc_box('graphic', 名称, l, t, r, b, a) 登记的关键图形（柱、地图主体等）也参与，文字不能压在上面
  ② 安全区（竖版）：关键信息进入右侧操作栏 x>920 & 900<y<1620、底部 y>1540、顶部 y<165（字幕本身在规定位置，不算）
  ③ 片尾：最后 1.9 s 还有可见的场景文字 / 数字 / 字幕
  ④ 出画：框超出画面
  ⑤ 字幕重复：画面上的文字 / 标签和同一时刻的字幕有 ≥ 3 个相同的汉字（数字和带数字的单位不算：大数字本身可以和字幕重复，用户 2026-10-17）
结果：build/qc[_16x9].txt（按问题合并连续时间段）+ build/qc/<序号>.jpg（红框标出问题的那一帧）。有问题时退出码 1。"""
import os, sys, importlib, math, re
args = sys.argv[1:]
STEP = float(args[args.index('--step') + 1]) if '--step' in args else 0.2
if '--land' in args: os.environ['FILM_W'], os.environ['FILM_H'] = '1920', '1080'
os.environ['SHUSHUO_QC'] = '1'
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skia
import brand as B
R = importlib.import_module(os.environ.get('RENDER', 'render'))                    # RENDER=render2：同一期的另一个画面版本
W, H, T, FPS = R.W, R.H, R.T, R.FPS
LAND = W > H
TAG = os.environ.get('QC_TAG', '_16x9' if LAND else '')                        # QC_TAG=_v2_long_en: keep reports of several cuts apart
OUT = os.path.join(os.getcwd(), 'build', 'qc' + TAG); os.makedirs(OUT, exist_ok=True)
VIS = .35


def inter(a, b, pad=3):
    l, t, r, bb = max(a[0], b[0]) + pad, max(a[1], b[1]) + pad, min(a[2], b[2]) - pad, min(a[3], b[3]) - pad
    return (r - l) * (bb - t) if r > l and bb > t else 0


def zones():
    if LAND: return []
    return [('右侧操作栏', (920, 900, W, 1620)), ('底部标题区', (0, 1540, W, H)), ('顶部标签栏', (0, 0, W, 165))]


def _cjk(s):
    """the words of a label: numbers, units-with-numbers and punctuation dropped (a bare big number may repeat the caption)"""
    return re.sub(r'[^一-鿿]', '', re.sub(r'[\d.,×⁰¹²³⁴⁵⁶⁷⁸⁹<>≈%]+\s*[种次串年百千亿万个分之一]*', '', s))


def _common(a, b):
    import difflib
    m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b)); return a[m.a:m.a + m.size]


issues = {}                                   # key → dict(first, last, n, desc, boxes)


OPEN = {}                                     # key → the issue currently being extended


def add(key, t, desc, boxes):
    key = tuple(re.sub(r'[\d,.]+', '#', k) if isinstance(k, str) else k for k in key)    # rolling counters = one issue
    it = OPEN.get(key)
    if it and t - it['last'] <= STEP * 1.5: it['last'] = t; it['n'] += 1; return
    it = dict(first=t, last=t, n=1, desc=desc, boxes=boxes, shot=None)
    issues[key + (round(t, 2),)] = it; OPEN[key] = it


t = 0.0; frames = 0
while t < T:
    B.QC.clear()
    i = int(round(t * FPS)); arr = R.frame(i); frames += 1
    vis = [b for b in B.QC if b['a'] >= VIS]
    for x in range(len(vis)):
        for y in range(x + 1, len(vis)):
            a, b = vis[x], vis[y]
            if a['kind'] == 'graphic' and b['kind'] == 'graphic': continue      # shapes may touch each other
            if inter(a['box'], b['box']) > 0:
                a, b = sorted((a, b), key=lambda z: (z['kind'], z['label']))     # stable key regardless of draw order
                add(('overlap', a['kind'], a['label'], b['kind'], b['label']), t, f"重叠：{a['kind']}「{a['label']}」× {b['kind']}「{b['label']}」", [a['box'], b['box']])
    for b in vis:
        l, tp, r, bt = b['box']
        if b['kind'] != 'graphic' and (l < -2 or tp < -2 or r > W + 2 or bt > H + 2):     # lines may run off-frame on purpose; text may not
            add(('outside', b['label']), t, f"出画：{b['kind']}「{b['label']}」", [b['box']])
        if b['kind'] not in ('caption', 'graphic'):
            for zn, z in zones():
                if inter(b['box'], z, 0) > 0: add(('zone', zn, b['label']), t, f"安全区（{zn}）：{b['kind']}「{b['label']}」", [b['box'], z])
    caps = [b for b in vis if b['kind'] == 'caption']                  # ⑤ 画面文字和同一时刻的字幕重复（用户 2026-10-17）
    for b in vis:
        if b['kind'] in ('caption', 'graphic'): continue
        s = _cjk(b['label'])
        for cp in caps:
            com = _common(s, _cjk(cp['label']))
            if len(com) >= 3: add(('dup', b['label'], cp['label']), t, f"字幕重复：{b['kind']}「{b['label']}」× 字幕「{cp['label']}」（「{com}」）", [b['box'], cp['box']])
    if t >= T - 1.9 + .25:
        for b in B.QC:
            if b['a'] > .1 and b['kind'] != 'graphic': add(('endcard', b['label']), t, f"片尾标志出现时仍可见：{b['kind']}「{b['label']}」", [b['box']])
    for it in issues.values():                 # screenshot the first frame of each new issue
        if it['shot'] is None and abs(it['first'] - t) < 1e-6:
            surf = skia.Surface.MakeRasterDirect(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType), arr) if False else None
            img = skia.Image.fromarray(arr.copy()); s2 = skia.Surface(W, H); c2 = s2.getCanvas(); c2.drawImage(img, 0, 0)
            for bx in it['boxes']: c2.drawRect(skia.Rect.MakeLTRB(*bx), skia.Paint(Color=skia.ColorRED, Style=skia.Paint.kStroke_Style, StrokeWidth=4))
            it['shot'] = f'{OUT}/{len(issues):03d}_{t:06.2f}.jpg'; s2.makeImageSnapshot().save(it['shot'], skia.kJPEG, 80)
    t = round(t + STEP, 4)

lines = [f'QC {os.path.basename(os.getcwd())}{TAG}: {frames} 帧（每 {STEP}s），{len(issues)} 个问题']
for it in sorted(issues.values(), key=lambda v: v['first']):
    lines.append(f"{it['first']:7.2f}–{it['last']:6.2f}s  {it['desc']}  → {os.path.basename(it['shot'] or '')}")
open(os.path.join(os.getcwd(), 'build', f'qc{TAG}.txt'), 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
sys.exit(1 if issues else 0)
