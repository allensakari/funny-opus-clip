"""S019 石油越用越多 — style test: three new styles tell the same 10 s hook (vertical 1080×1920, 30 fps, no narration).
Shared here: the timeline, captions, counters and the soundtrack, so the three samples differ only in their look.
Numbers are placeholders for the samples (BP / Energy Institute Statistical Review, to be checked at node ①):
proven reserves 683.4 → 1,732.4 thousand million barrels (1980 → 2020); about 1.1 trillion barrels burned in between."""
import os, sys, math, subprocess
import numpy as np, skia

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(HERE + '/../../..')
sys.path.insert(0, ROOT + '/skill/styles/print-cartoon')
import print_cartoon_audio as A

W, H = 1080, 1920
FPS, DUR, BEAT = 30, 10.0, .5
FONTS = ROOT + '/assets/fonts/'


def tf(n): return skia.Typeface.MakeFromFile(FONTS + n)


def clamp(x, a=0., b=1.): return a if x < a else b if x > b else x
def smooth(a, b, x): u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u)
def eio(u): u = clamp(u); return u * u * (3 - 2 * u)
def eout(u): u = clamp(u); return 1 - (1 - u) ** 3
def eback(u, s=2.2): u = clamp(u) - 1; return 1 + u * u * ((s + 1) * u + s)
def lerp(a, b, u): return a + (b - a) * u
def fade(t, a, b, fi=.3, fo=.3): return smooth(a, a + fi, t) * (1 - smooth(b - fo, b, t))
def hx(s, a=1.): s = s.lstrip('#'); return skia.Color4f(*(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)), a)


# ---------------------------------------------------------------- the story beats (seconds; 120 BPM, one beat = 0.5 s)
PUMP = (0.5, 4.5)            # pumping: the reservoir drains, "burned" counter 0 → 11,000 亿桶, year 1980 → 2020
TWIST = 4.5                  # the drill goes deeper
FINDS = (5.5, 6.0, 6.5, 7.0)  # new reservoirs light up, one per beat
RES = (5.5, 7.5)             # proven reserves 6,830 → 17,320 亿桶, year 1980 → 2020
STAMP = 8.0                  # ×2.5
R80, R20, USED = 6830, 17320, 11000

CAPS = [(0.1, 2.0, '石油，越用越多？', 'The more oil we burn, the more there is?'),
        (2.0, 4.5, '1980 年以来，人类又烧掉了约 1.1 万亿桶', 'Since 1980 we have burned about 1.1 trillion barrels.'),
        (4.5, 8.0, '可探明储量，反而从 6,830 亿涨到 1.7 万亿桶', 'Yet proven reserves rose from 683 billion to 1.7 trillion.'),
        (8.0, 9.9, '这是怎么回事？', 'How?')]
FIND_LABELS = [('深海', 'DEEP SEA'), ('页岩', 'SHALE'), ('油砂', 'OIL SANDS'), ('重油', 'HEAVY OIL')]


def drained(t): return eio((t - PUMP[0]) / (PUMP[1] - PUMP[0]))           # 0 → 1 while pumping
def used(t): return USED * drained(t)
def reserves(t): return lerp(R80, R20, eio((t - RES[0]) / (RES[1] - RES[0])))
def year_pump(t): return int(round(lerp(1980, 2020, drained(t))))
def year_res(t): return int(round(lerp(1980, 2020, eio((t - RES[0]) / (RES[1] - RES[0])))))
def found(t, i): return eout((t - FINDS[i]) / .35)                       # 0 → 1 as reservoir i appears
def num(v): return f'{int(round(v)):,}'
def caps_at(t): return [(a, b, zh, en) for a, b, zh, en in CAPS if a - .1 <= t <= b + .1]


# ---------------------------------------------------------------- soundtrack (shared): 120 BPM groove + events
def soundtrack(path):
    m = A.Mix(DUR); mf = A.mf
    prog = [(53, 57, 60), (50, 53, 57), (46, 50, 53), (48, 52, 55)]       # F  Dm  Bb  C
    for bar in range(5):
        ch = prog[bar % 4]; t0 = bar * 2
        m.add(t0, A.pad([mf(n) for n in ch], 2.1), .5)
        for k in range(4):
            tb = t0 + k * BEAT
            if bar >= 1 or k >= 1: m.add(tb, A.kick(), .55 if tb < TWIST else .75)
            m.add(tb, A.bass(mf(ch[0] - 12), .4), .28)
            if tb >= TWIST: m.add(tb + .25, A.scanner(.03), .05, .3)
        if bar >= 2:
            for k in range(8): m.add(t0 + k * .25, A.marimba(mf(ch[k % 3] + 12 + (12 if k % 4 == 3 else 0))), .08, -.2 + .4 * (k % 2))
    for k in range(8): m.add(PUMP[0] + k * BEAT, A.wood(420), .35)          # the pump's clunk on every beat
    for x in np.arange(PUMP[0], PUMP[1], .125): m.add(x, A.wood(2400), .05)  # counter ticks
    m.add(TWIST - .42, A.swoosh(True), .3); m.add(TWIST, A.kick(), 1.)
    x = A.tt(1.2); m.add(TWIST, A.lp(np.sin(2 * np.pi * np.cumsum(70 - 30 * x) / A.SR), 300) * A.env(1.2, .01, .5), .6)   # the drill's rumble
    for i, tf_ in enumerate(FINDS): m.add(tf_, A.bell(mf(72 + (0, 4, 7, 12)[i])), .18); m.add(tf_, A.pop(), .2)
    for x in np.arange(RES[0], RES[1], .1): m.add(x, A.wood(2600), .04)
    m.add(STAMP, A.kick(), 1.); m.add(STAMP, A.clap(), .5); m.add(STAMP, A.bell(mf(77), 2.), .15)
    A.save(m.stereo() * .9, path)


# ---------------------------------------------------------------- render loop: frame(t, canvas) draws one frame
def run(name, frame, surf_draw=None):
    """frame(t) → H×W×4 uint8 array. --still t … writes PNGs; otherwise renders build/<name>.mp4 with the soundtrack."""
    build = HERE + '/build'; os.makedirs(build, exist_ok=True)
    a = sys.argv[1:]
    if a and a[0] == '--still':
        import PIL.Image
        for s in a[1:]: PIL.Image.fromarray(frame(float(s))[..., :3]).save(f'{build}/{name}_{float(s):05.2f}.png')
        return
    wav = build + '/soundtrack.wav'
    if not os.path.exists(wav): soundtrack(wav)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                            '-shortest', f'{build}/{name}.mp4'], stdin=subprocess.PIPE)
    for f in range(int(DUR * FPS)): enc.stdin.write(np.ascontiguousarray(frame(f / FPS)).tobytes())
    enc.stdin.close(); enc.wait(); print('ok', f'{build}/{name}.mp4')
