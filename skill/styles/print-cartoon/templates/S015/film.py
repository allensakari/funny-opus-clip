"""S015 你总排到慢的那队 — 16:9 1920×1080 60 fps, risograph-print flat 2D (skia).
Cast: round 'bean' shoppers whose eyes do the acting; YOU = the yellow one. Every queue move is snapped to the 120 BPM beat grid.
usage: python film.py [--still T ...] | [--part i n] | (no args: render all, 8 parts in parallel, concat → build/video.mp4)
Events (dings, steps, pops …) are collected in EV for score.py."""
import os, sys, math, random, subprocess
from contextlib import contextmanager
import numpy as np, skia
from timeline import *

ROOT = os.path.dirname(os.path.dirname(HERE))
V = bool(os.environ.get('VERT'))                       # VERT=1 → 9:16 1080×1920: same world, lanes in the middle band, overlays re-placed
W, H = (1080, 1920) if V else (1920, 1080)
VY = 85 if V else 0                                    # vertical: world drawn at ZV, shifted down (lanes fill the middle of the frame)
ZV = 1.25 if V else 1.0                                # vertical shows world x 0–864: the counter + ~5 people per lane
XIN = 950 if V else 2080                               # where walk-ins start (just off the right edge)
CUT = os.environ.get('CUT', '')                        # '90' = the ~90 s edit (timeline.SEG90): cuts + 2× spans over film time
WARP = os.environ.get('WARP', '')                      # 'qnyh' = laid onto the 《千年以后》 grid (Douyin: upload without BGM, attach the song there)
BUILD = HERE + ('/build/v' if V else '/build') + ('/qnyh' if WARP else '') + ('/c90' if CUT else '')
# 《千年以后》 grid (S006 用户录屏 build/ref_qnyh/song.wav, 0 s = 人声进入): 110.6444 BPM, half-bar 1.0846 s, drums at 16.87 s,
# beats run 0.54 beat late from ~93.6 s. Film half-bar (1 s at 120 BPM) ↔ song half-bar, film 16 s (race) ↔ drums.
HALF_Q = 2 * 60 / 110.6444


def warp(tf):
    """film time → song time"""
    return 16.87 + (tf - 16) * HALF_Q + .54 * 60 / 110.6444 * min(1, max(0, tf - 86.7))


_WT = np.linspace(0, DUR, 200001); _WS = np.array([warp(x) for x in _WT[::100]])
def unwarp(ts): return float(np.interp(ts, _WS, _WT[::100]))
FONTS = ROOT + '/assets/fonts/'
def _tf(n): return skia.Typeface.MakeFromFile(FONTS + n)
ZH_B, ZH_H, ZH_M = _tf('SourceHanSansCN-Bold.otf'), _tf('SourceHanSansCN-Heavy.otf'), _tf('SourceHanSansCN-Medium.otf')
ZH_T = _tf('SmileySans-Oblique.ttf')
EN_K, EN_B, EN_S = _tf('Nunito-Black.ttf'), _tf('Nunito-ExtraBold.ttf'), _tf('Nunito-SemiBold.ttf')


def hx(s): s = s.lstrip('#'); return tuple(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4))
PAPER, INK, CARD = hx('F2ECDF'), hx('2A2A3C'), hx('FFFCF4')
TOMATO, COBALT, TEAL, PINK, LAV, MINT, SKY = (hx(c) for c in ('E8553D', '3657C7', '1E9C88', 'EF95AE', '9784D6', '7CC9A8', '6FB3E0'))
YOU, GOLD, GREYD, SHELF = hx('F5C247'), hx('D9A441'), hx('CFC6B4'), hx('E4DCCB')
SHOP = [COBALT, TEAL, PINK, LAV, MINT, SKY, hx('C9A27A'), hx('5D7A6B'), hx('E58F6F')]
LY = [480, 700, 920]                                   # lane baselines (feet)

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

# ---------------------------------------------------------------- sound events for score.py
EV = []
def ev(t, kind, **kw): EV.append(dict(t=float(t), kind=kind, **kw))

# ---------------------------------------------------------------- drawing primitives
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


def counter(c, y, s=1., light=0., cashier=1., cash_dx=0., cash_col=INK, sign=0.):
    """the checkout at the left end of a lane (drawn in screen space, lane baseline y, scale s)"""
    c.save(); c.translate(0, y); c.scale(s, s)
    if cashier > .01:
        bean(c, 200 + cash_dx, -22, cash_col, .92, (1, 0), .3, a=cashier, tag=False)
    c.drawLine(140, -150, 140, -82, P(INK, 1, 5))
    c.drawCircle(140, -158, 13, P(mix(GREYD, TEAL, light), 1))
    if light > .05: c.drawCircle(140, -158, 13 + 16 * light, P(TEAL, .25 * light))
    riso_rrect(c, 120, -84, 160, 84, 10, COBALT, 1, 6)
    rrect(c, 120, -84, 160, 16, 6, P(INK, .25))
    rrect(c, 222, -126, 46, 34, 5, P(INK, 1)); rrect(c, 228, -121, 34, 22, 3, P(TEAL, .8))
    if sign > .01:
        sc = eback(sign)
        c.save(); c.translate(200, -105); c.rotate(-8); c.scale(sc, sc)
        riso_rrect(c, -95, -40, 190, 80, 10, TOMATO, 1, 5)
        text(c, '暂停收银', 0, -2, ZH_H, 34, CARD); text(c, 'BACK SOON', 0, 28, EN_K, 20, CARD)
        c.restore()
    c.restore()


def background(c):
    c.clear(skia.Color4f(*PAPER, 1))
    if V: return                                                 # vertical: the band above the lanes belongs to the captions
    c.save(); c.translate(0, VY); c.scale(ZV, ZV)
    for i in range(14):                                          # back shelves (soft)
        x = 60 + i * 136
        rrect(c, x, 238, 120, 110, 6, P(SHELF, 1))
        rr = random.Random(i)
        for row in range(3):
            for k in range(4):
                c.drawRect(skia.Rect.MakeXYWH(x + 8 + k * 28, 246 + row * 34, 22, 26), P(rr.choice(SHOP), .22))
    c.drawLine(0, 352, W, 352, P(INK, .10, 3))
    c.restore()


_rg = np.random.default_rng(7)
_g = _rg.integers(0, 255, (H, W), dtype=np.uint8)
GRAIN = np.zeros((H, W, 4), np.uint8); GRAIN[..., 0] = GRAIN[..., 1] = GRAIN[..., 2] = 40
GRAIN[..., 3] = (_rg.random((H, W)) ** 6 * 70).astype(np.uint8)
GRAIN_IMG = skia.Image.fromarray(GRAIN, colorType=skia.kRGBA_8888_ColorType)


# ---------------------------------------------------------------- the queue model
class Lane:
    """people stand in order; person i is served when everyone ahead has left. Departures snap to beats.
    person keys: col, svc | end (scripted), arrive (walk in from the right), skip (leaves without paying), nodraw, you, gaze, mood, brow"""
    X0, GAP = 340, 112

    def __init__(self, y, people, start, s=1., win=(0, DUR), quiet=False):
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


def world(c, z=1.2):
    """lane scenes are drawn a bit closer: scale about the left edge, y = 700 (vertical: no zoom, the width is the limit)"""
    if V: return
    c.translate(0, 700); c.scale(z, z); c.translate(0, -700)


def crowd(seed, n, **kw):
    r = random.Random(seed)
    return [{**dict(col=r.choice(SHOP), svc=r.choice([1., 1.5, 1.5, 2.]), ph=r.random() * 5), **kw} for _ in range(n)]


def flowing(seed, y, n0, t0, t1, every=2.0, s=1., start=None):
    """a lane that keeps moving: n0 people at start, one arrival every ~`every` s"""
    r = random.Random(seed)
    ppl = crowd(seed, n0)
    t = t0 + r.uniform(.3, 1.2)
    while t < t1 - .5:
        ppl += [dict(col=r.choice(SHOP), svc=r.choice([1., 1.5, 1.5, 2.]), ph=r.random() * 5, arrive=t)]
        t += every * r.uniform(.7, 1.3)
    return Lane(y, ppl, t0 + .5 if start is None else start, s, (t0, t1))


# ---------------------------------------------------------------- captions, receipt wipe, overlays
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


def _kept(a0, a1): return film2out(a1, side='prev') - film2out(a0, side='next')
CAPS_ON = [cp for cp in CAPS if not CUT or _kept(cp[0], cp[1]) >= 1.0]       # the cut drops captions whose span is gone


def captions(c, t):
    for a0, a1, zh, en in CAPS_ON:
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


def wipe(c, t):
    """chapter card: a brand-yellow panel slides in from the right (0.35 s), the title types in, it slides out to the left.
    The scene changes at t0 while the panel covers the frame (t0 − 0.5 … t0 + 0.55). #01 also carries the film title."""
    for t0, num, zh, en, _ in WIPES:
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
        first = num == '01'
        if first:                                                          # the film's title on the first card
            ts = 88 if V else 96
            lines = wrap(TITLE[0], ZH_T, ts, W - 140) if V else [TITLE[0]]
            yy = cy - 150 - (len(lines) - 1) * ts * .6
            for ln in lines: text(c, ln, cx, yy, ZH_T, ts, INK, ta, riso=5); yy += ts * 1.15
            text(c, TITLE[1], cx, yy - ts * .35, EN_B, 26 if V else 28, INK, ta * .6)
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


FS = 1.3 if V else 1.0                                                # text inside cards: bigger in vertical (cards are shown at ~0.8)


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


# ================================================================= scenes
R = random.Random(15)

# ---------- 0 · hook (0–8)
def _hook_lane(seed, y, ends, arrivals):
    r = random.Random(seed)
    ppl = [dict(col=r.choice(SHOP), ph=r.random() * 5, end=e) for e in ends]
    ppl += [dict(col=r.choice(SHOP), ph=r.random() * 5, arrive=a, svc=1.0) for a in arrivals]
    return Lane(y, ppl, 0, win=(0, 8))


# before the choice (2.4 s) the side lanes creep; once you pick B they pay on every beat
H_top = _hook_lane(1, LY[0], [1.5, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0], [2.2, 2.9, 3.6, 4.3, 5.2, 6.2])
def _hook_gaze(t):
    if t < 2.4: return ((0, -1), (0, 1))[int(t / .45) % 2]                 # walking in, can't decide
    if t < 4.0: return (-1, 0)
    return ((0, -1), (0, 1))[int(t / .9) % 2]                               # …and now both neighbours are moving


H_mid = Lane(LY[1], crowd(2, 1, end=999) + crowd(3, 2) + [dict(you=True, end=999, arrive=1.0, gaze=_hook_gaze,
             mood=lambda t: .4 - smooth(4.2, 4.8, t) * 1.5, brow=lambda t: smooth(4.6, 5.2, t))] + crowd(4, 1, arrive=3.4), 0, win=(0, 8))
for p in H_mid.P[1:3]: p['end'] = 999
H_mid.P[4]['end'] = 999
H_bot = _hook_lane(5, LY[2], [1.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.5], [2.4, 3.1, 3.8, 4.6, 5.6, 6.6])
for k in range(3): ev(.2 + .15 * k, 'pop')
for j in range(4): ev(.5 + j * BEAT, 'tick', n=200 + j * 60)
ev(2.4, 'pick'); ev(3.5, 'stamp'); ev(4.2, 'stamp')


def lane_tag(c, k, y, t0, t):
    u = (t - t0) / .35
    if u <= 0: return
    g = eback(u) * (1 + .12 * (t < 2.4 and math.fmod(t, BEAT) < .12))      # pulse on the beat while you choose
    picked = k == 1 and t >= 2.4
    g *= 1 + .25 * (1 - eout((t - 2.4) / .3)) * picked
    c.save(); c.translate(62, y - 52); c.scale(g, g)
    c.drawCircle(3, 3, 34, P(TOMATO, .5)); c.drawCircle(0, 0, 34, P(YOU if picked else INK, 1))
    text(c, 'ABC'[k], 0, 15, EN_K, 42, INK if picked else CARD)
    c.restore()


def sc_hook(c, t):
    k = 1 if V else lerp(1, 1.07, eio(t / 8))
    c.save(); world(c); c.translate(676, 640); c.scale(k, k); c.translate(-676, -640)
    for L in (H_top, H_mid, H_bot): L.draw_counter(c, t)
    items = []
    for L in (H_top, H_mid, H_bot): L.draw_people(t, items)
    draw_beans(c, t, items)
    for k in range(3): lane_tag(c, k, LY[k], .2 + .15 * k, t)
    ab = fade(t, 2.4, 4.4, .05, .4)                                          # your lane lights up when you pick it
    if ab > 0: rrect(c, 296, LY[1] - 140, 600, 160, 18, P(YOU, .22 * ab))
    xy = H_mid.screen(3, t)
    if xy: stamp(c, '又是我？！', xy[0] + (-60 if V else 200), xy[1] - (195 if V else 175), (t - 3.5) * (t < 7.4), TOMATO, -8, 44)
    c.restore()
    a = fade(t, 4.2, 7.6, .2, .3)
    if a > 0:
        with ov(c, (1250, 450, 500, 330), (540, 1395, 400)):
            big(c, '2/3', 1500, 640, 240, TOMATO, a, (t - 4.2) / .45)
            text(c, '排到更慢的队', 1500, 728, ZH_H, 44, TOMATO, a)


# ---------- 1 · 1/3 (8–34)
def race_lane(y, svcs, you=False, seed=0, off=0.):
    ppl = crowd(seed, len(svcs))
    for j, (p, s) in enumerate(zip(ppl, svcs)): p['svc'] = s; p['arrive'] = 8.3 + j * .4 + off
    last = ppl[-1]
    if you: last.update(you=True, mood=lambda t: -smooth(16.6, 17.2, t), brow=lambda t: smooth(16.8, 17.3, t))
    else: last['ring'] = True
    return Lane(y, ppl, 12.0, win=(8, 34))


R_lanes = [race_lane(LY[0], [1, 1, 1.5, 1], seed=11), race_lane(LY[1], [1.5, 1.5, 1, 1.5], True, 12, .13), race_lane(LY[2], [1, 2, 1.5, 1.5], seed=13, off=.26)]
HOP = [random.Random(31).randrange(3) for _ in range(12)]
for k in range(3): ev(18.0 + .4 * k, 'pop')
for j in range(6): ev(19.4 + j * BEAT, 'tick', n=j * 40)
ev(12.0, 'go'); ev(16.5, 'stamp'); ev(17.4, 'pop')
_fy = crowd(22, 3) + [dict(you=True, mood=-1, brow=1)] + crowd(23, 2)
for j, p in enumerate(_fy): p['end'] = {0: 31.5, 1: 33.5}.get(j, 999)
five = [flowing(20 + i, 420 + i * 130, 6, 29.8, 34, 1.8, s=.62, start=30.6) if i != 2 else Lane(420 + i * 130, _fy, 30.6, .62, (29.8, 34))
        for i in range(5)]
TALLY = S['tally1000']
ev(29.9, 'pop')


def tally_n(t): return int(1000 * clamp((t - 22.9) / 4.0) ** 2)


for n in range(20, 1001, 20):                                        # tally ticks (accelerating)
    ev(22.9 + 4.0 * math.sqrt(n / 1000), 'tick', n=n)


def sc_13(c, t):
    dim = 1 - .75 * smooth(22.6, 23.0, t) * (1 - smooth(29.6, 30.0, t))
    if t < 30.0:
        c.save(); world(c)
        for L in R_lanes: L.draw_counter(c, t)
        items = []
        for L in R_lanes: L.draw_people(t, items)
        draw_beans(c, t, items)
        ah = fade(t, 19.4, 22.5, .2, .3)
        if ah > 0:                                                         # a highlight hops between the lanes: each gets 1/3
            k = HOP[min(len(HOP) - 1, int(max(0, t - 19.4) / BEAT))]
            rrect(c, 300, LY[k] - 130, 560, 150, 18, P(YOU if k == 1 else GREYD, .3 * ah))
        for k in range(3):
            u = (t - 18.0 - .4 * k) / .35
            if u > 0 and t < 22.6:
                g = eback(u); ac = 1 - smooth(22.2, 22.6, t)
                c.save(); c.translate(560, LY[k] - 50); c.scale(g, g)
                riso_rrect(c, -70, -38, 140, 66, 14, YOU if k == 1 else CARD, ac, 5)
                text(c, '1/3', 0, 14, EN_K, 40, INK, ac)
                c.restore()
        c.restore()
        if 11.6 < t < 12.6:
            with ov(c, (880, 330, 200, 140), (540, 1350, 1000)): big(c, 'GO!', 980, 400, 90, TOMATO, fade(t, 11.6, 12.6, .1, .3), (t - 11.6) / .3)
        stamp(c, '最快！', 640, LY[0] - 40, (t - 16.5) * (t < 17.9), TOMATO)
        if dim < 1:
            with ov(c): c.drawRect(skia.Rect.MakeWH(W, H), P(PAPER, (1 - dim)))
        a = fade(t, 17.4, 22.6, .2, .35)
        with ov(c, (1060, 450, 400, 380), (540, 1330, 1000)):
            big(c, '1/3', 1260, 700, 300, YOU, a, (t - 17.4) / .45)
            text(c, f"模拟 10 万次：{S['p_fastest_3']:.1%}", 1260, 790, ZH_M, 30, INK, a * .75)
    if 22.5 < t < 30.2:                                                  # 1000 trips
      with ov(c, (330, 260, 1260, 700), (540, 900, 1040)):
        a = fade(t, 22.6, 30.0, .35, .35)
        card(c, 330, 260, 1260, 700, a)
        n = tally_n(t); red = smooth(26.4, 27.0, t)
        wins = sum(TALLY[:n])
        for k in range(n):
            col = YOU if TALLY[k] else mix(GREYD, TOMATO, red)
            c.drawCircle(420 + (k % 50) * 22.4, 340 + (k // 50) * 22, 8, P(col, a))
        text(c, f'第 {n:,} 次', 420, 860, ZH_B, 36 * FS, INK, a, 'l')
        text(c, '你这队最快', 1080, 860, ZH_B, 36 * FS, INK, a, 'r')
        text(c, f'{wins / max(n, 1):.1%}', 1500, 868, EN_K, 64 * FS, mix(INK, hx('B98A12'), 1), a, 'r')
        if red > 0: text(c, f'别的队更快  {1 - wins / max(n, 1):.1%}', 1500, 928, ZH_B, 30 * FS, TOMATO, a * red, 'r')
    if t > 29.8:
        a = smooth(29.9, 30.4, t)
        for L in five: L.draw_counter(c, t)
        items = []
        for L in five: L.draw_people(t, items)
        c.saveLayer(paint=P(INK, a)) if a < 1 else c.save()
        draw_beans(c, t, items)
        c.restore()
        with ov(c, (1300, 430, 400, 330), (540, 1420, 330)):
            big(c, '1/5', 1500, 640, 240, YOU, a, (t - 29.9) / .45)
            text(c, f"模拟：{S['p_fastest_5']:.1%}", 1500, 720, ZH_M, 30, INK, a * .75)


# ---------- 2 · one person, one stuck line (34–58)
C_top = flowing(31, LY[0], 4, 34, 46, 1.5)
C_bot = flowing(32, LY[2], 4, 34, 46, 1.7)
COIN = dict(col=PINK, end=999, coin=True)
C_mid = Lane(LY[1], [COIN] + crowd(33, 1, end=999) + [dict(you=True, end=999, gaze=lambda t: (-1, 0) if math.fmod(t, 4) < 2 else (0, -1),
             mood=lambda t: -smooth(37, 38, t) * 1.1, brow=lambda t: smooth(38, 39, t))] +
             [dict(col=c_, end=999, arrive=a_, ph=a_) for c_, a_ in ((TEAL, 36.6), (LAV, 39.0), (SKY, 41.2), (MINT, 43.0))], 34, win=(34, 46))
Q100 = SEP['q100']
for k in range(0, 100, 4): ev(45.0 + k * .025 + .2, 'bar', k=k)
ev(49.6, 'pop'); ev(53.6, 'pop'); ev(53.9, 'whoosh'); ev(40.0, 'pop'); ev(41.5, 'pop'); ev(47.6, 'laser')
for b in range(int(34.5 / BEAT), int(44.6 / BEAT)):
    if b % 2 == 0: ev(b * BEAT + .25, 'coin')


def coin_bubble(c, x, y, t, t0, a=1., cyc=False):
    """speech card over the slow customer: coins stacking (or a return / a price check) + a stopwatch running"""
    if a <= .003: return
    riso_rrect(c, x - 110, y - 120, 220, 96, 18, CARD, a, 6)
    tri = skia.Path(); tri.moveTo(x - 14, y - 26); tri.lineTo(x + 14, y - 26); tri.lineTo(x, y - 6); tri.close(); c.drawPath(tri, P(CARD, a))
    mode = 'coin' if not cyc or t < 40.0 or t >= 43.0 else 'ret' if t < 41.5 else 'price'
    if mode != 'coin':
        g = eback((t - (40.0 if mode == 'ret' else 41.5)) / .3)
        c.save(); c.translate(x - 52, y - 72); c.scale(g, g)
        if mode == 'ret':
            rrect(c, -36, -26, 72, 52, 6, P(hx('C9A27A'), a)); c.drawLine(-36, -8, 36, -8, P(INK, a * .5, 3))
            text(c, '退货', 0, 20, ZH_H, 22, INK, a)
        else:
            pth = skia.Path(); pth.moveTo(-38, -22); pth.lineTo(22, -22); pth.lineTo(40, 0); pth.lineTo(22, 22); pth.lineTo(-38, 22); pth.close()
            c.drawPath(pth, P(TOMATO, a)); text(c, '¥?', -6, 12, EN_K, 30, CARD, a)
        c.restore()
    n = int(clamp((t - t0) / 1.0, 0, 7)) if mode == 'coin' else 0
    for k in range(n):
        c.drawOval(skia.Rect.MakeXYWH(x - 90 + (k % 4) * 8, y - 52 - k * 7, 44, 14), P(GOLD, a)); c.drawOval(skia.Rect.MakeXYWH(x - 90 + (k % 4) * 8, y - 52 - k * 7, 44, 14), P(INK, a * .6, 2))
    el = (t - t0) * 12
    cx, cy = x + 52, y - 72
    c.drawCircle(cx, cy, 30, P(CARD, a)); c.drawCircle(cx, cy, 30, P(INK, a, 4))
    th = el / 60 * math.tau
    c.drawLine(cx, cy, cx + math.sin(th) * 22, cy - math.cos(th) * 22, P(TOMATO, a, 4))
    text(c, f'{int(el // 60)}:{int(el % 60):02d}', cx, cy + 58, EN_K, 26, TOMATO, a)


def chart_geom(k):
    return 230 + k * 12, 900                                                # left x of bar k, baseline


PX_MIN = 22.5                                                                # pixels per minute


def sc_stuck(c, t):
    a_l = 1 - smooth(44.6, 45.4, t)
    if a_l > 0:
        c.save(); c.translate(0, 60 * smooth(44.6, 45.4, t)); world(c)
        zz = 1 + .32 * eio((t - 39.6) / 1.4)                                # push in on the hold-up
        c.translate(300, 430); c.scale(zz, zz); c.translate(-300, -430)
        for L in (C_top, C_mid, C_bot): L.draw_counter(c, t)
        items = []
        for L in (C_top, C_mid, C_bot): L.draw_people(t, items)
        if a_l < 1: c.saveLayer(paint=P(INK, a_l))
        else: c.save()
        draw_beans(c, t, items)
        x, y, _ = C_mid.screen(0, t)
        coin_bubble(c, x, y - 112, t, 35.0, fade(t, 35.4, 46, .3, .3), True)
        c.restore(); c.restore()
    if t > 44.8:
      with ov(c):
        G = CH_V if V else CH_H
        x0, pitch, bw, base, pxm = G['x0'], G['pitch'], G['bw'], G['base'], G['pxm']
        def bx_(k): return x0 + k * pitch
        a = smooth(44.8, 45.3, t)
        c.drawLine(G['xl'], base, G['xr'], base, P(INK, a, 3))
        for m in (0, 5, 10, 15, 20):
            yy = base - m * pxm
            c.drawLine(G['xl'], yy, G['xr'], yy, P(INK, a * .12, 2))
            text(c, f'{m}', G['xl'] - 14, yy + G['ax'] * .36, EN_B, G['ax'], INK, a * .6, 'r')
        text(c, '分钟', G['xl'] - 14, base - 21.5 * pxm - 14, ZH_M, G['ax'] * .9, INK, a * .6, 'r' if not V else 'l')
        text(c, '100 次排队，按等待时间从短到长排', G['nx'], G['ny'], ZH_B if V else ZH_M, G['n1'], INK, a * .75)
        text(c, '模拟：3 个收银台 · 90% 时间在忙 · 每人选人最少的队', G['nx'], G['ny'] + G['n1'] * 1.4, ZH_M, G['n2'], INK, a * .5)
        red = smooth(49.6, 50.1, t); fly = t > 53.8
        ux, uy = G['you']; bxc, byc, brx, bry = G['bub']
        bubble(c, bxc, byc, brx, bry, smooth(53.6, 53.9, t), (ux - 20, uy - 140))
        dimrest = 1 - .65 * smooth(53.8, 54.6, t)
        lx = lerp(G['xl'], bx_(100), eio((t - 47.6) / 2.0)) if 47.6 < t < 49.8 else None      # checkout-scanner laser sweeps the bars
        for k in range(100):
            g = eout((t - 45.0 - k * .025) / .45)
            if g <= 0: continue
            x = bx_(k); h = Q100[k] * pxm * g
            tail = k >= 90
            hit = lx is not None and abs(x - lx) < pitch * 3
            col = mix(COBALT, TOMATO, red) if tail else mix(SKY, COBALT, .2)
            if hit: col = TOMATO
            if tail and fly:
                j = k - 90
                u = eio((t - 53.8 - j * .07) / .9)
                tx, ty = bxc + (j % 5) * 24 - 52, byc + (j // 5) * 58 - 10
                hh = h * lerp(1, .1, u)
                X, Y = lerp(x, tx, u), lerp(base, ty, u) - math.sin(u * math.pi) * 160
                c.drawRect(skia.Rect.MakeXYWH(X, Y - hh, bw, hh), P(col, a))
            else:
                c.drawRect(skia.Rect.MakeXYWH(x, base - h, bw, h), P(col, a * (dimrest if not tail else 1)))
        if lx is not None:
            c.drawLine(lx, base - 22 * pxm, lx, base + 10, P(TOMATO, .9, 4)); c.drawLine(lx, base - 22 * pxm, lx, base + 10, P(TOMATO, .25, 18))
        if t > 49.6:
            am = fade(t, 49.6, 58, .3, .3) * dimrest
            xm = bx_(50) + bw / 2
            ytop = G['medy'] - G['lab'] * .9
            for yy in np.arange(ytop + G['lab'] * 1.3, base, 16): c.drawLine(xm, yy, xm, yy + 8, P(INK, am, 3))
            text(c, f"一般 {SEP['p50']:.1f} 分钟", xm + 14, G['medy'], ZH_B, G['lab'], INK, am, 'l')
            at = fade(t, 49.9, 58, .3, .3) * (1 - smooth(53.8, 54.2, t))
            x0_, x1_ = bx_(90), bx_(99) + bw
            by_ = G['brk']
            for p_ in ((x0_, by_, x1_, by_), (x0_, by_, x0_, by_ + 18), (x1_, by_, x1_, by_ + 18)): c.drawLine(*p_, P(TOMATO, at, 4))
            v = SEP['tail10_mean'] * eout((t - 49.9) / .9)
            tx_, al_ = ((x0_ + x1_) / 2 - 60, 'c') if not V else (x1_, 'r')
            text(c, "最倒霉的 10%", tx_, by_ - G['lab'] * 1.5, ZH_B, G['lab'], TOMATO, at, al_)
            text(c, f"平均 {v:.1f} 分钟", tx_, by_ - G['lab'] * .4, ZH_B, G['lab'], TOMATO, at, al_)
        ay = smooth(45.0, 45.6, t)                                          # YOU watching the chart, then remembering the tail
        bean(c, ux, uy, YOU, 1, (-1, -.3) if t < 53.8 else (-.4, -1), lerp(0, -1.1, smooth(50, 51, t)), smooth(51, 52, t), ay, True,
             1.2 * math.sin(t * 2.2), math.fmod(t, 3.7) < .11)


CH_H = dict(x0=230, pitch=12, bw=9, base=900, pxm=22.5, xl=220, xr=1440, ax=24, nx=830, ny=950, n1=26, n2=20,
            you=(1700, 930), bub=(1560, 600, 150, 110), medy=580, lab=30, brk=360)
CH_V = dict(x0=96, pitch=9.1, bw=7, base=1170, pxm=24, xl=86, xr=1010, ax=32, nx=540, ny=1236, n1=36, n2=26,
            you=(860, 1500), bub=(600, 1410, 160, 92), medy=760, lab=42, brk=640)


# ---------- 3 · switching (58–72)
YOU_SW = dict(you=True, end=999, nodraw=True)
S_mid = Lane(LY[1], [dict(col=PINK, end=62.5, coin=True), dict(col=TEAL, end=63.5), dict(you=True, skip=True, end=61.0, nodraw=True),
                     dict(col=LAV, end=64.5), dict(col=SKY, end=65.5), dict(col=MINT, end=66.5),
                     dict(col=COBALT, arrive=65.2, svc=1.5), dict(col=PINK, arrive=67.0, svc=2.0)], 58, win=(58, 72))
S_bot = Lane(LY[2], [dict(col=COBALT, end=60.0), dict(col=hx('C9A27A'), end=70.5), dict(you=True, end=999, arrive=61.0, nodraw=True)], 58, win=(58, 72))
S_top = flowing(43, LY[0], 4, 58, 72, 1.6)
ev(61.0, 'boing'); ev(63.6, 'womp'); ev(62.5, 'pop')
for k in range(4): ev(62.5 + k, 'ding2')


def sc_switch(c, t):
    c.save(); world(c); _sc_switch(c, t); c.restore()


def _sc_switch(c, t):
    S_top.draw_counter(c, t); S_mid.draw_counter(c, t)
    away = smooth(63.5, 64.3, t) * (1 - smooth(69.0, 69.8, t))
    newc = t > 69.0
    S_bot.draw_counter(c, t, cash_dx=-260 * away, cashier=1 - .999 * away if not newc else 1, cash_col=TEAL if newc else INK,
                       sign=clamp((t - 63.7) / .4) * (1 - smooth(69.4, 69.8, t)))
    items = []
    for L in (S_top, S_mid, S_bot): L.draw_people(t, items)
    draw_beans(c, t, items)
    if t < 62.6:
        x, y, _ = S_mid.screen(0, t)
        coin_bubble(c, x, y - 112, t, 52.0, fade(t, 58.3, 62.6, .3, .3))
    # YOU: in the middle lane until 61.0, hops to the bottom lane
    xa = Lane.X0 + Lane.GAP * 2
    xb = Lane.X0 + Lane.GAP * S_bot.slot(2, max(t, 61.9))
    u = eio((t - 61.0) / .8)
    x, y = lerp(xa, xb, u), lerp(LY[1], LY[2], u) - math.sin(u * math.pi) * 150
    gz = (0, 1) if t < 61 else (0, -1) if 62.6 < t < 66.4 else (-1, 0)
    mood = -1.1 if t < 61 else .7 if t < 62.6 else -1.2
    brow = 1 if t < 60.6 else 0 if t < 62.6 else 1.2
    bean(c, x, y, YOU, 1, gz, mood, brow, 1, True, 1.2 * math.sin(t * 2.2), math.fmod(t, 3.7) < .11)


# ---------- 4 · one line (72–100)
D_top = Lane(LY[0], [dict(col=SKY, end=75.5), dict(col=TOMATO, arrive=75.0, svc=2.0, late=True)] + crowd(51, 1, arrive=79.0, svc=4.0), 72, win=(72, 81))
D_mid = Lane(LY[1], [dict(col=MINT, end=77.0), dict(col=LAV, end=81.0), dict(you=True, svc=1.5, gaze=lambda t: (0, -1) if 75.5 < t < 80.5 else (-1, 0),
             mood=lambda t: -smooth(77.5, 78.2, t) * 1.1, brow=lambda t: smooth(77.8, 78.4, t))] + crowd(52, 1, svc=1.5), 72, win=(72, 81))
D_bot = Lane(LY[2], crowd(53, 3) + crowd(54, 1, arrive=76.5), 72.5, win=(72, 81))
ev(75.2, 'pop'); ev(77.6, 'pop')
for k in range(10): ev(76.9 + k * .08, 'tick', n=k)

T_M, T_S = 81.0, 83.4                                                # morph start / snake running
SNAKE_PTS = [(640, 560), (1700, 560), (1700, 760), (760, 760), (760, 960), (1940, 960)]
BELTS = ((660, 600, 1640), (860, 820, 1890))
if V:                                                                # five short rows to the right of the counters
    SNAKE_PTS = [(470, 560), (820, 560), (820, 685), (500, 685), (500, 810), (820, 810), (820, 935), (980, 935)]
    BELTS = ((622, 450, 760), (747, 560, 870), (872, 450, 760))
TAIL_Y = SNAKE_PTS[-1][1]
SG = 104


def path_pt(d):
    for (x0, y0), (x1, y1) in zip(SNAKE_PTS, SNAKE_PTS[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if d <= L: return x0 + (x1 - x0) * d / L, y0 + (y1 - y0) * d / L
        d -= L
    return SNAKE_PTS[-1]


def _build_snake():
    inserv, queue = [], []
    for k, L in enumerate((D_top, D_mid, D_bot)):
        for i, p in enumerate(L.P):
            r = L.screen(i, T_M)
            if r is None or T_M >= p['end']: continue
            if L.slot(i, T_M) < .02 and p['start'] <= T_M: inserv.append(dict(p, k=k, x=r[0], y=r[1]))
            else: queue.append(dict(p, fx=r[0], fy=r[1], arrive=None))
    queue.sort(key=lambda q: (q['fx'], q['fy']))
    rr = random.Random(77)
    queue += [dict(col=rr.choice(SHOP), svc=rr.choice([1.5, 2., 2.5]), ph=rr.random() * 5, fx=XIN + 20 + j * 70, fy=TAIL_Y, arrive=None) for j in range(8 if V else 11)]
    late = []
    t = 84.4
    while t < 99:
        late.append(dict(col=rr.choice(SHOP), svc=rr.choice([1.5, 2., 2.5]), ph=rr.random() * 5, arrive=t)); t += rr.uniform(1.0, 1.5) if V else rr.uniform(.8, 1.3)
    Q = queue + late
    yi = next(i for i, q in enumerate(Q) if q.get('you'))           # YOU waits a little in the snake, then glides past the slow customer
    Q.insert(6, Q.pop(yi))
    for i, q in enumerate(Q):                                                 # the slow customer of this act
        if i == (5 if V else 2): q.update(svc=9.0, coin=True, col=PINK)          # vertical: keep the slow one off the top counter (captions)
        if q.get('you'): q.update(gaze=(-1, 0), mood=lambda t: .3 + .5 * smooth(90, 91, t), brow=0, svc=2.0)
    free = [T_S] * 3
    for s in inserv:
        s['end'] = max(s['end'], T_S + 1.0); free[s['k']] = s['end']
    prev = T_S - BEAT
    for q in Q:
        ready = T_S if q.get('arrive') is None else q['arrive'] + 2.2
        k = min(range(3), key=lambda k: free[k])
        st = snap(max(free[k], ready, prev + BEAT))
        q['start'], q['k'] = st, k
        q['end'] = snap(st + .8 + q['svc'])
        free[k] = q['end']; prev = st
    for s in inserv: ev(s['end'], 'ding', lane=LY[s['k']])
    for q in Q:
        if q['end'] < 100: ev(q['end'], 'ding', lane=LY[q['k']])
        if q['start'] < 100: ev(q['start'], 'next', k=q['k'])
        if q.get('arrive') and q['arrive'] < 99: ev(q['arrive'] + 1.4, 'step')
    return inserv, Q


SN_IN, SN_Q = _build_snake()
ev(T_M + .1, 'whoosh'); ev(96.6, 'stamp')


def snake_pos(i, q, t):
    """(x, y, alpha, moving) in screen space"""
    if q.get('arrive') is not None and t < q['arrive']: return None
    if t >= q['end']:
        u = (t - q['end']) / .9
        if u >= 1: return None
        return Lane.X0 - 110 * eio(u), LY[q['k']] - 70 * eio(u), 1 - smooth(.15, .8, u), True
    if t >= q['start']:
        u = eio((t - q['start']) / .8)
        hx_, hy = path_pt(0)
        return lerp(hx_, Lane.X0, u), lerp(hy, LY[q['k']], u), 1., u < 1
    slot = i - sum(eio((t - p['start']) / .55) for p in SN_Q[:i])
    x, y = path_pt(slot * SG)
    if q.get('arrive') is not None:
        u = (t - q['arrive']) / 2.0
        if u < 1: x, y = lerp(XIN, x, eout(u)), lerp(TAIL_Y, y, eout(u))
    if t < T_S and q.get('fx') is not None:
        u = eio((t - T_M - min(i, 6) * .07 - max(0, i - 6) * .06) / 1.6)
        return lerp(q['fx'], x, u), lerp(q['fy'], y, u) - math.sin(u * math.pi) * 40, 1., 0 < u < 1
    return x, y, 1., False


def stanchions(c, a):
    for y, x0, x1 in BELTS:
        c.drawLine(x0, y - 52, x1, y - 52, P(TOMATO, a * .85, 7))
        for x in np.linspace(x0, x1, 4 if V else 6):
            c.drawLine(x, y - 60, x, y, P(INK, a, 6)); c.drawOval(skia.Rect.MakeXYWH(x - 16, y - 5, 32, 10), P(INK, a))


def sc_one(c, t):
    if t < T_M:
        c.save(); world(c, lerp(1.2, 1, eio((t - 79.6) / 1.4)))
        for L in (D_top, D_mid, D_bot): L.draw_counter(c, t)
        items = []
        for L in (D_top, D_mid, D_bot): L.draw_people(t, items)
        draw_beans(c, t, items)
        late = D_top.screen(1, t)
        if late and t < T_M:
            x, y, _ = late
            al = fade(t, 75.2, T_M, .3, .3)
            rrect(c, x - 52, y - 170, 104, 36, 10, P(TOMATO, al)); text(c, '后来的', x, y - 142, ZH_B, 24, CARD, al)
            if 77.6 < t < T_M:
                ab = fade(t, 77.6, T_M, .3, .3)
                yx, yy, _ = D_mid.screen(2, t)
                if V: text(c, '比你晚到，却比你先走', yx - 40, yy + 66, ZH_B, 34, TOMATO, ab, 'l')
                else: text(c, '比你晚到，却比你先走', yx + 160, yy - 130, ZH_B, 30, TOMATO, ab, 'l')
                for k in range(8):
                    u0, u1 = k / 8, (k + .5) / 8
                    c.drawLine(lerp(yx + 30, x + 40, u0), lerp(yy - 110, y - 60, u0), lerp(yx + 30, x + 40, u1), lerp(yy - 110, y - 60, u1), P(TOMATO, ab, 4))
        c.restore()
        ai = fade(t, 76.8, T_M + .3, .3, .3)                          # 10 people, 4 overtaken
        if ai > 0:
          with ov(c):
            sx, sp, yb, sc_ = (126, 92, 1400, .62) if V else (700, 52, 1050, .38)
            for k in range(10):
                g = eback((t - 76.9 - k * .08) / .3) if t > 76.9 + k * .08 else 0
                if g > 0: bean(c, sx + k * sp, yb, TOMATO if k < 4 else GREYD, sc_ * g, (-1, 0), 0, a=ai, tag=False)
            if V: text(c, f"{SEP['overtaken_frac']:.1%} 的人被插到前面", 540, 1490, ZH_H, 46, TOMATO, ai)
            else: text(c, f"{SEP['overtaken_frac']:.1%}  被插到前面", 1240, 1040, ZH_B, 30, TOMATO, ai, 'l')
    if t >= T_M:
        a = smooth(T_M, T_M + .6, t)
        stanchions(c, a)
        for k in range(3):
            busy = any(s['k'] == k and t < s['end'] for s in SN_IN) or any(q['k'] == k and q['start'] + .8 <= t < q['end'] for q in SN_Q)
            nxt = any(q['k'] == k and q['start'] <= t < q['start'] + .5 for q in SN_Q)
            light = 1 if nxt else (.55 + .45 * (math.fmod(t, BEAT) < .18) if busy else 0)
            counter(c, LY[k], 1, light)
        items = []
        for s in SN_IN:
            if t < s['end'] + .9:
                u = (t - s['end']) / .9
                x, y, al = (Lane.X0, LY[s['k']], 1.) if u < 0 else (Lane.X0 - 110 * eio(u), LY[s['k']] - 70 * eio(u), 1 - smooth(.15, .8, u))
                items.append((y, x, s, al, u >= 0))
        for i, q in enumerate(SN_Q):
            r = snake_pos(i, q, t)
            if r: items.append((r[1], r[0], q, r[2], r[3]))
        items.sort(key=lambda it: (it[0], -it[1]))
        for y, x, q, al, mv in items:
            bob = abs(math.sin(t * 13)) * 7 if mv else 1.2 * math.sin(t * 2.2 + q['ph'])
            bean(c, x, y, YOU if q.get('you') else q['col'], 1, val(q.get('gaze', (-1, 0)), t), val(q.get('mood', .2), t), 0,
                 al * (a if t < T_M + .6 and q.get('fx') is None and q.get('arrive') is None else 1), q.get('you', False), bob, math.fmod(t + q['ph'], 3.7) < .11)
        for q in SN_Q:
            if q.get('coin') and q['start'] + .8 <= t < q['end'] and t < 93.2:
                coin_bubble(c, Lane.X0, LY[q['k']] - 112, t, q['start'] + .8, fade(t, q['start'] + .8, min(q['end'], 93.2), .3, .3))
        if 84.6 < t < 89.4:
            ah = fade(t, 84.6, 89.4, .3, .3)
            text(c, '下一位 →', 560, 470, ZH_B, 30, TEAL, ah, 'r')
    if t > 92.8:                                                            # the numbers
      a = fade(t, 93.0, 99.8, .4, .4)
      with ov(c): c.drawRect(skia.Rect.MakeWH(W, H), P(PAPER, a * .6))
      with ov(c, (330, 250, 1260, 680), (540, 900, 1040)):
        card(c, 330, 250, 1260, 680, a)
        text(c, '分开排', 1130, 340, ZH_B, 32 * FS, INK, a * .6); text(c, '只排一队', 1420, 340, ZH_B, 32 * FS, TEAL, a)
        rows = [('被比自己晚到的人超过', f"{SEP['overtaken_frac']:.1%}", '0%', 93.4),
                ('平均等待（分钟）', f"{SEP['mean']:.1f}", f"{SNK['mean']:.1f}", 94.4),
                ('最倒霉的 1%（分钟）', f"{SEP['p99']:.1f}", f"{SNK['p99']:.1f}", 95.4)]
        for j, (lab, v1, v2, t0) in enumerate(rows):
            ar = a * smooth(t0, t0 + .35, t); y = 470 + j * 130
            emph = 1 - .55 * smooth(96.6, 97.0, t) if j else 1                # the row that matters stays lit
            text(c, lab if not V else lab.replace('被比自己晚到的人超过', '被晚到的人超过'), 420, y, ZH_B, 40 * FS, INK, ar * emph, 'l')
            big(c, v1, 1130, y + 4, (52 if j == 0 else 42) * FS, INK if j else TOMATO, ar * (.6 if j else 1) * emph, (t - t0) / .4, EN_K)
            big(c, v2, 1420, y + 4, (52 if j == 0 else 42) * FS, TEAL, ar * emph, (t - t0 - .25) / .4, EN_K)
            if j < 2: c.drawLine(420, y + 50, 1500, y + 50, P(INK, ar * .12, 2))
        if V:
            text(c, f"模拟：3 个收银台 · 90% 繁忙 · {S['params']['customers'] // 10000} 万名顾客", 960, 846, ZH_M, 30, INK, a * .6)
            text(c, '银行柜台、机场安检，大多这样排', 960, 890, ZH_M, 30, INK, a * .6)
        else:
            text(c, f"模拟：3 个收银台 · 90% 时间在忙 · {S['params']['customers'] // 10000} 万名顾客 · 平均每人结账 1 分钟", 960, 860, ZH_M, 22, INK, a * .5)
            text(c, '银行柜台、机场安检，大多就是这么排的', 960, 896, ZH_M, 22, INK, a * .5)
        stamp(c, '没人插队', 1400, 700, (t - 96.6) * (t < 99.8), TEAL, -8, 52 * FS)


# ---------- 5 · everyone is watching (100–121)
E_lanes = []
for k, y in enumerate(LY):
    ppl = crowd(60 + k, 8)
    for j, p in enumerate(ppl): p['end'] = 999 if j else 117.0          # all three fronts pay on the same beat
    E_lanes.append(Lane(y, ppl, 100, quiet=True))
YOU_E = E_lanes[1].P[2]; YOU_E.update(you=True)
NB = E_lanes[0].P[2]; NB.update(col=TEAL)
THINK = []                                                                 # 2/3 of everyone else get a thought bubble
_rt = random.Random(5)
for k, L in enumerate(E_lanes):
    for j, p in enumerate(L.P):
        if p is YOU_E: continue
        p['bt'] = 106.8 + _rt.random() * 1.8
for L in E_lanes:
    cand = [p for p in L.P if p is not YOU_E and p['end'] > 120]
    _rt.shuffle(cand)
    for p in cand[:5 if L is not E_lanes[1] else 6]: THINK.append(p)
for p in THINK: ev(p['bt'], 'pop')
ev(113.4, 'pop2'); ev(113.2, 'theme'); ev(117.0, 'step_all'); ev(121.0, 'chime'); ev(118.0, 'pop'); ev(118.25, 'pop'); ev(109.3, 'stamp')


EG = 104 if V else 172                                                     # wider spacing in the finale (room for the bubbles)


def e_gaze(lane_k, p, t):
    if p is YOU_E: return (0, -1) if t < 114.6 else (0, -1)
    if p is NB: return (-1, 0) if t < 104.7 else (0, 1)
    if t < p.get('bt', 106) - .6 or t > 113.2 + p['ph'] * .3: return (-1, 0)
    dart = .55 * (1 if int((t + p['ph']) / 1.1) % 2 else -1)              # eyes keep darting along the other line
    if lane_k == 0: return (dart, 1)
    if lane_k == 2: return (dart, -1)
    return (dart, -1) if int((t + p['ph']) / 1.7) % 2 else (dart, 1)


def sc_end(c, t):
    u = eio((t - 104.6) / 2.8)
    if V: z, fx, fy, cx, cy = lerp(1.9, 1.0, u), lerp(Lane.X0 + 2 * EG, 540, u), lerp(640, 650, u), 540, 980
    else: z, fx, fy, cx, cy = lerp(1.7, 1.0, u), lerp(Lane.X0 + 2 * EG, W / 2, u), lerp(560, H / 2 + 60, u), W / 2, H / 2 + 60
    c.save(); c.resetMatrix(); c.translate(cx, cy); c.scale(z, z); c.translate(-fx, -fy)
    for L in E_lanes: L.draw_counter(c, t)
    items = []
    for k, L in enumerate(E_lanes):
        for j, p in enumerate(L.P):
            if p['end'] < 999 and t >= p['end']:
                u = (t - p['end']) / .9
                if u < 1: items.append((L.y, k, p, Lane.X0 - 110 * eio(u), 1 - smooth(.15, .8, u), True))
                continue
            sl = L.slot(j, t)
            items.append((L.y, k, p, Lane.X0 + EG * sl, 1., any(0 < t - q['end'] < .55 for q in L.P[:j])))
    items.sort(key=lambda it: (it[0], -it[3]))
    for y, k, p, x, al, mv in items:
        bob = abs(math.sin(t * 13)) * 7 if mv else 1.2 * math.sin(t * 2.2 + p['ph'])
        if p is YOU_E: g, mood, brow = ((0, -1), lerp(-.9, 1, smooth(113.6, 114.2, t)), lerp(.8, 0, smooth(113.2, 113.8, t)))
        elif p is NB: g, mood, brow = (e_gaze(k, p, t), lerp(-.6, 1, smooth(113.8, 114.4, t)), 0)
        else: g, mood, brow = (e_gaze(k, p, t), lerp(-.5 if t > p.get('bt', 200) else 0, .9, smooth(114.4 + p['ph'] * .2, 115.0 + p['ph'] * .2, t)), 0)
        bean(c, x, y, YOU if p is YOU_E else p['col'], 1, g, mood, brow, al, p is YOU_E, bob, math.fmod(t + p['ph'], 3.7) < .11, tag=t < 104.6 or t > 107)
    for y, k, p, x, al, mv in items:
        if p in THINK and t > p['bt']:
            u = clamp((t - p['bt']) / .35); out = smooth(113.0 + p['ph'] * .08, 113.4 + p['ph'] * .08, t)
            a = clamp(u * 3) * (1 - out)
            if a <= 0: continue
            k_ = eback(u) * (1 - out * .4)
            bx, by = x + 46, y - 170
            if V: by -= 44 * (E_lanes[k].P.index(p) % 2); k_ *= .78
            c.save(); c.translate(bx, by); c.scale(k_, k_); c.rotate(4 * math.sin(t * 3.1 + p['ph'] * 2))
            bubble(c, 0, 0, 68, 38, a, (-34, 56))
            text(c, '那队更快…', 0, 8, ZH_B, 22, INK, a)
            c.restore()
    c.restore()
    a2 = fade(t, 109.3, 113.0, .25, .3)                                       # 2/3
    if a2 > 0:
        with ov(c):
            if V: big(c, '2/3', 540, 1420, 200, TOMATO, a2, (t - 109.3) / .45); text(c, '觉得别人那队更快', 540, 1500, ZH_H, 44, TOMATO, a2)
            else: big(c, '2/3', 1765, 640, 150, TOMATO, a2, (t - 109.3) / .45); text(c, '觉得别人更快', 1765, 700, ZH_H, 30, TOMATO, a2)
    th = THEME
    if th[0] - .1 < t < 121.6:                                                # the thesis card, then the vote
        with ov(c): c.drawRect(skia.Rect.MakeWH(W, H), P(PAPER, .9 * smooth(th[0], th[0] + .35, t)))
    if th[0] < t < th[1] + .3:
        a = fade(t, th[0], th[1], .3, .35)
        with ov(c):
            size = 100 if V else 96
            lines = ['你不是运气差，', '只是总盯着', '比你快的那一队。'] if V else th[2]
            y0 = H / 2 - (230 if V else 110)
            for li, line in enumerate(lines):
                t0 = th[0] + .15 + li * .55                               # each line types in, one character per 40 ms
                n = int(clamp((t - t0) / .04, 0, len(line)))
                f = skia.Font(ZH_T, size); full = f.measureText(line)
                scale = min(1, (W - 120) / full)
                c.save(); c.translate(W / 2, y0 + li * size * 1.35 * scale); c.scale(scale, scale)
                x = -full / 2
                for ch in line[:n]:
                    w_ = f.measureText(ch)
                    col = TOMATO if '比你快' in line and line.index('比') <= line[:n].rfind(ch) and ch in '比你快的那一队' else INK
                    c.drawString(ch, x + 5, 4, f, P(mix(col, INK, .35), a * .45)); c.drawString(ch, x, 0, f, P(col, a))
                    x += w_
                c.restore()
            y0 += (len(lines) - 2) * size * 1.35
            text(c, th[3], W / 2, y0 + 2 * size * 1.35 + (10 if V else 0), EN_S, 34 if V else 30, INK, a * .6 * smooth(th[0] + 1.6, th[0] + 2.0, t))
            u = smooth(th[0] + 2.4, th[0] + 2.8, t)
            c.drawLine(W / 2 - 60, y0 + 2 * size * 1.35 + 70, W / 2 + 60, y0 + 2 * size * 1.35 + 70, P(INK, a * u * .4, 3))
            text(c, th[4], W / 2, y0 + 2 * size * 1.35 + 150, ZH_B, 48 if V else 44, INK, a * u)
            text(c, th[5], W / 2, y0 + 2 * size * 1.35 + 200, EN_S, 28, INK, a * u * .55)
    if 117.6 < t < 121.6:                                                     # the vote: comment 1 or 2
        pass
        with ov(c, (540, 300, 840, 420), (540, 900, 1000)):
            for i, (num, lab, col) in enumerate((('1', '换队', TOMATO), ('2', '死守', TEAL))):
                u = (t - 118.0 - .25 * i) / .4
                if u <= 0: continue
                pulse = 1 + .05 * (math.fmod(t - .25 * i, 2 * BEAT) < .12)
                cx_, cy_ = 750 + i * 420, 510
                c.save(); c.translate(cx_, cy_); c.scale(eback(u) * pulse, eback(u) * pulse)
                riso_rrect(c, -180, -200, 360, 400, 28, CARD, 1, 10)
                rrect(c, -180, -200, 360, 400, 28, P(col, 1, 6))
                text(c, num, -70, -40, EN_K, 150, col, 1, riso=5)
                text(c, lab, 60, -70, ZH_H, 64, INK, 1)
                hop = abs(math.sin((t - 118) * math.pi / BEAT)) * 26 if i == 0 else 0
                bean(c, 60 if i == 0 else 60, 150, YOU, .9, (1, 0) if i == 0 else (-1, 0), .8 if i == 0 else 0, 0 if i == 0 else 1.1, 1, False, hop)
                text(c, '扣 ' + num, -70, 140, ZH_H, 44, col, 1)
                c.restore()
    if t > 121.0:                                                            # end card
      with ov(c):
        a = smooth(121.0, 121.6, t)
        c.drawRect(skia.Rect.MakeWH(W, H), P(PAPER, a))
        if a > 0:
            s = (.33 if V else .42) * lerp(.96, 1, eout((t - 121.0) / 1.5))
            c.save(); c.translate(W / 2, H / 2); c.scale(s, s)
            c.drawImage(LOGO, -LOGO.width() / 2, -LOGO.height() / 2, skia.SamplingOptions(skia.FilterMode.kLinear), P(INK, a))
            c.restore()


sys.path.insert(0, ROOT + "/engine"); import channel as _CH   # the channel's horizontal logo (profile marks.end_logo_h)
_logo = _CH.mark(_CH.P['marks'].get('end_logo_h', _CH.P['marks']['end_logo']))
LOGO = skia.Image.open(_logo)


# ================================================================= frame
SCENES = [(0, 8, sc_hook), (8, 34, sc_13), (34, 58, sc_stuck), (58, 72, sc_switch), (72, 100, sc_one), (100, DUR + 1, sc_end)]
for t0, *_ in WIPES:
    ev(t0 - .85, 'wipe'); ev(t0 + .55, 'tear')
    for k in range(len(_[1])): ev(t0 - .5 + k * .045, 'type', k=k)


def frame(t, surf):
    c = surf.getCanvas()
    background(c)
    c.save(); c.translate(0, VY); c.scale(ZV, ZV)
    for a, b, fn in SCENES:
        if a <= t < b: fn(c, t); break
    c.restore()
    captions(c, t)
    wipe(c, t)
    c.drawImage(GRAIN_IMG, 0, 0)
    return surf.makeImageSnapshot().toarray()


def render(f0, f1, path):
    surf = skia.Surface(W, H)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for f in range(f0, f1): enc.stdin.write(frame(unwarp(f / FPS) if WARP else out2film(f / FPS) if CUT else f / FPS, surf).tobytes())
    enc.stdin.close(); enc.wait()


if __name__ == '__main__':
    a = sys.argv[1:]
    os.makedirs(BUILD + '/parts', exist_ok=True)
    NF = int((warp(DUR) if WARP else seg_table(SEG90)[1] if CUT else DUR) * FPS)
    if a and a[0] == '--still':
        import PIL.Image
        surf = skia.Surface(W, H)
        os.makedirs(BUILD + '/stills', exist_ok=True)
        for s in a[1:]:
            PIL.Image.fromarray(frame(float(s), surf)[..., :3]).save(f'{BUILD}/stills/{float(s):06.2f}.png')
    elif a and a[0] == '--part':
        i, n = int(a[1]), int(a[2])
        render(NF * i // n, NF * (i + 1) // n, f'{BUILD}/parts/p{i}.mp4')
    else:
        n = int(os.environ.get('PARTS', 8))
        ps = [subprocess.Popen([sys.executable, __file__, '--part', str(i), str(n)]) for i in range(n)]
        for p in ps: p.wait()
        with open(BUILD + '/parts/list.txt', 'w') as f:
            for i in range(n): f.write(f"file 'p{i}.mp4'\n")
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', BUILD + '/parts/list.txt', '-c', 'copy', BUILD + '/video.mp4'])
        print('frames', subprocess.check_output(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', BUILD + '/video.mp4']).decode().strip(), 'expected', NF)
