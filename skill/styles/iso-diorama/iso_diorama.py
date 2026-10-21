"""iso-diorama 等距微缩 · 画面工具包 —— 源自 S019《石油，越用越多》风格样片（2026-10-21 用户选定）。
低多边形 3D 小场景（moderngl：正交等距相机、暖色太阳光 + 天光、5×5 PCF 阴影、4× MSAA）→ skia 合成：底色、接触阴影、
移轴虚化、暗角，再叠白色药丸卡片 / 字幕 / 标签。横版默认，VERT=1 出竖版（和 print-cartoon 一样）。
期目录 film.py：每帧 build(t) 返回一个 Scene，camera(t) 返回 (target, 半高)；frame() 调 render() + composite() + 叠加层。"""
import os, math
import numpy as np, skia

ROOT = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../../..')
FONTS = ROOT + '/assets/fonts/'
V = bool(os.environ.get('VERT'))
W, H = (1080, 1920) if V else (1920, 1080)
FPS = int(os.environ.get('FPS', 60))


def LV(land, vert): return vert if V else land


def _tf(n): return skia.Typeface.MakeFromFile(FONTS + n)
ZH_B, ZH_H = _tf('SourceHanSansCN-Bold.otf'), _tf('SourceHanSansCN-Heavy.otf')
EN_B, EN_K = _tf('Nunito-ExtraBold.ttf'), _tf('Nunito-Black.ttf')


def clamp(x, a=0., b=1.): return a if x < a else b if x > b else x
def smooth(a, b, x): u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u)
def eio(u): u = clamp(u); return u * u * (3 - 2 * u)
def eout(u): u = clamp(u); return 1 - (1 - u) ** 3
def eback(u, s=2.2): u = clamp(u) - 1; return 1 + u * u * ((s + 1) * u + s)
def lerp(a, b, u): return a + (b - a) * u
def fade(t, a, b, fi=.3, fo=.3): return smooth(a, a + fi, t) * (1 - smooth(b - fo, b, t))


def rgb(s): s = s.lstrip('#'); return np.array([int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
def c4(s, a=1.): r = rgb(s); return skia.Color4f(float(r[0]), float(r[1]), float(r[2]), a)


# ---------------------------------------------------------------- palette: 3D materials (linear-ish RGB) and 2D overlay colours
PAL = {k: rgb(v) for k, v in dict(
    bg='#FFF6EA',                                                    # backdrop (also the GL clear colour)
    grass='#8FC27F', grass2='#7BB06E', tree='#5FA070', trunk='#8A5A3C',
    sand='#EDCB8E', shale='#D99B6A', cap='#BC7A5B', deep='#965A4A', base='#6E4840', base2='#563832',
    oil='#2A2226', teal='#2F6F73', red='#E2553B', cream='#F7EFE3', steel='#8A8A8E', gold='#F2A93B', water='#6FB7D6',
).items()}
INK, CARD, TOMATO, GOLD = c4('#2D2A33'), c4('#FFFFFF'), c4('#E2553B'), c4('#F2A93B')


# ---------------------------------------------------------------- unit meshes (centred, size 1): (positions, normals) as triangle lists
def _box():
    v = []
    for ax in range(3):
        for s in (-1, 1):
            n = np.zeros(3); n[ax] = s
            u, w = [a for a in range(3) if a != ax]
            q = []
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = np.zeros(3); p[ax] = s; p[u] = a; p[w] = b; q.append(p)
            if s * np.dot(np.cross(q[1] - q[0], q[2] - q[0]), n) < 0: q = q[::-1]
            for i in (0, 1, 2, 0, 2, 3): v.append((q[i] * .5, n))
    return np.array([a for a, _ in v], np.float32), np.array([b for _, b in v], np.float32)


def _cyl(n=24):
    P, N = [], []
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        c0, s0, c1, s1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
        for p, q in (((c0, -.5, s0), (c0, s0)), ((c1, .5, s1), (c1, s1)), ((c1, -.5, s1), (c1, s1)),
                     ((c0, -.5, s0), (c0, s0)), ((c0, .5, s0), (c0, s0)), ((c1, .5, s1), (c1, s1))):
            P.append(p); N.append((q[0], 0, q[1]))
        P += [(0, .5, 0), (c1, .5, s1), (c0, .5, s0)]; N += [(0, 1, 0)] * 3
        P += [(0, -.5, 0), (c0, -.5, s0), (c1, -.5, s1)]; N += [(0, -1, 0)] * 3
    P = np.array(P, np.float32); P[:, [0, 2]] *= .5
    return P, np.array(N, np.float32)


def _sph(nu=18, nv=10):
    def pt(i, j):
        th, ph = math.pi * i / nv, 2 * math.pi * j / nu
        return (math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph))
    P = []
    for i in range(nv):
        for j in range(nu):
            a, b, c_, d = pt(i, j), pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1); P += [a, c_, b, a, d, c_]
    P = np.array(P, np.float32) * .5; return P, P * 2


def _cone(n=10):
    P, N = [], []
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p0, p1, top = (math.cos(a0) * .5, -.5, math.sin(a0) * .5), (math.cos(a1) * .5, -.5, math.sin(a1) * .5), (0, .5, 0)
        nn = np.cross(np.subtract(p1, p0), np.subtract(top, p0)); nn = -nn / np.linalg.norm(nn)
        P += [p0, top, p1]; N += [nn] * 3
        P += [(0, -.5, 0), p0, p1]; N += [(0, -1, 0)] * 3
    return np.array(P, np.float32), np.array(N, np.float32)


BOX, CYL, SPH, CONE = _box(), _cyl(), _sph(), _cone()


def rot(axis, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    if axis == 'x': return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float32)
    if axis == 'y': return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float32)


class Scene:
    """add(mesh, centre, size, colour, R=rotation, gloss=0–1, pivot=world point to rotate about). gloss 1 = wet / oily (specular + gold rim)"""
    def __init__(self): self.chunks = []

    def add(self, mesh, pos, size, col, R=None, gloss=0., pivot=None):
        P, N = mesh; sz = np.asarray(size, np.float32); P = P * sz
        N = N / np.maximum(np.abs(sz), 1e-6); N = N / np.linalg.norm(N, axis=1, keepdims=True)
        if R is not None:
            P = (P + np.asarray(pos) - pivot) @ R.T + pivot - np.asarray(pos) if pivot is not None else P @ R.T
            N = N @ R.T
        P = P + np.asarray(pos, np.float32)
        col = np.broadcast_to(np.asarray(col, np.float32), (len(P), 3)); g = np.full((len(P), 1), gloss, np.float32)
        self.chunks.append(np.hstack([P, N, col, g]).astype(np.float32))

    def tree(self, x, z, s=1., col=None, y=0.):
        self.add(CYL, (x, y + .3 * s, z), (.08 * s, .18 * s, .08 * s), PAL['trunk'])
        self.add(CONE, (x, y + .9 * s + .25 * s, z), (.6 * s, 1.2 * s, .6 * s), PAL['tree'] if col is None else col)

    def data(self): return np.vstack(self.chunks).astype('f4').tobytes() if self.chunks else b''


# ---------------------------------------------------------------- cameras
VIEW_DIR = np.array([1, .78, 1.05]); VIEW_DIR = VIEW_DIR / np.linalg.norm(VIEW_DIR)     # sees the +x, +y, +z faces
LIGHT = np.array([.35, 1., .62]); LIGHT = LIGHT / np.linalg.norm(LIGHT)                # sun from the upper front; the +z face is the lit one


def look_at(eye, tgt, up=(0, 1, 0)):
    f = np.subtract(tgt, eye); f = f / np.linalg.norm(f); s = np.cross(f, up); s /= np.linalg.norm(s); u = np.cross(s, f)
    M = np.eye(4, dtype=np.float32); M[0, :3], M[1, :3], M[2, :3] = s, u, -f; M[:3, 3] = -M[:3, :3] @ np.asarray(eye); return M


def ortho(hw, hh, n, f):
    M = np.eye(4, dtype=np.float32); M[0, 0], M[1, 1], M[2, 2], M[2, 3] = 1 / hw, 1 / hh, -2 / (f - n), -(f + n) / (f - n); return M


def iso_vp(target, hh, view_dir=VIEW_DIR):
    """orthographic camera looking at target; hh = half the frame height in world units (smaller = closer)"""
    target = np.asarray(target, np.float32)
    return ortho(hh * W / H, hh, 1, 80) @ look_at(target + view_dir * 30, target)


def light_vp(target=(0, -2, 0), extent=7.5, light=LIGHT):
    target = np.asarray(target, np.float32); return ortho(extent, extent, 1, 80) @ look_at(target + light * 30, target)


def project(VP, p):
    q = VP @ np.array([*p, 1.]); return (q[0] * .5 + .5) * W, (1 - (q[1] * .5 + .5)) * H


# ---------------------------------------------------------------- GL renderer (created on first use: one context per process)
_GL = {}
_VS = '''#version 330
uniform mat4 VP; uniform mat4 LVP;
in vec3 p; in vec3 n; in vec3 c; in float g;
out vec3 vn; out vec3 vc; out float vg; out vec4 ls;
void main(){ vn = n; vc = c; vg = g; ls = LVP * vec4(p, 1.); gl_Position = VP * vec4(p, 1.); }'''
_FS = '''#version 330
uniform sampler2D SH; uniform vec3 L; uniform vec3 V; uniform float SMN; uniform vec3 SUN; uniform vec3 SKY;
in vec3 vn; in vec3 vc; in float vg; in vec4 ls; out vec4 o;
void main(){
  vec3 n = normalize(vn);
  vec3 s = ls.xyz / ls.w * .5 + .5; float sh = 0.;
  for (int i = -2; i <= 2; i++) for (int j = -2; j <= 2; j++) {
    float d = texture(SH, s.xy + vec2(i, j) / SMN * 1.5).r; sh += (s.z - .004 > d) ? 0. : 1.; }
  sh /= 25.;
  if (any(lessThan(s.xy, vec2(0.))) || any(greaterThan(s.xy, vec2(1.)))) sh = 1.;   // outside the shadow map = lit
  float dif = max(dot(n, L), 0.) * mix(.35, 1., sh);
  vec3 sky = mix(vec3(.62,.55,.52), vec3(1.,.97,.93), n.y * .5 + .5) * SKY;
  vec3 col = vc * (sky * .58 + SUN * dif * .62);
  vec3 h = normalize(L + V); col += vg * pow(max(dot(n, h), 0.), 40.) * vec3(1.,.9,.7) * sh;
  col += vg * .9 * pow(1. - max(dot(n, V), 0.), 2.) * vec3(.95,.62,.2);             // gold rim on glossy (oily) things
  col += vg * .07 * vec3(.95,.62,.2);                                               // and a faint warm glow, so 'counted' oil reads as lit
  o = vec4(pow(col, vec3(.98)), 1.);
}'''


def _gl():
    if _GL: return _GL
    import moderngl
    ctx = moderngl.create_standalone_context(require=330); ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
    SM = 4096; st = ctx.depth_texture((SM, SM))                                       # finer than screen pixels, so shadow edges don't crawl when the camera drifts; st.compare_func = ''; st.repeat_x = st.repeat_y = False
    prog = ctx.program(vertex_shader=_VS, fragment_shader=_FS)
    prog_s = ctx.program(vertex_shader='#version 330\nuniform mat4 LVP; in vec3 p; void main(){ gl_Position = LVP * vec4(p, 1.); }',
                         fragment_shader='#version 330\nvoid main(){}')
    vbo = ctx.buffer(reserve=4 * 10 * 400000)
    _GL.update(ctx=ctx, SM=SM, st=st, sfbo=ctx.framebuffer(depth_attachment=st), prog=prog, prog_s=prog_s, vbo=vbo,
               ms=ctx.framebuffer(ctx.renderbuffer((W, H), 4, samples=4), ctx.depth_renderbuffer((W, H), samples=4)),
               out=ctx.framebuffer(ctx.renderbuffer((W, H), 4)),
               vao=ctx.vertex_array(prog, [(vbo, '3f 3f 3f 1f', 'p', 'n', 'c', 'g')]),
               vao_s=ctx.vertex_array(prog_s, [(vbo, '3f 28x', 'p')]))
    return _GL


SUN0, SKY0 = (1., .95, .86), (1., 1., 1.)


def render(scene, VP, LVP=None, sun=SUN0, sky=SKY0):
    """→ H×W×4 uint8, premultiplied (cleared to transparent black, so edges carry no fringe on a dark backdrop); alpha 0 where nothing was drawn.
    sun / sky tint the light per scene (a cold morning, a desert sunset)"""
    g = _gl(); ctx = g['ctx']; LVP = light_vp() if LVP is None else LVP
    data = scene.data(); g['vbo'].orphan(max(len(data), 40)); g['vbo'].write(data); n = len(data) // 40
    g['sfbo'].use(); g['sfbo'].clear(depth=1.); ctx.viewport = (0, 0, g['SM'], g['SM'])
    g['prog_s']['LVP'].write(LVP.T.astype('f4').tobytes()); g['vao_s'].render(vertices=n)
    g['ms'].use(); ctx.viewport = (0, 0, W, H); g['ms'].clear(0., 0., 0., 0.)
    p = g['prog']; p['VP'].write(VP.T.astype('f4').tobytes()); p['LVP'].write(LVP.T.astype('f4').tobytes())
    p['L'].value = tuple(LIGHT); p['V'].value = tuple(VIEW_DIR); p['SMN'].value = float(g['SM']); p['SUN'].value = tuple(map(float, sun)); p['SKY'].value = tuple(map(float, sky)); g['st'].use(0); p['SH'].value = 0
    g['vao'].render(vertices=n)
    ctx.copy_framebuffer(g['out'], g['ms'])
    return np.frombuffer(g['out'].read(components=4), np.uint8).reshape(H, W, 4)[::-1].copy()


# ---------------------------------------------------------------- 2D: compositing and overlays
def paint(col, a=1., w=0.):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(col.fR, col.fG, col.fB, col.fA * a))
    if w: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w); p.setStrokeCap(skia.Paint.kRound_Cap)
    return p


def soft(col, a=1.):
    """a fill with the style's soft drop shadow (cards, pills, stamps)"""
    p = paint(col, a); p.setImageFilter(skia.ImageFilters.DropShadow(0, 8, 14, 14, skia.Color4f(.25, .15, .1, .18 * a))); return p


_BRAND = []


def _qc(kind, label, rect, a):
    """with SHUSHUO_QC=1 (engine/qc.py) every text box is registered in brand.QC, mapped through the canvas transform"""
    if not _BRAND:
        import sys; sys.path.insert(0, ROOT + '/engine'); import brand; _BRAND.append(brand)
    _BRAND[0].qc_box(kind, label, rect.left(), rect.top(), rect.right(), rect.bottom(), a)


QC_ON = bool(os.environ.get('SHUSHUO_QC'))


def text(c, s, x, y, font, size, col=INK, a=1., align='c', kind='text'):
    if a <= .003: return 0
    f = skia.Font(font, size); w = f.measureText(s)
    x0 = x - w / 2 if align == 'c' else x - w if align == 'r' else x
    c.drawString(s, x0, y, f, paint(col, a))
    if QC_ON: _qc(kind, s, c.getTotalMatrix().mapRect(skia.Rect.MakeLTRB(x0, y - size * .86, x0 + w, y + size * .18)), a)
    return w


def backdrop(c, top, bot=None, horiz=False):
    """a two-colour gradient backdrop (rgb arrays); horiz = left → right (two places side by side)"""
    bot = top if bot is None else bot
    k = [skia.Color4f(*map(float, top), 1), skia.Color4f(*map(float, bot), 1)]
    pts = [(0, 0), (W, 0)] if horiz else [(0, 0), (0, H)]
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear(pts, k)))


def composite(c, img, focus_y, contact=None, blur=9, band=(760, 700), bg=None, decor=None):
    """backdrop → decor (clouds, sun …) → soft contact shadow under the diorama (contact = (x, y, width) in px) → the 3D image → tilt-shift → vignette.
    focus_y: the sharp band's centre (px); band = (blur ramp above, below). bg = (top, bottom[, horiz]) colours, None = the cream PAL['bg']"""
    si = skia.Image.fromarray(img, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    if bg is None: c.drawColor(skia.Color4f(*map(float, PAL['bg']), 1))
    else: backdrop(c, *bg)
    if decor: decor(c)
    if contact:
        x, y, w = contact
        sp = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.35, .2, .12, .16), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40))
        c.drawOval(skia.Rect.MakeXYWH(x - w / 2, y + 40, w, w / 6), sp)
    c.drawImage(si, 0, 0)
    c.saveLayer()
    c.drawImage(si, 0, 0, skia.SamplingOptions(), skia.Paint(ImageFilter=skia.ImageFilters.Blur(blur, blur)))
    k0, k1 = skia.Color4f(0, 0, 0, 1), skia.Color4f(0, 0, 0, 0)
    m = skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, focus_y - band[0]), (0, focus_y + band[1])], [k0, k1, k1, k0], [0, .4, .62, 1]))
    m.setBlendMode(skia.BlendMode.kDstIn); c.drawRect(skia.Rect.MakeWH(W, H), m)
    c.restore()
    vg = skia.Paint(Shader=skia.GradientShader.MakeRadial((W / 2, H * .55), max(W, H) * .7, [skia.Color4f(0, 0, 0, 0), skia.Color4f(.3, .16, .1, .12)], [.6, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), vg)


def counter_card(c, l, tp, w, label, value, unit, col=INK, a=1., h=170):
    """white rounded card: small label, big number, unit on the right"""
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(l, tp, w, h), 36, 36), soft(CARD, .94 * a))
    text(c, label, l + 34, tp + 52, ZH_B, 28, INK, .6 * a, 'l')
    text(c, value, l + 32, tp + 132, EN_K, 80, col, a, 'l', kind='number')
    text(c, unit, l + w - 32, tp + 132, ZH_B, 28, INK, .55 * a, 'r')


def stamp_pill(c, s, x, y, u, col=TOMATO, rot_=8, size=96, a=1.):
    """a tomato pill that pops in (u = seconds since it landed); a fades it (never let it vanish in one frame)"""
    if u < 0 or a <= .003: return
    k = eback(smooth(0, .35, u)); c.save(); c.translate(x, y); c.rotate(rot_); c.scale(k, k)
    tf = ZH_H if any('\u4e00' <= ch <= '\u9fff' for ch in s) else EN_K                # Nunito has no CJK glyphs
    f = skia.Font(tf, size); w = f.measureText(s)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 - 26, -size * .92, w + 52, size * 1.2), size * .6, size * .6), soft(col, a))
    text(c, s, 0, 0, tf, size, CARD, a); c.restore()


def pill_label(c, s, x, y, a=1., col=TOMATO, size=30):
    """a small white pill label sitting above a projected 3D point (x, y)"""
    if a <= 0: return
    f = skia.Font(ZH_H, size); w = f.measureText(s) + 34
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - size * 1.33, w, size * 1.73), size * .87, size * .87), soft(CARD, .96 * a))
    text(c, s, x, y - size * .13, ZH_H, size, col, a, kind='tag')


def wrap2(s, font, size, maxw):
    """one line if it fits, otherwise break once at the first comma"""
    if skia.Font(font, size).measureText(s) < maxw or '，' not in s: return [s]
    a, b = s.split('，', 1); return [a + '，', b]


def captions(c, t, caps):
    """top captions: Chinese Source Han Sans Bold in ink, English Nunito below at 55%"""
    for a0, a1, zh, en in caps:
        if not a0 - .1 <= t <= a1 + .1: continue
        u = fade(t, a0, a1, .25, .2); dy = (1 - eout((t - a0) / .3)) * 14
        sz = LV(56, 60); lines = wrap2(zh, ZH_B, sz, LV(1700, 940)); y = LV(118, 268) + dy
        for ln in lines: text(c, ln, W / 2, y, ZH_B, sz, INK, u, kind='caption'); y += sz * 1.27
        text(c, en, W / 2, y - 18, EN_B, LV(28, 30), INK, u * .55, kind='caption')


# ---------------------------------------------------------------- 2D scenery behind / in front of the diorama (so each place has its own sky)
def _blob(c, x, y, w, col, a):
    p = paint(col, a); p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2))
    for dx, dy, r in ((-.32, .1, .26), (-.05, -.08, .34), (.27, .06, .28), (0, .14, .3)): c.drawCircle(x + dx * w, y + dy * w, r * w, p)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - .55 * w, y + .05 * w, 1.1 * w, .32 * w), .16 * w, .16 * w), p)


def clouds(c, t, n=4, seed=1, y0=.18, y1=.5, a=.85, speed=14., col=CARD):
    """soft white clouds drifting left → right; each fades at the frame edges (no pop when it wraps)"""
    r = np.random.default_rng(seed)
    for i in range(n):
        w = r.uniform(.09, .16) * max(W, H); span = W + 2 * w
        x = (r.uniform(0, span) + t * speed * r.uniform(.7, 1.3)) % span - w; y = H * r.uniform(y0, y1)
        e = clamp((x + w) / (w * 1.2)) * clamp((W + w - x) / (w * 1.2))
        _blob(c, x, y, w, col, a * e)


def sun(c, x, y, r, col, a=1.):
    """a flat sun disc with a soft glow"""
    g = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x, y), r * 2.6, [skia.Color4f(col.fR, col.fG, col.fB, .35 * a), skia.Color4f(col.fR, col.fG, col.fB, 0)]))
    c.drawCircle(x, y, r * 2.6, g); c.drawCircle(x, y, r, paint(col, a))


def snow(c, t, n=70, seed=3, a=.9):
    """flakes falling in front of the diorama, each wrapping smoothly (fades in at the top, out at the bottom)"""
    r = np.random.default_rng(seed)
    for i in range(n):
        sp = r.uniform(40, 90); ph = r.uniform(0, H + 80); x0 = r.uniform(0, W); sz = r.uniform(3, 8)
        y = (ph + t * sp) % (H + 80) - 40; x = x0 + 18 * math.sin(t * r.uniform(.6, 1.2) + i)
        e = clamp((y + 40) / 160) * clamp((H + 40 - y) / 160)
        c.drawCircle(x, y, sz, paint(CARD, a * e))


def grid(c, step, col, a=.35, w=1.5):
    """a faint blueprint grid (the X-ray chapter)"""
    p = paint(col, a, w)
    for x in range(0, W + 1, step): c.drawLine(x, 0, x, H, p)
    for y in range(0, H + 1, step): c.drawLine(0, y, W, y, p)


def birds(c, t, n=3, seed=5, a=.6, col=INK):
    """little 'v' birds crossing slowly"""
    r = np.random.default_rng(seed)
    for i in range(n):
        span = W + 200; x = (r.uniform(0, span) + t * r.uniform(30, 50)) % span - 100; y = H * r.uniform(.2, .36) + 8 * math.sin(t * 1.3 + i)
        fl = 10 * math.sin(t * 7 + i * 2); s = r.uniform(12, 18); e = clamp((x + 100) / 150) * clamp((W + 100 - x) / 150)
        pth = skia.Path(); pth.moveTo(x - s, y - fl * .6); pth.quadTo(x - s * .4, y - fl * .2 - 4, x, y); pth.quadTo(x + s * .4, y - fl * .2 - 4, x + s, y - fl * .6)
        c.drawPath(pth, paint(col, a * e, 3))


# ---------------------------------------------------------------- full-frame cards: chapter card, theme card, end logo
PANEL = c4('#FFF8EE')


def wipe(c, t, wipes, title=None, hold=0.):
    """chapter card: a cream panel with a soft shadow slides in from the right (0.35 s), a tomato number pill pops, the title types in,
    then the panel slides out to the left. The scene changes at t0 while the panel covers the frame (t0 − 0.5 … t0 + 0.55).
    wipes = [(t0, '01', '中文标题', 'ENGLISH'), …]; the first card also carries the film title.
    hold = extra seconds the card stays up (S019: 2 s, one bar — under 1 s was too short to read the title)."""
    for t0, num, zh, en, *_ in wipes:
        u = t - (t0 - .85)
        if not 0 <= u <= 1.75 + hold: continue
        if u < .35: x0 = lerp(W + 60, 0, eio(u / .35))
        elif u < 1.4 + hold: x0 = 0
        else: x0 = lerp(0, -W - 60, eio((u - 1.4 - hold) / .35))
        c.save(); c.translate(x0, 0)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-40, -40, W + 80, H + 80), 60, 60), soft(PANEL))
        ta = smooth(.3, .45, u) * (1 - smooth(1.38 + hold, 1.5 + hold, u)); dx = (1 - eout((u - .3) / .5)) * 60
        cx, cy = W / 2 + dx, H / 2
        if title is not None and num == wipes[0][1]:
            ts = LV(84, 80); lines = wrap2(title[0], ZH_H, ts, W - 140) if V else [title[0]]
            if V and len(lines) == 1 and skia.Font(ZH_H, ts).measureText(title[0]) > W - 140: lines = [title[0][:len(title[0]) // 2], title[0][len(title[0]) // 2:]]
            yy = cy - LV(170, 230) - (len(lines) - 1) * ts * .6
            for ln in lines: text(c, ln, cx, yy, ZH_H, ts, INK, ta); yy += ts * 1.18
            text(c, title[1], cx, yy - ts * .4, EN_B, LV(26, 26), INK, ta * .55)
            cy += LV(70, 60)
        stamp_pill(c, num, cx, cy - 40, u - .3, TOMATO, 0, 54, ta)
        n_ = int(clamp((u - .35) / .045, 0, len(zh)))
        f = skia.Font(ZH_H, LV(104, 96)); full = f.measureText(zh); x = cx - full / 2
        for k, ch in enumerate(zh[:n_]):
            g = eback(clamp((u - .35 - k * .045) / .16)); w_ = f.measureText(ch)
            c.save(); c.translate(x + w_ / 2, cy + 90); c.scale(g, g); c.drawString(ch, -w_ / 2, 0, f, paint(INK, ta)); c.restore(); x += w_
        text(c, en, cx, cy + 150, EN_B, 28, INK, ta * .55 * smooth(.7, .9, u))
        c.restore()


def theme_card(c, t, t0, t1, lines, en='', sub='', sub_en='', emph='', lines_v=None):
    """the film's thesis: cream panel fades up, the lines type in (emph in tomato), then a small line floats in below"""
    if not t0 - .1 < t < t1 + .3: return
    if V and lines_v: lines = lines_v
    c.drawRect(skia.Rect.MakeWH(W, H), paint(PANEL, .94 * smooth(t0, t0 + .35, t) * (1 - smooth(t1, t1 + .3, t))))
    a = fade(t, t0, t1, .3, .35); size = LV(92, 96); y0 = H / 2 - LV(110, 230)
    for li, line in enumerate(lines):
        tl = t0 + .15 + li * .55; n = int(clamp((t - tl) / .04, 0, len(line)))
        f = skia.Font(ZH_H, size); full = f.measureText(line); k = min(1, (W - 120) / full)
        c.save(); c.translate(W / 2, y0 + li * size * 1.35 * k); c.scale(k, k); x = -full / 2
        e0 = line.find(emph) if emph else -1
        for ci, ch in enumerate(line[:n]):
            c.drawString(ch, x, 0, f, paint(TOMATO if e0 >= 0 and e0 <= ci < e0 + len(emph) else INK, a)); x += f.measureText(ch)
        c.restore()
    yb = y0 + (len(lines) - 1) * size * 1.35
    if en: text(c, en, W / 2, yb + LV(80, 90), EN_B, LV(30, 28), INK, a * .55 * smooth(t0 + 1.6, t0 + 2.0, t))
    if sub:
        u = smooth(t0 + 2.4, t0 + 2.8, t)
        c.drawLine(W / 2 - 60, yb + LV(140, 160), W / 2 + 60, yb + LV(140, 160), paint(INK, a * u * .35, 3))
        text(c, sub, W / 2, yb + LV(215, 240), ZH_B, LV(44, 40), INK, a * u)
        if sub_en: text(c, sub_en, W / 2, yb + LV(265, 292), EN_B, LV(28, 26), INK, a * u * .55)


import sys; sys.path.insert(0, ROOT + '/engine'); import channel as _CH       # the channel's horizontal logo (profile marks.end_logo_h), tinted with the ink colour
LOGO = skia.Image.open(_CH.mark(_CH.P['marks'].get('end_logo_h', _CH.P['marks']['end_logo'])))


def end_logo(c, t, t0, t1):
    """only the logo, on the cream panel (no slogan), between t0 and t1"""
    if not t0 - .1 < t < t1 + .1: return
    a = fade(t, t0, t1, .5, .5)
    c.drawRect(skia.Rect.MakeWH(W, H), paint(PANEL, a))
    s = LV(.42, .33) * lerp(.96, 1, eout((t - t0) / 1.5))
    c.save(); c.translate(W / 2, H / 2); c.scale(s, s)
    p = paint(INK, a); c.drawImage(LOGO, -LOGO.width() / 2, -LOGO.height() / 2, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()
