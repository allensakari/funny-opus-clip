"""math-beauty v2 · shared engine: one continuous camera over the complex plane, everything drawn as light.
- every visible thing is a gaussian light segment (points = zero-length segments, trails = the last L seconds of a point)
- two-level bloom, deep-space background, film grain; no flashes / glitches / zoom punches (user dislikes them)
- text: 霞鹜文楷 (Chinese) + Cormorant Garamond (Latin, numerals, formulas), characters resolve out of a blur"""
import os, math, subprocess
import numpy as np
import skia

W, H = int(os.environ.get('W', 1920)), int(os.environ.get('H', 1080))
FPS = int(os.environ.get('FPS', 60))
EN = bool(os.environ.get('EN'))                                     # English-only cut (YouTube): no Chinese anywhere on screen


def lang(zh, en): return en if EN else zh
HERE = os.path.dirname(os.path.abspath(__file__))
def _root(p):                                                  # the skill root = the first parent that has engine/channel.py
    while not os.path.exists(os.path.join(p, 'engine', 'channel.py')) and os.path.dirname(p) != p: p = os.path.dirname(p)
    return p
FD = _root(HERE) + '/assets/fonts/'
WK = skia.Typeface.MakeFromFile(FD + 'LXGWWenKai-Medium.ttf')
CG, CG_SB, CG_I, CG_SBI = (skia.Typeface.MakeFromFile(FD + f'CormorantGaramond-{n}-LF.ttf') for n in ('Medium', 'SemiBold', 'MediumItalic', 'SemiBoldItalic'))   # lining figures (1 ≠ I in formulas)
CGO_SB, CGO_I = (skia.Typeface.MakeFromFile(FD + f'CormorantGaramond-{n}.ttf') for n in ('SemiBold', 'MediumItalic'))   # v4「星夜」caption faces (old-style figures)
NOTO = skia.Typeface.MakeFromFile(FD + 'NotoSerifSC-Regular.otf')          # Greek letters Cormorant lacks (θ φ Σ …)


def has(tf, ch): return tf.unicharToGlyph(ord(ch)) != 0


def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def smooth(a, b, x): u = clamp((x - a) / (b - a)) if b != a else float(x >= a); return u * u * (3 - 2 * u)
def eio(u): u = clamp(u); return u * u * (3 - 2 * u)
def eout(u): u = clamp(u); return 1 - (1 - u) ** 3
def ein(u): u = clamp(u); return u ** 3
def esine(u): u = clamp(u); return .5 - .5 * math.cos(math.pi * u)
def lerp(a, b, u): return a + (b - a) * u
def fade(t, a, b, fi=.4, fo=.4): return smooth(a, a + fi, t) * (1 - smooth(b - fo, b, t))


def srgb(h): return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
def lin(h): return np.array([c ** 2.2 for c in srgb(h)])


# light palette (linear)
GOLD, GOLD_W = lin('#ffbf5e'), lin('#ffe9c2')
ROSE = lin('#ff6f8e')
CYAN, CYAN_W = lin('#5fc8ff'), lin('#d8f1ff')
IVORY = lin('#f3ead8')
DIM = lin('#5d6b8f')
# text (sRGB)
T_IVORY, T_SUB, T_GOLD, T_CYAN = srgb('#f3ead8'), srgb('#9aa8c8'), srgb('#ffd08a'), srgb('#a9dcff')


class Cam:
    """2D camera over the complex plane: centre (cx, cy) in world units, s = pixels per unit"""
    def __init__(self, cx, cy, s): self.cx, self.cy, self.s = cx, cy, s

    def P(self, z):
        z = np.asarray(z)
        if np.iscomplexobj(z) or z.ndim == 0 or z.shape[-1] != 2: z = z.astype(complex); x, y = z.real, z.imag
        else: x, y = z[..., 0], z[..., 1]
        return np.stack([W / 2 + (x - self.cx) * self.s, H / 2 - (y - self.cy) * self.s], -1)


def cam_mix(a, b, u):
    """zoom in log space so scale changes feel even"""
    s = math.exp(lerp(math.log(a.s), math.log(b.s), u))
    return Cam(lerp(a.cx, b.cx, u), lerp(a.cy, b.cy, u), s)


class PS:
    """ordered light points (screen px). The same points must be added in the same order at every t (trails need identity)."""
    def __init__(self): self.p, self.r, self.c = [], [], []

    def add(self, xy, r, col, a=1.0):
        xy = np.asarray(xy, float).reshape(-1, 2); n = len(xy)
        a = np.broadcast_to(np.asarray(a, float), (n,))
        self.p.append(xy); self.r.append(np.broadcast_to(np.asarray(r, float), (n,)).astype(float))
        self.c.append(np.broadcast_to(np.asarray(col, float), (n, 3)) * np.clip(a, 0, None)[:, None])

    def arrays(self):
        if not self.p: return np.zeros((0, 2)), np.zeros(0), np.zeros((0, 3))
        return np.concatenate(self.p), np.concatenate(self.r), np.concatenate(self.c)


def polyline(P, r, col, a=1.0, closed=False):
    """static line segments (no trail): rows of (x0 y0 x1 y1 r R G B)"""
    P = np.asarray(P, float)
    if closed: P = np.vstack([P, P[:1]])
    n = len(P) - 1
    if n <= 0: return np.zeros((0, 8))
    a = np.broadcast_to(np.asarray(a, float), (len(P),))[:n]
    c = np.broadcast_to(np.asarray(col, float), (n, 3)) * a[:, None]
    return np.concatenate([P[:-1], P[1:], np.full((n, 1), r), c], 1)


def trail_segs(fn, t, L, k=8, gain=.85):
    """long exposure: the head dot at full strength + a fading line through the last L seconds"""
    hist = [fn(t - L * j / k) for j in range(k + 1)]
    P0, R0, C0 = hist[0]
    out = [np.concatenate([P0, P0, R0[:, None], C0], 1)]
    for j in range(k):
        Pa, Ra, Ca = hist[j]; Pb = hist[j + 1][0]
        Ln = np.hypot(*(Pa - Pb).T)
        w = gain * (1 - (j + .5) / k) ** 1.3 * Ln / (Ln + 3 * Ra)
        out.append(np.concatenate([Pa, Pb, Ra[:, None], Ca * w[:, None]], 1))
    return np.concatenate(out)


def cull(S):
    S = S[S[:, 5:8].max(1) > 2e-4]
    S[:, 4] = np.maximum(S[:, 4], .6)
    m = (np.minimum(S[:, 0], S[:, 2]) < W + 60) & (np.maximum(S[:, 0], S[:, 2]) > -60) & (np.minimum(S[:, 1], S[:, 3]) < H + 60) & (np.maximum(S[:, 1], S[:, 3]) > -60)
    return S[m]


# ---------------------------------------------------------------- GPU
VS_SEG = '''#version 330
in vec2 corner; in vec2 a; in vec2 b; in float r; in vec3 c;
uniform vec2 res;
out vec2 fp; flat out vec2 fa; flat out vec2 fb; flat out float fr; flat out vec3 fc;
void main(){
  vec2 d = b - a; float L = length(d); vec2 dir = L > 1e-4 ? d / L : vec2(1., 0.); vec2 nr = vec2(-dir.y, dir.x);
  float m = r * 3.2 + 1.5;
  vec2 p = (a + b) * .5 + dir * corner.x * (L * .5 + m) + nr * corner.y * m;
  fp = p; fa = a; fb = b; fr = r; fc = c;
  gl_Position = vec4(p.x / res.x * 2. - 1., 1. - p.y / res.y * 2., 0., 1.);
}'''
FS_SEG = '''#version 330
in vec2 fp; flat in vec2 fa; flat in vec2 fb; flat in float fr; flat in vec3 fc; out vec4 o;
void main(){
  vec2 pa = fp - fa, ba = fb - fa; float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0., 1.);
  float d = length(pa - ba * h); o = vec4(fc * exp(-d * d / (2. * fr * fr)), 1.);
}'''
VS_Q = '''#version 330
in vec2 p; out vec2 uv; void main(){ uv = p * .5 + .5; gl_Position = vec4(p, 0, 1); }'''
FS_BLUR = '''#version 330
in vec2 uv; out vec4 o; uniform sampler2D src; uniform float lod; uniform vec2 dir;
void main(){ vec3 s = vec3(0.); float wt = 0.;
  for (int i = -6; i <= 6; i++){ float w = exp(-float(i * i) / 18.); s += textureLod(src, uv + dir * float(i), lod).rgb * w; wt += w; }
  o = vec4(s / wt, 1.); }'''
FS_BLIT = '''#version 330
in vec2 uv; out vec4 o; uniform sampler2D src; uniform float k, gam;
void main(){ o = vec4(pow(max(texture(src, uv).rgb, 0.), vec3(gam)) * k, 1.); }'''
FS_COMP = '''#version 330
in vec2 uv; out vec4 o;
uniform sampler2D S, B1, B2; uniform float t, bgK, expo; uniform vec2 res;
float h(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n2(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
  return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float s = 0., a = .5; for (int i = 0; i < 5; i++){ s += a * n2(p); p *= 2.03; a *= .5; } return s; }
void main(){
  vec2 q = vec2(uv.x, 1. - uv.y);
  vec2 v = q - .5; v.x *= res.x / res.y;
  vec3 bg = mix(vec3(.0022, .003, .0075), vec3(.0005, .0007, .002), smoothstep(.0, .9, length(v)));
  float m = fbm(vec2(q.x * 2.4 + t * .006, q.y * 2.4 - t * .004) + 3.) * fbm(vec2(q.x * 1.2 - t * .004, q.y * 1.6 + 9.));
  bg += vec3(.006, .007, .016) * smoothstep(.15, .55, m);
  vec3 c = bg * bgK + (texture(S, uv).rgb + texture(B1, uv).rgb * .6 + texture(B2, uv).rgb * .55) * expo;
  c = 1. - exp(-c * 1.05);
  c *= 1. - .5 * dot(v, v);
  c = pow(max(c, 0.), vec3(1. / 2.2));
  c += (h(q * res + fract(t * 7.13) * 91.) - .5) * .022;
  o = vec4(c, 1.);
}'''


class GL:
    def __init__(self):
        import moderngl as mg
        import sys as _s; _s.path.insert(0, os.path.dirname(HERE)); import core
        self.mg = mg; ctx = self.ctx = core.ctx()
        self.pblit = ctx.program(vertex_shader=VS_Q, fragment_shader=FS_BLIT)
        self.pseg = ctx.program(vertex_shader=VS_SEG, fragment_shader=FS_SEG)
        self.pblur = ctx.program(vertex_shader=VS_Q, fragment_shader=FS_BLUR)
        self.pcomp = ctx.program(vertex_shader=VS_Q, fragment_shader=FS_COMP)
        self.pseg['res'].value = (W, H); self.pcomp['res'].value = (W, H)
        q = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], 'f4').tobytes())
        self.inst = ctx.buffer(reserve=4 * 8 * 600000, dynamic=True)
        self.vseg = ctx.vertex_array(self.pseg, [(q, '2f', 'corner'), (self.inst, '2f 2f 1f 3f/i', 'a', 'b', 'r', 'c')])
        self.vblur = ctx.vertex_array(self.pblur, [(q, '2f', 'p')])
        self.vcomp = ctx.vertex_array(self.pcomp, [(q, '2f', 'p')])
        self.vblit = ctx.vertex_array(self.pblit, [(q, '2f', 'p')])

        def tex(w, h, mip=False):
            x = ctx.texture((w, h), 4, dtype='f2'); x.filter = (mg.LINEAR_MIPMAP_LINEAR if mip else mg.LINEAR, mg.LINEAR); x.repeat_x = x.repeat_y = False; return x
        self.S = tex(W, H, True); self.fS = ctx.framebuffer([self.S])
        self.T = [tex(W // 4, H // 4), tex(W // 4, H // 4), tex(W // 16, H // 16), tex(W // 16, H // 16)]
        self.fT = [ctx.framebuffer([x]) for x in self.T]
        self.O = ctx.texture((W, H), 3); self.fO = ctx.framebuffer([self.O])

    def blur(self, src, lod, dst, w, h, d):
        self.fT[dst].use(); self.ctx.viewport = (0, 0, w, h); src.use(0); self.pblur['src'].value = 0; self.pblur['lod'].value = lod
        self.pblur['dir'].value = (d[0] / w, d[1] / h); self.vblur.render(self.mg.TRIANGLE_STRIP)

    def run(self, segs, t, bgK=1.0, expo=1.0, layers=()):
        ctx, mg = self.ctx, self.mg
        self.fS.use(); ctx.viewport = (0, 0, W, H); ctx.clear(0, 0, 0, 1)
        ctx.enable(mg.BLEND); ctx.blend_func = (mg.ONE, mg.ONE)
        for tex, k, *g in layers:                                   # fractal layers (linear HDR) go under the lights and through the bloom
            if k <= 0: continue
            tex.use(0); self.pblit['src'].value = 0; self.pblit['k'].value = k; self.pblit['gam'].value = g[0] if g else 2.2; self.vblit.render(mg.TRIANGLE_STRIP)
        segs = segs[:600000]
        if len(segs): self.inst.write(segs.astype('f4').tobytes()); self.vseg.render(mg.TRIANGLE_STRIP, instances=len(segs))
        ctx.disable(mg.BLEND)
        self.S.build_mipmaps()
        w4, h4, w16, h16 = W // 4, H // 4, W // 16, H // 16
        self.blur(self.S, 2, 0, w4, h4, (1.6, 0)); self.blur(self.T[0], 0, 1, w4, h4, (0, 1.6))
        self.blur(self.S, 4, 2, w16, h16, (1.4, 0)); self.blur(self.T[2], 0, 3, w16, h16, (0, 1.4))
        self.fO.use(); ctx.viewport = (0, 0, W, H)
        for i, x in enumerate((self.S, self.T[1], self.T[3])): x.use(i)
        self.pcomp['S'].value, self.pcomp['B1'].value, self.pcomp['B2'].value = 0, 1, 2
        self.pcomp['t'].value = t; self.pcomp['bgK'].value = bgK; self.pcomp['expo'].value = expo
        self.vcomp.render(mg.TRIANGLE_STRIP)
        return np.frombuffer(self.fO.read(components=3), np.uint8).reshape(H, W, 3)[::-1]


# ---------------------------------------------------------------- dust: deep bokeh field for parallax / depth of field
_rd = np.random.default_rng(5); ND = 2600
DUST = np.stack([_rd.uniform(-1.4, 1.4, ND), _rd.uniform(-1.4, 1.4, ND), _rd.uniform(0, 1, ND), _rd.uniform(0, 6.28, ND)], 1)


def dust(cam, t, k=1.0):
    """points live at depth d (0 near … 1 far); parallax follows the camera's log-zoom and pan"""
    d = DUST[:, 2]; par = .15 + .5 * (1 - d)
    z = math.log(cam.s / 200.0)
    sx = W * (DUST[:, 0] + .02 * np.sin(t * .11 + DUST[:, 3])) - cam.cx * cam.s * par * .08
    sy = H * (DUST[:, 1] + .02 * np.cos(t * .09 + DUST[:, 3])) + cam.cy * cam.s * par * .08
    cx, cy = W / 2, H / 2
    g = np.exp(z * par * .6)
    x = cx + (sx - cx) * g; y = cy + (sy - cy) * g
    x = (x + W * 2) % (W * 2.8) - W * .4; y = (y + H * 2) % (H * 2.8) - H * .4
    r = .7 + 5.5 * (1 - d) ** 3                     # near = big soft bokeh
    b = (.05 + .12 * d) * (1.0 / (1 + .25 * r)) * k * (.75 + .25 * np.sin(t * .7 + DUST[:, 3] * 3))
    col = np.where((DUST[:, 3] > 4.5)[:, None], CYAN_W[None], IVORY[None]) * b[:, None]
    return np.concatenate([np.stack([x, y], 1), np.stack([x, y], 1), r[:, None], col], 1)


# ---------------------------------------------------------------- text
def runs(s, size, zf=None, lf=None):
    fc, fl = skia.Font(zf or WK, size), skia.Font(lf or CG_SB, size * 1.1)
    out = []
    for ch in s:
        f = fl if (ord(ch) < 0x2000 or ch in '≥−×–—“”·°πθφ√∑∞≈') else fc
        if f is fl and not has(lf or CG_SB, ch): f = skia.Font(NOTO, size * .95)
        out.append((ch, f, f.measureText(ch) if ch != ' ' else size * .28))
    return out


def paint(c, a=1.0, blur=0):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(c[0], c[1], c[2], clamp(a)))
    if blur > .3: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def tx(cv, s, x, y, size, col=T_IVORY, al=1.0, align='l', zf=None, lf=None, glow=.35):
    rs = runs(s, size, zf, lf); wd = sum(r[2] for r in rs)
    if al <= .003: return wd
    x0 = x - (wd / 2 if align == 'c' else wd if align == 'r' else 0)
    for k in (('g', 'f') if glow else ('f',)):
        xx = x0
        for ch, f, adv in rs:
            cv.drawString(ch, xx, y, f, paint(col, al * (glow if k == 'g' else 1), blur=size * .22 if k == 'g' else 0)); xx += adv
    return wd


def math_tx(cv, parts, x, y, size, col=T_IVORY, al=1.0, align='l', glow=.4):
    """parts: [(text, scale, rise, italic)] — a tiny formula setter (superscripts via scale / rise in em)"""
    items = []
    for s, sc, rise, it in parts:
        tf = CG_SBI if it else CG_SB
        for ch in s:
            f = skia.Font(tf if has(tf, ch) else NOTO, size * sc * (1 if has(tf, ch) else .9))
            items.append((ch, f, rise * size, f.measureText(ch)))
    wd = sum(i[3] for i in items)
    if al <= .003: return wd
    x0 = x - (wd / 2 if align == 'c' else wd if align == 'r' else 0)
    for k in ('g', 'f'):
        xx = x0
        for s, f, ry, adv in items:
            cv.drawString(s, xx, y - ry, f, paint(col, al * (glow if k == 'g' else 1), blur=size * .2 if k == 'g' else 0)); xx += adv
    return wd


def caption(cv, zh, en, t, t0, t1, size=46):
    """「星夜」captions: Chinese (霞鹜文楷 + Cormorant) resolves character by character out of a blur; English (Cormorant italic) fades in under it"""
    if not (t0 - .1 <= t <= t1 + .1): return
    y, ye = H - 126, H - 78
    out = smooth(t1 - .35, t1, t)
    if EN:                                                     # English only: the English line takes the main slot and resolves the same way
        rs = runs(en, size * .86, lf=CG_SB); wd = sum(r[2] for r in rs); sc = min(1.0, 1640 / wd)
        if sc < 1: rs = runs(en, size * .86 * sc, lf=CG_SB); wd = sum(r[2] for r in rs)
        x = (W - wd) / 2; step = min(.035, .9 / max(1, len(en)))
        for j, (ch, f, adv) in enumerate(rs):
            u = clamp((t - t0 + .1 - j * step) / .55); a = eio(u) * (1 - out)
            if a > .003 and ch != ' ':
                dy = (1 - eout(u)) * 10
                cv.drawString(ch, x, y + 22 + dy, f, paint(T_IVORY, a * .35, blur=10))
                cv.drawString(ch, x, y + 22 + dy, f, paint(T_IVORY, a, blur=(1 - u) * 7 + out * 4))
            x += adv
        return
    rs = runs(zh, size, lf=CG_SB); wd = sum(r[2] for r in rs); x = (W - wd) / 2          # lining figures: '−1' must not read as '−I'
    for j, (ch, f, adv) in enumerate(rs):
        u = clamp((t - t0 + .1 - j * .035) / .55); a = eio(u) * (1 - out)
        if a > .003 and ch != ' ':
            dy = (1 - eout(u)) * 10
            cv.drawString(ch, x, y + dy, f, paint(T_IVORY, a * .35, blur=10))
            cv.drawString(ch, x, y + dy, f, paint(T_IVORY, a, blur=(1 - u) * 7 + out * 4))
        x += adv
    ke = smooth(t0 + .25, t0 + .8, t) * (1 - out)
    if ke > .003 and en:
        f = skia.Font(CG_I, 27); we = f.measureText(en)
        if we > 1640: f = skia.Font(CG_I, 27 * 1640 / we); we = f.measureText(en)
        cv.drawString(en, (W - we) / 2, ye, f, paint(T_SUB, ke))


# ---------------------------------------------------------------- particle text and morphs
_TP = {}


def _tokens(s):
    """'e^{iπ} + c_n' → [(text, level)] with level +1 superscript, −1 subscript ('^x' / '_x' take one character)"""
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch in '^_' and i + 1 < len(s):
            lv = 1 if ch == '^' else -1
            if s[i + 1] == '{': j = s.index('}', i); out.append((s[i + 2:j], lv)); i = j + 1
            else: out.append((s[i + 1], lv)); i += 2
        else: out.append((ch, 0)); i += 1
    return out


def text_pts(s, size, n, seed=0, tf=None):
    """n points sampled from the ink of s (supports ^{} / _{}), centred on (0, 0); missing glyphs fall back to Noto Serif; returns (pts, width)"""
    key = (s, size, n, seed, id(tf))
    if key in _TP: return _TP[key]
    tf = tf or WK
    items = []
    for txt, lv in _tokens(s):
        for ch in txt:
            sz = size * (.62 if lv else 1); f = skia.Font(tf if has(tf, ch) else NOTO, sz)
            items.append((ch, f, {1: -.42, -1: .18, 0: 0}[lv] * size, f.measureText(ch)))
    wd = sum(it[3] for it in items); hh = int(size * 1.8); ww = int(wd + 24)
    surf = skia.Surface(ww, hh); cv = surf.getCanvas(); cv.clear(skia.ColorBLACK); x = 12
    for ch, f, dy, adv in items: cv.drawString(ch, x, size * 1.25 + dy, f, paint((1, 1, 1))); x += adv
    m = surf.makeImageSnapshot().toarray()[..., 0].astype(float) / 255
    ys, xs = np.nonzero(m > .5); rr = np.random.default_rng(seed)
    pick = rr.choice(len(xs), n, replace=len(xs) < n)
    pts = np.stack([xs[pick] + rr.uniform(-.5, .5, n) - 12 - wd / 2, ys[pick] + rr.uniform(-.5, .5, n) - size * 1.25 + size * .36], 1)
    _TP[key] = (pts, wd); return _TP[key]


def morph(A, B, u, seed=0, swirl=.35, spread=.45):
    """screen-space morph A → B: each point leaves at its own time and arcs sideways (no straight-line tween)"""
    n = len(A); rr = np.random.default_rng(seed); d = rr.random(n) * spread; side = rr.choice((-1, 1), n) * (.5 + rr.random(n))
    v = np.clip((u - d) / (1 - spread), 0, 1); v = v * v * (3 - 2 * v)
    D = B - A; nrm = np.stack([-D[:, 1], D[:, 0]], 1)
    return A + D * v[:, None] + nrm * (swirl * side * np.sin(np.pi * v))[:, None]


# ---------------------------------------------------------------- output
class Writer:
    def __init__(self, path, fps=FPS):
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                                   '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)

    def write(self, rgba): self.p.stdin.write(rgba.tobytes())

    def close(self): self.p.stdin.close(); self.p.wait()
