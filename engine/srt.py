"""captions → SRT on stdout (same phrase timing as the burned-in captions): python engine/srt.py  (run in the episode dir; RENDER=render_v2 for another renderer)"""
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.getcwd())
render = importlib.import_module(os.environ.get('RENDER', 'render'))
caps = render.TL.CAPS


def ts(t):
    ms = int(round(max(0, t) * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


for i, c in enumerate(caps, 1):
    nxt = caps[i]['a'] if i < len(caps) else 1e9
    print(f"{i}\n{ts(c['a'] - .1)} --> {ts(min(nxt - .12, c['b'] + .8))}\n{c['show'].replace('[', '').replace(']', '')}\n")
