"""print-cartoon（印刷卡通）风格工具包 —— 源自 S015《你总排到慢的那队》。规则见同目录 STYLE.md。
米色纸面 + 孔版印刷颗粒 / 套色偏移阴影；胶囊小人只靠眼神、眉毛、嘴演戏，黄色的那个是「你」；动作卡 120 BPM 网格。
横竖两版共用一个「世界坐标」：横版 1920×1080 原样画；VERT=1 → 竖版 1080×1920，世界放大 ZV 并下移 VY，叠加层用 ov() 重新安放。

期目录里：
    import sys; sys.path.insert(0, ROOT + '/skill/styles/print-cartoon'); from print_cartoon import *
场景函数只管画世界坐标里的东西；frame() 负责底色、场景、字幕、章节卡、颗粒。参考 templates/S015/film.py。"""
import os, sys, math, random, subprocess
from contextlib import contextmanager
import numpy as np, skia

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))   # skill root (skill/styles/print-cartoon/ → ../../..)
V = bool(os.environ.get('VERT'))
W, H = (1080, 1920) if V else (1920, 1080)
FPS = 60
BPM = 120
BEAT = 60 / BPM
VY = 85 if V else 0                     # 竖版：世界坐标整体下移（字幕在上面，底部 1540 以下是平台遮挡区）
ZV = 1.25 if V else 1.0                 # 竖版：世界放大，能看到 x 0–864
XIN = 950 if V else 2080                # 入画的人从右侧画外走进来的起点（世界坐标）

FONTS = ROOT + '/assets/fonts/'
def _tf(n): return skia.Typeface.MakeFromFile(FONTS + n)
ZH_B, ZH_H, ZH_M = _tf('SourceHanSansCN-Bold.otf'), _tf('SourceHanSansCN-Heavy.otf'), _tf('SourceHanSansCN-Medium.otf')
ZH_T = _tf('SmileySans-Oblique.ttf')                                  # 得意黑：章节卡、主题句
EN_K, EN_B, EN_S = _tf('Nunito-Black.ttf'), _tf('Nunito-ExtraBold.ttf'), _tf('Nunito-SemiBold.ttf')


def hx(s): s = s.lstrip('#'); return tuple(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4))
PAPER, INK, CARD = hx('F2ECDF'), hx('2A2A3C'), hx('FFFCF4')            # 纸 / 墨 / 卡片白
TOMATO, COBALT, TEAL, PINK, LAV, MINT, SKY = (hx(c) for c in ('E8553D', '3657C7', '1E9C88', 'EF95AE', '9784D6', '7CC9A8', '6FB3E0'))
YOU, GOLD, GREYD, SHELF = hx('F5C247'), hx('D9A441'), hx('CFC6B4'), hx('E4DCCB')   # YOU = 品牌黄，只给「你」和章节卡
SHOP = [COBALT, TEAL, PINK, LAV, MINT, SKY, hx('C9A27A'), hx('5D7A6B'), hx('E58F6F')]   # 路人配色（不含黄色）
FS = 1.3 if V else 1.0                                                  # 卡片里的字：竖版放大（卡片在竖版里约缩到 0.8）

# ---------------------------------------------------------------- easing
def clamp(x, a=0., b=1.): return a if x < a else b if x > b else x
def smooth(a, b, x): u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u)
def eio(u): u = clamp(u); return u * u * (3 - 2 * u)
def eout(u): u = clamp(u); return 1 - (1 - u) ** 3
def eback(u, s=2.2): u = clamp(u) - 1; return 1 + u * u * ((s + 1) * u + s)
def lerp(a, b, u): return a + (b - a) * u
def fade(t, a, b, fi=.3, fo=.3): return smooth(a, a + fi, t) * (1 - smooth(b - fo, b, t))
def mix(c1, c2, u): return tuple(lerp(a, b, u) for a, b in zip(c1, c2))
def val(v, t): return v(t) if callable(v) else v


def snap(t):                                                            # 下一个拍点（含 t）
    return math.ceil(t / BEAT - 1e-6) * BEAT


# ---------------------------------------------------------------- 音效事件：画面登记，score 读取
EV = []
def ev(t, kind, **kw): EV.append(dict(t=float(t), kind=kind, **kw))


# ---------------------------------------------------------------- 基本图元
def P(col, a=1., stroke=0., cap=False):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*col, clamp(a)))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke); p.setStrokeCap(skia.Paint.kRound_Cap if cap or True else 0); p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def text(c, s, x, y, tf, size, col=INK, a=1., align='c', riso=0.):
    if a <= .003: return 0
    f = skia.Font(tf, size); w = f.measureText(s)
    x0 = x - w / 2 if align == 'c' else x - w if align == 'r' else x
    if riso: c.drawString(s, x0 + riso, y + riso * .8, f, P(mix(col, INK, .35), a * .45))
    c.drawString(s, x0, y, f, P(col, a))
    return w


def rrect(c, l, t, w, h, r, paint): c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(l, t, w, h), r, r), paint)


def riso_rrect(c, l, t, w, h, r, col, a=1., off=6):
    rrect(c, l + off, t + off * .8, w, h, r, P(mix(col, INK, .35), a * .5))
    rrect(c, l, t, w, h, r, P(col, a))


def bean(c, x, y, col, s=1., gaze=(-1, 0), mood=0., brow=0., a=1., you=False, bob=0., blink=False, tag=True):
    if a <= .003: return
    w, h = 64 * s, 104 * s
    top = y - h - bob
    c.drawOval(skia.Rect.MakeXYWH(x - w * .6, y - 6 * s, w * 1.2, 12 * s), P(INK, .10 * a))
    riso_rrect(c, x - w / 2, top, w, h, w / 2, col, a, 5 * s)
    gx, gy = gaze
    for side in (-1, 1):
        cx, cy = x + side * 13 * s + gx * 7 * s, top + .31 * h + gy * 5 * s
        if blink:
            c.drawLine(cx - 8 * s, cy, cx + 8 * s, cy, P(INK, a, 3 * s))
        else:
            c.drawCircle(cx, cy, 10.5 * s, P(CARD, a))
            c.drawCircle(cx + gx * 4.2 * s, cy + gy * 4.2 * s, 5.6 * s, P(INK, a))
        if abs(brow) > .02:                                   # annoyed: inner end of the brow drops
            c.drawLine(cx - side * 9 * s, cy - 14 * s + brow * 5 * s, cx + side * 9 * s, cy - 17 * s - brow * 1.5 * s, P(INK, a, 3.2 * s))
    mx, my = x + gx * 6 * s, top + .56 * h + gy * 3 * s
    pth = skia.Path(); pth.moveTo(mx - 8 * s, my); pth.quadTo(mx, my + 9 * s * clamp(mood, -1.2, 1.2), mx + 8 * s, my)
    c.drawPath(pth, P(INK, a, 3 * s))
    if you and tag:                                           # little marker above YOU
        ty = top - 18 * s
        tri = skia.Path(); tri.moveTo(x - 9 * s, ty - 12 * s); tri.lineTo(x + 9 * s, ty - 12 * s); tri.lineTo(x, ty); tri.close()
        c.drawPath(tri, P(INK, a))
        text(c, '你', x, ty - 20 * s, ZH_H, 30 * s, INK, a)


def paper(c):
    c.clear(skia.Color4f(*PAPER, 1))


_rg = np.random.default_rng(7)
GRAIN = np.zeros((H, W, 4), np.uint8); GRAIN[..., 0] = GRAIN[..., 1] = GRAIN[..., 2] = 40
GRAIN[..., 3] = (_rg.random((H, W)) ** 6 * 70).astype(np.uint8)
GRAIN_IMG = skia.Image.fromarray(GRAIN, colorType=skia.kRGBA_8888_ColorType)    # 孔版颗粒：每帧最后盖一层


# ---------------------------------------------------------------- 排队模型（任何「一个接一个」的题材都能用：排队、收银、过闸、等电梯）
class Lane:
    """people stand in order; person i is served when everyone ahead has left. Departures snap to beats.
    person keys: col, svc | end (scripted), arrive (walk in from the right), skip (leaves without paying), nodraw, you, gaze, mood, brow"""
    X0, GAP = 340, 112

    def __init__(self, y, people, start, s=1., win=(0, 1e9), quiet=False):
        self.y, self.s, self.P = y, s, people
        free = start
        for i, p in enumerate(people):
            p.setdefault('col', SHOP[i % len(SHOP)]); p.setdefault('ph', random.Random(int(y) * 100 + i).random() * 5)
            if p.get('skip'): continue
            ready = p['arrive'] + 1.4 if p.get('arrive') is not None else start
            p['start'] = max(free, ready)
            if 'end' not in p: p['end'] = snap(p['start'] + p.get('svc', 1.5))
            free = p['end']
        if not quiet:
            for p in people:
                if not p.get('skip') and win[0] < p['end'] < win[1] and p['end'] < 900: ev(p['end'], 'ding', lane=y)
                if p.get('arrive') is not None and win[0] < p['arrive'] < win[1]: ev(p['arrive'] + 1.1, 'step', lane=y)

    def slot(self, i, t):
        return i - sum(eio((t - q['end']) / .55) for q in self.P[:i])

    def pos(self, i, t):
        """local (x, dy, alpha) or None"""
        p = self.P[i]
        if p.get('arrive') is not None and t < p['arrive']: return None
        if t >= p['end']:
            if p.get('skip'): return None
            u = (t - p['end']) / .9
            if u >= 1: return None
            return self.X0 - 110 * eio(u), -70 * eio(u), 1 - smooth(.15, .8, u)
        x = self.X0 + self.GAP * self.slot(i, t)
        if p.get('arrive') is not None:
            u = (t - p['arrive']) / 1.4
            if u < 1: x = lerp(XIN / self.s, x, eout(u))
        return x, 0., 1.

    def screen(self, i, t):
        r = self.pos(i, t)
        if r is None: return None
        return r[0] * self.s, self.y + r[1] * self.s, r[2]

    def serving(self, t):
        return any(not p.get('skip') and p['start'] + .55 <= t < p['end'] for p in self.P)

    def draw_people(self, t, out):
        for i, p in enumerate(self.P):
            if p.get('nodraw'): continue
            r = self.pos(i, t)
            if r is None: continue
            r2 = self.pos(i, t - .04)
            moving = r2 is not None and abs(r[0] - r2[0]) > .8
            out.append((self.y, self, p, r, moving))

    def draw_counter(self, c, t, **kw):
        light = .55 + .45 * (math.fmod(t, BEAT) < .18) if self.serving(t) else 0.
        counter(c, self.y, self.s, light, **kw)


def draw_beans(c, t, items, gaze_all=None):
    items.sort(key=lambda it: (it[0], -it[3][0]))
    for y, lane, p, (x, dy, a), moving in items:
        c.save(); c.translate(0, lane.y); c.scale(lane.s, lane.s)
        bob = abs(math.sin(t * 13)) * 7 if moving else 1.2 * math.sin(t * 2.2 + p['ph'])
        g = val(p.get('gaze', (-1, 0)), t)
        if gaze_all and not p.get('you') and 'gaze' not in p: g = gaze_all(p, t)
        blink = math.fmod(t + p['ph'], 3.7) < .11
        if moving and a > .5:
            for j, (yy, ln) in enumerate(((-34, 34), (-60, 52), (-86, 30))):
                c.drawLine(x + 44 + j * 6, dy + yy, x + 44 + j * 6 + ln, dy + yy, P(INK, .28 * a, 3.5))
        bean(c, x, dy, YOU if p.get('you') else p['col'], 1, g, val(p.get('mood', 0), t), val(p.get('brow', 0), t), a,
             p.get('you', False), bob, blink, tag=p.get('tag', True))
        c.restore()


def crowd(seed, n, **kw):
    r = random.Random(seed)
    return [{**dict(col=r.choice(SHOP), svc=r.choice([1., 1.5, 1.5, 2.]), ph=r.random() * 5), **kw} for _ in range(n)]


# ---------------------------------------------------------------- 字幕、章节卡、叠加层
def wrap(s, tf, size, maxw, words=False):
    import re
    f = skia.Font(tf, size); lines, cur = [], ''
    if not words and f.measureText(s) > maxw:                       # prefer one break at the pause nearest the middle
        cuts = [i + 1 for i, ch in enumerate(s) if ch in '，；：' and i + 1 < len(s)] + [i for i in range(len(s)) if s.startswith('——', i) and i > 0]
        cuts = [i for i in cuts if f.measureText(s[:i]) <= maxw and f.measureText(s[i:]) <= maxw]
        if cuts:
            i = min(cuts, key=lambda i: abs(f.measureText(s[:i]) - f.measureText(s) / 2)); return [s[:i], s[i:]]
    for tok in (s.split(' ') if words else re.findall(r'[A-Za-z0-9.%,]+|.', s)):
        nxt = (cur + ' ' + tok if cur else tok) if words else cur + tok
        if f.measureText(nxt) > maxw and cur and not (not words and tok in '，。；：？！—…）、'):
            lines.append(cur); cur = tok
        else: cur = nxt
    return lines + [cur]


def captions(c, t, caps):
    for a0, a1, zh, en in caps:
        if a0 - .1 <= t <= a1 + .1:
            u = fade(t, a0, a1, .28, .22); dy = (1 - eout((t - a0) / .35)) * 14
            if not V:
                text(c, zh, W / 2, 128 + dy, ZH_B, 56, INK, u, riso=3)
                text(c, en, W / 2, 182 + dy, EN_S, 28, INK, u * .62)
                continue
            zl, el = wrap(zh, ZH_B, 62, 940), wrap(en, EN_S, 32, 940, True)
            y = 312 + dy
            for ln in zl: text(c, ln, W / 2, y, ZH_B, 62, INK, u, riso=3); y += 76
            y -= 12
            for ln in el: text(c, ln, W / 2, y, EN_S, 32, INK, u * .62); y += 42


def wipe(c, t, wipes, title=None):
    """chapter card: a brand-yellow panel slides in from the right (0.35 s), the title types in, it slides out to the left.
    The scene changes at t0 while the panel covers the frame (t0 − 0.5 … t0 + 0.55). #01 also carries the film title."""
    for t0, num, zh, en, *_ in wipes:
        u = t - (t0 - .85)
        if not 0 <= u <= 1.75: continue
        sk = 140 if not V else 220                                        # slanted edge
        if u < .35: xl, xr = lerp(W + sk, -sk, eio(u / .35)), W + sk * 2
        elif u < 1.4: xl, xr = -sk, W + sk * 2
        else: xl, xr = -sk, lerp(W + sk * 2, -sk * 2, eio((u - 1.4) / .35))
        pth = skia.Path(); pth.moveTo(xl + sk, 0); pth.lineTo(xr + sk, 0); pth.lineTo(xr - sk, H); pth.lineTo(xl - sk, H); pth.close()
        c.save(); c.translate(-14, 0); c.drawPath(pth, P(TOMATO, 1)); c.restore()   # a tomato edge leads the panel (riso offset)
        c.drawPath(pth, P(YOU, 1))
        c.save(); c.clipPath(pth, doAntiAlias=True)
        ta = smooth(.3, .45, u) * (1 - smooth(1.38, 1.5, u))
        dx = (1 - eout((u - .3) / .5)) * 60
        cx, cy = W / 2 + dx, H / 2
        first = title is not None and num == wipes[0][1]
        if first:                                                          # the film's title on the first card
            ts = 88 if V else 96
            lines = wrap(title[0], ZH_T, ts, W - 140) if V else [title[0]]
            yy = cy - 150 - (len(lines) - 1) * ts * .6
            for ln in lines: text(c, ln, cx, yy, ZH_T, ts, INK, ta, riso=5); yy += ts * 1.15
            text(c, title[1], cx, yy - ts * .35, EN_B, 26 if V else 28, INK, ta * .6)
            cy += 90
        n_ = int(clamp((u - .35) / .045, 0, len(zh)))                        # title types in
        text(c, num, cx, cy - 70, EN_K, 64, TOMATO, ta)
        f = skia.Font(ZH_T, 110 if not first else 84); full = f.measureText(zh); x = cx - full / 2
        for k, ch in enumerate(zh[:n_]):
            g = eback(clamp((u - .35 - k * .045) / .16))
            w_ = f.measureText(ch)
            c.save(); c.translate(x + w_ / 2, cy + 50); c.scale(g, g)
            c.drawString(ch, -w_ / 2 + 5, 4, f, P(CARD, ta * .8)); c.drawString(ch, -w_ / 2, 0, f, P(INK, ta))
            c.restore(); x += w_
        text(c, en, cx, cy + 110, EN_B, 28, INK, ta * .6 * smooth(.7, .9, u))
        c.restore()


def big(c, s, x, y, size, col, a, u=1., tf=EN_K):
    if a <= .003: return
    k = eback(u)
    c.save(); c.translate(x, y); c.scale(k, k)
    text(c, s, 0, 0, tf, size, col, a, riso=size * .035)
    c.restore()


def card(c, l, t, w, h, a=1.):
    riso_rrect(c, l, t, w, h, 26, CARD, a, 10)


@contextmanager
def ov(c, src=None, dst=None):
    """screen-space overlay. Landscape: plain screen coords. Vertical: the landscape rect src=(l, t, w, h) is fitted into dst=(cx, cy, max_w)"""
    c.save(); c.resetMatrix()
    if V and src:
        l, t, w, h = src; cx, cy, mw = dst; k = min(1, mw / w)
        c.translate(cx, cy); c.scale(k, k); c.translate(-(l + w / 2), -(t + h / 2))
    try: yield
    finally: c.restore()


def stamp(c, s, x, y, u, col=TOMATO, rot=-10, size=56):
    if u <= 0: return
    k = lerp(2.2, 1, eout(u / .25)) if u < .25 else 1
    a = clamp(u / .12)
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(k, k)
    f = skia.Font(ZH_H, size); w = f.measureText(s) + 50
    rrect(c, -w / 2, -size * .95, w, size * 1.35, 12, P(col, a * .95, 6))
    text(c, s, 0, size * .22, ZH_H, size, col, a)
    c.restore()


def bubble(c, x, y, rx, ry, a, tail=None):
    """thought cloud centred at (x, y); tail = (tx, ty) where the small dots lead"""
    if a <= .003: return
    pp = P(CARD, a); edge = P(INK, a * .9, 3.5)
    pth = skia.Path()
    for k in range(9):
        th = k / 9 * math.tau
        pth.addCircle(x + math.cos(th) * rx * .78, y + math.sin(th) * ry * .7, min(rx, ry) * .42)
    pth.addOval(skia.Rect.MakeXYWH(x - rx * .85, y - ry * .78, rx * 1.7, ry * 1.56))
    pth = pth.makeAsWinding() if hasattr(pth, 'makeAsWinding') else pth
    c.drawPath(pth, edge); c.drawPath(pth, pp)
    if tail:
        tx, ty = tail
        for k, r in enumerate((10, 7)):
            u = .55 + k * .25
            cx, cy = lerp(x, tx, u), lerp(y + ry * .6, ty, u)
            c.drawCircle(cx, cy, r, P(CARD, a)); c.drawCircle(cx, cy, r, P(INK, a * .9, 3))


def dim(c, a):
    """整屏铺一层纸色（主题卡、投票卡、数据卡之前）"""
    if a > 0:
        with ov(c): c.drawRect(skia.Rect.MakeWH(W, H), P(PAPER, a))


def theme_card(c, t, t0, t1, lines, en='', sub='', sub_en='', emph='', lines_v=None):
    """主题句卡（片子讲的道理）：逐字打出，`emph` 这串字用番茄红；横版 2 行，竖版用 lines_v（拆成 3 行、字更大）。之后浮出一行小字 sub。"""
    if not t0 - .1 < t < t1 + .3: return
    if V and lines_v: lines = lines_v
    dim(c, .9 * smooth(t0, t0 + .35, t))
    a = fade(t, t0, t1, .3, .35)
    with ov(c):
        size = 100 if V else 96
        y0 = H / 2 - (230 if V else 110)
        for li, line in enumerate(lines):
            tl = t0 + .15 + li * .55
            n = int(clamp((t - tl) / .04, 0, len(line)))
            f = skia.Font(ZH_T, size); full = f.measureText(line)
            k = min(1, (W - 120) / full)
            c.save(); c.translate(W / 2, y0 + li * size * 1.35 * k); c.scale(k, k)
            x = -full / 2
            e0 = line.find(emph) if emph else -1
            for ci, ch in enumerate(line[:n]):
                col = TOMATO if e0 >= 0 and e0 <= ci < e0 + len(emph) else INK
                c.drawString(ch, x + 5, 4, f, P(mix(col, INK, .35), a * .45)); c.drawString(ch, x, 0, f, P(col, a))
                x += f.measureText(ch)
            c.restore()
        y0 += (len(lines) - 2) * size * 1.35
        if en: text(c, en, W / 2, y0 + 2 * size * 1.35 + (10 if V else 0), EN_S, 34 if V else 30, INK, a * .6 * smooth(t0 + 1.6, t0 + 2.0, t))
        if sub:
            u = smooth(t0 + 2.4, t0 + 2.8, t)
            c.drawLine(W / 2 - 60, y0 + 2 * size * 1.35 + 70, W / 2 + 60, y0 + 2 * size * 1.35 + 70, P(INK, a * u * .4, 3))
            text(c, sub, W / 2, y0 + 2 * size * 1.35 + 150, ZH_B, 48 if V else 44, INK, a * u)
            if sub_en: text(c, sub_en, W / 2, y0 + 2 * size * 1.35 + 200, EN_S, 28, INK, a * u * .55)


def vote_card(c, t, t0, t1, options=(('1', '换队', 'switch'), ('2', '死守', 'stay'))):
    """投票引导：两张随节拍跳动的卡（评论区扣 1 / 扣 2），一个小人在第一张卡里跳。字幕负责把问题说出来。"""
    if not t0 - .4 < t < t1 + .4: return
    dim(c, .86 * smooth(t0 - .3, t0 + .1, t) * (1 - smooth(t1, t1 + .4, t)))
    with ov(c, (540, 300, 840, 420), (540, 900, 1000)):
        for i, (num, lab, _) in enumerate(options):
            u = (t - t0 - .25 * i) / .4
            if u <= 0: continue
            col = (TOMATO, TEAL)[i % 2]
            pulse = 1 + .05 * (math.fmod(t - .25 * i, 2 * BEAT) < .12)
            c.save(); c.translate(750 + i * 420, 510); c.scale(eback(u) * pulse, eback(u) * pulse)
            riso_rrect(c, -180, -200, 360, 400, 28, CARD, 1, 10)
            rrect(c, -180, -200, 360, 400, 28, P(col, 1, 6))
            text(c, num, -70, -40, EN_K, 150, col, 1, riso=5)
            text(c, lab, 60, -70, ZH_H, 64, INK, 1)
            hop = abs(math.sin((t - t0) * math.pi / BEAT)) * 26 if i == 0 else 0
            bean(c, 60, 150, YOU, .9, (1, 0) if i == 0 else (-1, 0), .8 if i == 0 else 0, 0 if i == 0 else 1.1, 1, False, hop)
            text(c, '扣 ' + num, -70, 140, ZH_H, 44, col, 1)
            c.restore()


sys.path.insert(0, ROOT + '/engine'); import channel as _CH       # the channel's horizontal logo (profile marks.end_logo_h), tinted with the ink colour
LOGO = skia.Image.open(_CH.mark(_CH.P['marks'].get('end_logo_h', _CH.P['marks']['end_logo'])))


def end_logo(c, t, t0):
    """片尾：纸面 + 横排黑字标志，只放标志（不加口号，用户 2026-10-18）"""
    if t <= t0 - .6: return
    a = smooth(t0, t0 + .6, t)
    with ov(c):
        c.drawRect(skia.Rect.MakeWH(W, H), P(PAPER, a))
        s = (.33 if V else .42) * lerp(.96, 1, eout((t - t0) / 1.5))
        c.save(); c.translate(W / 2, H / 2); c.scale(s, s)
        c.drawImage(LOGO, -LOGO.width() / 2, -LOGO.height() / 2, skia.SamplingOptions(skia.FilterMode.kLinear), P(INK, a))
        c.restore()


# ---------------------------------------------------------------- 剪辑表：先做完整版，再压到 ~90 s（film time → output time）
def seg_table(seg):
    out, o = [], 0.
    for a, b, sp in seg: out.append((a, b, sp, o)); o += (b - a) / sp
    return out, o


def film2out(t, seg, side=None):
    tab, _ = seg_table(seg)
    for i, (a, b, sp, o) in enumerate(tab):
        if a <= t < b or (t == b and i == len(tab) - 1): return o + (t - a) / sp
        if t < a:
            if side == 'next': return o
            if side == 'prev' and i: pa, pb, psp, po = tab[i - 1]; return po + (pb - pa) / psp
            return None
    return tab[-1][3] + (tab[-1][1] - tab[-1][0]) / tab[-1][2] if side else None


def out2film(T, seg):
    tab, _ = seg_table(seg)
    for a, b, sp, o in tab:
        if T < o + (b - a) / sp: return a + max(0., T - o) * sp
    return tab[-1][1]


def caps_kept(caps, seg, min_s=1.0):
    """剪辑后还看得到（≥ min_s 秒）的字幕"""
    return [cp for cp in caps if film2out(cp[1], seg, 'prev') - film2out(cp[0], seg, 'next') >= min_s]


# ---------------------------------------------------------------- 出片：分段并行渲染（60 fps），ffprobe 核对帧数
def render_main(frame, dur, build, script, tmap=None):
    """frame(t_film, surf) → RGBA 数组；tmap(T_out) → t_film（剪辑版 / 卡点版），None = 原样。
    在期目录 film.py 的 __main__ 里调用：--still t … | --part i n | 无参数 = 8 段并行 + concat → build/video.mp4"""
    a = sys.argv[1:]
    os.makedirs(build + '/parts', exist_ok=True)
    NF = int(dur * FPS)
    if a and a[0] == '--still':
        import PIL.Image
        surf = skia.Surface(W, H); os.makedirs(build + '/stills', exist_ok=True)
        for s in a[1:]: PIL.Image.fromarray(frame(float(s), surf)[..., :3]).save(f'{build}/stills/{float(s):06.2f}.png')
    elif a and a[0] == '--part':
        i, n = int(a[1]), int(a[2]); surf = skia.Surface(W, H)
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', f'{build}/parts/p{i}.mp4'], stdin=subprocess.PIPE)
        for f in range(NF * i // n, NF * (i + 1) // n):
            T = f / FPS; enc.stdin.write(frame(tmap(T) if tmap else T, surf).tobytes())
        enc.stdin.close(); enc.wait()
    else:
        n = int(os.environ.get('PARTS', 8))
        ps = [subprocess.Popen([sys.executable, script, '--part', str(i), str(n)]) for i in range(n)]
        for p in ps: p.wait()
        with open(build + '/parts/list.txt', 'w') as f:
            for i in range(n): f.write(f"file 'p{i}.mp4'\n")
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', build + '/parts/list.txt', '-c', 'copy', build + '/video.mp4'])
        got = subprocess.check_output(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v', '-show_entries', 'stream=nb_read_packets',
                                       '-of', 'csv=p=0', build + '/video.mp4']).decode().strip()
        print('frames', got, 'expected', NF)
