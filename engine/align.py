"""逐字对齐（Gemini 没有时间戳）：python align.py audio.wav "原稿文本" out.json
Whisper 词级时间戳 → 把 Whisper 写成阿拉伯数字的词转回汉字读法（时长均分到展开后的每个字）→ 和原稿逐字比对；
对不上的字在相邻已对齐的字之间按位置插值。匹配率 < 0.9 时去掉 initial_prompt 再识别一次，取更好的那次。
输出 {text, chars, start, end, matched}。"""
import difflib, json, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mlx_whisper
from scriptlib import normalize

PUN = set('，。、：；！？—,.!?;: ')
EN = os.environ.get('LANG_VO') == 'en'       # English narration: align letter by letter (lower-case), no Chinese number normalisation
if EN: PUN |= set("'-–\"()[]")
audio, text, out = sys.argv[1], sys.argv[2], sys.argv[3]
DUR = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio]))


def hyp_chars(prompt):
    r = mlx_whisper.transcribe(audio, path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language='en' if EN else 'zh', word_timestamps=True,
                               **({'initial_prompt': prompt} if prompt else {}))
    hyp = []
    for s in r['segments']:
        for w in s.get('words', []):
            cs = [c for c in (w['word'].strip().lower() if EN else normalize(w['word'].strip())) if c not in PUN]
            for k, c in enumerate(cs):
                d = (w['end'] - w['start']) / len(cs); hyp.append((c, w['start'] + k * d, w['start'] + (k + 1) * d))
    return hyp


def align(hyp):
    st, en = [None] * len(text), [None] * len(text)
    ref_idx = [i for i, c in enumerate(text) if c not in PUN]
    sm = difflib.SequenceMatcher(None, [text[i].lower() for i in ref_idx], [h[0] for h in hyp], autojunk=False)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n): i = ref_idx[a + k]; st[i], en[i] = hyp[b + k][1], hyp[b + k][2]
    known = [i for i in range(len(text)) if st[i] is not None]
    matched = len([i for i in ref_idx if st[i] is not None]) / len(ref_idx)
    return st, en, known, matched


best = None
for prompt in (text, None):
    st, en, known, m = align(hyp_chars(prompt))
    if best is None or m > best[3]: best = (st, en, known, m)
    if m >= .9: break
st, en, known, matched = best
assert len(known) >= 2, 'alignment failed'
end_speech = max(en[k] for k in known)
for i in range(len(text)):                   # interpolate the gaps (unmatched chars and punctuation)
    if st[i] is not None: continue
    lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
    t0 = en[lo] if lo is not None else 0.0; t1 = st[hi] if hi is not None else min(DUR, end_speech + .25 * (len(text) - i))
    a = lo if lo is not None else -1; b = hi if hi is not None else len(text)
    f0, f1 = (i - a - 1) / (b - a - 1), (i - a) / (b - a - 1)
    st[i], en[i] = t0 + (t1 - t0) * f0, t0 + (t1 - t0) * f1
json.dump(dict(text=text, chars=list(text), start=st, end=en, matched=round(matched, 3)), open(out, 'w'), ensure_ascii=False)
print('aligned', out, f'matched {matched:.0%}')
