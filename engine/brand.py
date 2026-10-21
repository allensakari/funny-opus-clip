"""Brand layer (skia, 1080×1920): palette, fonts, text helpers, the dot-anchor watermark, source tags, counters.
Everything here is topic-independent; episodes import it and draw on top of their own scenes.
Channel-specific values (colours, fonts, mark images and their geometry) come from the channel profile (engine/channel.py)."""
import os, math
import skia
import channel as CH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# QC registry (engine/qc.py): with SHUSHUO_QC=1 every text / number / tag / caption drawn records its box → overlap & safe-zone checks
QC_ON = bool(os.environ.get('SHUSHUO_QC'))
QC = []


QC_T = None                                      # (scale, dx, dy) when an episode draws a group under a canvas transform


def qc_box(kind, label, l, t, r, b, a):
    if QC_ON and a > .003:
        if QC_T: s, dx, dy = QC_T; l, t, r, b = l * s + dx, t * s + dy, r * s + dx, b * s + dy
        QC.append(dict(kind=kind, label=label, box=(float(l), float(t), float(r), float(b)), a=float(a)))
FONTS = os.path.join(CH.ROOT, CH.P['fonts'].get('dir', 'assets/fonts'), '')      # episodes load extra faces from here
W, H = 1080, 1920

# ---------------------------------------------------------------- palette (profile [colors])
_C = CH.P['colors']
BG = CH.rgb(_C['bg'])
WHITE = CH.rgb(_C['ink'])                          # 'WHITE' = the main ink colour of the theme
YELLOW = CH.rgb(_C['accent'])                      # the brand dot (name kept: episodes import YELLOW)
GREY = CH.rgb(_C['grey'])
RED = CH.rgb(_C['red'])                            # warnings / danger numbers only
CYAN = CH.rgb(_C['cyan'])                          # secondary data colour (sparingly)
ACCENT = YELLOW                                    # accent used for TEXT / numbers (the dot and logo always stay YELLOW)
PAIR = tuple(CH.rgb(c) for c in _C['pair'])        # the episode's two sides (默认橙 / 青；期内可改成语义色) — fixed meaning for the whole film
SHADOW = (0.0, 0.0, 0.0)                           # soft halo behind text
TAG_FG, TAG_BG, TAG_BG_A = (0.80, 0.82, 0.86), (0.0, 0.0, 0.0), .45

# ---------------------------------------------------------------- themes: SHUSHUO_THEME=dark (default) | sand
# Brand elements never change (dot, logo, fonts, caption motion); only the ground colour, ink and the text accent follow the topic.
# 'sand' = light paper / sand ground for nature, life and society topics (first used S003, user 2026-10-10).
THEME = os.environ.get('SHUSHUO_THEME', 'dark')
if THEME == 'sand':
    _S = _C['sand']
    BG = CH.rgb(_S['bg'])                          # warm sand paper
    WHITE = CH.rgb(_S['ink'])
    GREY = CH.rgb(_S['grey'])
    ACCENT = CH.rgb(_S['accent_text'])             # the brand accent is usually too pale for text on sand
    CYAN = CH.rgb(_S['cyan'])
    SHADOW = BG
    TAG_FG, TAG_BG, TAG_BG_A = (0.30, 0.28, 0.25), (0.11, 0.10, 0.09), .08

# ---------------------------------------------------------------- fonts (profile [fonts]; all OFL, in assets/fonts)
CJK_H, CJK_B, CJK_M, CJK_R = (skia.Typeface.MakeFromFile(CH.font('cjk', w)) for w in ('Heavy', 'Bold', 'Medium', 'Regular'))
NUM, NUM_B, NUM_M = (skia.Typeface.MakeFromFile(CH.font('num', w)) for w in ('ExtraBold', 'Bold', 'Medium'))

# platform safe area (Douyin / XHS UI): top tabs ≈ 0–160, right action column x > 930 for y 900–1620, bottom title area y > 1560
SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT = 165, 1540, 920


def set_canvas(w, h):
    """switch the brand layer to another frame size (9:16 = 1080×1920 default; 16:9 = 1920×1080). Call before drawing."""
    global W, H, SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT, WM_Y, DOT, LOGO_DOT, LOGO_S
    W, H = w, h
    land = w > h
    SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT = (60, h - 90, w - 60) if land else (165, 1540, 920)
    WM_Y = SAFE_TOP
    DOT = (WM_X + (_M['wm_dot'][0] - _M['wm_bbox'][0]) * WM_S, WM_Y + (_M['wm_dot'][1] - _M['wm_bbox'][1]) * WM_S)
    LOGO_S = 0.34 if land else 0.40
    LOGO_DOT = (W / 2 + (_M['logo_dot'][0] - _M['logo_center_x']) * LOGO_S, H * (.47 if land else .448))
    import captions as _C
    _C.CAP_X, _C.CAP_Y, _C.MAX_W = (W / 2, H - 150, 1300) if land else (520, 1330, 820)


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def smooth(a, b, x): u = clamp((x - a) / (b - a)) if b != a else float(x >= a); return u * u * (3 - 2 * u)
def eout(u): u = clamp(u); return 1 - (1 - u) ** 3
def eio(u): u = clamp(u); return u * u * (3 - 2 * u)
def eback(u, s=1.7): u = clamp(u) - 1; return 1 + u * u * ((s + 1) * u + s)
def lerp(a, b, u): return a + (b - a) * u
def fade(t, a, b, fi=.25, fo=.2): return smooth(a, a + fi, t) * (1 - smooth(b - fo, b, t))
def fmt_int(v): return f'{int(round(v)):,}'


def paint(c, a=1.0, stroke=0, blur=0):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(c[0], c[1], c[2], clamp(a)))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def runs(s, size, cjk=None, num=None, track=0.0):
    """split a display string into glyph runs: [..] = accent; ASCII digits/latin use the numeral face"""
    cjk, num = cjk or CJK_H, num or NUM
    fc, fn = skia.Font(cjk, size), skia.Font(num, size * 1.18)
    out, hot = [], False
    for ch in s:
        if ch == '[': hot = True; continue
        if ch == ']': hot = False; continue
        f = fn if ord(ch) < 0x80 and ch != ' ' else fc
        adv = f.measureText(ch) if ch != ' ' else size * .28
        out.append((ch, f, hot, adv + track))
    return out


def text(cv, s, x, y, size, c=None, a=1.0, align='l', cjk=None, num=None, track=0.0, shadow=.6, accent=None, glow=0.0, _qc=True):
    """one line of mixed CJK / numerals; returns width"""
    c = WHITE if c is None else c; accent = ACCENT if accent is None else accent
    if c == YELLOW: c = ACCENT
    rs = runs(s, size, cjk, num, track)
    wd = sum(r[3] for r in rs) - track
    if a <= .003: return wd
    x0 = x - (wd / 2 if align == 'c' else wd if align == 'r' else 0)
    if _qc: qc_box('text', s.replace('[', '').replace(']', ''), x0, y - size * .88, x0 + wd, y + size * .12, a)
    for kind in (['s'] if shadow else []) + (['g'] if glow else []) + ['f']:
        xx = x0
        for ch, f, h, adv in rs:
            cc = accent if h else c
            if kind == 's': cv.drawString(ch, xx, y + size * .04, f, paint(SHADOW, a * shadow, blur=size * .16))
            elif kind == 'g': cv.drawString(ch, xx, y, f, paint(cc, a * glow, blur=size * .25))
            else: cv.drawString(ch, xx, y, f, paint(cc, a))
            xx += adv
    return wd


def scrim(cv, y0, y1, a0, a1):
    """vertical black gradient band for legibility"""
    g = skia.Paint(); g.setShader(skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [skia.Color4f(*SHADOW, a0).toColor(), skia.Color4f(*SHADOW, a1).toColor()]))
    cv.drawRect(skia.Rect.MakeLTRB(0, y0, W, y1), g)


# ---------------------------------------------------------------- big number + source tag
def bignum(cv, al, value, unit='', label=None, src=None, y=560, size=200, c=None, x=W / 2, pop=1.0, lc=None, tab=False):
    """the account's hero number: label above, numeral (Barlow ExtraBold), unit, grey source tag 「机构 · 年份」 below.
    `value` is a string (already formatted); `src` like 'CelesTrak · 2026-10-09' (required for every key number).
    tab=True: every digit gets the same cell width, so a rolling counter does not jitter left and right (transqc, S005 / S001 v2)."""
    if al <= .003: return
    c = WHITE if c is None else ACCENT if c == YELLOW else c
    fn, fc = skia.Font(NUM, size), skia.Font(CJK_H, size * .62)          # CJK inside a numeral (万 / 亿) at a smaller heavy face
    parts = [(ch, fn if ord(ch) < 0x2000 or ch in '≈×' else fc) for ch in value]
    dw = max(fn.measureText(d) for d in '0123456789') if tab else 0
    def adv(ch, f): return dw if tab and ch.isdigit() else f.measureText(ch)
    wv = sum(adv(ch, f) for ch, f in parts)
    fu = skia.Font(CJK_B, size * .26); wu = fu.measureText(unit) + 16 if unit else 0
    x0 = x - (wv + wu) / 2
    if label: text(cv, label, x, y - size * .9, 38, lc or WHITE, al * .92, 'c', cjk=CJK_B, track=2)
    cv.save(); cy = y - size * .36; cv.translate(x, cy); cv.scale(pop, pop); cv.translate(-x, -cy)
    xx = x0
    for ch, f in parts:
        dx = (adv(ch, f) - f.measureText(ch)) / 2
        cv.drawString(ch, xx + dx, y + size * .03, f, paint(SHADOW, al * .55, blur=size * .1)); cv.drawString(ch, xx + dx, y, f, paint(c, al)); xx += adv(ch, f)
    if unit: cv.drawString(unit, x0 + wv + 16, y - 6, fu, paint(c, al * .95))
    cv.restore()
    qc_box('number', value + unit, x - (wv + wu) / 2 * pop, y - size * .74 * pop, x + (wv + wu) / 2 * pop, y + size * .06, al)
    if src: source_tag(cv, al, src, x, y + 64, 'c')


def source_tag(cv, al, src, x, y, align='c'):
    """small grey 「机构 · 年份」 line: the on-screen citation under a key number"""
    wd = text(cv, src, 0, 0, 26, a=0, cjk=CJK_M, num=NUM_M, track=1.5)
    x0 = x - (wd / 2 if align == 'c' else wd if align == 'r' else 0)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0 - 14, y - 27, wd + 28, 38), 19, 19), paint(TAG_BG, al * TAG_BG_A))
    text(cv, src, x, y, 26, TAG_FG, al, align, cjk=CJK_M, num=NUM_M, track=1.5, shadow=0, _qc=False)
    qc_box('tag', src, x0 - 14, y - 27, x0 + wd + 14, y + 11, al)


def pop_k(t, t0, k=.10, rate=9): return 1 + k * math.exp(-max(0, t - t0) * rate) if t >= t0 else 1.0


def count(t, t0, t1, v0, v1, ease=eout):
    """rolling counter value between t0..t1"""
    return lerp(v0, v1, ease((t - t0) / max(1e-6, t1 - t0)))


# ---------------------------------------------------------------- watermark: 黄点锚定 (dot anchor)
_IMG = {}
LANG = os.environ.get('BRAND_LANG', 'zh')          # 'en': the profile's [marks.en] images (brand_en.py) for English-only cuts
_M = CH.P['marks']


def _img(key):
    name = (_M.get('en', {}).get(key) if LANG == 'en' else None) or _M[key]
    if name not in _IMG: _IMG[name] = skia.Image.open(CH.mark(name))
    return _IMG[name]

# small mark (letter + name), the dot is drawn by the engine at marks.wm_dot of the image; marks.wm_bbox = top-left of the drawn shape
WM_S, WM_X, WM_Y = 0.30, 50, SAFE_TOP          # scale and top-left of the mark's bbox on screen
DOT = (WM_X + (_M['wm_dot'][0] - _M['wm_bbox'][0]) * WM_S, WM_Y + (_M['wm_dot'][1] - _M['wm_bbox'][1]) * WM_S)
DOT_R, DOT_A = 6.5, .78                          # the lone dot during the body
# end card = the vertical logo, its full stop at marks.logo_dot (radius logo_dot_r), horizontal centre logo_center_x
LOGO_S = 0.40; LOGO_DOT = (W / 2 + (_M['logo_dot'][0] - _M['logo_center_x']) * LOGO_S - 0, 860.0)


def _ipaint(a):
    """paint for the white logo PNGs, tinted to the theme ink"""
    p = skia.Paint(AntiAlias=True, ColorFilter=skia.ColorFilters.Blend(skia.Color4f(*WHITE, 1).toColor(), skia.BlendMode.kSrcIn)); p.setAlphaf(clamp(a)); return p


def _dot(cv, x, y, r, a):
    cv.drawCircle(x, y + 1.5, r * 1.1, paint((0, 0, 0), a * (.2 if THEME == 'sand' else .45), blur=r * .8))
    cv.drawCircle(x, y, r, paint(YELLOW, a))


def watermark(cv, t, T, expand_at, hold=2.0, end_len=1.8, end=True):
    """draw the brand mark for time t of a film of length T.
    0 … expand_at: lone dot · expand_at: unfold into the small mark (letter + name), hold, fold back · body: lone dot · last end_len s: end card."""
    t_end = T - end_len
    # --- unfold / fold (0.6 s each way)
    k = smooth(expand_at, expand_at + .6, t) * (1 - smooth(expand_at + hold, expand_at + hold + .45, t))
    if t >= t_end and end:
        _end_card(cv, t - t_end, end_len); return
    r = lerp(DOT_R, 12.5 * WM_S * 1.15, eout(k)); a = lerp(DOT_A, 1.0, k)
    bx, by = _M['wm_bbox']; xl, xn = _M['wm_letter_end'], _M['wm_name_end']
    if k > .003:
        img = _img('watermark'); s = WM_S
        # the A grows out of the dot
        ka = eback(clamp(k / .7)) if k < 1 else 1.0
        cv.save(); cv.translate(*DOT); cv.scale(ka, ka); cv.translate(-DOT[0], -DOT[1])
        cv.clipRect(skia.Rect.MakeLTRB(0, 0, WM_X + (xl - bx) * s, H))
        cv.drawImageRect(img, skia.Rect.MakeXYWH(WM_X - bx * s, WM_Y - by * s, img.width() * s, img.height() * s), skia.SamplingOptions(skia.FilterMode.kLinear), _ipaint(k * 1.6))
        cv.restore()
        # the name wipes in to the right
        kw = eout(clamp((k - .25) / .75)); x_a = WM_X + (xl - bx) * s; x_b = WM_X + ((img.width() + 8) if LANG == 'en' else xn - bx) * s
        cv.save(); cv.clipRect(skia.Rect.MakeLTRB(x_a, 0, lerp(x_a, x_b, kw), H))
        cv.drawImageRect(img, skia.Rect.MakeXYWH(WM_X - bx * s, WM_Y - by * s, img.width() * s, img.height() * s), skia.SamplingOptions(skia.FilterMode.kLinear), _ipaint(k * 1.4))
        cv.restore()
    _dot(cv, DOT[0], DOT[1], r, a)


def _end_card(cv, lt, L):
    """the corner dot flies to the logo's full stop and grows; the name unrolls leftwards out of it"""
    u = eio(clamp(lt / .5)); dim = smooth(0, .5, lt)
    cv.drawRect(skia.Rect.MakeWH(W, H), paint(BG, .85 * dim))      # strong enough that nothing of the scene reads through the logo (user, S004)
    img = _img('end_logo'); s = LOGO_S
    ox, oy = W / 2 - _M['logo_center_x'] * s, LOGO_DOT[1] - _M['logo_dot'][1] * s          # logo image origin so its dot lands on LOGO_DOT
    dx = ox + _M['logo_dot'][0] * s
    x = lerp(DOT[0], dx, u); y = lerp(DOT[1], LOGO_DOT[1], u) - math.sin(math.pi * u) * 120
    r = lerp(DOT_R, _M['logo_dot_r'] * s, u)
    kw = eout(clamp((lt - .42) / .55))
    if kw > 0:
        cv.save(); cv.clipRect(skia.Rect.MakeLTRB(lerp(dx, ox + _M['logo_name_x'] * s, kw), 0, dx + 50 * s, H))
        cv.drawImageRect(img, skia.Rect.MakeXYWH(ox, oy, img.width() * s, img.height() * s), skia.SamplingOptions(skia.FilterMode.kLinear), _ipaint(1.0))
        cv.restore()
    _dot(cv, x, y, r, lerp(DOT_A, 1.0, u))
