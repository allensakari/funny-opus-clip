"""Voice-driven timeline on a musical grid.
Each segment starts on the grid (UNIT beats of the score), the voice enters LEAD after the cut; the last segment keeps TAIL
seconds after its last word (end card).  Caption chunks get global (a, b) times from the aligned characters.
usage: from timeline import build;  TL = build(SEGMENTS, 'build/voice', beat=0.5608, unit=2)"""
import json, math
from scriptlib import spoken, shown

PUN = set('，。、：；！？—')


class Timeline:
    def __init__(self, segs, beat, unit):
        self.SEGS = segs; self.SEG = {s['name']: s for s in segs}; self.T = segs[-1]['t1']; self.beat = beat; self.unit = unit
        self.CAPS = [c for s in segs for c in s['caps']]

    def when(self, name, sub, edge='a', nth=0):
        """global time a spoken substring starts ('a') or ends ('b')"""
        s = self.SEG[name]; k = -1
        for _ in range(nth + 1): k = s['text'].index(sub, k + 1)
        idx = [q for q in range(k, k + len(sub)) if s['text'][q] not in PUN]
        return s['voice_at'] + (s['st'][idx[0]] if edge == 'a' else s['en'][idx[-1]])

    def snap(self, t, sub=4):
        """nearest 1/sub-beat (for hits that must sit on the music)"""
        q = self.beat / sub; return round(t / q) * q

    def show(self):
        for s in self.SEGS: print(f"{s['name']:9s} {s['t0']:6.2f} – {s['t1']:6.2f}  ({s['t1'] - s['t0']:.2f} s)  voice {s['voice_at']:.2f}")
        print(f'T = {self.T:.2f} s')


def build(SEGMENTS, voice_dir, beat, unit=2, lead=.25, first_lead=.12, gap=.35, tail=2.6, pause=None):
    """pause={seg: seconds}: extra time before that segment's voice (e.g. a chapter card), rounded with the segment to the grid"""
    pause = pause or {}
    segs, t, grid = [], 0.0, beat * unit
    for i, (name, chunks) in enumerate(SEGMENTS):
        j = json.load(open(f'{voice_dir}/{name}.json'))
        text, st, en = j['text'], j['start'], j['end']
        speech_end = max(e for c, e in zip(text, en) if c not in PUN)
        ld = (first_lead if i == 0 else lead) + pause.get(name, 0.0)
        L = math.ceil((ld + speech_end + gap) / grid) * grid if i < len(SEGMENTS) - 1 else ld + speech_end + tail
        caps, k = [], 0
        for c in chunks:
            s = spoken(c); a = text.index(s, k); k = a + len(s)
            idx = [q for q in range(a, a + len(s)) if text[q] not in PUN]
            caps.append(dict(show=shown(c), a=t + ld + st[idx[0]], b=t + ld + en[idx[-1]]))
        segs.append(dict(name=name, t0=t, t1=t + L, voice_at=t + ld, text=text, st=st, en=en, caps=caps, audio=f'{voice_dir}/{name}.wav'))
        t += L
    return Timeline(segs, beat, unit)
