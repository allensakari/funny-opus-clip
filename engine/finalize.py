"""成片出片（用户 2026-10-11）：画面 + 混音 → 响度 −14 LUFS、真峰值 ≤ −2 dBFS，加细颗粒防色带，H.264 恒定码率（默认 12 Mbps）。
为什么：纯色 / 矢量画面在 CRF 下码率极低（S005 只有 0.6 Mbps），平台二次压缩时大面积渐变容易出色带；固定高码率 + 细颗粒让交给平台的原片更「厚实」。
usage: python engine/finalize.py <video.mp4> <mix.wav> <out.mp4> [--mbps 12] [--grain 3]"""
import subprocess, sys, json
a = sys.argv[1:]
video, mix, out = a[0], a[1], a[2]
mbps = float(a[a.index('--mbps') + 1]) if '--mbps' in a else 12.0
grain = float(a[a.index('--grain') + 1]) if '--grain' in a else 3.0
b = f'{mbps:g}M'
vf = f'noise=alls={grain:g}:allf=t' if grain > 0 else 'null'
subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', mix, '-map', '0:v', '-map', '1:a',
                       '-vf', vf, '-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
                       '-b:v', b, '-minrate', b, '-maxrate', b, '-bufsize', f'{mbps * 2:g}M', '-x264-params', 'nal-hrd=cbr:force-cfr=1',
                       '-af', 'loudnorm=I=-14:TP=-2:LRA=11,alimiter=limit=0.82:level=false', '-ar', '48000', '-c:a', 'aac', '-b:a', '256k',
                       '-shortest', '-movflags', '+faststart', out])
info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate,bit_rate', '-show_entries', 'format=duration,size', '-of', 'json', out]))
v = next(s for s in info['streams'] if s['codec_type'] == 'video')
print(f"{out}: {v['width']}x{v['height']} {v['r_frame_rate']} · video {int(v['bit_rate']) / 1e6:.1f} Mbps · {float(info['format']['duration']):.2f} s · {int(info['format']['size']) / 2**20:.0f} MB")
