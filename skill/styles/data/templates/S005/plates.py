"""S005 封面底图（片中画面去掉文字）→ build/review/plates/<name>_<theme>_<W>x<H>.png
usage: SHUSHUO_THEME=sand|dark [FILM_W=1920 FILM_H=1080] python plates.py
  A_road  红灯前 8 辆车，绿牌那辆亮起（road 段）
  B_grid  路上每 100 辆：13 绿 87 蓝（total 段）"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
import skia
import render as R
from grade import grade, curve

OUT = HERE + '/build/review/plates/'; os.makedirs(OUT, exist_ok=True)
_no = lambda *a, **k: 0
R.text = _no; R.bignum = lambda *a, **k: None; R.source_tag = _no            # plates carry no text — the cover adds its own


def plate(name, t):
    surf = skia.Surface(R.W, R.H); cv = surf.getCanvas()
    R.scene(cv, t)
    arr = surf.makeImageSnapshot().toarray()
    skia.Image.fromarray(arr).save(f'{OUT}{name}_{R.B.THEME}_{R.W}x{R.H}.png', skia.kPNG); print(name, R.B.THEME, R.W, R.H)


if __name__ == '__main__':
    plate('A_road', R.wt('road', '挂着绿牌') + .6)
    plate('B_grid', R.SEG['total']['t0'] + 2.5)
