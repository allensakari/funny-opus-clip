"""Per-episode choices from the intake (skill step 0) → episode.toml in the episode dir; every later step reads them from here.
  python ../../engine/episode.py init --topic 核钟 --style data --voice yes --land no --music library   → writes ./episode.toml
  python ../../engine/episode.py check                                                                    → readiness report
  import episode; episode.get('formats')                                                                  → value or default
Keys: topic, style (skill/styles/index.toml), voice (bool), tts_voice (profile [tts.voices] key), formats (['9x16'] / + '16x9'),
duration (s), music (library | synth | lyria), music_track, covers (always all four sizes), platforms (profile channel.platforms).
check prints which TTS / music / font / tool requirements are met; for keys it prints variable NAMES only, never values."""
import os, sys, shutil, tomllib, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import channel as CH

STYLES = tomllib.load(open(ROOT + '/skill/styles/index.toml', 'rb'))
COVERS = ['9x16', '3x4', '16x9', '4x3']
FILE = 'episode.toml'


def load(d='.'):
    p = os.path.join(d, FILE)
    return tomllib.load(open(p, 'rb')) if os.path.exists(p) else {}


def get(key, default=None, d='.'):
    return load(d).get(key, default)


def resolve(style, voice, land, music):
    """apply the style's capabilities to the four answers → (choices dict, notes for the user)"""
    if style not in STYLES: raise SystemExit(f'unknown style {style!r}: {", ".join(STYLES)}')
    S = STYLES[style]; notes = []
    if voice and S['voice'] == 'none': voice = False; notes.append(f'{S["name"]} 是纯音乐风格，不支持旁白：改成不配音（字幕讲述）。')
    if not voice and S['voice'] == 'required': voice = True; notes.append(f'{S["name"]} 的时间轴跟着旁白走，必须配音。')
    native = S['native']; fmts = [native]
    if S.get('both'):
        fmts = [native] + S['extra']
        if not land: notes.append(f'{S["name"]} 横竖两版一起出。')
    elif land and native == '9x16' and '16x9' in S['extra']: fmts.append('16x9')
    elif native == '16x9': notes.append(f'{S["name"]} 原生是 16:9 横版，没有 9:16 版本。')
    if music not in S['music']: notes.append(f'{S["name"]} 不支持配乐 {music}，改用 {S["music"][0]}。'); music = S['music'][0]
    return dict(style=style, voice=voice, formats=fmts, duration=S['duration'], music=music, covers=COVERS), notes


def _toml(v):
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, (int, float)): return str(v)
    if isinstance(v, list): return '[' + ', '.join(_toml(x) for x in v) + ']'
    return '"' + str(v).replace('\\', '\\\\').replace('"', '\\"') + '"'


def write(choices, d='.'):
    with open(os.path.join(d, FILE), 'w') as f:
        f.write('# 开工问答的答案（engine/episode.py init 生成；改了就从对应的步骤重做）\n')
        for k, v in choices.items(): f.write(f'{k} = {_toml(v)}\n')


def _env_names():
    """names defined in the profile's key file (values are never read into the report)"""
    p = os.path.join(ROOT, CH.P['tts'].get('env_file', '.env')); names = set()
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line and line.split('=', 1)[1].strip(): names.add(line.split('=', 1)[0].strip())
    return names | {k for k, v in os.environ.items() if v}


def check(d='.'):
    import tts
    E = load(d); ok = True; env = _env_names(); T = CH.P['tts']
    def line(good, msg):
        nonlocal ok; ok &= good; print(('  ✓ ' if good else '  ✗ ') + msg)
    print(f'频道配置：{CH.DIR}（{CH.P["channel"]["name"]}）')
    line(shutil.which('ffmpeg') is not None, 'ffmpeg')
    for key, ws in (('cjk', ('Heavy', 'Bold', 'Medium', 'Regular')), ('num', ('ExtraBold', 'Bold', 'Medium'))):
        miss = [w for w in ws if not os.path.exists(CH.font(key, w))]
        line(not miss, f'字体 {CH.P["fonts"][key]}' + (f'：缺 {", ".join(miss)}' if miss else ''))
    for k in ('watermark', 'end_logo'):
        line(os.path.exists(CH.mark(CH.P['marks'][k])), f'标志 {CH.P["marks"][k]}')
    if not E: print('  · 还没有 episode.toml（先跑 init）'); return ok
    print(f'本期：{E.get("topic", "")} · 风格 {E["style"]} · 画幅 {" + ".join(E["formats"])} · 配乐 {E["music"]} · 封面 {len(E["covers"])} 个尺寸')
    if E['voice']:
        name = E.get('tts_voice') or T['default_voice']; V = T['voices'].get(name)
        line(V is not None, f'旁白音色 {name}' + ('' if V else '：profile [tts.voices] 里没有'))
        if V:
            prov = V.get('provider', T['provider'])
            need = tts.REQUIRES.get(prov, []) + ([V['env']] if 'env' in V else [])
            for n in need: line(n in env, f'{prov}：环境变量 {n}' + ('' if n in env else f'（写进 {T.get("env_file", ".env")}）'))
            if prov == 'edge': line(bool(shutil.which('edge-tts') or shutil.which('uvx')), 'edge-tts（或 uvx）')
            if 'designed' in V: line(os.path.exists(HERE + '/cache/voices_designed.json'), '设计音色 ID（engine/design.py 生成）')
        line(importlib.util.find_spec('mlx_whisper') is not None, 'mlx-whisper（读音自检，Apple Silicon）')
    if E['music'] == 'library':
        man = ROOT + '/assets/music/music.toml'
        n = len(tomllib.load(open(man, 'rb')).get('track', [])) if os.path.exists(man) else 0
        line(n > 0, f'曲库 assets/music/music.toml：{n} 首' if n else '曲库：assets/music/music.toml 没有曲子')
    if E['music'] == 'lyria': line('GEMINI_API_KEY' in env, 'Lyria：环境变量 GEMINI_API_KEY')
    print('可以开工' if ok else '有未满足的项（✗），先补齐')
    return ok


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['init', 'check'])
    ap.add_argument('--topic', default=''); ap.add_argument('--style', default='data')
    ap.add_argument('--voice', default='no'); ap.add_argument('--tts-voice', default='')
    ap.add_argument('--land', default='no'); ap.add_argument('--music', default='synth')
    a = ap.parse_args(); yes = lambda s: s.lower() in ('yes', 'y', 'true', '1', '是')
    if a.cmd == 'init':
        c, notes = resolve(a.style, yes(a.voice), yes(a.land), a.music)
        c = dict(topic=a.topic, **c)
        if c['voice'] and a.tts_voice: c['tts_voice'] = a.tts_voice
        c['platforms'] = CH.P['channel'].get('platforms', [])
        write(c); [print('注意：' + n) for n in notes]; print('wrote', FILE)
    sys.exit(0 if check() else 1)
