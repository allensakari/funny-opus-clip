"""界面道具（借鉴「万象有因《缘分》」深夜输入框打字又删掉）：用真实感的界面讲数字。
  input_box(cv, x, y, w, text_seq, t, t0, ...)  输入框：按脚本打字 / 删除，光标闪烁；text_seq = [(文本, 停留秒), …]
  notify(cv, x, y, w, title, body, k, ...)       通知卡片（k: 0→1 滑入）
  notify_stack(cv, x, y, w, items, t, period)    每 period 秒弹出一条，向下堆叠（频率类数字：每 2.4 秒一条）
全部跟随 brand 主题（深色 / 沙土）。"""
import math
import skia
import brand as B
from brand import paint, text, clamp, eout, CJK_B, CJK_M, CJK_H, NUM_B, NUM_M


def _card_bg(): return (.16, .18, .22) if B.THEME != 'sand' else (.985, .975, .955)


def _ink(): return B.WHITE


def typed(seq, t, t0, cps=7.0):
    """seq = [(text, hold_s), …] → the text visible at time t (types in at cps, deletes back to the common prefix)"""
    cur, tt = '', t - t0
    for target, hold in seq:
        common = 0
        while common < min(len(cur), len(target)) and cur[common] == target[common]: common += 1
        dele = len(cur) - common; dur_del = dele / (cps * 2.2)
        if tt < dur_del: return cur[:len(cur) - int(tt * cps * 2.2)]
        tt -= dur_del; cur = cur[:common]
        add = len(target) - common; dur_add = add / cps
        if tt < dur_add: return target[:common + int(tt * cps)]
        tt -= dur_add; cur = target
        if tt < hold: return cur
        tt -= hold
    return cur


def input_box(cv, x, y, w, seq, t, t0, al=1.0, size=40, label=None, send_k=0.0):
    if al <= .003: return
    h = size * 1.9
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h), h / 2, h / 2), paint(_card_bg(), al * .92))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h), h / 2, h / 2), paint(B.GREY, al * .35, stroke=1.5))
    s = typed(seq, t, t0)
    wd = text(cv, s, x - w / 2 + h * .55, y + size * .36, size, _ink(), al, cjk=CJK_M, num=NUM_M, shadow=0)
    if (t * 2) % 2 < 1.2:
        cx = x - w / 2 + h * .55 + wd + 4
        cv.drawRect(skia.Rect.MakeXYWH(cx, y - size * .55, 3, size * 1.1), paint(B.ACCENT, al))
    bx = x + w / 2 - h * .55
    cv.drawCircle(bx, y, h * .36, paint(B.CYAN if B.THEME != 'sand' else B.ACCENT, al))
    cv.drawLine(bx, y + h * .16, bx, y - h * .16, paint(_card_bg(), al, stroke=4)); cv.drawLine(bx - h * .12, y - h * .04, bx, y - h * .16, paint(_card_bg(), al, stroke=4)); cv.drawLine(bx + h * .12, y - h * .04, bx, y - h * .16, paint(_card_bg(), al, stroke=4))
    if label: text(cv, label, x, y - h * .9, 26, B.GREY, al, 'c', cjk=CJK_M, num=NUM_M)


def notify(cv, x, y, w, title, body, k, al=1.0, icon=(0.30, 0.75, 0.45), stamp='现在'):
    """one notification card, top-centre at (x, y); k 0→1 slides it down into place"""
    k = eout(k)
    if k <= 0 or al <= .003: return
    h = 120; yy = y - (1 - k) * 60
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, yy + 6, w, h), 26, 26), paint((0, 0, 0), al * k * .25, blur=14))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, yy, w, h), 26, 26), paint(_card_bg(), al * k * .96))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2 + 22, yy + 24, 48, 48), 12, 12), paint(icon, al * k))
    text(cv, title, x - w / 2 + 88, yy + 46, 26, B.GREY, al * k, cjk=CJK_B, num=NUM_B, shadow=0)
    text(cv, stamp, x + w / 2 - 24, yy + 46, 24, B.GREY, al * k, 'r', cjk=CJK_M, num=NUM_M, shadow=0)
    text(cv, body, x - w / 2 + 88, yy + 92, 32, _ink(), al * k, cjk=CJK_M, num=NUM_B, shadow=0)


def notify_stack(cv, x, y, w, make_item, t, t0, period, n_max=5, al=1.0, gap=134):
    """a new card every `period` s starting at t0; newest on top, older ones pushed down and fading.
    make_item(i) -> (title, body)"""
    if t < t0 or al <= .003: return 0
    n = int((t - t0) / period) + 1
    for j in range(min(n, n_max)):
        i = n - 1 - j; ti = t0 + i * period
        k = clamp((t - ti) / .35); slide = j - 1 + eout(clamp((t - (t0 + (n - 1) * period)) / .35)) if j > 0 else 0
        yy = y + max(0, slide) * gap if j > 0 else y
        title, body = make_item(i)
        notify(cv, x, yy, w, title, body, k if j == 0 else 1.0, al * (1 - j / (n_max + .5)))
    return n
