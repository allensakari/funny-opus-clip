"""S012 人类只是过客 · 纯展示版（16:9，60 fps，中英字幕，无配音；用户 2026-10-15）
配乐：Google Lyria 3.5（S011 第一批 lyria_a_1：大提琴 + 小提琴 + 钢琴 + 鼓，B 小调 110 BPM；用户「太棒了…非常绝望」→ 用在这一期）。
情绪线跟着音乐：希望（0–17.9 钢琴）→ 绝望（17.9 鼓进）→ 人类的努力（57.2 最强）→ 屏息（76.8）→ 宿命（92.1 再起）→ 吞没（109.6 高潮）→ 熄灭（116.1 回到慢）。
差异化（README 矩阵）：写实 3D 宇宙模拟（space.glsl）· 深蓝 → 血红 → 纯黑 · 每镜缓慢后拉 · 时间从过去推到 10¹⁴ 年 · 「距今 + X 年」计数器 ·
希望的画面 → 黑场一句话 · 8 种宇宙转场（trans.glsl）。文字用数学之美引擎的 tx / caption（霞鹜文楷 + Cormorant）。
镜头一般 ≤ 5 秒，重要情绪段可到 8 秒（用户 2026-10-15）。usage: python film.py --still t … | --shots | --part i n"""
import os, sys, math, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); EP = os.path.dirname(HERE)
def _root(p):                                                  # the skill root = the first parent that has engine/channel.py
    while not os.path.exists(os.path.join(p, 'engine', 'channel.py')) and os.path.dirname(p) != p: p = os.path.dirname(p)
    return p
R = _root(HERE); sys.path.insert(0, R + '/engine'); sys.path.insert(0, R + '/skill/styles/particle-math/templates/math-beauty-v2'); sys.path.insert(0, HERE)
import numpy as np
import skia
PURE = os.environ.get('SUB') == 'pure'                          # SUB=pure: English-only cut for YouTube (no Chinese anywhere; English watermark)
if PURE: os.environ['BRAND_LANG'] = 'en'
import engine as E
if PURE:                                                         # every string drawn goes through the English table (show/en_text.py)
    from en_text import tr as _tr
    _tx_raw = E.tx
    E.tx = lambda cv, s_, *a, **k: _tx_raw(cv, _tr(s_), *a, **k)
import brand as B
W, H = 1920, 1080
B.set_canvas(W, H)
from brand import smooth, eio, eout, lerp, clamp, count
from gl import GL

DRAFT = bool(os.environ.get('DRAFT'))                            # DRAFT=1: 30 fps, 960×540, for checking rhythm and mood
FPS = 30 if DRAFT else 60
BUILD = EP + ('/build/draft/' if DRAFT else '/build/show/')
os.makedirs(BUILD, exist_ok=True)

# ---------------------------------------------------------------- the music's grid (beatmap.py on lyria_a_1: 110.0 BPM)
MUSIC = EP + '/build/music/lyria_a_1.mp3'
_BT = np.array(json.load(open(EP + '/build/music/lyria_a_1.beats.json'))['beats'])
_I0 = int(np.argmin(abs(_BT - 17.90))) - 32; BEAT = float(np.median(np.diff(_BT)))
def h(n):
    """time of half-bar n (2 beats); n = 16 is the drums' entry at 17.90 s"""
    i = _I0 + int(round(2 * n)); return float(_BT[i]) if 0 <= i < len(_BT) else float(_BT[-1] + (i - len(_BT) + 1) * BEAT) if i >= len(_BT) else float(_BT[0] + i * BEAT)
T = 131.15
CX, CY = W / 2, H / 2
INK, SUBC, ACC, RED, DARK = (.95, .95, .96), (.66, .70, .78), (.55, .75, 1.0), (1.0, .38, .22), (0, 0, 0)

# ---------------------------------------------------------------- camera math (mirrors space.glsl)
def basis(cam, tgt):
    cam, tgt = np.array(cam, float), np.array(tgt, float); fw = tgt - cam; fw /= np.linalg.norm(fw)
    rt = np.cross(fw, [0, 1, 0]); rt /= np.linalg.norm(rt); up = np.cross(rt, fw); return cam, fw, rt, up
def proj(s, p):
    cam, fw, rt, up = basis(s['cam'], s['tgt']); d = np.array(p, float) - cam; z = d @ fw
    k = 1 / (2 * math.tan(s['fov'] / 2)); return CX + (d @ rt) / z * k * H, CY - (d @ up) / z * k * H
def prad(s, p, r):
    cam, fw, rt, up = basis(s['cam'], s['tgt']); z = (np.array(p, float) - cam) @ fw
    return r / z / (2 * math.tan(s['fov'] / 2)) * H


def SCN(**k):
    d = dict(cam=(0, 0, 3.2), tgt=(0, 0, 0), fov=.6, earth=(0, 0, 0, 1.0), sun=(0, 0, 0, 0), moon=(0, 0, 0, 0), sundir=(.6, .3, 1), yaw=.26, lights=1.0, clouds=.5,
             dry=0., scorch=0., sunk=0., stardeath=0., stars=1., milky=1., expose=1., glow=0., sunglow=1.)
    d.update(k); return d
NONE = dict(earth=(0, 0, 0, 0))
def dolly(a, b, u): return tuple(lerp(np.array(a, float), np.array(b, float), eio(u)))      # the slow pull-back every shot uses


# ---------------------------------------------------------------- text and drawing helpers
def T_(cv, s, x, y, size, col=None, a=1.0, align='c', lf=None):
    if a <= .003: return
    E.tx(cv, s, x, y + 2, size, DARK, a * .7, align, lf=lf, glow=1.0); E.tx(cv, s, x, y, size, col or INK, a, align, lf=lf, glow=0)
def SRC(cv, s, x, y, a=1.0, align='c'): T_(cv, s, x, y, 24, SUBC, a * .9, align, lf=E.CGO_I)
def paint(c, a=1.0, stroke=0, blur=0):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(c[0], c[1], c[2], clamp(a)))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
    if blur > .3: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p
def glowdot(cv, x, y, r, c, a=1.0):
    if a <= .003: return
    cv.drawCircle(x, y, r * 4, paint(c, .18 * a, blur=r * 3)); cv.drawCircle(x, y, r, paint(c, a)); cv.drawCircle(x, y, r * .45, paint((1, 1, 1), a))


def counter(cv, label, a=1.0, x=W - 90, y=120):
    """the fate counter in the upper right: 「距今 + 13 亿年」 in Cormorant figures"""
    if a <= .003: return
    T_(cv, '距今', x, y - 58, 26, SUBC, a, 'r'); T_(cv, label, x, y, 60, RED, a, 'r', lf=E.CG_SB)


def voyager(cv, x, y, sc=1.0, a=1.0, rim=(1, .9, .75)):
    """Voyager in silhouette with a rim light: dish, bus, magnetometer boom, RTG boom"""
    if a <= .003: return
    cv.save(); cv.translate(x, y); cv.scale(sc, sc); cv.rotate(-12)
    body = paint((.10, .10, .11), a); edge = paint(rim, .8 * a, stroke=1.6)
    dish = skia.Rect.MakeLTRB(-60, -60, 60, 60); cv.drawOval(skia.Rect.MakeLTRB(-62, -20, 62, 14), body); cv.drawArc(skia.Rect.MakeLTRB(-62, -20, 62, 14), 180, 180, False, edge)
    cv.drawRect(skia.Rect.MakeLTRB(-22, 10, 22, 40), body); cv.drawLine(-22, 10, -22, 40, edge)
    cv.drawLine(0, 40, 0, 52, paint((.2, .2, .2), a, stroke=3))
    cv.drawLine(15, 30, 230, 70, paint((.25, .25, .26), a, stroke=2)); cv.drawLine(-15, 30, -110, 80, paint((.25, .25, .26), a, stroke=4))
    cv.drawRect(skia.Rect.MakeLTRB(-122, 72, -96, 90), body); cv.drawLine(-122, 72, -96, 72, edge)
    cv.restore()


# ---------------------------------------------------------------- shots
def S(n0, n1, scene, draw, mode=0, focus=(CX, CY)): return dict(t0=h(n0), t1=h(n1), scene=scene, draw=draw, mode=mode, focus=focus)
def d_none(cv, t, u, s): pass

# ===== 希望 HOPE (0–17.9 s, solo piano)
NIGHT = dict(sundir=(-1, .15, -.7))
def sc_hook(t, u): return SCN(**NIGHT, cam=dolly((.55, .45, 2.05), (.75, .55, 2.6), u), tgt=(-.55, .35, 0), lights=1.0)
def d_hook(cv, t, u, s):
    T_(cv, '把宇宙 138 亿年压成一年，', 140, 200, 62, INK, smooth(.1, .6, t), 'l')
    T_(cv, '人类只活在最后', 140, 290, 62, INK, smooth(.6, 1.1, t), 'l'); T_(cv, '12 分钟', 590 if not PURE else 166 + sum(r[2] for r in E.runs(_tr('人类只活在最后'), 62)), 300, 110, ACC, smooth(.9, 1.5, t), 'l', lf=E.CG_SB)
    T_(cv, 'Squeeze 13.8 billion years into one year: humans exist only in its last 12 minutes.', 140, 360, 28, SUBC, smooth(1.3, 1.9, t), 'l', lf=E.CGO_I)
    SRC(cv, '宇宙年龄 Planck 2018 · 智人 31.5 万年 Hublin et al. 2017 · 计算', 140, 400, smooth(1.6, 2.2, t), 'l')


def sc_space(t, u, **k): return SCN(**{**NONE, **k})
def d_calendar(cv, t, u, s):
    """the cosmic year as a ring of 12 months; the last sliver opens into a clock face of Dec 31"""
    cx, cy, R = 700, 560, 330; k = eio(smooth(.0, .45, u))
    for m in range(12):
        a0 = -90 + m * 30 + 1.2; sweep = 27.6 * clamp(k * 12 - m)
        if sweep > 0: cv.drawArc(skia.Rect.MakeXYWH(cx - R, cy - R, 2 * R, 2 * R), a0, sweep, False, paint((.55, .62, .78), .55, stroke=26))
        tx_a = math.radians(a0 + 13.8); T_(cv, f'{m + 1}月', cx + math.cos(tx_a) * (R + 50), cy + math.sin(tx_a) * (R + 50) + 10, 26, SUBC, clamp(k * 12 - m))
    kk = smooth(.45, .75, u)
    cv.drawArc(skia.Rect.MakeXYWH(cx - R, cy - R, 2 * R, 2 * R), -90 - 1.8, 1.6, False, paint(ACC, kk, stroke=40))
    glowdot(cv, cx + math.cos(math.radians(-91)) * R, cy + math.sin(math.radians(-91)) * R, 8, ACC, kk)
    # the zoomed clock of the last hour on the right
    zx, zy, ZR = 1420, 520, 230; kz = smooth(.55, .8, u)
    if kz > .003:
        cv.drawLine(cx + 10, cy - R, zx - ZR * .8, zy - ZR * .6, paint(SUBC, .4 * kz, stroke=1.2))
        cv.drawCircle(zx, zy, ZR, paint((.06, .07, .1), .9 * kz)); cv.drawCircle(zx, zy, ZR, paint(SUBC, .7 * kz, stroke=2))
        for j in range(60): a = math.radians(-90 + j * 6); L = 22 if j % 5 == 0 else 10; cv.drawLine(zx + math.cos(a) * (ZR - L), zy + math.sin(a) * (ZR - L), zx + math.cos(a) * ZR, zy + math.sin(a) * ZR, paint(SUBC, .8 * kz, stroke=2 if j % 5 == 0 else 1))
        cv.drawArc(skia.Rect.MakeXYWH(zx - ZR + 30, zy - ZR + 30, 2 * ZR - 60, 2 * ZR - 60), -90 - 72, 72 * smooth(.65, .95, u), True, paint(ACC, .45 * kz))
        T_(cv, '12 月 31 日 23:48', zx, zy + ZR + 60, 34, INK, kz, lf=E.CG_SB); T_(cv, '人类出现', zx, zy + 16, 40, ACC, smooth(.75, .95, u))
    T_(cv, '宇宙日历', cx, cy + 12, 50, INK, smooth(.05, .3, u)); T_(cv, '138 亿年 = 1 年', cx, cy + 62, 30, SUBC, smooth(.1, .35, u), lf=E.CG_SB)


def sc_lights(t, u): return SCN(**NIGHT, cam=dolly((.25, .55, 1.65), (.32, .6, 1.95), u), tgt=(-.2, .5, 0), lights=lerp(.0, 1.0, eio(smooth(.0, .9, u))), yaw=.26)
def d_lights(cv, t, u, s):
    T_(cv, f'{count(u, .0, .9, 0, 30):.0f} 万年', W - 140, 200, 88, ACC, 1, 'r', lf=E.CG_SB); T_(cv, '智人的灯，一点点亮起来', W - 140, 255, 30, SUBC, 1, 'r')


SUNRISE_SUN = (-14., .9, -30., .9)
def sc_sunrise(t, u):
    c = dolly((0, 1.04, 1.9), (0, 1.12, 2.05), u)
    return SCN(sun=SUNRISE_SUN, cam=c, tgt=(-.4, 1.22, -1.0), fov=.55, lights=.6, clouds=.6, sunglow=lerp(.4, 1.2, eio(u)), expose=lerp(.85, 1.05, u))


def sc_pullout(t, u):
    z = 3.0 * (60 / 3.0) ** eio(smooth(.0, 1., u))                            # exponential pull-back: Earth → Earth-Moon system
    return SCN(cam=(z * .18, z * .12, z), tgt=(0, 0, 0), sundir=(.8, .25, .5), moon=(-58, 8, -10, .273), fov=.6, lights=.4)
def d_pullout(cv, t, u, s):
    T_(cv, '1,170 亿人', 160, 760, 96, ACC, smooth(0.12, 0.30, u), 'l', lf=E.CG_SB); T_(cv, '都在这里活过', 160, 830, 40, INK, smooth(0.14, 0.31, u), 'l')
    SRC(cv, '有史以来出生人数 · Kaneda & Haub, PRB 2022', 160, 875, smooth(0.16, 0.34, u), 'l')


# ===== 绝望 DESPAIR (17.9–57.2 s, drums enter)
def _dots():
    r = np.random.default_rng(7); n = 4000; cols = 100
    return [(168 + (j % cols) * 16.0, 280 + (j // cols) * 14.5, r.uniform()) for j in range(n)]
DOTS = _dots()
def d_species(cv, t, u, s):
    k = smooth(.25, .85, u)
    for x, y, h_ in DOTS:
        alive = h_ > .99 or h_ > k * .99
        if alive: cv.drawCircle(x, y, 4.2 if h_ > .99 else 3.6, paint((.55, 1, .7) if h_ > .99 else (.72, .8, .95), 1 if h_ > .99 else .8))
        else: cv.drawCircle(x, y, 2.4, paint((.3, .28, .3), .45))
    T_(cv, '约 40 亿个物种', CX, 150, 46, INK, smooth(.0, .2, u)); T_(cv, f'{count(u, .25, .85, 0, 99):.0f}% 已经灭绝', CX, 215, 64, RED, smooth(.25, .4, u), lf=E.CG_SB)
    SRC(cv, '每个点约 100 万个物种 · Barnosky et al., Nature 2011', CX, 990 - 120, smooth(.3, .5, u))


EXT = [(445, '奥陶纪末'), (372, '晚泥盆世'), (252, '二叠纪末'), (201, '三叠纪末'), (66, '白垩纪末')]
def d_extinct(cv, t, u, s):
    x0, x1, y = 160, 1760, 620; X = lambda my: lerp(x0, x1, 1 - my / 540)
    k = eio(smooth(.0, .9, u)); xe = lerp(x0, x1, k)
    p = skia.Path(); p.moveTo(x0, y)
    r = np.random.default_rng(3); level = 0.0; pts = []
    for j in range(400):
        my = 540 * (1 - j / 399); xx = X(my); level += r.normal(0, .6) + .35
        for e, _ in EXT:
            if abs(my - e) < 540 / 399 * .6: level *= .22
        pts.append((xx, y - 40 - min(level, 260)))
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]:
        if q[0] > xe: break
        p.lineTo(*q)
    cv.drawPath(p, paint((.6, .7, .85), .9, stroke=3))
    cv.drawLine(x0, y, x1, y, paint(SUBC, .6, stroke=1.5))
    for j, (e, nm) in enumerate(EXT):
        xx = X(e); kk = clamp((xe - xx) / 40)
        if kk <= 0: continue
        cv.drawLine(xx, y + 10, xx, y - 320, paint(RED, .5 * kk, stroke=2)); T_(cv, f'{e / 100:g} 亿年前' if e >= 100 else '6,600 万年前', xx, y + 50, 24, INK, kk, lf=E.CG_SB); T_(cv, nm, xx, y + 84, 22, SUBC, kk)
    T_(cv, '五次大灭绝', CX, 150, 56, INK, smooth(.0, .2, u)); T_(cv, '每一次，带走四分之三以上的物种', CX, 210, 32, SUBC, smooth(.1, .3, u))
    SRC(cv, '生物多样性曲线为示意 · 年代 ICS 2023 · 定义 Barnosky et al. 2011', CX, 990 - 120, smooth(.2, .4, u))


IMPACT = np.array([.62, .55, .55]); IMPACT = IMPACT / np.linalg.norm(IMPACT)
def sc_impact(t, u): return SCN(cam=dolly((.4, .35, 2.7), (.5, .4, 3.0), u), tgt=(.15, .1, 0), sundir=(.8, .4, .7), lights=0, yaw=1.7, clouds=.45)
def d_impact(cv, t, u, s):
    hit = .55; q = smooth(.0, hit, u); p0 = IMPACT * 4.5 + np.array([1.6, 1.4, .3]); pe = IMPACT * 1.0
    if u < hit:
        p = p0 + (pe - p0) * q ** 1.6; x, y = proj(s, p); x0, y0 = proj(s, p0 + (pe - p0) * max(0, q - .12) ** 1.6)
        g = skia.Paint(AntiAlias=True, StrokeWidth=10, Style=skia.Paint.kStroke_Style); g.setShader(skia.GradientShader.MakeLinear([(x0, y0), (x, y)], [skia.Color4f(1, .5, .2, 0).toColor(), skia.Color4f(1, .8, .5, .9).toColor()]))
        g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)); cv.drawLine(x0, y0, x, y, g); glowdot(cv, x, y, 5, (1, .8, .5), 1)
    else:
        x, y = proj(s, pe); k = smooth(hit, 1, u)
        for j in range(3):
            kr = clamp(k * 1.3 - j * .15); rr = 30 + 330 * eout(kr)
            cv.drawOval(skia.Rect.MakeXYWH(x - rr, y - rr * .55, 2 * rr, 1.1 * rr), paint((1, .55, .25), (1 - kr) * .55, stroke=8 - j * 2, blur=6))
        cv.drawCircle(x, y, 40 + 60 * k, paint((1, .6, .3), .5 * (1 - k * .6), blur=30))
    T_(cv, '6,600 万年前', 160, 200, 72, RED, smooth(.05, .25, u), 'l', lf=E.CG_SB); T_(cv, '恐龙统治了 1.6 亿年', 160, 260, 32, SUBC, smooth(0.24, 0.38, u), 'l')
    SRC(cv, '希克苏鲁伯撞击 · Schulte et al., Science 2010', 160, 300, smooth(0.24, 0.38, u), 'l')


DC_SWEEP, DC_REVEAL = .8, (.8, .95)                              # (3 分钟版改成 .4 / (.4, .5)：揭晓后停 2 秒再切)
def d_dayclock(cv, t, u, s):
    cx, cy, R = 760, 560, 320; k = eio(smooth(.0, DC_SWEEP, u)); ang = -90 + 360 * k
    cv.drawCircle(cx, cy, R, paint((.05, .06, .08), .9)); cv.drawCircle(cx, cy, R, paint(SUBC, .7, stroke=2))
    for j in range(24): a = math.radians(-90 + j * 15); cv.drawLine(cx + math.cos(a) * (R - 24), cy + math.sin(a) * (R - 24), cx + math.cos(a) * R, cy + math.sin(a) * R, paint(SUBC, .8, stroke=2))
    for j, lab in ((0, '0 点'), (6, '6'), (12, '12'), (18, '18')): a = math.radians(-90 + j * 15); T_(cv, lab, cx + math.cos(a) * (R - 60), cy + math.sin(a) * (R - 60) + 10, 28, SUBC, 1, lf=E.CG_SB)
    cv.drawArc(skia.Rect.MakeXYWH(cx - R + 40, cy - R + 40, 2 * R - 80, 2 * R - 80), -90, 360 * k, True, paint((.3, .36, .45), .5))
    a = math.radians(ang); cv.drawLine(cx, cy, cx + math.cos(a) * (R - 30), cy + math.sin(a) * (R - 30), paint(INK, .9, stroke=4))
    kk = smooth(*DC_REVEAL, u)
    cv.drawArc(skia.Rect.MakeXYWH(cx - R - 18, cy - R - 18, 2 * R + 36, 2 * R + 36), -90 - .25, .25, False, paint(ACC, kk, stroke=26)); glowdot(cv, cx, cy - R - 18, 7, ACC, kk)
    T_(cv, '地球 45.4 亿年 = 1 天', 1460, 430, 40, INK, smooth(.0, .2, u)); T_(cv, '最后 6 秒', 1460, 540, 110, ACC, kk, lf=E.CG_SB); T_(cv, '才轮到智人', 1460, 600, 36, INK, kk)
    SRC(cv, '地球年龄 Dalrymple 2001 · 智人 Hublin et al. 2017 · 计算', 1460, 650, kk)


def d_people(cv, t, u, s):
    cols = 13; gx, gy = 96, 96; x0, y0 = CX - (cols - 1) * gx / 2, 260; r = np.random.default_rng(11)
    order = r.permutation(117); alive = set(order[:8]); k = smooth(.2, .85, u)
    for j in range(117):
        x, y = x0 + (j % cols) * gx, y0 + (j // cols) * gy
        rank = np.where(order == j)[0][0]; off = rank >= 8 and (rank - 8) / 109 < k
        if off: cv.drawCircle(x, y, 5, paint((.3, .27, .25), .5))
        else: glowdot(cv, x, y, 7, (1, .78, .45), 1)
    T_(cv, '1,170 亿人来过', CX, 140, 52, INK, smooth(.0, .2, u)); T_(cv, f'{count(u, .2, .85, 0, 93):.0f}% 已经离开', CX, 205, 60, RED, smooth(.2, .35, u), lf=E.CG_SB)
    SRC(cv, '每盏灯 10 亿人 · 2022 年在世 79.6 亿 · Kaneda & Haub, PRB 2022', CX, H - 220, smooth(.3, .5, u))


def sc_dot(t, u): return SCN(**NONE, stars=.6, milky=.5)
def d_dot(cv, t, u, s):
    """the pale blue dot: a sunbeam crossing the dark, the Earth less than a pixel inside it"""
    for j, (x, w_, a) in enumerate(((560, 120, .10), (900, 70, .14), (1180, 160, .07), (1500, 90, .1))):
        g = skia.Paint(AntiAlias=True); g.setShader(skia.GradientShader.MakeLinear([(x - w_, 0), (x + w_, 0)], [skia.Color4f(.9, .7, .55, 0).toColor(), skia.Color4f(.95, .78, .62, a).toColor(), skia.Color4f(.9, .7, .55, 0).toColor()]))
        cv.save(); cv.rotate(-14); cv.drawRect(skia.Rect.MakeLTRB(x - w_ + 200, -400, x + w_ + 200, 1600), g); cv.restore()
    k = smooth(.15, .45, u); px_, py_ = 1170, 640
    cv.drawCircle(px_, py_, 1.3, paint((.65, .8, 1), k)); cv.drawCircle(px_, py_, 4, paint((.6, .75, 1), .25 * k, blur=3))
    kk = smooth(.4, .65, u); cv.drawCircle(px_, py_, 34, paint(INK, .6 * kk, stroke=1.4)); cv.drawLine(px_ + 26, py_ - 24, px_ + 130, py_ - 120, paint(INK, .5 * kk, stroke=1.2))
    T_(cv, '地球', px_ + 140, py_ - 126, 32, INK, kk, 'l')
    SRC(cv, '仿 1990 年旅行者 1 号「暗淡蓝点」视角 · 示意', W - 60, H - 220, kk, 'r')


def sc_sun(t, u): return SCN(**NONE, sun=(0, 0, 0, 1.0), cam=dolly((.15, .05, 2.6), (.2, .08, 3.0), u), tgt=(.55, 0, 0), sunglow=lerp(1.0, 1.4, u), expose=lerp(1.0, 1.15, u))
def d_sun(cv, t, u, s):
    T_(cv, '每 10 亿年', 1500, 420, 40, INK, smooth(.1, .3, u)); T_(cv, '亮约 10%', 1500, 520, 96, RED, smooth(0.08, 0.26, u), lf=E.CG_SB)
    SRC(cv, '太阳光度演化 · Gough, Solar Physics 1981', 1500, 570, smooth(0.12, 0.26, u))


def sc_off(t, u):                                                             # night Earth: lights flicker out, region by region
    return SCN(**NIGHT, cam=dolly((-.35, .45, 2.2), (-.45, .5, 2.55), u), tgt=(.4, .3, 0), lights=lerp(1, .0, eio(smooth(.15, .95, u))), yaw=.9)


def sc_pad(t, u): return SCN(**NIGHT, cam=dolly((.0, 1.06, 1.35), (.0, 1.1, 1.5), u), tgt=(0, 1.18, -.6), fov=.5, lights=1.0, yaw=2.75, clouds=.4)
PAD = None
def d_pad(cv, t, u, s):
    x, y = CX + 140, H * .5 + 210; k = .25 + .1 * math.sin(t * 2)
    for j in range(5): cv.drawCircle(x, y, 30 + j * 26 * (.5 + k), paint((1, .75, .45), (.22 - j * .04) * (.4 + .6 * k), blur=12 + j * 6))   # ignition glow at the cape
    glowdot(cv, x, y, 4 + 3 * k, (1, .85, .6), .9)
    T_(cv, '于是，我们开始往外走', CX, 170, 52, INK, smooth(.1, .35, u))
def d_ignite(cv, t, u, s):
    x, y = CX + 140, H * .5 + 210; k = eio(smooth(.0, 1, u))
    for j in range(6): cv.drawCircle(x, y, 40 + j * 40 * (.4 + k), paint((1, .75, .45), (.25 - j * .035) * (.3 + .7 * k), blur=14 + j * 8))
    glowdot(cv, x, y, 5 + 6 * k, (1, .88, .65), 1)
    T_(cv, f'T − {max(0, 10 - int(u * 11))}', W - 160, 200, 72, INK, smooth(.0, .15, u), 'r', lf=E.CG_SB)


def sc_launch(t, u): return SCN(**NIGHT, cam=(0, 1.1, 1.5), tgt=(0, 1.3, -.6), fov=.5, lights=1.0, yaw=2.75, clouds=.4)
def d_launch(cv, t, u, s):
    x0, y0 = CX + 140, H * .5 + 210; k = eio(smooth(.0, .95, u)); pts = []
    for j in range(60):
        q = j / 59 * k; pts.append((x0 + 420 * q ** 1.6, y0 - 860 * q))
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    cv.drawPath(p, paint((1, .7, .4), .35, stroke=18, blur=10)); cv.drawPath(p, paint((1, .9, .75), .9, stroke=3))
    glowdot(cv, *pts[-1], 7, (1, .9, .7), 1)
    T_(cv, '1969', 160, 200, 110, ACC, smooth(.05, .25, u), 'l', lf=E.CG_SB); T_(cv, '阿波罗 11 号', 160, 260, 34, SUBC, smooth(.1, .3, u), 'l')


def sc_earthrise(t, u): return SCN(earth=(0, 9, -220, 3.67), moon=(0, -1.0, 0, 1.0), sun=(0, 0, 0, 0), sundir=(1, .35, .25), cam=dolly((0, .012, .5), (0, .014, .56), u), tgt=(0, 1.9 - .3 * u, -220), fov=.12, lights=.3)
def d_earthrise(cv, t, u, s):
    T_(cv, '12 个人', 1560, 760, 100, ACC, smooth(0.08, 0.26, u), 'c', lf=E.CG_SB); T_(cv, '在月球上走过', 1560, 825, 38, INK, smooth(0.10, 0.28, u)); SRC(cv, 'Apollo 11–17 · NASA', 1560, 865, smooth(0.12, 0.30, u))


def sc_artemis(t, u): return SCN(moon=(-.9, -.15, 0, 1.0), earth=(160, 20, -330, 3.67), sundir=(.9, .4, .6), cam=dolly((1.9, .3, 2.4), (2.1, .35, 2.75), u), tgt=(.6, .1, 0), fov=.6, lights=.3)
def d_artemis(cv, t, u, s):
    x, y = proj(s, (1.25, .55, .35)); glowdot(cv, x, y, 4, (1, .95, .85), smooth(.0, .2, u))
    cv.drawLine(x + 10, y - 10, x + 120, y - 90, paint(INK, .5 * smooth(0.08, 0.22, u), stroke=1.2)); T_(cv, '阿尔忒弥斯 2 号', x + 128, y - 96, 28, INK, smooth(0.08, 0.22, u), 'l')
    T_(cv, '406,771 公里', 160, 200, 92, ACC, smooth(0.10, 0.28, u), 'l', lf=E.CG_SB); T_(cv, '2026 年 4 月，人类到过最远的地方', 160, 260, 32, INK, smooth(0.12, 0.30, u), 'l')
    T_(cv, '光只要 1.36 秒', 160, 330, 40, INK, smooth(0.14, 0.28, u), 'l', lf=E.CG_SB)
    SRC(cv, 'NASA Artemis II · 2026-04-06 · 光速换算', 160, 370, smooth(0.14, 0.31, u), 'l')


def d_lightpulse(cv, t, u, s):
    x0, x1, y = 260, 1660, 560; k = clamp((u - .15) / .55)
    cv.drawLine(x0, y, x1, y, paint(SUBC, .5, stroke=2))
    glowdot(cv, x0, y, 14, (.45, .65, 1), 1); T_(cv, '地球', x0, y + 70, 32, INK, 1); glowdot(cv, x1, y, 4, (1, .95, .85), 1); T_(cv, '人类到过最远处', x1, y + 70, 30, INK, 1)
    xp = lerp(x0, x1, k); cv.drawLine(max(x0, xp - 240), y, xp, y, paint((1, .95, .8), .7, stroke=6, blur=4)); glowdot(cv, xp, y, 6, (1, .97, .9), 1 if 0 < k < 1 else 0)
    T_(cv, f'{k * 1.36:.2f} 秒', CX, 420, 96, ACC, 1, lf=E.CG_SB); T_(cv, '光走完这段路', CX, 470, 34, SUBC, 1)
    SRC(cv, '406,771 km ÷ 光速 · 计算', CX, H - 220, smooth(.6, .8, u))


def sc_vgr_launch(t, u): return SCN(**NONE, sun=(-60, -6, -150, 1.2), cam=dolly((0, 0, 3.0), (0, 0, 3.3), u), tgt=(0, 0, 0), sunglow=1.4)
def d_vgr_launch(cv, t, u, s):
    voyager(cv, lerp(1150, 1040, eio(u)), lerp(480, 520, eio(u)), 1.8, smooth(.0, .3, u))
    T_(cv, '1977', 160, 200, 110, ACC, smooth(.05, .25, u), 'l', lf=E.CG_SB); T_(cv, '旅行者 1 号出发', 160, 260, 34, INK, smooth(.1, .3, u), 'l'); SRC(cv, 'NASA / JPL', 160, 300, smooth(0.06, 0.20, u), 'l')


def sc_helio(t, u): return SCN(**NONE, sun=(-12, -1.5, -40, .25), cam=(0, 0, 3.0), tgt=(0, 0, 0), sunglow=1.0)
def d_helio(cv, t, u, s):
    sx, sy = proj(s, (-12, -1.5, -40)); k = smooth(.0, .6, u)
    for j in range(5):
        rr = 520 + j * 60; cv.drawArc(skia.Rect.MakeXYWH(sx - rr, sy - rr * .8, 2 * rr, 1.6 * rr), -40, 80, False, paint((.45, .65, 1), (.25 - j * .04) * k, stroke=10 + j * 6, blur=8))
    voyager(cv, lerp(1300, 1560, eio(u)), lerp(470, 420, eio(u)), 1.0, 1)
    T_(cv, '2012 年', 160, 200, 72, ACC, smooth(.1, .3, u), 'l', lf=E.CG_SB); T_(cv, '它飞出了太阳风吹到的边界', 160, 255, 32, INK, smooth(0.06, 0.20, u), 'l'); SRC(cv, 'NASA / JPL 2013 · Stone et al., Science 2013', 160, 295, smooth(0.08, 0.22, u), 'l')


# ===== 屏息 BREATH (76.8–92.1 s)
def sc_alone(t, u): return SCN(**NONE, sun=(-8, -2, -60, .05), cam=dolly((0, 0, 3.0), (0, 0, 3.2), u), tgt=(0, 0, 0), sunglow=.6, milky=1.2)
def d_alone(cv, t, u, s):
    voyager(cv, 980, 560, .55, 1, rim=(.9, .85, .8))
    km = 259.02 * eio(smooth(.0, .75, u))
    T_(cv, f'{km:,.1f} 亿公里', CX, 300, 90, ACC, 1, lf=E.CG_SB)
    T_(cv, '= 1 光日', CX, 370, 52, INK, smooth(.7, .85, u), lf=E.CG_SB)
    SRC(cv, 'NASA：2026 年 11 月 18 日，旅行者 1 号距地球 1 光日', CX, H - 220, smooth(.75, .9, u))


def d_scalebar(cv, t, u, s):
    x0, x1, y = 160, 1760, 600; k = eio(smooth(.0, .7, u))
    cv.drawLine(x0, y, lerp(x0, x1, k), y, paint(SUBC, .7, stroke=2))
    glowdot(cv, x0, y, 6, (.45, .65, 1), 1); T_(cv, '地球', x0, y + 60, 28, INK, 1)
    vx = x0 + (x1 - x0) / 1551; glowdot(cv, vx + 1, y, 2.5, (1, .9, .7), 1)
    cv.drawLine(vx, y - 10, vx + 40, y - 110, paint(INK, .5, stroke=1.2)); T_(cv, '旅行者 1 号（1 光日）', vx + 46, y - 118, 26, INK, smooth(.1, .3, u), 'l')
    glowdot(cv, x1, y, 8, (1, .55, .35), clamp(k * 1.2 - .2)); T_(cv, '比邻星', x1, y + 60, 28, INK, clamp(k * 1.2 - .2)); T_(cv, '1,551 光日', x1, y + 100, 30, ACC, clamp(k * 1.2 - .2), lf=E.CG_SB)
    T_(cv, '最近的恒星', CX, 280, 52, INK, smooth(.4, .6, u)); SRC(cv, '比邻星 1.3020 pc · Gaia DR3 · 计算', CX, 330, smooth(.4, .6, u))


def sc_drift(t, u): return SCN(**NONE, cam=dolly((0, 0, 3.0), (0, 0, 3.15), u), tgt=(0, 0, 0), milky=1.3, sundir=(1, 0, 0))
def d_drift(cv, t, u, s):
    voyager(cv, lerp(900, 930, u), 600, .3, 1, rim=(.7, .7, .75))
    T_(cv, '照这个速度', CX, 300, 44, INK, smooth(.05, .25, u)); T_(cv, '还要 7.7 万年', CX, 390, 96, ACC, smooth(0.08, 0.26, u), lf=E.CG_SB)
    SRC(cv, '每年约 5.2 亿公里（NASA）· 计算', CX, 440, smooth(0.12, 0.26, u))


# ===== 宿命 FATE (92.1–109.6 s): the counter runs
def sc_bright(t, u): return SCN(**NONE, sun=(0, 0, 0, 1.0), cam=dolly((-.2, .05, 2.4), (-.25, .06, 2.7), u), tgt=(-.55, -.42, 0), expose=lerp(.62, .9, eio(u)), sunglow=lerp(.8, 1.4, eio(u)))
def d_bright(cv, t, u, s): counter(cv, f'+{count(u, .0, 1, 1, 10):.0f} 亿年')
def sc_dry(t, u): return SCN(cam=dolly((.3, .2, 2.5), (.35, .25, 2.9), u), tgt=(.25, .1, 0), sundir=(.7, .3, .8), dry=eio(smooth(.05, .95, u)), clouds=lerp(.6, .05, eio(u)), lights=0, yaw=.26)
def d_dry(cv, t, u, s):
    counter(cv, f'+{count(u, .0, 1, 10, 13):.0f} 亿年'); T_(cv, '海洋开始散失', 160, 800, 60, INK, smooth(0.16, 0.30, u), 'l')
    SRC(cv, 'Gough 1981 光度 + Wolf & Toon 2015 湿温室阈值 · 计算', 160, 845, smooth(0.16, 0.30, u), 'l')
def sc_scorch(t, u): return SCN(cam=dolly((-.3, .25, 2.4), (-.35, .3, 2.75), u), tgt=(-.2, .1, 0), sundir=(.7, .3, .8), dry=1.0, scorch=lerp(.15, .75, eio(u)), clouds=0, lights=0, yaw=.9)
def d_scorch(cv, t, u, s): counter(cv, f'+{count(u, .0, 1, 15, 50):.0f} 亿年')
def sc_swell(t, u):
    r = lerp(1.0, 4.2, eio(smooth(.0, 1., u)) ** 1.3)
    return SCN(**NONE, sun=(0, 0, -r * .2, r), sunk=eio(smooth(.05, .9, u)), cam=(0, 0, 9.0), tgt=(0, 0, 0), fov=.75, sunglow=1.0)
def d_swell(cv, t, u, s): counter(cv, f'+{count(u, .0, 1, 50, 76):.0f} 亿年')
def sc_giant(t, u): return SCN(earth=(0, 0, 2.4, .16), sun=(0, 0, -7, 7.6), sunk=1.0, sundir=(0, 0, -1), dry=1, scorch=.45, lights=0, clouds=0, cam=dolly((.18, .06, 3.2), (.2, .07, 3.5), u), tgt=(0, 0, 2.0), fov=.6, sunglow=1.0)
def d_giant(cv, t, u, s):
    x, y = proj(s, (0, 0, 2.4)); r = prad(s, (0, 0, 2.4), .16); ka = smooth(.1, .3, u)
    cv.drawLine(x + r * .8, y - r * .8, x + r + 120, y - r - 110, paint(INK, .6 * ka, stroke=1.4)); T_(cv, '地球', x + r + 128, y - r - 116, 34, INK, ka, 'l')
    counter(cv, '+76 亿年'); T_(cv, '太阳变成红巨星', 160, 820, 60, INK, smooth(0.08, 0.22, u), 'l'); SRC(cv, 'Schröder & Smith, MNRAS 2008', 160, 865, smooth(0.08, 0.22, u), 'l')


# ===== 吞没 ENGULF (109.6–116.1 s)
def sc_engulf(t, u):
    k = eio(smooth(.0, 1., u)); z = lerp(1.4, .55, k)
    return SCN(earth=(0, 0, z, .12 * (1 - .9 * smooth(.55, 1., u)) + 1e-4), sun=(0, 0, -7, 7.6), sunk=1.0, dry=1, scorch=1.0, lights=0, clouds=0, cam=(.12, .04, 2.1), tgt=(0, 0, 0), fov=.6, sunglow=1.0, expose=lerp(1, 1.25, k))
def d_engulf(cv, t, u, s):
    x, y = proj(s, (0, 0, lerp(1.4, .55, eio(u)))); k = smooth(.5, 1, u)
    cv.drawCircle(x, y, 60 + 240 * k, paint((1, .55, .2), .35 * k * (1 - smooth(.85, 1, u)), blur=40))
    counter(cv, '+76 亿年')
def sc_dwarf(t, u):
    r = lerp(7.6, .02, eio(smooth(.0, .8, u)))
    return SCN(**NONE, sun=(0, 0, -7, r), sunk=lerp(1.0, .0, eio(smooth(.3, 1, u))), cam=dolly((0, 0, 9.0), (0, 0, 12.0), u), tgt=(0, 0, -7), fov=.75, sunglow=lerp(1, 2.5, u))


# ===== 熄灭 THE LIGHTS GO OUT (116.1–131 s)
def sc_stars(t, u): return SCN(**NONE, cam=dolly((0, 0, 3.0), (0, 0, 3.4), u), tgt=(0, 0, 0), stardeath=lerp(.0, .85, eio(u)), milky=1.2)
def d_stars(cv, t, u, s): counter(cv, '10¹³ 年', a=smooth(.0, .2, u)); T_(cv, '最后的恒星也会熄灭', 160, 820, 56, INK, smooth(0.08, 0.22, u), 'l'); SRC(cv, 'Laughlin, Bodenheimer & Adams, ApJ 1997', 160, 865, smooth(0.08, 0.22, u), 'l')
def sc_last(t, u): return SCN(**NONE, cam=dolly((0, 0, 3.0), (0, 0, 3.3), u), tgt=(0, 0, 0), stardeath=lerp(.85, .9995, eio(smooth(.0, .9, u))), milky=1.2)
def d_last(cv, t, u, s): counter(cv, '10¹⁴ 年'); T_(cv, '再也没有新的星星', 160, 820, 56, INK, smooth(.1, .3, u), 'l'); SRC(cv, 'Adams & Laughlin, Rev. Mod. Phys. 1997', 160, 865, smooth(.1, .3, u), 'l')
def sc_black(t, u): return SCN(**NONE, stars=0., milky=0.)
def d_black(cv, t, u, s):
    T_(cv, '宇宙不会记得我们来过', CX, CY - 10, 64, INK, smooth(.12, .3, u))                       # holds to the last frame (no end logo)
    T_(cv, 'The universe will not remember we were here.', CX, CY + 50, 30, SUBC, smooth(.2, .38, u), lf=E.CGO_I)


SH = [
    # 希望 0–17.9 s（v2 节奏：用户 2026-10-15「有些镜头切得过快，字还没看清楚」→ 段落锚点不动，段内少切几刀、每个镜头多停一会儿）
    S(0, 4, sc_hook, d_hook, 0),
    S(4, 8, sc_space, d_calendar, 7, (300, 200)),
    S(8, 11, sc_lights, d_lights, 3, (1100, 500)),
    S(11, 13, sc_sunrise, d_none, 7, (400, 300)),
    S(13, 16, sc_pullout, d_pullout, 2),
    # 绝望 17.9 s（鼓进）
    S(16, 20, sc_space, d_species, 0),
    S(20, 24, sc_space, d_extinct, 4),
    S(24, 28, sc_impact, d_impact, 2),
    S(28, 32, sc_space, d_dayclock, 3, (760, 560)),
    S(32, 36, sc_space, d_people, 0),
    S(36, 39, sc_dot, d_dot, 4),
    S(39, 43, sc_sun, d_sun, 7, (800, 540)),
    S(43, 46, sc_off, d_none, 1),
    S(46, 49, sc_pad, d_pad, 0),
    S(49, 52, sc_pad, d_ignite, 2, (CX + 140, H * .5 + 210)),
    # 人类的努力 57.2 s（最强）
    S(52, 55, sc_launch, d_launch, 5, (CX + 140, H * .5 + 210)),
    S(55, 59, sc_earthrise, d_earthrise, 6),
    S(59, 63, sc_artemis, d_artemis, 3, (CX, CY)),
    S(63, 66, sc_vgr_launch, d_vgr_launch, 5, (CX, CY)),
    S(66, 70, sc_helio, d_helio, 2),
    # 屏息 76.8 s
    S(70, 75, sc_alone, d_alone, 3, (980, 560)),
    S(75, 79, sc_space, d_scalebar, 2),
    S(79, 84, sc_drift, d_drift, 0),
    # 宿命 92.1 s（再起）
    S(84, 87, sc_bright, d_bright, 7, (700, 540)),
    S(87, 91, sc_dry, d_dry, 1),
    S(91, 94, sc_scorch, d_scorch, 4),
    S(94, 96, sc_swell, d_swell, 1),
    S(96, 100, sc_giant, d_giant, 3, (CX, CY)),
    # 吞没 109.6 s（高潮）
    S(100, 103, sc_engulf, d_engulf, 1),
    S(103, 106, sc_dwarf, d_none, 4),
    # 熄灭 116.1 s（回到慢）
    S(106, 110, sc_stars, d_stars, 2),
    S(110, 114, sc_last, d_last, 0),
    S(114, 120, sc_black, d_black, 0),
]
SH[0]['t0'] = 0.0; SH[-1]['t1'] = T
for j in range(1, len(SH)):
    n = min(SH[j - 1]['t1'] - SH[j - 1]['t0'], SH[j]['t1'] - SH[j]['t0']) / BEAT
    SH[j]['td'] = (2.0 if n > 5 else 1.5) * BEAT
MODES = {0: 'lights-out', 1: 'redshift', 2: 'time-smear', 3: 'lensing', 4: 'dust', 5: 'warp', 6: 'eclipse', 7: 'god-ray'}

def C(name):
    for sh in SH:
        if sh['draw'].__name__ == 'd_' + name or sh['scene'].__name__ == 'sc_' + name: return sh
    raise KeyError(name)
CAPS = [
    (C('calendar'), '人类只占最后 12 分钟', 'Humans: the last 12 minutes.'),
    (C('lights'), '智人，30 万年前才出现', 'Homo sapiens: only 300,000 years ago.'),
    (C('sunrise'), '我们把夜晚点亮', 'We lit up the night.'),
    (C('pullout'), '1,170 亿人，都在这里活过', '117 billion people have lived here.'),
    (C('species'), '地球上的物种，约 99% 已经灭绝', 'About 99% of all species are gone.'),
    (C('extinct'), '五次大灭绝', 'Five mass extinctions.'),
    (C('impact'), '一颗小行星，结束了恐龙的时代', 'One asteroid ended the dinosaurs.'),
    (C('dayclock'), '地球的一天里，人类只有最后 6 秒', 'In Earth’s day, we are the last 6 seconds.'),
    (C('people'), '1,170 亿人里，93% 已经离开', '93% of them are already gone.'),
    (C('dot'), '所有人，都在这个小点上', 'Everyone, on this one small dot.'),
    (C('sun'), '而太阳，正在一点点变亮', 'And the Sun keeps getting brighter.'),
    (C('off'), '灯，总会熄灭', 'The lights will go out.'),
    (C('pad'), '于是，我们开始往外走', 'So we began to leave.'),
    (C('earthrise'), '12 个人在月球上走过', 'Twelve people walked on the Moon.'),
    (C('artemis'), '人类到过最远：40.7 万公里', 'Our farthest: 406,771 km — 1.36 light-seconds.'),
    (C('vgr_launch'), '1977 年，旅行者 1 号出发', '1977: Voyager 1 sets out.'),
    (C('helio'), '飞出了太阳风的边界', 'Past the edge of the solar wind.'),
    (C('alone'), '飞了 49 年，才走出 1 光日', '49 years: just one light-day.'),
    (C('scalebar'), '最近的恒星，在 1,551 光日之外', 'The nearest star: 1,551 light-days.'),
    (C('drift'), '照这个速度，还要 7.7 万年', 'At that pace: 77,000 more years.'),
    (C('bright'), '太阳越来越亮', 'The Sun grows brighter.'),
    (C('dry'), '约 13 亿年后，海洋开始散失', 'In ~1.3 billion years the oceans begin to go.'),
    (C('scorch'), '地球，不再适合任何生命', 'Earth can no longer hold life.'),
    (C('swell'), '太阳开始膨胀', 'The Sun begins to swell.'),
    (C('giant'), '约 76 亿年后，它变成红巨星', 'In ~7.6 billion years: a red giant.'),
    (C('engulf'), '吞没地球', 'It swallows the Earth.'),
    (C('stars'), '最后的恒星也会熄灭', 'Even the last stars burn out.'),
    (C('last'), '再也没有新的星星', 'No new stars, ever again.'),
]
CAPS = [(s['t0'] + .25, s['t1'] - .3, zh, en) for s, zh, en in CAPS]

G = None
_tx0 = E.tx


def shot_img(k, t, ta=1.0):
    E.tx = lambda cv, s_, x, y, size, col=INK, al=1.0, *a, **kw: _tx0(cv, s_, x, y, size, col, al * ta, *a, **kw)
    sh = SH[k]; u = clamp((t - sh['t0']) / (sh['t1'] - sh['t0'])); s = sh['scene'](t, u)
    rgb = G.scene(t, s)
    buf = np.ascontiguousarray(np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)]))         # keep the pixels alive: skia.Surface only borrows this memory
    surf = skia.Surface(buf); cv = surf.getCanvas()
    sh['draw'](cv, t, u, s); E.tx = _tx0
    out = surf.makeImageSnapshot().toarray(); del surf; return out


def caption(cv, zh, en, t, t0, t1):
    if not (t0 - .1 <= t <= t1 + .1): return
    y, ye = H - 126, H - 78; out = smooth(t1 - .35, t1, t); size = 46
    if PURE: zh, en, y, size = en, '', H - 100, 44                   # English only: the English line takes the main caption's place
    rs = E.runs(zh, size, lf=E.CG_SB); wd = sum(r[2] for r in rs); x = (W - wd) / 2
    step = .035 if not PURE else min(.035, .9 / max(1, len(rs)))
    for j, (ch, f, adv) in enumerate(rs):
        u = clamp((t - t0 + .1 - j * step) / .55); a = eio(u) * (1 - out)
        if a > .003 and ch != ' ':
            dy = (1 - eout(u)) * 10
            cv.drawString(ch, x, y + dy, f, paint(DARK, a * .8, blur=6)); cv.drawString(ch, x, y + dy, f, paint(INK, a, blur=(1 - u) * 7 + out * 4))
        x += adv
    ke = smooth(t0 + .25, t0 + .8, t) * (1 - out)
    if ke > .003 and en:
        f = skia.Font(E.CG_I, 27); we = f.measureText(en); cv.drawString(en, (W - we) / 2, ye, f, paint(SUBC, ke))


def frame(i):
    global G
    t = i / FPS
    if G is None: G = GL(W, H)
    k = max(j for j, s in enumerate(SH) if s['t0'] <= t or j == 0)
    nxt = k + 1 if k + 1 < len(SH) and t > SH[k + 1]['t0'] - SH[k + 1]['td'] / 2 else None
    prv = k - 1 if k > 0 and t < SH[k]['t0'] + SH[k]['td'] / 2 else None
    if nxt is not None or prv is not None:
        j0, j1 = (k, nxt) if nxt is not None else (prv, k)
        cut, td = SH[j1]['t0'], SH[j1]['td']; u = clamp((t - (cut - td / 2)) / td)
        rgb = G.trans(shot_img(j0, t, 1 - smooth(.3, .5, u)), shot_img(j1, t, smooth(.5, .7, u)), u, SH[j1]['mode'], SH[j1]['focus'], t)
        a = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])
    else:
        a = shot_img(k, t)
    buf = np.ascontiguousarray(a); surf = skia.Surface(buf); cv = surf.getCanvas()
    if not os.environ.get('NOTEXT'):
        g = skia.Paint(); g.setShader(skia.GradientShader.MakeLinear([(0, H - 210), (0, H)], [skia.Color4f(0, 0, 0, 0).toColor(), skia.Color4f(0, 0, 0, .5).toColor()]))
        cv.drawRect(skia.Rect.MakeLTRB(0, H - 210, W, H), g)
        for t0, t1, zh, en in CAPS: caption(cv, zh, en, t, t0, t1)
        B.watermark(cv, t, T, expand_at=SH[1]['t0'] + .2, hold=2.0, end_len=1.9, end=False)     # 用户 2026-10-15：这一期不要片尾标志，停在最后一句话上
    out = surf.makeImageSnapshot().toarray(); del surf; return out


class Writer:
    def __init__(self, path):
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                   *(['-vf', 'scale=960:540', '-c:v', 'libx264', '-preset', 'fast', '-crf', '24'] if DRAFT else ['-c:v', 'libx264', '-preset', 'medium', '-crf', '14']), '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    def write(self, a): self.p.stdin.write(a.tobytes())
    def close(self): self.p.stdin.close(); self.p.wait()


if __name__ == '__main__':
    os.makedirs(BUILD + 'stills', exist_ok=True); NF = int(round(T * FPS))
    if len(sys.argv) > 1 and sys.argv[1] == '--still':
        for a in sys.argv[2:]: skia.Image.fromarray(frame(int(float(a) * FPS))).save(f'{BUILD}stills/f_{float(a):06.2f}.jpg', skia.kJPEG, 90); print('still', a, flush=True)
    elif len(sys.argv) > 1 and sys.argv[1] == '--shots':
        for j, s in enumerate(SH): print(f'{j:2d} {s["t0"]:7.2f}–{s["t1"]:7.2f}  {s["t1"] - s["t0"]:.2f} s  {MODES[s["mode"]]:10s} {s["draw"].__name__ if s["draw"].__name__ != "d_none" else s["scene"].__name__}')
        for t0, t1, zh, en in CAPS:
            if len(zh.replace(' ', '')) > 20: print('caption > 20:', zh)
    elif len(sys.argv) > 1 and sys.argv[1] == '--part':
        i, n = int(sys.argv[2]), int(sys.argv[3]); a, b = NF * i // n, NF * (i + 1) // n
        w = Writer(f'{BUILD}c_{i:02d}.mp4')
        for f in range(a, b): w.write(frame(f))
        w.close()
