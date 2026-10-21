"""招牌字幕 (signature captions). One phrase on screen at a time; [..] marks key words / numbers (brand yellow).
caps: list of dict(show, a, b) — phrase text and its spoken span (global seconds).
Styles (the account uses ONE; candidates kept for the style pick):
  'period'  句点 — heavy white words rise in fast, key words yellow, a yellow brand dot lands as the full stop
  'bar'     标签条 — phrase on a dark bar that opens from the left, numbers on a yellow block with dark digits
  'odo'     数字跳格 — clean white text, numbers in big yellow Barlow that roll in digit by digit like an odometer"""
import math
import skia
from brand import *

CAP_Y, CAP_SIZE, CAP_X = 1330, 60, 520      # centre x shifted left of the right-hand action column
MAX_W = 820


def _active(caps, t):
    for i, c in enumerate(caps):
        nxt = caps[i + 1]['a'] if i + 1 < len(caps) else 1e9
        on, off = c['a'] - .10, min(nxt - .05, c['b'] + .8)
        if on <= t <= off: return c, on, off
    return None, 0, 0


def _strip_punct(s):
    while s and s[-1] in '，。、：；！？—': s = s[:-1]
    return s


def draw(cv, caps, t, style='period'):
    c, on, off = _active(caps, t)
    if not c: return
    {'period': _period, 'bar': _bar, 'odo': _odo}[style](cv, c, t, on, off)


# ---------------------------------------------------------------- 句点
def _period(cv, c, t, on, off):
    size = CAP_SIZE; rs = runs(_strip_punct(c['show']), size, CJK_H, NUM, track=1)
    wd = sum(r[3] for r in rs); sc = min(1.0, MAX_W / wd); size *= sc
    rs = runs(_strip_punct(c['show']), size, CJK_H, NUM, track=1); wd = sum(r[3] for r in rs)
    out = smooth(off - .12, off, t)
    x = CAP_X - wd / 2 - 12; y = CAP_Y
    n = len(rs); span = max(.25, min(.55, (c['b'] - c['a']) * .5))
    for j, (ch, f, hot, adv) in enumerate(rs):
        tj = on + span * j / max(1, n)
        k = eout((t - tj) / .16)
        if k <= 0: x += adv; continue
        dy = (1 - k) * 22 - out * 10
        col = ACCENT if hot else WHITE
        cv.drawString(ch, x, y + dy + size * .05, f, paint(SHADOW, k * (1 - out) * .85, blur=size * .18))
        cv.drawString(ch, x, y + dy, f, paint(col, k * (1 - out)))
        x += adv
    # the brand full stop
    td = on + span + .05; kd = clamp((t - td) / .22)
    if kd > 0:
        r = 9 * eback(kd, 2.4) * (1 - out)
        cv.drawCircle(x + 14, y - 4, r * 1.15, paint((0, 0, 0), .5 * (1 - out), blur=6))
        cv.drawCircle(x + 14, y - 4, r, paint(YELLOW, 1 - out))


# ---------------------------------------------------------------- 标签条
def _bar(cv, c, t, on, off):
    size = CAP_SIZE * .92; s = _strip_punct(c['show'])
    rs = runs(s, size, CJK_B, NUM_B, track=1); wd = sum(r[3] for r in rs)
    sc = min(1.0, (MAX_W - 60) / wd); size *= sc; rs = runs(s, size, CJK_B, NUM_B, track=1); wd = sum(r[3] for r in rs)
    k = eout((t - on) / .2); out = smooth(off - .12, off, t)
    padx, h = 30, size * 1.55; x0 = CAP_X - wd / 2 - padx; y = CAP_Y
    bw = (wd + 2 * padx) * k
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y - size * 1.08, bw, h), 10, 10)
    cv.drawRRect(rr, paint((0.03, 0.04, 0.07), .82 * (1 - out)))
    cv.drawRect(skia.Rect.MakeXYWH(x0, y - size * 1.08, 7, h), paint(YELLOW, 1 - out))
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, y - size * 1.3, bw, h * 1.3))
    x = x0 + padx; j = 0
    while j < len(rs):                                   # group consecutive hot glyphs into one yellow block
        ch, f, hot, adv = rs[j]
        if hot:
            jj = j
            while jj < len(rs) and rs[jj][2]: jj += 1
            gw = sum(r[3] for r in rs[j:jj])
            kb = eout((t - on - .12) / .18)
            cv.drawRect(skia.Rect.MakeXYWH(x - 6, y - size * .92, (gw + 12) * kb, size * 1.18), paint(YELLOW, 1 - out))
            for ch2, f2, _, adv2 in rs[j:jj]: cv.drawString(ch2, x, y, f2, paint(BG, 1 - out)); x += adv2
            j = jj; continue
        cv.drawString(ch, x, y, f, paint(WHITE, 1 - out)); x += adv; j += 1
    cv.restore()


# ---------------------------------------------------------------- 数字跳格
def _odo(cv, c, t, on, off):
    size = CAP_SIZE * .9; s = _strip_punct(c['show'])
    # numbers inside [..] are drawn 1.45× in yellow with a digit roll; other hot words just yellow
    parts, hot, buf = [], False, ''
    for ch in s:
        if ch in '[]':
            if buf: parts.append((buf, hot)); buf = ''
            hot = ch == '['; continue
        buf += ch
    if buf: parts.append((buf, hot))
    out = smooth(off - .12, off, t); k = eout((t - on) / .18)
    def isnum(p): return any(ch.isdigit() for ch in p)
    items = []
    for p, h in parts:
        big = h and isnum(p)
        rs = runs(p, size * (1.45 if big else 1), CJK_B, NUM, track=1)
        items.append((rs, h, big, sum(r[3] for r in rs)))
    wd = sum(i[3] for i in items); sc = min(1.0, MAX_W / wd)
    x = CAP_X - wd * sc / 2; y = CAP_Y
    cv.save(); cv.translate(x, y); cv.scale(sc, sc); cv.translate(-x, -y)
    a = k * (1 - out)
    tall = 1.45 if any(i[2] for i in items) else 1.0                         # big rolling digits reach higher
    qc_box('caption', ''.join(p for p, _ in parts), x, y - size * .95 * tall * sc, x + wd * sc, y + size * .25 * sc, a)
    for rs, h, big, w in items:
        for q, (ch, f, _, adv) in enumerate(rs):
            col = ACCENT if h else WHITE
            if big and ch.isdigit():
                tq = on + .05 + q * .06; kq = eout((t - tq) / .28)
                cv.save(); cv.clipRect(skia.Rect.MakeLTRB(x - 2, y - size * 1.5, x + adv + 2, y + size * .35))
                for dd in range(3):                       # digits rolling down into place
                    d = (int(ch) - 2 + dd) % 10 if kq < 1 else int(ch)
                    off_y = (1 - kq) * size * 1.4 * (2 - dd)
                    if kq >= 1 and dd: break
                    cv.drawString(str(d) if kq < 1 else ch, x, y - off_y, f, paint(col, a * (1 if dd == 2 or kq >= 1 else .5)))
                cv.restore()
            else:
                cv.drawString(ch, x, y + size * .05, f, paint(SHADOW, a * .8, blur=size * .18))
                cv.drawString(ch, x, y, f, paint(col, a))
            x += adv
    cv.restore()
