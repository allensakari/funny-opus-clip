"""纯展示版中英双语 SRT（和画面字幕同一时间轴）：python srt.py > ../发布/人类只是过客.srt"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.pop('DRAFT', None)
import film as F
if os.environ.get('CUT') == '3min': import film_3min                 # CUT=3min python srt.py > ../发布/人类只是过客_3分钟版.srt
if os.environ.get('CUT') == '3m30': import film_3m30                 # CUT=3m30 → the 3:30 cut (all lines, including those shown on screen)
if os.environ.get('CUT') == '3m30v5': import film_3m30_v5             # the v5 cut; SUB=pure → English lines only


def ts(t): ms = int(round(max(0, t) * 1000)); s, ms = divmod(ms, 1000); m, s = divmod(s, 60); h, m = divmod(m, 60); return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


rows = [(0.3, F.CAPS[0][0] - .2, '把宇宙 138 亿年压成一年，人类只活在最后 12 分钟', 'Squeeze 13.8 billion years into one year: humans exist only in its last 12 minutes.')]
if os.environ.get('CUT') == '3m30v5':                             # v5 opens on the ending (cold open), then the cosmic-year hook
    rows = [(0.3, F.SH[1]['t0'] - .1, '76 亿年后，太阳会吞掉地球。我们能逃到哪里？', 'In 7.6 billion years, the Sun will swallow the Earth. Where can we go?'),
            (F.SH[1]['t0'] + .2, F.SH[2]['t0'] - .1, rows[0][2], rows[0][3])]
rows += getattr(F, 'CAPS_ALL', F.CAPS)
b = F.C('black'); rows.append((b['t0'] + .5, F.T, '宇宙不会记得我们来过', 'The universe will not remember we were here.'))
for n, (t0, t1, zh, en) in enumerate(rows, 1): print(f'{n}\n{ts(t0)} --> {ts(t1)}\n' + (f'{en}\n' if F.PURE else f'{zh}\n{en}\n'))
