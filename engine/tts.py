"""Narration providers behind one call, so the channel profile picks the TTS (profile [tts] provider, per voice `provider = ...`).
  say(provider, text, out, style, voice)   → writes an audio file (wav for gemini / openai, mp3 converted to wav for edge)
  model(provider)                          → model id, part of voice.py's cache key (changing the model re-synthesises)
Keys are read from the environment only (voice.py loads profile tts.env_file first); REQUIRES lists the variable names per provider.
  gemini  GEMINI_API_KEY; voices are ids (designed / cloned, engine/design.py) · style prompt honoured
  openai  OPENAI_API_KEY; OPENAI_TTS_MODEL (default gpt-4o-mini-tts); voices are names (alloy, onyx, …) · style → instructions
  edge    no key: Microsoft Edge read-aloud through the edge-tts CLI (`uvx edge-tts` if not installed); voices like zh-CN-YunxiNeural · style ignored"""
import json, os, pathlib, shutil, subprocess, tempfile, urllib.error, urllib.request

REQUIRES = {'gemini': ['GEMINI_API_KEY'], 'openai': ['OPENAI_API_KEY'], 'edge': []}


def model(provider):
    if provider == 'gemini':
        import gemini; return gemini.MODEL
    if provider == 'openai': return os.environ.get('OPENAI_TTS_MODEL', 'gpt-4o-mini-tts')
    if provider == 'edge': return 'edge-tts'
    raise SystemExit(f'unknown TTS provider {provider!r} (gemini / openai / edge)')


def say(provider, text, out, style=None, voice=None):
    out = pathlib.Path(out)
    if provider == 'gemini':
        import gemini; return gemini.say(text, out, style, voice)
    if provider == 'openai':
        body = {'model': model('openai'), 'voice': voice or 'onyx', 'input': text, 'response_format': 'wav'}
        if style: body['instructions'] = style
        req = urllib.request.Request(os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1') + '/audio/speech', data=json.dumps(body).encode(),
                                     headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=300) as r: out.write_bytes(r.read())
        except urllib.error.HTTPError as e: raise SystemExit(f'openai TTS {e.code}: {e.read().decode()[:800]}')
        return 'audio/wav'
    if provider == 'edge':
        cli = [shutil.which('edge-tts')] if shutil.which('edge-tts') else ['uvx', 'edge-tts']
        with tempfile.TemporaryDirectory() as d:
            mp3 = pathlib.Path(d) / 'a.mp3'
            subprocess.check_call(cli + ['--voice', voice or 'zh-CN-YunxiNeural', '--text', text, '--write-media', str(mp3)], stdout=subprocess.DEVNULL)
            subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', str(mp3), '-ar', '24000', '-ac', '1', str(out)])
        return 'audio/wav'
    model(provider)
