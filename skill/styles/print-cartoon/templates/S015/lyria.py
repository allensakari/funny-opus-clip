"""S015 配乐 · Google Lyria 3.5（Gemini API，Interactions 接口；每首 0.08 美元，2026-10 价格）
提示词按片子的段落写：120 BPM 恒定（动画的每一步都卡在 0.5 s 网格上），F 大调，俏皮的超市 indie-pop。
密钥只从 .gemini.env 读进环境变量，不打印。
usage: python show/lyria.py N [tag]   → build/music/lyria_<tag>_<k>.mp3 + .txt"""
import os, sys, json, base64, pathlib
HERE = pathlib.Path(__file__).resolve().parent; EP = HERE.parent; ROOT = EP.parent.parent
sys.path.insert(0, str(ROOT / 'engine'))
for line in open(ROOT / '.gemini.env'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
import gemini

OUT = EP / 'build/music'; OUT.mkdir(parents=True, exist_ok=True)

PROMPTS = {'a': """Instrumental only, no vocals, no humming, no whistling. Playful, witty indie-pop score for an animated short about waiting in supermarket checkout lines.
Instruments: marimba, glockenspiel, pizzicato strings, upright bass, a clean muted electric guitar, handclaps, a light dry drum kit with shaker, a ticking woodblock, and a toy music box for the ending.
Key F major. EXACTLY 120 BPM, steady tempo throughout (constant beat grid, no tempo changes, no ritardando), 4/4. Total length about 2 minutes 4 seconds.
[0:00 - 0:08] Intro: ticking woodblock and pizzicato, curious and a bit impatient, upright bass enters at 0:04.
[0:08 - 0:34] Bouncy groove: drums, handclaps on 2 and 4, marimba chords on the offbeats, a catchy glockenspiel melody from 0:12. Cheerful, cheeky.
[0:34 - 0:44] Stuck: the groove suddenly stops. Only a ticking clock and a lone pizzicato bass note repeating, slightly minor, comic suspense.
[0:44 - 0:54] Build: rising marimba arpeggios, claps getting denser, anticipation.
[0:54 - 0:58] Drop to a soft sustained pad, a wistful moment.
[0:58 - 1:02] Cartoonish tiptoe pizzicato, sneaky.
[1:02 - 1:04] The groove bursts back in.
[1:04 - 1:06] Sudden comic stop, silence-like pause.
[1:06 - 1:12] Light marimba returns, shrugging.
[1:12 - 1:40] Main theme, full band, brighter and confident, glockenspiel melody an octave higher, satisfying and smooth like everything finally flowing.
[1:40 - 1:57] Tender and reflective: toy music box plays the melody slowly over soft warm keys, no drums. Gentle, human, a quiet smile.
[1:57 - 2:04] One warm, full F major chord with a soft bell, ringing out to a natural decay.
Clear strong downbeats so a video can cut on them.""",
    # 'q': same tempo and section map as the Douyin song grid (110.6 BPM; drums at 0:17, drop-outs at 1:28 and 1:46, second climax at 1:52),
    # so the WARP=qnyh picture can run with it unchanged. Style: a Mandarin pop-rock ballad, instrumental.
    'q': """Instrumental only, no vocals, no humming, no choir. A Mandarin pop-rock ballad arrangement, cinematic and nostalgic: bittersweet but uplifting, like looking back on a long journey.
Instruments: grand piano, string section, warm electric guitars (clean arpeggios and a soaring lead), electric bass, live pop-rock drums with big crash cymbals.
EXACTLY 110 BPM, steady tempo throughout (constant beat grid, no tempo changes, no ritardando), 4/4. Total length about 2 minutes 15 seconds.
[0:00 - 0:17] Intro: solo piano with soft strings, gentle and emotional, a lyrical melody. No drums.
[0:17] Drums and the full band enter together on a strong downbeat.
[0:17 - 1:17] Main section: driving pop-rock eighth-note groove, bass and drums locked, the piano and electric guitar carry a big singable anthem melody; it keeps growing, with a lift around 0:50.
[1:17 - 1:28] Transition: lighter, piano and bass with soft drums, reflective.
[1:28 - 1:33] Drop-out: almost silence, a few soft piano notes only.
[1:33 - 1:46] Rebuild: strings rise, snare roll crescendo, tension building.
[1:46 - 1:50] Second drop-out: a held breath, very quiet.
[1:50 - 2:08] Final climax: full band and strings at full power, the biggest, most emotional moment, soaring guitar lead, crash cymbals.
[2:08 - 2:15] Ending: one big final chord, ringing out with piano, natural decay.
Clear strong downbeats so a video can cut on them."""}


def gen(tag, k):
    r = gemini.call('/v1beta/interactions', {'model': 'lyria-3.5', 'input': PROMPTS[tag]})
    audio, text = None, []
    for s in r.get('steps', []) + [r]:
        for c in (s.get('content') or s.get('outputs') or []) if isinstance(s, dict) else []:
            if c.get('type') == 'audio' and c.get('data'): audio = c
            if c.get('type') == 'text' and c.get('text'): text.append(c['text'])
    if audio is None: audio = gemini.find_audio(r)
    if audio is None: print('no audio in response', flush=True); return
    ext = 'wav' if 'wav' in (audio.get('mime_type') or audio.get('mimeType') or '') else 'mp3'
    p = OUT / f'lyria_{tag}_{k}.{ext}'; p.write_bytes(base64.b64decode(audio['data']))
    (OUT / f'lyria_{tag}_{k}.txt').write_text('\n'.join(text) or '(no text)')
    print('saved', p.name, flush=True)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1; tag = sys.argv[2] if len(sys.argv) > 2 else 'a'
    (OUT / f'prompt_{tag}.txt').write_text(PROMPTS[tag])
    for k in range(n): gen(tag, k)
