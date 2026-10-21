"""英文旁白的 Gemini 设计音色（YouTube 英文配音版，用户 2026-10-18：成熟男声）→ engine/cache/voices_designed.json（不入库）
+ 试听 build/design/英文音色试听.wav（按 E1 / E2 / E3 的顺序，每个音色读同样两句，中间响 1 / 2 / 3 声提示音）。
usage（在根目录）：.venv/bin/python engine/design_en.py"""
import json, pathlib, subprocess, wave, os, sys
import numpy as np
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import channel as CH
for line in open(ROOT / CH.P['tts']['env_file']):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
import gemini as G

_D = CH.P['tts']['design']['en']
DESIGNS = {k: (g, d + _D['neutral']) for k, (g, d) in _D['voices'].items()}   # profile [tts.design.en]: description + shared accent rules
LINES = _D['lines']
STYLE = CH.P['tts']['style_en']
D = ROOT / 'build/design'; D.mkdir(parents=True, exist_ok=True)
vf = HERE / 'cache/voices_designed.json'; vf.parent.mkdir(exist_ok=True)
voices = json.loads(vf.read_text()) if vf.exists() else {}


def beep(n, sr):
    t = np.arange(int(.12 * sr)) / sr; b = (np.sin(2 * np.pi * 880 * t) * 9000 * np.hanning(len(t))).astype(np.int16)
    gap = np.zeros(int(.12 * sr), np.int16)
    return np.concatenate([np.concatenate([b, gap]) for _ in range(n)] + [np.zeros(int(.4 * sr), np.int16)])


def main():
    for name, (gender, desc) in DESIGNS.items():
        if name not in voices:
            r = G.call('/v1beta/voices', {'store': True, 'voice': {'model': G.MODEL, 'type': 'prompted', 'display_name': f"{CH.P['tts'].get('voice_label_en', CH.P['channel']['name'])} {name}",
                                                                   'gender': gender, 'language_code': 'en-US', 'prompted': {'input': desc}}})
            v = r.get('voice', r); voices[name] = v['id']; vf.write_text(json.dumps(voices, ensure_ascii=False, indent=1))
            print('created', name)
    SR = 24000; parts = []
    for k, name in enumerate(DESIGNS, 1):
        parts.append(beep(k, SR))
        for i, line in enumerate(LINES):
            p = D / f'{name}_{i}.wav'
            if not p.exists(): G.say(line, p, STYLE, voices[name])
            x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout, np.int16)
            parts += [x, np.zeros(int(.45 * SR), np.int16)]
        parts.append(np.zeros(int(1.2 * SR), np.int16))
        print('audition', name)
    with wave.open(str(D / '英文音色试听.wav'), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.concatenate(parts).tobytes())
    print('order:', ' / '.join(DESIGNS))


if __name__ == '__main__':
    main()
