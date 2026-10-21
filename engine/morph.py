"""共享元素变形转场（借鉴「万象有因《缘分》」：0 个硬切，同一元素一路变下去）。
上一段的图形直接变成下一段的图形：把两边的元素都表示成同样数量的「件」，按 u 插值位置 / 尺寸 / 颜色 / 圆角。
  Piece = dict(x, y, w, h, r(圆角), c(颜色 rgb), a(不透明度))
  tween(A, B, u, stagger=0.0)  → 插值后的 pieces（stagger > 0 时按序错开，形成「流过去」的感觉）
  draw(cv, pieces)             → skia 画出来
  resample(points, n)          → 折线按弧长重采样到 n 点（线 ↔ 线 变形用）
  line_tween(P, Q, u)          → 两条折线插值"""
import math
import numpy as np
import skia


def _ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def tween(A, B, u, stagger=0.0, ease=_ease):
    n = max(len(A), len(B)); out = []
    for i in range(n):
        a, b = A[i % len(A)], B[i % len(B)]
        ui = u if stagger <= 0 else (u * (1 + stagger) - stagger * i / max(1, n - 1))
        k = ease(ui)
        p = {key: a[key] + (b[key] - a[key]) * k for key in ('x', 'y', 'w', 'h', 'r', 'a')}
        p['c'] = tuple(ca + (cb - ca) * k for ca, cb in zip(a['c'], b['c']))
        out.append(p)
    return out


def piece(x, y, w, h, c, r=0.0, a=1.0): return dict(x=x, y=y, w=w, h=h, r=r, c=c, a=a)


def draw(cv, pieces, al=1.0, qc=None):
    """qc='名称': register every visible piece as a QC 'graphic' (text must not sit on it)"""
    if qc:
        import brand as _B
        for p in pieces:
            if p['a'] * al > .35: _B.qc_box('graphic', qc, p['x'] - p['w'] / 2, p['y'] - p['h'] / 2, p['x'] + p['w'] / 2, p['y'] + p['h'] / 2, p['a'] * al)
    for p in pieces:
        if p['a'] * al <= .003 or p['w'] <= .1 or p['h'] <= .1: continue
        paint = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*p['c'], min(1, p['a'] * al)))
        rect = skia.Rect.MakeXYWH(p['x'] - p['w'] / 2, p['y'] - p['h'] / 2, p['w'], p['h'])
        cv.drawRRect(skia.RRect.MakeRectXY(rect, p['r'], p['r']), paint)


def resample(points, n):
    P = np.asarray(points, float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    s = np.linspace(0, d[-1], n)
    return np.stack([np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], 1)


def line_tween(P, Q, u, n=200):
    k = _ease(u); A, B = resample(P, n), resample(Q, n)
    return A + (B - A) * k
