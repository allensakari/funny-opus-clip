"""色温叙事：整帧调色（借鉴「万象有因《缘分》」冷蓝 → 暖棕）。
usage: arr = grade(arr, warm=0.6, sat=1.0, lift=0.0)   # arr: HxWx4 uint8 RGBA（skia toarray），原地返回
  warm  −1（冷蓝）… 0（不变）… +1（暖橙）；sat 饱和度倍数；lift 整体提亮（−0.2…0.2）
  curve(t, keys) 按时间关键帧插值：keys = [(t0, warm0), (t1, warm1), …]"""
import numpy as np

_WARM = np.array([1.10, 1.00, 0.84], np.float32)          # gain at warm = +1
_COOL = np.array([0.88, 0.98, 1.14], np.float32)          # gain at warm = −1


def grade(arr, warm=0.0, sat=1.0, lift=0.0):
    if abs(warm) < 1e-3 and abs(sat - 1) < 1e-3 and abs(lift) < 1e-3: return arr
    rgb = arr[..., :3].astype(np.float32) / 255
    g = 1 + (_WARM - 1) * max(0.0, warm) + (_COOL - 1) * max(0.0, -warm)
    rgb = rgb * g
    if abs(sat - 1) > 1e-3:
        y = (rgb * np.array([.299, .587, .114], np.float32)).sum(-1, keepdims=True)
        rgb = y + (rgb - y) * sat
    if lift: rgb = rgb + lift * (1 - rgb)
    arr[..., :3] = np.clip(rgb * 255 + .5, 0, 255).astype(np.uint8)
    return arr


def curve(t, keys):
    """piecewise smooth interpolation of (time, value) keyframes"""
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / max(1e-6, t1 - t0); u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return keys[-1][1]
