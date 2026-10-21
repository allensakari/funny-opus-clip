"""《千年以后》循环版音乐床（只用于试听和测拍，不进上传成片）：
录屏 0 → 89.53 s（第 81 个半小节），接回 11.44 s（第 9 个半小节）一直放到录屏结尾。
两处前后 4 s 的音色 / 和声相似度 1.93 / 2：间奏的收空段和前奏结尾是同一段音乐，所以接缝听不出来；
跳回 72 个半小节（36 小节，78.09 s），节拍网格 h(n) 在接缝后照样连续。总长 = h(190) = 207.75 s。
usage: python loop_bed.py → build/loop/song_loop.wav"""
import os, wave, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('LOOP_SONG', HERE + '/song.wav')          # the reference song (《千年以后》) is copyrighted and not included
def h(n): return 1.6811 + 1.0846 * n
SEAM_A, SEAM_B = h(81), h(9)
JUMP = SEAM_A - SEAM_B
if __name__ == '__main__':
    w = wave.open(SRC); sr, ch = w.getframerate(), w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, ch).astype(np.float32)
    a, b, xf = int(SEAM_A * sr), int(SEAM_B * sr), int(.03 * sr)        # 30 ms equal-power crossfade on the downbeat
    r = np.linspace(0, 1, xf)[:, None]
    seam = x[a - xf:a] * np.cos(r * np.pi / 2) + x[b - xf:b] * np.sin(r * np.pi / 2)
    y = np.concatenate([x[:a - xf], seam, x[b:]])
    o = wave.open(HERE + '/build/loop/song_loop.wav', 'wb'); o.setnchannels(ch); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes(np.clip(y, -32768, 32767).astype(np.int16).tobytes()); o.close()
    print(f'ok {len(y) / sr:.2f} s, seam {SEAM_A:.2f} → {SEAM_B:.2f} (jump {JUMP:.2f} s)')
