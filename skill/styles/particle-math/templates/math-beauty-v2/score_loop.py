"""循环版声音（3:28）：
  python score_loop.py          → build/loop/nobgm.wav（抖音上传用，只有音效）+ mix_preview.wav（叠上循环好的《千年以后》，只用于试听）
  python score_loop.py --full   → build/loop/score.wav（小红书 / B站全长版：原创配乐 + 带音高的音效）
全长版配乐：把 score.py 的配乐在原时间轴上合成，再在和歌一样的位置接回（h(81) → h(9)）。跳回 72 个半小节 = 36 小节，
正好是 Dm–B♭–C–A 四小节循环的整数倍，两边又都在小节中间同一拍，所以和声、律动都接得上。
旧片的音效原样沿用（h(48) 之后的整体后移 JUMP，和画面一致），四个新段落另加：
  ζ：质数汇成公式的气声、公式落定的微光；曲线每穿过一次原点，一声轻击 + 低音
  混沌游戏：慢拍里每跳一次一声轻击，加速后变成越来越密的「沙沙」声
  第二次鼓点进来：气声 + 低音，超立方体展开；最后收进漏斗
  高尔顿板：前八颗球每碰一颗钉子一声轻击，之后是一阵「雨声」，钟形曲线出现时一道微光
usage: python score_loop.py"""
import os, sys, wave
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import score as S
import film_loop as L
import film as F

SR = S.SR; S.N = N = int(L.T * SR)
h = L.h
_put = S.put


def put_shift(out, x, t0, g=1.0):
    """the old film's effects: everything from the c-grid on moves 72 half-bars later"""
    _put(out, x, t0 + (L.JUMP if t0 >= F.G0 - .2 else 0), g)


def effects_loop(pitched):
    S.put = put_shift
    fx = S.effects(pitched)
    S.put = _put
    put = _put
    if F.HOOK == 'A':                                                           # the opening: the zoom rushes in, collapses, blooms into the equations
        put(fx, S.whoosh(2.6, .035, 200, 4000, 58), 0.0); put(fx, S.whoosh(.9, .05, 500, 9000, 59, rev=True), 2.5)
        put(fx, S.shimmer(1.6, .03, 57), 3.0)
        if pitched: put(fx, S.bell(S.hz(62), 3.0, .05), 3.3)
    # ---- ζ
    put(fx, S.whoosh(2.6, .05, 500, 8000, 60), L.ZF0 - .1)
    put(fx, S.shimmer(2.0, .025, 61), L.ZF1 - .3)
    put(fx, S.whoosh(3.0, .03, 300, 5000, 62), L.ZD0)
    for i, tk in enumerate(L.ZERO_T):
        put(fx, S.tick(.05, 70 + i), tk); put(fx, S.thump(.07, 50, .35), tk)
        if pitched: put(fx, S.bell(S.hz([62, 65, 69, 72, 74, 77, 81, 74, 77, 81][i]), 2.2, .05), tk)                # each zero rings a note of D minor
    put(fx, S.whoosh(2.4, .05, 400, 7000, 63, rev=True), L.ZC0)
    for i in range(3): put(fx, S.tick(.04, 80 + i), h(69) + i * .12)
    # ---- chaos game
    for k in range(L.NSLOW):
        put(fx, S.pluck(S.hz([74, 69, 77, 72][L.CK[k]] if L.CK[k] < 3 else 74), .04) if pitched else S.tick(.045, 90 + k), L.APPEAR[k])     # each corner has its own note
    for tk in L.APPEAR[L.NSLOW::7]:                                             # the jumps speed up into a hiss
        put(fx, S.tick(.006, int(tk * 1000) % 9973), tk)
    put(fx, S.shimmer(4.0, .03, 92), h(82))
    # ---- tesseract (the second drum entry)
    put(fx, S.whoosh(2.4, .07, 300, 9000, 93), L.Q0 - .4)
    put(fx, S.thump(.15, 44, 1.4), L.Q0); put(fx, S.shimmer(2.0, .03, 94), L.QM)
    put(fx, S.whoosh(6.0, .02, 150, 2500, 95), h(95))
    put(fx, S.whoosh(1.4, .06, 400, 8000, 96, rev=True), h(103) - .2)
    # ---- Galton board
    for j in range(L.NSLOW):
        for i in range(L.ROWS): put(fx, S.tick(.02, 100 + j * 13 + i), L.REL[j] + i * L.DR)
        put(fx, S.pluck(S.hz(62 + 2 * int(L.BIN[j])), .035) if pitched else S.tick(.03, 300 + j), L.REL[j] + L.ROWS * L.DR + L.TFALL)    # the bin it lands in sets the pitch
    for tk in L.REL[L.NSLOW::3]:                                                 # the rain of thousands of balls
        put(fx, S.tick(.004, int(tk * 1000) % 7919), tk + L.ROWS * L.DR * .5)
    put(fx, S.shimmer(3.0, .035, 97), h(113))
    if pitched: put(fx, S.bell(S.hz(69), 4.5, .06), h(113)); put(fx, S.bell(S.hz(62), 5.0, .05), L.Q0)
    return fx


fade = (np.clip(np.arange(N) / SR / .3, 0, 1) * np.clip((L.T - np.arange(N) / SR) / 1.0, 0, 1))[:, None]
B = L.BUILD
if '--full' in sys.argv:
    S.N = int(F.T * SR); m = S.score(); S.N = N                                    # the score on the 2:10 timeline …
    a, b, xf = int(h(81) * SR), int(h(9) * SR), int(.03 * SR)                       # … then the same seam as the song
    r = np.linspace(0, 1, xf)
    m = np.concatenate([m[:a - xf], m[a - xf:a] * np.cos(r * np.pi / 2) + m[b - xf:b] * np.sin(r * np.pi / 2), m[b:]])
    m = np.concatenate([m, np.zeros(max(0, N - len(m)))])[:N]
    full = S.reverb(S.stereo(effects_loop(True) + m), mix=.3) * fade
    S.save(full, B + 'score.wav'); print('ok', B + 'score.wav', f'{L.T:.2f} s'); sys.exit()
fx = effects_loop(False)
dy = S.reverb(S.stereo(fx), mix=.2) * fade
B = L.BUILD
S.save(dy, B + 'nobgm.wav')

# preview: the looped song under the effects (not for upload)
w = wave.open(HERE + '/build/loop/song_loop.wav'); sr2, ch = w.getframerate(), w.getnchannels()
song = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, ch).astype(np.float32) / 32768
if song.shape[1] == 1: song = np.repeat(song, 2, 1)
if sr2 != SR:
    from scipy.signal import resample_poly
    song = resample_poly(song, SR, sr2, axis=0)
song = np.vstack([song, np.zeros((max(0, N - len(song)), 2))])[:N]
nb = dy * (.6 / np.abs(dy).max())
mix = song * .8 + nb * .45
S.save(mix, B + 'mix_preview.wav')
print('ok', B + 'nobgm.wav', B + 'mix_preview.wav', f'{L.T:.2f} s')
