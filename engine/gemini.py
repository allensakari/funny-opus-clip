"""Gemini TTS（声音复刻）：sh gm.sh gemini.py create            → 用 voice_rec/ 两段录音建音色，ID 存 build/gemini_voice.json
                         sh gm.sh gemini.py say "文本" out.wav [风格]  → 用该音色合成
密钥只从环境变量读（GEMINI_API_KEY，由 gm.sh 从 .gemini.env 载入）。"""
import base64, json, os, sys, urllib.request, urllib.error, pathlib
BASE = os.environ.get('GEMINI_API_BASE_URL', 'https://generativelanguage.googleapis.com')
MODEL = os.environ.get('GEMINI_TTS_MODEL', 'gemini-3.8-flash-tts')
HERE = pathlib.Path(__file__).parent; VFILE = HERE / 'build/gemini_voice.json'
sys.path.insert(0, str(HERE))
import channel as CH
LABEL = CH.P['tts'].get('clone_label', CH.P['channel']['name'])


def call(path, body=None, method=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={'x-goog-api-key': os.environ['GEMINI_API_KEY'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r: return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e: raise SystemExit(f'{e.code} {path}: {e.read().decode()[:int(os.environ.get('ERRLEN', 800))]}')


def b64(p): return base64.b64encode(pathlib.Path(p).read_bytes()).decode()


def shape(o, d=0):
    """structure of a response without the (huge / sensitive) data fields"""
    if isinstance(o, dict): return {k: (f'<{len(v)} chars>' if k in ('data', 'key') and isinstance(v, str) else shape(v, d + 1)) for k, v in o.items()}
    if isinstance(o, list): return [shape(x, d + 1) for x in o[:4]]
    return o


def find_audio(o):
    if isinstance(o, dict):
        if o.get('type') == 'audio' and 'data' in o: return o
        if 'inlineData' in o: return {'data': o['inlineData']['data'], 'mime_type': o['inlineData'].get('mimeType')}
        for v in o.values():
            r = find_audio(v)
            if r: return r
    if isinstance(o, list):
        for v in o:
            r = find_audio(v)
            if r: return r


def say(text, out, style=None, voice=None):
    voice = voice or json.load(open(VFILE))['id']
    content = {'type': 'text', 'text': text}
    if style: content['annotations'] = [{'type': 'speech_metadata', 'style': style}]
    r = call('/v1beta/interactions', {'model': MODEL, 'input': [{'type': 'user_input', 'content': [content]}],
                                      'response_format': {'type': 'audio'}, 'generation_config': {'speech_config': [{'voice': voice}]}})
    a = find_audio(r)
    if not a: raise SystemExit('no audio in response: ' + json.dumps(shape(r), ensure_ascii=False)[:1500])
    raw = base64.b64decode(a['data']); mt = a.get('mime_type') or a.get('mimeType') or ''
    out = pathlib.Path(out)
    if raw[:4] == b'RIFF': out.write_bytes(raw)
    else:   # raw PCM (e.g. audio/L16;rate=24000) -> wav
        import wave; rate = int(mt.split('rate=')[1].split(';')[0]) if 'rate=' in mt else 24000
        with wave.open(str(out), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(raw)
    return mt


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'create':
        r = call('/v1beta/voices', {'store': True, 'voice': {'model': MODEL, 'type': 'replicated', 'display_name': LABEL,
                 'replicated': {'source_audio': {'mime_type': 'audio/wav', 'data': b64(HERE / 'voice_rec/source_样本.wav')},
                                'consent_audio': {'mime_type': 'audio/wav', 'data': b64(HERE / 'voice_rec/consent_授权声明.wav')}}}})
        print(json.dumps(shape(r), ensure_ascii=False, indent=1)[:1500])
        v = r.get('voice', r); vid = v.get('id') or v.get('name')
        if vid: VFILE.parent.mkdir(exist_ok=True); json.dump({'id': vid, 'display_name': LABEL}, open(VFILE, 'w')); print('saved voice id ->', VFILE)
    elif cmd == 'list':
        print(json.dumps(shape(call('/v1beta/voices')), ensure_ascii=False, indent=1)[:3000])
    elif cmd == 'say':
        print(say(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None), '->', sys.argv[3])
