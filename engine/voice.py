"""旁白：频道配置 [tts] 里的音色（Gemini）→ Whisper 逐字对齐 → 读音自检。
usage (from an episode dir):  python ../../engine/voice.py [seg ...]     → build/voice/<seg>.wav + <seg>.json + index.json + check.txt
script.py in the episode defines SEGMENTS = [(name, [(屏幕显示, 读法|None), ...]), ...]
GM_TAKES="hook=2,debris=3" re-rolls a segment; requests are cached in build/voice_cache (same text + take = same audio)."""
import hashlib, json, os, pathlib, re, subprocess, sys, difflib
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import channel as CH
import tts
T = CH.P['tts']


def load_env():
    if not (ROOT / T['env_file']).exists(): return              # e.g. the keyless edge provider
    for line in open(ROOT / T['env_file']):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
from scriptlib import normalize

# 旁白音色：VOICE=<profile [tts.voices] 的键>（takes.env），否则 episode.toml 的 tts_voice，否则 tts.default_voice
#   每个音色：id = 写死的音色名（openai / edge）| env = 密钥文件里存音色 ID 的变量名 | designed = design*.py 生成的设计音色；provider 缺省用 tts.provider
import episode
VOICE_NAME = os.environ.get('VOICE') or episode.get('tts_voice') or T['default_voice']
_V = T['voices'][VOICE_NAME]
PROVIDER = os.environ.get('TTS_PROVIDER') or _V.get('provider', T['provider'])
EN = os.environ.get('LANG_VO') == 'en'              # English narration (YouTube English cut)
if 'designed' in _V: VOICE = json.load(open(HERE / 'cache/voices_designed.json'))[_V['designed']]
elif 'id' in _V: VOICE = _V['id']
else: VOICE = os.environ.get('SHUSHUO_VOICE') or os.environ.get(_V['env'])
TEMPO = float(os.environ.get('TEMPO', T['tempo']))  # pitch-preserving slow-down
STYLE = os.environ.get('GM_STYLE', T['style_en'] if EN else T['style'])
# 发音硬性要求，拼接在所有风格提示（含 script.py 的 STYLES）之后；legacy 音色不拼
MANDARIN = os.environ.get('GM_MANDARIN', T.get('pronunciation', ''))
PUN = set('，。、：；！？—,.!?;: ')


def synth(text, wav, cache, take=1, style=None):
    style = (style or STYLE) + '。' + MANDARIN if MANDARIN and not _V.get('legacy') and not EN else (style or STYLE)   # legacy voice (A): keep S001–S004 takes reproducible
    h = hashlib.sha1(json.dumps([VOICE, text, style, tts.model(PROVIDER)] + ([take] if take > 1 else []), ensure_ascii=False).encode()).hexdigest()[:16]
    p = cache / f"{'gm' if PROVIDER == 'gemini' else PROVIDER}_{h}.wav"
    if not p.exists(): tts.say(PROVIDER, text, p, style, VOICE)
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', str(p), '-af', f'atempo={TEMPO}', '-ar', '48000', '-ac', '1', str(wav)])


def insert_pauses(wav, js, pauses):
    """script.py PAUSES = {seg: [(句子片段, 秒), ...]}: insert silence after that phrase (midway between its last char and the next char)
    and shift the aligned times, so a deliberate beat doesn't depend on the TTS"""
    import wave, numpy as np
    j = json.load(open(js)); text, st, en = j['text'], j['start'], j['end']
    w = wave.open(str(wav)); sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16); w.close()
    for sub, sec in sorted(pauses, key=lambda p: -text.index(p[0])):          # back to front: earlier indices stay valid
        k = text.index(sub) + len(sub)
        last = max(q for q in range(k) if text[q] not in PUN); nxt = min(q for q in range(k, len(text)) if text[q] not in PUN)
        at = (en[last] + st[nxt]) / 2; i = int(at * sr)
        a = np.concatenate([a[:i], np.zeros(int(sec * sr), np.int16), a[i:]])
        for q in range(nxt, len(text)): st[q] += sec; en[q] += sec
    w = wave.open(str(wav), 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(a.tobytes()); w.close()
    json.dump(j, open(js, 'w'), ensure_ascii=False)


def heard(wav):
    """plain Whisper transcript (no prompt) for the pronunciation check"""
    import mlx_whisper
    return ''.join(s['text'] for s in mlx_whisper.transcribe(str(wav), path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language='en' if EN else 'zh')['segments'])


def main():
    ep = pathlib.Path.cwd(); sys.path.insert(0, str(ep))
    import importlib
    _sc = importlib.import_module(os.environ.get('SCRIPT', 'script'))       # SCRIPT=script_v1: an older version of the episode's script
    SEGMENTS, seg_text = _sc.SEGMENTS, _sc.seg_text
    styles = getattr(_sc, 'STYLES', {})
    pauses = getattr(_sc, 'PAUSES', {})              # optional deliberate pauses inside a segment (inserted silence)              # optional per-segment style prompts in the episode's script.py
    only = set(sys.argv[1:]); takes = dict(x.split('=') for x in os.environ.get('GM_TAKES', '').split(',') if x)
    out = ep / 'build' / os.environ.get('VOICE_DIR', 'voice'); cache = ep / 'build/voice_cache'; out.mkdir(parents=True, exist_ok=True); cache.mkdir(parents=True, exist_ok=True)
    idx = json.load(open(out / 'index.json')) if (out / 'index.json').exists() else {}
    report = []
    for name, chunks in SEGMENTS:
        if only and name not in only: continue
        text = seg_text(chunks); wav = out / f'{name}.wav'
        synth(text, wav, cache, int(takes.get(name, 1)), styles.get(name))
        subprocess.check_call([sys.executable, str(HERE / 'align.py'), str(wav), text, str(out / f'{name}.json')])
        if pauses.get(name): insert_pauses(wav, out / f'{name}.json', pauses[name])
        dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(wav)]))
        h = heard(wav)
        if EN: a, b = (re.sub(r'[^a-z0-9]', '', x.lower()) for x in (text, h))       # numbers: script spells some out, Whisper writes digits → shows up as 差异, judge by ear
        else: a = ''.join(c for c in text if c not in PUN); b = ''.join(c for c in normalize(h) if c not in PUN)
        sm = difflib.SequenceMatcher(None, a, b); sim = sm.ratio()
        diff = [f'{a[i1:i2] or "∅"}→{b[j1:j2] or "∅"}' for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
        erhua = h.count('儿') - text.count('儿')               # Whisper heard an 儿 the script doesn't have → 儿化音
        if erhua > 0: diff.append(f'⚠儿化音×{erhua}')
        idx[name] = dict(text=text, dur=round(dur, 3), take=int(takes.get(name, 1)), whisper=h, match=round(sim, 3), diff=diff)
        report.append(f'{name:10s} {dur:5.2f}s  match {sim:.2f}  take {idx[name]["take"]}\n   稿: {text}\n   听: {h}\n   差异: {"  ".join(diff) or "无"}')
        print(report[-1])
    json.dump(idx, open(out / 'index.json', 'w'), ensure_ascii=False, indent=1)
    (out / 'check.txt').write_text('\n'.join(report) + '\n')
    print('total', round(sum(v['dur'] for v in idx.values()), 2), 's')


if __name__ == '__main__':
    main()
