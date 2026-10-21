"""Gemini 设计音色（按文字描述生成）→ engine/cache/voices_designed.json（不入库）+ 试听 build/design/设计音色试听.wav
用户 2026-10-11：音色 A 的京腔儿化音太重——原描述写了 "standard Beijing Mandarin"；新音色明确要求中性标准普通话、无儿化。
usage（在根目录）：.venv/bin/python engine/design.py"""
import json, pathlib, subprocess, wave, base64, os, sys
import numpy as np
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import channel as CH
for line in open(ROOT / CH.P['tts']['env_file']):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
import gemini as G

_D = CH.P['tts']['design']['zh']
DESIGNS = {k: (g, d + _D['neutral']) for k, (g, d) in _D['voices'].items()}   # profile [tts.design.zh]: description + shared accent rules
LINES = _D['lines']
STYLE = CH.P['tts']['style']
D = ROOT / 'build/design'; D.mkdir(parents=True, exist_ok=True)
vf = HERE / 'cache/voices_designed.json'; vf.parent.mkdir(exist_ok=True)
voices = json.loads(vf.read_text()) if vf.exists() else {}


def main():
    names = list(DESIGNS)
    for name in names:
        if name not in voices:
            gender, desc = DESIGNS[name]
            r = G.call('/v1beta/voices', {'store': True, 'voice': {'model': G.MODEL, 'type': 'prompted', 'display_name': f"{CH.P['tts'].get('voice_label', CH.P['channel']['name'])} {name}", 'gender': gender,
                                                                   'language_code': 'zh-CN', 'prompted': {'input': desc}}})
            v = r.get('voice', r); voices[name] = v['id']; vf.write_text(json.dumps(voices, ensure_ascii=False, indent=1))
            print('created', name)
    # audition: the old voice A first (for comparison), then the new ones; same style prompt, no extra MANDARIN suffix
    ce = CH.P['tts']['design']['zh'].get('compare_env')
    cand = ([('A_旧', os.environ[ce])] if ce else []) + [(n, voices[n]) for n in names]
    SR = 24000; parts = []
    for name, vid in cand:
        for i, line in enumerate(LINES):
            p = D / f'{name}_{i}.wav'
            if not p.exists(): G.say(line, p, STYLE, vid)
            x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout, np.int16)
            parts += [x, np.zeros(int(.45 * SR), np.int16)]
        parts.append(np.zeros(int(1.3 * SR), np.int16))
        print('audition', name)
    with wave.open(str(D / '设计音色试听.wav'), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.concatenate(parts).tobytes())
    print('order:', ' / '.join(n for n, _ in cand))


if __name__ == '__main__':
    main()
