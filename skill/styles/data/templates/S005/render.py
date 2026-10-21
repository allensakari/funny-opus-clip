"""S005 新能源车 — 全片 0 个硬切：车牌（N 个 morph 元素）从通知 → 柱 → 红灯前的车尾 → 方阵 → 折线 → 纯电 / 插混堆叠 → 充电枪 → 全球圆环 → 车尾。
颜色编码固定：绿 = 新能源（绿牌），蓝 = 燃油（蓝牌）；深绿 / 浅绿 = 纯电 / 插混。色温：铺垫偏冷，「只看新车」起回暖。
9:16（默认 1080×1920）与 16:9（FILM_W=1920 FILM_H=1080）共用：图形组在 16:9 里整体缩放放到右侧，大数字在左侧。
usage:  python render.py | --still t … | --times        （每个屏幕数字旁的注释是 来源表.md 的编号）"""
import os, sys, math, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE + '/../../engine'); sys.path.insert(0, HERE)
import numpy as np
import skia
import brand as B
from brand import *
import captions as C
import morph as MO
import ui as UI
from grade import grade, curve
from script import SEGMENTS
from timeline import build
from music import BEAT, SUFFIX

W, H = int(os.environ.get('FILM_W', 1080)), int(os.environ.get('FILM_H', 1920)); LAND = W > H
B.set_canvas(W, H)
FPS = 30
TAG = ('_16x9' if LAND else '') + SUFFIX
BUILD = HERE + '/build/'
TL = build(SEGMENTS, BUILD + os.environ.get('VOICE_DIR', 'voice'), beat=BEAT, unit=2, gap=.35, tail=2.6)
T, SEG, when = TL.T, TL.SEG, TL.when
S = json.load(open(HERE + '/stats.json'))
GREEN, BLUE = (.13, .60, .34), (.20, .38, .74)          # 颜色编码（全片固定）
BEV, PHEV = (.06, .45, .24), (.52, .80, .55)            # 纯电 / 插混
B.PAIR = (GREEN, BLUE)
ROAD, LANE = (.30, .30, .32), (.92, .90, .86)
INKD = (.36, .34, .31) if B.THEME == 'sand' else (.62, .64, .68)        # private chargers: ink on sand, light grey on dark
N = 240                                                  # morph actors
rng = np.random.default_rng(7)
SEC = S['sec_per_new_2025']

# layout: the graphic group lives in portrait coordinates (x 0–1080, y ≈ 540–1220); in 16:9 it is scaled into the right half
G_S, G_DX, G_DY = (.80, W * .56 - 540 * .80, H * .52 - 880 * .80) if LAND else (1.0, 0.0, 0.0)
NUMX, NUMY = (W * .25, H * .44) if LAND else (W / 2, 470)


def wt(seg, sub, edge='a'): return when(seg, sub, edge)


# ---------------------------------------------------------------- morph states (N pieces, portrait coordinates)
LANES = [330, 460, 590, 720]; ROWS = [830, 1070]
CARS = [(x, y) for y in ROWS for x in LANES]; GREEN_CAR = 6


def hidden(x, y, c=BLUE): return MO.piece(x, y, 4, 4, c, 2, 0)


def st_cards():                                          # pieces hidden inside the notification stack area, then they condense
    return [MO.piece(140 + (i % 40) * 20, 640 + (i // 40) * 70, 12, 12, GREEN, 3, 0) for i in range(N)]


BAR_MAX, BAR_B = 470, 1120
_nl = round(N * 120 / (120 + 1293))


def st_bars():                                           # 2019 120 万 vs 2025 1,293 万 (#3 #5)
    out = []
    for i in range(N):
        if i < _nl: k, n, x, h = i, _nl, 360, BAR_MAX * 120 / 1293
        else: k, n, x, h = i - _nl, N - _nl, 720, BAR_MAX
        sh = h / n; out.append(MO.piece(x, BAR_B - (k + .5) * sh, 170, sh + .6, GREEN, 0, 1))
    return out


def st_queue():
    out = []
    for i in range(N):
        x, y = CARS[i % 8]
        out.append(MO.piece(x, y + 84, 56, 18, GREEN if i == GREEN_CAR else BLUE, 3, 1 if i < 8 else 0))
    return out


_ol, _or = rng.permutation(100), rng.permutation(100)
GL, GR = set(_ol[:13]), set(_or[:49])                    # 13 / 100 on the road, 49 / 100 new cars (#1 #2)


def _grid(x0, y0, k, green): return MO.piece(x0 + (k % 10) * 46, y0 + (k // 10) * 46, 38, 14, GREEN if k in green else BLUE, 3, 1)


def st_grid1(): return [_grid(333, 700, i, GL) if i < 100 else dict(_grid(333, 700, i % 100, GL), a=0) for i in range(N)]
def st_grid2(): return [_grid(93, 700, i, GL) if i < 100 else _grid(573, 700, i - 100, GR) if i < 200 else dict(_grid(573, 700, i - 200, GR), a=0) for i in range(N)]


STOCK = S['stock']
def _xd(d): y, m = int(d[:4]), int(d[5:7]); return 170 + (y + (m - 1) / 12 - 2022.42) / (2026.42 - 2022.42) * 710
def _ys(p): return 1110 - p / 15 * 430
LINE = [(_xd(d), _ys(p)) for d, _, p in STOCK]


def st_line():
    P = MO.resample(LINE, N)
    return [MO.piece(float(x), float(y), 9, 9, GREEN, 4.5, 1) for x, y in P]


def st_bev():                                            # two stacked bars of 100 slices: 2022-06 81 : 19 → 2026-06 69 : 31 (#8)
    out = []
    for i in range(N):
        j = i % 120; bar = 0 if i < 120 else 1
        x = 360 if bar == 0 else 720; share = 80.93 if bar == 0 else 68.77
        k = min(j, 99); h = 420; sh = h / 100
        out.append(MO.piece(x, 1120 - (k + .5) * sh, 200, sh + .6, BEV if k < round(share) else PHEV, 0, 1 if j < 100 else 0))
    return out


N_PRIV, N_PUB = round(1804.8 / 10), round(500.9 / 10)    # one icon = 10 万 chargers (#9)


def st_charge():
    out = []
    for i in range(N):
        if i < N_PRIV: x, y, c = 150 + (i % 15) * 32, 640 + (i // 15) * 34, INKD
        elif i < N_PRIV + N_PUB: k = i - N_PRIV; x, y, c = 690 + (k % 8) * 32, 640 + (k // 8) * 34, ACCENT
        else: x, y, c = 540, 900, INKD
        out.append(MO.piece(x, y, 22, 26, c, 5, 1 if i < N_PRIV + N_PUB else 0))
    return out


def st_world():                                          # ring: 60 % Chinese makers (#11)
    out = []
    for i in range(N):
        a = -math.pi / 2 + 2 * math.pi * i / N; r = 250
        out.append(MO.piece(540 + math.cos(a) * r, 870 + math.sin(a) * r, 18, 18, ACCENT if i < N * .6 else (.70, .67, .62), 9, 1))
    return out


def keyframes():
    return [(st_cards, 0.0),
            (st_bars, wt('speed', '而二零一九') - .3),
            (st_queue, SEG['road']['t0'] - .1),
            (st_grid1, SEG['total']['t0'] + .2),
            (st_grid2, wt('new', '差不多') - .1),
            (st_line, wt('new', '路上的绿牌') - .2),
            (st_bev, SEG['twist']['t0'] + .2),
            (st_charge, SEG['charge']['t0'] + .2),
            (st_world, SEG['world']['t0'] + .1),
            (st_queue, SEG['end']['t0'] + .1)]


KF = None; TR = 1.1


def plates_at(t):
    global KF
    if KF is None: KF = [(fn(), t0) for fn, t0 in keyframes()]
    prev = KF[0][0]
    for j in range(1, len(KF)):
        st, t0 = KF[j]
        if t < t0: return prev, 1.0
        if t < t0 + TR: return MO.tween(prev, st, (t - t0) / TR, stagger=.6), (t - t0) / TR
        prev = st
    return prev, 1.0


# ---------------------------------------------------------------- props
def road(cv, al, lit=0.0, t=0.0):
    if al <= .003: return
    if al > .9: qc_box('graphic', '路口', 265, 560, 860, 1200, al)          # text must not sit on the crossing
    cv.drawRect(skia.Rect.MakeLTRB(265, 560, 785, 1200), paint(ROAD, al))
    for x in (395, 525, 655):
        for y in range(720, 1200, 70): cv.drawRect(skia.Rect.MakeXYWH(x - 3, y, 6, 36), paint(LANE, al * .7))
    cv.drawRect(skia.Rect.MakeLTRB(265, 700, 785, 712), paint(LANE, al))
    for i in range(7): cv.drawRect(skia.Rect.MakeXYWH(280 + i * 72, 600, 46, 80), paint(LANE, al * .8))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(800, 580, 60, 150), 14, 14), paint((.12, .12, .13), al))
    cv.drawCircle(830, 615, 18, paint((.92, .22, .18), al)); cv.drawCircle(830, 615, 34, paint((.95, .3, .2), al * .35, blur=16))
    cv.drawCircle(830, 655, 15, paint((.3, .3, .3), al)); cv.drawCircle(830, 695, 15, paint((.3, .3, .3), al))
    for i, (x, y) in enumerate(CARS):
        body = (.93, .93, .92) if i % 3 == 0 else (.26, .27, .30) if i % 3 == 1 else (.62, .64, .68)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 52, y - 100, 104, 200), 26, 26), paint((0, 0, 0), al * .25, blur=10))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 52, y - 100, 104, 200), 26, 26), paint(body, al))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 42, y - 62, 84, 40), 10, 10), paint((.10, .12, .15), al * .85))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 40, y + 30, 80, 34), 10, 10), paint((.10, .12, .15), al * .7))
    if lit > 0:
        x, y = CARS[GREEN_CAR]; r = 120 + 8 * math.sin(t * 5)
        cv.drawCircle(x, y, r, paint(GREEN, al * lit, stroke=5)); cv.drawCircle(x, y, r + 16, paint(GREEN, al * lit * .35, stroke=3))


def big(cv, al, v, unit='', label=None, src=None, c=None, size=None, pop=1.0, x=None, y=None):
    bignum(cv, al, v, unit, label=label, src=src, y=y or NUMY, x=x or NUMX, size=size or (170 if LAND else 190), c=c or YELLOW, pop=pop)


def sub(cv, s, dy, size, col, al, cjk=CJK_H, num=NUM, accent=None):
    """a line under / above the big number (left column in 16:9)"""
    text(cv, s, NUMX, NUMY + dy, size, col, al, 'c', cjk=cjk, num=num, accent=accent)


def counter(cv, t, al):                                  # plates added since the film started, at the real 2025 rate (#4)
    n = int(max(0, t - .3) / SEC)
    x, y = (W - 150, 300) if not LAND else (W * .25, H * .72)
    text(cv, '本片开始后', x, y - 80, 28, GREY, al, 'c', cjk=CJK_B)
    text(cv, f'+{n}', x, y + 20, 88, GREEN, al * pop_k(t, .3 + n * SEC, .0), 'c', num=NUM)
    text(cv, '辆', x, y + 60, 28, GREY, al, 'c', cjk=CJK_B)
    return n


# ---------------------------------------------------------------- scene
def scene(cv, t):
    s = next((x for x in TL.SEGS if x['t0'] <= t < x['t1']), TL.SEGS[-1])['name']
    t0, t1 = SEG[s]['t0'], SEG[s]['t1']
    cv.clear(skia.Color4f(*BG, 1))
    pl, u = plates_at(t)
    tq1, tq2 = SEG['road']['t0'] - .1, SEG['total']['t0'] + .2
    tb = SEG['end']['t0'] + .1
    road_al = smooth(tq1 + .4, tq1 + TR, t) * (1 - smooth(tq2, tq2 + .6, t)) + smooth(tb + .4, tb + TR, t)
    lit = (smooth(wt('road', '挂着绿牌') - .2, wt('road', '挂着绿牌') + .3, t) if s == 'road' else
           smooth(wt('end', '你身边') - .3, wt('end', '你身边') + .1, t) if s == 'end' else 0)

    # ---- graphic group (portrait coordinates; scaled into the right half in 16:9)
    cv.save(); cv.translate(G_DX, G_DY); cv.scale(G_S, G_S); B.QC_T = (G_S, G_DX, G_DY) if LAND else None
    road(cv, clamp(road_al), lit, t)
    dim = 1.0
    MO.draw(cv, pl, dim, qc='图形' if u >= 1 else None)
    if s in ('hook', 'speed'):
        tb2 = wt('speed', '而二零一九') - .3
        a_cards = 1 - smooth(tb2 - .2, tb2 + .3, t)
        UI.notify_stack(cv, 520, 640, 740, lambda i: ('上牌通知 · 示意', '新能源汽车注册登记  +1'), t, .3, SEC, n_max=4, al=a_cards)   # #4
        if s == 'speed' and t > tb2 + .4:
            a2 = fade(t, tb2 + .6, t1 + .4, .3, .2)
            text(cv, '2019', 360, 1162, 40, GREY, a2, 'c', num=NUM_B); text(cv, '2025', 720, 1162, 40, GREY, a2, 'c', num=NUM_B)
            text(cv, '120万', 360, BAR_B - BAR_MAX * 120 / 1293 - 24, 54, WHITE, a2, 'c', num=NUM, cjk=CJK_H)
            text(cv, '1,293万', 720, BAR_B - BAR_MAX - 24, 54, GREEN, a2, 'c', num=NUM, cjk=CJK_H)
            text(cv, '× 10.8', 500, 860, 70, ACCENT, a2 * smooth(wt('speed', '一百二十万'), wt('speed', '一百二十万') + .4, t), 'c', num=NUM)
            source_tag(cv, a2, '公安部 · 新注册登记新能源汽车', 540, 1212)                                                       # #5
            if u >= 1: qc_box('graphic', '2025 柱', 635, BAR_B - BAR_MAX, 805, BAR_B, a2); qc_box('graphic', '2019 柱', 275, BAR_B - BAR_MAX * 120 / 1293, 445, BAR_B, a2)
    elif s == 'total':
        a = fade(t, tq2 + .6, t1 + .3, .3, .2)
        text(cv, '路上 · 每 100 辆', 540, 640, 34, WHITE, a, 'c', cjk=CJK_B, num=NUM_B)
        for sx, col, lab in ((350, GREEN, '绿牌 13'), (560, BLUE, '蓝牌 87')):
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(sx, 1150, 30, 12), 3, 3), paint(col, a)); text(cv, lab, sx + 40, 1166, 30, GREY, a, cjk=CJK_M, num=NUM_M)
    elif s == 'new':
        tg2, tln = wt('new', '差不多') - .1, wt('new', '路上的绿牌') - .2
        a = fade(t, t0, tln + .2, .2, .3)
        lx = lerp(540, 300, smooth(tg2, tg2 + TR, t))
        text(cv, '路上 · 每 100 辆', lx, 640, 34, WHITE, a, 'c', cjk=CJK_B, num=NUM_B); text(cv, '13', lx, 600, 90, GREEN, a, 'c', num=NUM)
        k2 = smooth(tg2 + .4, tg2 + 1.0, t)
        text(cv, '新车 · 每 100 辆', 780, 640, 34, WHITE, a * k2, 'c', cjk=CJK_B, num=NUM_B); text(cv, '49', 780, 600, 90, GREEN, a * k2, 'c', num=NUM)
        source_tag(cv, a * k2, '公安部 · 2026 年上半年新注册登记 49.42%', 540, 1205)                                             # #2
        a2 = fade(t, tln + .8, t1 + .3, .3, .2)
        if a2 > 0:
            text(cv, '新能源车占全部汽车', 540, 600, 40, WHITE, a2, 'c', cjk=CJK_B)
            for p_ in (5, 10, 15): cv.drawLine(170, _ys(p_), 880, _ys(p_), paint(GREY, a2 * .25, stroke=1)); text(cv, f'{p_}%', 150, _ys(p_) + 9, 26, GREY, a2, 'r', num=NUM_M)
            x0, y0 = LINE[0]; x1, y1 = LINE[-1]
            k3 = smooth(wt('new', '百分之三') - .2, wt('new', '百分之三') + .2, t)
            text(cv, '3.23%', x0 + 20, y0 + 54, 46, GREEN, a2 * k3, 'l', num=NUM); text(cv, '2022-06', x0, 1150, 28, GREY, a2, 'c', num=NUM_M)
            k13 = smooth(wt('new', '百分之十三') - .2, wt('new', '百分之十三') + .2, t)
            text(cv, '13.19%', x1, y1 - 34, 64, GREEN, a2 * k13, 'r', num=NUM); text(cv, '2026-06', x1, 1150, 28, GREY, a2, 'r', num=NUM_M)
            source_tag(cv, a2, '公安部 · 2022–2026 历次发布', 540, 1205)                                                          # #6
    elif s == 'twist':
        a = fade(t, t0 + .8, t1 + .3, .3, .2)
        text(cv, '2022-06', 360, 1162, 36, GREY, a, 'c', num=NUM_B); text(cv, '2026-06', 720, 1162, 36, GREY, a, 'c', num=NUM_B)
        k81 = smooth(wt('twist', '八十一') - .2, wt('twist', '八十一') + .2, t); k69 = smooth(wt('twist', '六十九') - .2, wt('twist', '六十九') + .2, t)
        text(cv, '纯电 81%', 360, 1120 - 420 - 24, 46, BEV, a * k81, 'c', cjk=CJK_H, num=NUM); text(cv, '纯电 69%', 720, 1120 - 420 - 24, 46, BEV, a * k69, 'c', cjk=CJK_H, num=NUM)
        kp = smooth(wt('twist', '插电混动') - .3, wt('twist', '插电混动') + .1, t)
        for sx, col, lab in ((330, BEV, '纯电动'), (560, PHEV, '插电混动等')):
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(sx, 1188, 30, 12), 3, 3), paint(col, a)); text(cv, lab, sx + 40, 1204, 28, GREY, a, cjk=CJK_M)
    elif s == 'charge':
        a = fade(t, t0 + .8, t1 + .3, .3, .2)
        text(cv, '私人 1,805 万', 390, 600, 40, INKD, a * smooth(wt('charge', '自家车位') - .3, wt('charge', '自家车位'), t), 'c', cjk=CJK_H, num=NUM)
        text(cv, '公共 501 万', 802, 600, 40, ACCENT, a * smooth(wt('charge', '公共的') - .3, wt('charge', '公共的'), t), 'c', cjk=CJK_H, num=NUM)
        text(cv, '每个图标 = 10 万个充电枪', 540, 1100, 28, GREY, a, 'c', cjk=CJK_M, num=NUM_M)
        source_tag(cv, a, '国家能源局 · 2026-06', 540, 1160)                                                                     # #9
    elif s == 'world':
        a = fade(t, t0 + .7, t1 + .3, .3, .2)
        k = smooth(wt('world', '百分之六十') - .2, wt('world', '百分之六十') + .2, t)
        text(cv, '60%', 540, 900, 130, ACCENT, a * k, 'c', num=NUM)
        text(cv, '出自中国车企', 540, 960, 36, WHITE, a * k, 'c', cjk=CJK_B)
        source_tag(cv, a, 'IEA《全球电动汽车展望 2026》', 540, 1205)                                                             # #11
    B.QC_T = None; cv.restore()

    # ---- left / top column: big numbers and one-liners
    if s == 'hook':
        land = wt('hook', '四千八百九十七万', 'b')
        v = count(t, -.1, land, 4000, 4897)
        big(cv, 1 if t < t1 else 0, f'{int(v):,}万', '辆', label='中国路上的新能源车', src='公安部 · 2026-06', pop=pop_k(t, land))   # #1
        counter(cv, t, fade(t, wt('hook', '刚说完') - .3, t1 + .4, .3, .2))
    elif s == 'speed':
        tb2 = wt('speed', '而二零一九') - .3
        a1 = fade(t, t0, tb2 + .2, .2, .3)
        big(cv, a1, '1,293万', '辆', label='2025 年 · 新上牌的新能源车', src='公安部 · 2026-01', pop=pop_k(t, wt('speed', '一千二百九十三万')))   # #3
        sub(cv, '每 2.4 秒 1 辆 · 一天 3.5 万辆', 150, 46, GREEN, a1 * smooth(wt('speed', '平均每') - .2, wt('speed', '平均每') + .2, t), cjk=CJK_H, accent=GREEN)   # #4 #13
        counter(cv, t, a1)
    elif s == 'road':
        a = fade(t, t0 + .2, t1 + .3, .3, .2)
        oy = -90 if not LAND else 0                      # portrait: keep the lines above the crossing (y < 560)
        sub(cv, '你每天等的那个红灯', -120 + oy, 40, GREY, a, cjk=CJK_B)
        sub(cv, '前面 8 辆车', -20 + oy, 72, WHITE, a * smooth(wt('road', '八辆') - .2, wt('road', '八辆') + .1, t))
        sub(cv, '≈ 1 块绿牌', 70 + oy, 80, GREEN, a * smooth(wt('road', '大约只有') - .1, wt('road', '一辆') + .2, t), accent=GREEN)
        source_tag(cv, a * smooth(wt('road', '一辆'), wt('road', '一辆') + .3, t), '公安部 2026-06 · 全国平均 13.19% 推算', NUMX, NUMY + 130 + oy - 15)   # #7
    elif s == 'total':
        a = fade(t, t0 + .2, t1 + .3, .3, .2)
        big(cv, a, '3.71亿', '辆', label='路上的全部汽车', src='公安部 · 2026-06', c=WHITE, pop=pop_k(t, wt('total', '三点七一亿')))   # #12
    elif s == 'twist':
        a = fade(t, t0 + .2, t1 + .3, .3, .2)
        sub(cv, '纯电的比例', -110, 44, WHITE, a, cjk=CJK_B)
        sub(cv, '81% → 69%', 0, 96, BEV, a * smooth(wt('twist', '八十一') - .2, wt('twist', '六十九') + .2, t))
        sub(cv, '涨得更快的是插电混动', 80, 40, GREEN, a * smooth(wt('twist', '插电混动') - .3, wt('twist', '插电混动') + .1, t), cjk=CJK_B, accent=GREEN)
        source_tag(cv, a, '公安部 · 2022–2026 历次发布', NUMX, NUMY + 130)                                                         # #8
    elif s == 'charge':
        a = fade(t, t0 + .2, t1 + .3, .3, .2)
        big(cv, a, '2,306万', '个', label='全国充电枪', src=None, c=YELLOW, pop=pop_k(t, wt('charge', '两千三百零六万')))           # #9
        sub(cv, '≈ 每 2 辆新能源车 1 个（推算）', 70, 36, GREY, a * smooth(wt('charge', '平均每') - .2, wt('charge', '平均每') + .2, t), cjk=CJK_B, num=NUM_B)   # #10
    elif s == 'world':
        a = fade(t, t0 + .2, t1 + .3, .3, .2)
        big(cv, a, '2,000万+', '辆', label='2025 年 · 全球电动车销量', src=None, c=WHITE, pop=pop_k(t, wt('world', '两千万')))      # #11
    elif s == 'end':
        t_card = T - 1.95
        a0 = fade(t, t0 + .6, wt('end', '再想想') - .1, .3, .3)
        sub(cv, '下次等红灯，数一数绿牌', 0, 56 if not LAND else 50, WHITE, a0)
        a = fade(t, wt('end', '再想想') - .2, t_card, .3, .3)
        sub(cv, '你身边第一个', -70, 70 if not LAND else 60, WHITE, a)
        sub(cv, '换绿牌的人，是谁？', 30, 76 if not LAND else 64, GREEN, a, accent=GREEN)


GRADE = None


def frame(i):
    global GRADE
    t = i / FPS
    if GRADE is None:                                    # 色温叙事：铺垫偏冷 → 「只看新车」回暖 → 结尾最暖
        GRADE = [(0, -.10), (SEG['road']['t0'], -.25), (SEG['total']['t1'], -.25), (SEG['new']['t0'] + 1.5, .05), (SEG['twist']['t0'], .15),
                 (SEG['world']['t0'], .30), (SEG['end']['t0'] + 1, .50)]
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    scene(cv, t)
    if not os.environ.get('NOTEXT'):
        if not LAND: scrim(cv, 1260, 1460, 0, .55); scrim(cv, 1460, 1920, .55, .2)
        else: scrim(cv, H - 240, H, 0, .5)
        C.draw(cv, TL.CAPS, t, 'odo')
        watermark(cv, t, T, expand_at=SEG['speed']['t0'] + .2, hold=2.0, end_len=1.9)
    return grade(surf.makeImageSnapshot().toarray(), curve(t, GRADE), sat=1.05)


def render_range(i0, i1, path):
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for i in range(i0, i1): enc.stdin.write(frame(i).tobytes())
    enc.stdin.close(); enc.wait()


if __name__ == '__main__':
    SD = BUILD + 'stills' + TAG + '/'; os.makedirs(SD, exist_ok=True); NF = int(round(T * FPS))
    if len(sys.argv) > 1 and sys.argv[1] == '--still':
        for a in sys.argv[2:]:
            skia.Image.fromarray(frame(int(float(a) * FPS))).save(f'{SD}still_{float(a):05.1f}.jpg', skia.kJPEG, 88); print('still', a)
    elif len(sys.argv) > 1 and sys.argv[1] == '--part':
        i, n = int(sys.argv[2]), int(sys.argv[3]); render_range(NF * i // n, NF * (i + 1) // n, f'{BUILD}part{TAG}_{i:02d}.mp4')
    elif len(sys.argv) > 1 and sys.argv[1] == '--times':
        TL.show()
    else:
        n = int(os.environ.get('JOBS', 4))
        ps = [subprocess.Popen([sys.executable, __file__, '--part', str(i), str(n)]) for i in range(n)]
        if any(p.wait() for p in ps): raise SystemExit('render failed')
        open(BUILD + f'concat{TAG}.txt', 'w').write(''.join(f"file 'part{TAG}_{i:02d}.mp4'\n" for i in range(n)))
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', BUILD + f'concat{TAG}.txt', '-c', 'copy', BUILD + f'video{TAG}.mp4'])
        print('ok', BUILD + f'video{TAG}.mp4', f'{T:.2f} s')
