"""招牌字幕 + 黄点水印 preview clips: python engine/style_preview.py <background.png> <out_dir>
-> preview_<style>.mp4 (8 s each) + preview_sheet.jpg (one still per style)"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, skia
from brand import *
import captions as C

BGP, OUT = sys.argv[1], sys.argv[2]
FPS, T = 30, 8.0
CAPS = [dict(show='此刻，有[34,967]个人造物体', a=.25, b=1.9), dict(show='正从你头顶飞过', a=2.05, b=3.1),
        dict(show='每 3 颗在用卫星', a=3.35, b=4.3), dict(show='就有[2]颗属于同一家公司', a=4.4, b=5.8)]
bg = skia.Image.open(BGP)


def frame(t, style):
    surf = skia.Surface(W, H); cv = surf.getCanvas(); cv.clear(skia.Color4f(*BG, 1).toColor())
    z = 1 + .03 * t / T; cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-W / 2, -H / 2)
    cv.drawImage(bg, 0, 0); cv.restore()
    scrim(cv, 0, 760, .55, 0); scrim(cv, 1150, 1700, 0, .5)
    v = count(t, .2, 1.6, 0, 34967)
    bignum(cv, fade(t, 0, 3.2, .15, .3), fmt_int(v), '个', label='此刻在轨的人造物体', src='CelesTrak 编目 · 2026-10-09', y=600, pop=pop_k(t, 1.6))
    bignum(cv, fade(t, 3.3, 6.2, .2, .3), '2/3', '', label='在用卫星里的星链', src='CelesTrak · 2026-10-09', y=600, size=230, pop=pop_k(t, 4.45))
    C.draw(cv, CAPS, t, style)
    watermark(cv, t, T, expand_at=2.1)
    return surf.makeImageSnapshot().toarray()


os.makedirs(OUT, exist_ok=True); sheet = []
for style in ('period', 'bar', 'odo'):
    p = f'{OUT}/preview_{style}.mp4'
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', p], stdin=subprocess.PIPE)
    for i in range(int(T * FPS)):
        a = frame(i / FPS, style); enc.stdin.write(a.tobytes())
        if i == int(5.2 * FPS): sheet.append(a.copy())
        if style == 'period' and i in (int(2.9 * FPS), int(7.6 * FPS)): skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType).save(f'{OUT}/wm_{i / FPS:.1f}s.jpg', skia.kJPEG, 90)
    enc.stdin.close(); enc.wait(); print('ok', p)
s = np.concatenate([x[::2, ::2] for x in sheet], 1)
skia.Image.fromarray(np.ascontiguousarray(s), colorType=skia.kRGBA_8888_ColorType).save(f'{OUT}/preview_sheet.jpg', skia.kJPEG, 90); print('sheet')
