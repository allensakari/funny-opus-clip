"""English brand marks for English-only cuts (BRAND_LANG=en): the profile's [marks.en] watermark and end_logo images.
Same canvases and the same dot anchors as the Chinese files, so brand.watermark / _end_card need no new geometry:
  wm      Λ copied from the watermark image (dot inside it at marks.wm_dot), then marks.en.name where the Chinese name was;
  logo_v  ALLEN copied from the end logo (moved up), then marks.en.lines with the full stop = the dot at marks.logo_dot.
The crop rows / columns below are specific to the 数说世界 marks.
usage: python engine/brand_en.py"""
import os
import numpy as np, skia
import channel as CH

M = CH.P['marks']; EN = M['en']
FONT = skia.Typeface.MakeFromFile(CH.font('mark_en'))
WHITE = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE)


def wm():
    src = skia.Image.open(CH.mark(M['watermark'])).toarray()
    f = skia.Font(FONT, 175); s = EN['name']; x0 = 259
    b = skia.Rect(); f.measureText(s, bounds=b)
    w = int(x0 + f.measureText(s) + 50); h = src.shape[0]
    surf = skia.Surface(w, h); cv = surf.getCanvas(); cv.clear(skia.ColorTRANSPARENT)
    cv.drawImage(skia.Image.fromarray(np.ascontiguousarray(src[:, :216])), 0, 0)
    base = 192                                                     # caps centred on the Λ (y 47–201)
    cv.drawString(s, x0, base, f, WHITE)
    surf.makeImageSnapshot().save(CH.mark(EN['watermark']), skia.kPNG); print(EN['watermark'], w, h)


def logo_v():
    src = skia.Image.open(CH.mark(M['end_logo'])).toarray(); h, w = src.shape[:2]
    allen = np.ascontiguousarray(src[353:408])                         # the ALLEN band, full width
    f = skia.Font(FONT, 100); s1, s2 = EN['lines']
    xr = M['logo_dot'][0] - M['logo_dot_r'] - 34; x0 = 395                                 # line 2 ends just before the dot; both lines start at the ALLEN column
    f.setSize(100 * (xr - x0) / f.measureText(s2))
    b = skia.Rect(); f.measureText('N', bounds=b); cap = -b.top()
    base2 = M['logo_dot'][1] + M['logo_dot_r']; base1 = base2 - cap * 1.22
    surf = skia.Surface(w, h); cv = surf.getCanvas(); cv.clear(skia.ColorTRANSPARENT)
    cv.drawImage(skia.Image.fromarray(allen), 0, int(base1 - cap - 60 - 55))
    cv.drawString(s1, x0, base1, f, WHITE); cv.drawString(s2, x0, base2, f, WHITE)
    surf.makeImageSnapshot().save(CH.mark(EN['end_logo']), skia.kPNG); print(EN['end_logo'], round(f.getSize()), 'cap', round(cap))


if __name__ == '__main__':
    wm(); logo_v()
