"""封面：4 种母版 × 3 个尺寸（9:16 抖音 1080×1920、3:4 小红书 1080×1440、16:9 B站 1920×1080）。
文字只放：一个大数字 + 一句钩子 + 片名（+ 角落小标志）。不放标签、说明、署名。
usage (python):  covers.make(master, out_prefix, **spec)
  master = 'bignum'  巨数字    spec: number, unit, hook, title, plate(可选，压暗做底)
           'versus'  对比      spec: a=(数, 说明), b=(数, 说明), hook, title, plate
           'scene'   实景+数字  spec: number, unit, hook, title, plate(必需，满版)
           'chart'   图表      spec: values=[...], labels=[...], hot=[idx...], number, hook, title
→ <out_prefix>_9x16.jpg, _3x4.jpg, _16x9.jpg, _4x3.jpg（sizes=['4x3'] 只出指定尺寸）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skia
import brand as B
import channel as CH
from brand import paint, text, YELLOW, WHITE, GREY, BG, CJK_H, CJK_B, CJK_M, NUM, ACCENT, SHADOW, THEME
TIER_C = (.25, .23, .21) if THEME == 'sand' else (.86, .88, .92)      # light top line of the 层级 layout

SIZES = {'9x16': (1080, 1920), '3x4': (1080, 1440), '16x9': (1920, 1080), '4x3': (1440, 1080)}   # 4x3 added 2026-10-10 (user); landscape layout, crops the 16:9 plate


def _plate(cv, W, H, path, dark=.45, focus=(.5, .5), zoom=1.0, shift=(0, 0)):
    """background plate, cover-fit; zoom > 1 enlarges around the centre, shift moves it (fractions of W, H)"""
    cv.clear(skia.Color4f(*BG, 1).toColor())
    if not path: return
    im = skia.Image.open(path); s = max(W / im.width(), H / im.height()) * zoom
    w, h = im.width() * s, im.height() * s; x = (W - w) * focus[0] + shift[0] * W; y = (H - h) * focus[1] + shift[1] * H
    cv.drawImageRect(im, skia.Rect.MakeXYWH(x, y, w, h), skia.SamplingOptions(skia.FilterMode.kLinear))
    cv.drawRect(skia.Rect.MakeWH(W, H), paint(SHADOW, dark))


def _grad(cv, W, y0, y1, a0, a1):
    g = skia.Paint(); g.setShader(skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [skia.Color4f(*SHADOW, a0).toColor(), skia.Color4f(*SHADOW, a1).toColor()]))
    cv.drawRect(skia.Rect.MakeLTRB(0, y0, W, y1), g)


def _big(cv, s, x, y, size, c=WHITE, align='c', unit='', unit_c=None, maxw=None):
    """numeral with CJK-safe glyphs (万/亿 smaller) + unit, shrunk to fit maxw; returns width"""
    if maxw:
        w0 = sum(skia.Font(NUM if ord(ch) < 0x2000 or ch in '≈×' else CJK_H, size * (1 if ord(ch) < 0x2000 or ch in '≈×' else .6)).measureText(ch) for ch in s)
        w0 += skia.Font(CJK_H, size * .24).measureText(unit) + 18 if unit else 0
        size *= min(1.0, maxw / w0)
    fn, fc = skia.Font(NUM, size), skia.Font(CJK_H, size * .6)
    parts = [(ch, fn if ord(ch) < 0x2000 or ch in '≈×' else fc) for ch in s]
    wv = sum(f.measureText(ch) for ch, f in parts); fu = skia.Font(CJK_H, size * .24); wu = fu.measureText(unit) + 18 if unit else 0
    x0 = x - ((wv + wu) / 2 if align == 'c' else 0)
    xx = x0
    for ch, f in parts:
        cv.drawString(ch, xx, y + size * .04, f, paint(SHADOW, .6, blur=size * .08)); cv.drawString(ch, xx, y, f, paint(c)); xx += f.measureText(ch)
    if unit: cv.drawString(unit, xx + 18, y - size * .02, fu, paint(unit_c or c))
    return wv + wu


def _mark(cv, W, H):
    """small brand mark top-left: brand dot + channel name (profile [channel] name)"""
    sc = min(W, H) / 1080
    cv.drawCircle(64 * sc, 74 * sc, 11 * sc, paint(YELLOW))
    text(cv, CH.P['channel']['name'], 88 * sc, 88 * sc, 38 * sc, WHITE, .95, cjk=CJK_H, shadow=.6)


def _title(cv, s, x, y, size, align='c'):
    if not s: return                                                   # covers carry no title by default (user, 2026-10-10)
    w = text(cv, s, x, y, size, WHITE, 1, align, cjk=CJK_H, shadow=.7)
    xd = (x + w / 2 if align == 'c' else x + w) + size * .16
    cv.drawCircle(xd, y - size * .08, size * .11, paint(YELLOW))      # the brand full stop


def _fit(s, size, maxw, cjk=CJK_H):
    w = text(None, s, 0, 0, size, a=0, cjk=cjk) if False else skia.Font(cjk, size).measureText(s.replace('[', '').replace(']', ''))
    return size * min(1, maxw / max(1, w))


def make(master, out, sizes=None, **k):
    """sizes: subset of SIZES keys to (re)render, e.g. ['4x3'] to add one size without touching the others"""
    for key, (W, H) in SIZES.items():
        if sizes and key not in sizes: continue
        surf = skia.Surface(W, H); cv = surf.getCanvas(); land = W > H; sc = min(W, H) / 1080
        if master in ('bignum', 'scene', 'versus'):
            _plate(cv, W, H, k.get('plate'), dark=.25 if master == 'scene' else .6, focus=k.get('focus', (.5, .5)), zoom=k.get('zoom', 1.0), shift=k.get('shift', {}).get(key, (0, 0)))
        else:
            cv.clear(skia.Color4f(*BG, 1).toColor())
        _grad(cv, W, 0, H * .35, .55, 0); _grad(cv, W, H * .55, H, 0, k.get('floor', .8))      # floor / fog: lighter for a plate whose subject sits at the bottom (S001 v2 night sky)
        hook, title = k.get('hook', ''), k.get('title', '')
        if master in ('bignum', 'scene') and land and k.get('plate_land'):
            _plate(cv, W, H, k['plate_land'], dark=.2, focus=(.5, .5), zoom=k.get('zoom_land', 1.0), shift=k.get('shift', {}).get(key, k.get('shift', {}).get('16x9', (0, 0)))); _grad(cv, W, 0, H * .35, .55, 0); _grad(cv, W, H * .55, H, 0, .8)
            g = skia.Paint(); g.setShader(skia.GradientShader.MakeLinear([(0, 0), (W * .7, 0)], [skia.Color4f(*SHADOW, .75).toColor(), skia.Color4f(*SHADOW, 0).toColor()])); cv.drawRect(skia.Rect.MakeWH(W, H), g)
        if master in ('bignum', 'scene') and k.get('pre'):
            # stacked sentence: small line / giant number / small line — reads as one phrase, sits on the lower half of the plate
            pre, post = k['pre'], k.get('post', '')
            if land:
                xl, yc = 110, H * .52; ns = 300
                _grad(cv, W, H * .25, H, 0, .35)
                if k.get('text_style', 'tier') != 'tier': text(cv, pre, xl + 6, yc - ns * .78, 64, WHITE, 1, cjk=CJK_H)
                _big(cv, k['number'], xl, yc, ns, ACCENT, 'l', k.get('unit', ''), WHITE, maxw=W * .52)
                if k.get('text_style', 'tier') == 'tier':
                    text(cv, pre, xl + 6, yc - ns * .78, 50, TIER_C, 1, cjk=CJK_M, track=10, shadow=.8)
                    _title(cv, post, xl + 6, yc + ns * .38, 84, 'l')
                else:
                    text(cv, post, xl + 6, yc + ns * .36, 80, WHITE, 1, cjk=CJK_H)
            else:
                yc = H * (.665 if key == '9x16' else .70); ns = 400 if key == '9x16' else 360
                fog = k.get('fog', .45 if THEME == 'sand' else .7)                # the sand plate stays visible under the text
                _grad(cv, W, H * .45, H * .8, 0, fog); cv.drawRect(skia.Rect.MakeLTRB(0, H * .8 - 1, W, H), paint(SHADOW, fog))
                ts = k.get('text_style', 'tier')           # 默认 = ① 层级（用户 2026-10-10 选定）
                _big(cv, k['number'], W / 2, yc, ns, ACCENT, 'c', k.get('unit', ''), WHITE, maxw=W * .9)
                if ts == 'plain':
                    text(cv, pre, W / 2, yc - ns * .80, _fit(pre, 76, W - 160), WHITE, 1, 'c', cjk=CJK_H)
                    text(cv, post, W / 2, yc + ns * .40, _fit(post, 92, W - 160), WHITE, 1, 'c', cjk=CJK_H)
                elif ts == 'tier':        # 层级：上行轻、字距拉开；下行重、带品牌句点
                    text(cv, pre, W / 2, yc - ns * .82, 54, TIER_C, 1, 'c', cjk=CJK_M, track=10, shadow=.8)
                    _title(cv, post, W / 2, yc + ns * .42, 96)
                elif ts == 'label':       # 标签：上行放进品牌黄描边胶囊；下行重
                    f = 52; wpre = skia.Font(CJK_B, f).measureText(pre) + 8 * len(pre); yy = yc - ns * .84
                    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(W / 2 - wpre / 2 - 34, yy - f * 1.05, wpre + 68, f * 1.55), f * .78, f * .78), paint((0, 0, 0), .55))
                    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(W / 2 - wpre / 2 - 34, yy - f * 1.05, wpre + 68, f * 1.55), f * .78, f * .78), paint(YELLOW, 1, stroke=3))
                    text(cv, pre, W / 2, yy, f, WHITE, 1, 'c', cjk=CJK_B, track=8, shadow=0)
                    text(cv, post, W / 2, yc + ns * .42, 96, WHITE, 1, 'c', cjk=CJK_H, track=6)
                elif ts == 'hilite':      # 高亮：关键词「头顶」用黄色，上下两行同一字重、字距加大
                    text(cv, k.get('pre_hl', pre), W / 2, yc - ns * .80, 70, WHITE, 1, 'c', cjk=CJK_H, track=6)
                    text(cv, post, W / 2, yc + ns * .42, 88, WHITE, 1, 'c', cjk=CJK_H, track=14)
        elif master in ('bignum', 'scene'):
            ny = H * (k.get('num_y', .27) if not land else .50); ns = (400 if key == '9x16' else 330 if key == '3x4' else 320) * (k.get('num_scale', 1.0))
            if land:
                _big(cv, k['number'], 110, ny, ns, ACCENT if k.get('yellow', True) else WHITE, 'l', k.get('unit', ''), WHITE, maxw=W * .5)
                for i, ln in enumerate(hook.split('\n')): text(cv, ln, 110, ny + 120 + i * 84, _fit(ln, 66, W * .5), WHITE, 1, cjk=CJK_H)
                _title(cv, title, 110, H - 90, 84, 'l')
            else:
                _big(cv, k['number'], W / 2, ny, ns, ACCENT if k.get('yellow', True) else WHITE, 'c', k.get('unit', ''), WHITE, maxw=W * .84)
                for i, ln in enumerate(hook.split('\n')): text(cv, ln, W / 2, ny + 150 * sc + i * 96 * sc, _fit(ln, 78 * sc, W - 140), WHITE, 1, 'c', cjk=CJK_H)
                _title(cv, title, W / 2, H - (300 if key == '9x16' else 120), 120 if key == '9x16' else 104)
        elif master == 'versus':
            (va, la), (vb, lb) = k['a'], k['b']
            if land:
                _big(cv, va, W * .27, H * .52, 260, WHITE); text(cv, la, W * .27, H * .52 + 80, 48, GREY, 1, 'c', cjk=CJK_B)
                text(cv, '→', W * .5, H * .46, 140, YELLOW, 1, 'c', cjk=CJK_H)
                _big(cv, vb, W * .73, H * .52, 260, ACCENT); text(cv, lb, W * .73, H * .52 + 80, 48, WHITE, 1, 'c', cjk=CJK_B)
                hs = _fit(hook, 60, W - 220); text(cv, hook, W / 2, H * .78, hs, WHITE, 1, 'c', cjk=CJK_H); _title(cv, title, W / 2, H - 70, 70)
            else:
                y1, y2 = H * .28, H * .56
                _big(cv, va, W / 2, y1, 300, WHITE); text(cv, la, W / 2, y1 + 80, 48, GREY, 1, 'c', cjk=CJK_B)
                text(cv, '↓', W / 2, (y1 + y2) / 2 + 10, 110, YELLOW, 1, 'c', cjk=CJK_H)
                _big(cv, vb, W / 2, y2 + 60, 340, ACCENT); text(cv, lb, W / 2, y2 + 140, 48, WHITE, 1, 'c', cjk=CJK_B)
                hs = _fit(hook, 62, W - 140); text(cv, hook, W / 2, y2 + 260, hs, WHITE, 1, 'c', cjk=CJK_H)
                _title(cv, title, W / 2, H - (260 if key == '9x16' else 110), 110 if key == '9x16' else 90)
        elif master == 'chart':
            vals, hot = k['values'], set(k.get('hot', []))
            x0, x1 = (110, W * .55) if land else (90, W - 90); yb = H * (.82 if land else .62); hm = H * (.55 if land else .32)
            bw = (x1 - x0) / len(vals) * .72; vmax = max(vals)
            for i, v in enumerate(vals):
                x = x0 + (i + .5) * (x1 - x0) / len(vals); hh = hm * v / vmax
                cv.drawRect(skia.Rect.MakeLTRB(x - bw / 2, yb - hh, x + bw / 2, yb), paint(YELLOW if i in hot else (.45, .5, .58)))
            if land:
                _big(cv, k['number'], W * .6, H * .45, 250, ACCENT, 'l', k.get('unit', ''), WHITE)
                hs = _fit(hook, 58, W * .38); text(cv, hook, W * .6, H * .45 + 100, hs, WHITE, 1, cjk=CJK_H); _title(cv, title, W * .6, H - 110, 80, 'l')
            else:
                _big(cv, k['number'], W / 2, H * .22, 300, ACCENT, 'c', k.get('unit', ''), WHITE)
                hs = _fit(hook, 64, W - 140); text(cv, hook, W / 2, yb + 120, hs, WHITE, 1, 'c', cjk=CJK_H)
                _title(cv, title, W / 2, H - (220 if key == '9x16' else 90), 110 if key == '9x16' else 90)
        _mark(cv, W, H)
        surf.makeImageSnapshot().save(f'{out}_{key}.jpg', skia.kJPEG, 92)
        print('cover', f'{out}_{key}.jpg')
