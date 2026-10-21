"""Text-only brand marks for a channel profile that has no logo files yet: python engine/make_marks.py
Draws white transparent PNGs into the profile's marks/ from [channel] name / name_en and writes their geometry into [marks]:
  watermark      a ring (the dot sits in it) + the channel name     → wm_dot, wm_bbox, wm_letter_end, wm_name_end
  end_logo       the channel name, the brand dot as its full stop, name_en underneath → logo_dot, logo_dot_r, logo_center_x, logo_name_x
  end_logo_h     the name with the dot drawn in, one colour (print-cartoon / iso-diorama end cards tint it with their ink)
  [marks.en]     the same with name_en (BRAND_LANG=en), laid out on the same coordinates
The dot itself is never in the images: engine/brand.py draws it in colors.accent at these coordinates."""
import os, re
import skia
import channel as CH

C = CH.P['channel']; M = CH.P['marks']; EN = M.get('en', {})
CJK = skia.Typeface.MakeFromFile(CH.font('cjk', 'Heavy')); LAT = skia.Typeface.MakeFromFile(CH.font('mark_en'))
INK = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE)


def face(s): return LAT if all(ord(ch) < 0x2000 for ch in s) else CJK


def save(surf, name):
    d = os.path.join(CH.DIR, M.get('dir', 'marks')); os.makedirs(d, exist_ok=True)
    surf.makeImageSnapshot().save(os.path.join(d, name), skia.kPNG); print('wrote', name)


def watermark(name, out):
    f = skia.Font(face(name), 128); x0, base, ring = 236, 196, 52      # ring centred on the dot, name starts after it
    dot = (40 + ring + 12, 153.0)
    w = int(x0 + f.measureText(name) + 40); surf = skia.Surface(w, 240); cv = surf.getCanvas(); cv.clear(skia.ColorTRANSPARENT)
    p = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE, Style=skia.Paint.kStroke_Style, StrokeWidth=16); cv.drawCircle(*dot, ring, p)
    cv.drawString(name, x0, base, f, INK); save(surf, out)
    return dict(wm_dot=list(dot), wm_bbox=[int(dot[0] - ring - 8), int(dot[1] - ring - 8)], wm_letter_end=int(dot[0] + ring + 16), wm_name_end=w - 20)


def end_logo(name, sub, out, width=None):
    """width: make the name exactly this wide, so the English logo keeps the Chinese logo's dot position"""
    f = skia.Font(face(name), 300); fs = skia.Font(LAT, 110); r = 38.5
    if width: f.setSize(300 * width / f.measureText(name))
    wn = f.measureText(name); x0 = 300; base = 866.5 + r                    # the dot sits on the baseline after the name
    dot = (x0 + wn + 40 + r, base - r)
    W = int(dot[0] + r + 300); surf = skia.Surface(W, 1401); cv = surf.getCanvas(); cv.clear(skia.ColorTRANSPARENT)
    cv.drawString(name, x0, base, f, INK)
    if sub: cv.drawString(sub, x0, base + 200, fs, INK)
    save(surf, out)
    return dict(logo_dot=list(dot), logo_dot_r=r, logo_center_x=W / 2, logo_name_x=x0 - 10), wn


def logo_h(name, out):
    f = skia.Font(face(name), 200); wn = f.measureText(name); r = 26
    surf = skia.Surface(int(wn + 3 * r + 80), 300); cv = surf.getCanvas(); cv.clear(skia.ColorTRANSPARENT)
    cv.drawString(name, 40, 220, f, INK); cv.drawCircle(40 + wn + 14 + r, 220 - r, r, INK); save(surf, out)


def write_geometry(g):
    """these keys only exist in [marks]: replace each value in place (keeping its comment), or add it under the [marks] header"""
    p = os.path.join(CH.DIR, 'profile.toml'); s = open(p).read()
    for k, v in g.items():
        val = '[' + ', '.join(str(x) for x in v) + ']' if isinstance(v, list) else str(v)
        s, n = re.subn(rf'(?m)^({k}\s*=\s*)(\[[^\]]*\]|[^\s#]+)', lambda m: m.group(1) + val, s)
        if not n: s = s.replace('\n[marks]\n', f'\n[marks]\n{k} = {val}\n', 1)
    open(p, 'w').write(s); print('updated [marks] in', p)


if __name__ == '__main__':
    g = watermark(C['name'], M['watermark'])
    lg, wn = end_logo(C['name'], C.get('name_en', ''), M['end_logo']); g |= lg
    en = C.get('name_en') or C['name']
    watermark(en, EN.get('watermark', 'wm_en.png')); end_logo(en, '', EN.get('end_logo', 'logo_en.png'), width=wn)
    logo_h(C['name'], M.get('end_logo_h', 'logo_h.png'))
    write_geometry(g)
