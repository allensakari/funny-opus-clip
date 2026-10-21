"""Channel profile: everything that belongs to one channel rather than to the engine (name, marks, colours, fonts, narrator voices).
STORY_PROFILE=<dir> picks it, otherwise the profile named in profiles/DEFAULT (one line, e.g. `example`); the dir holds profile.toml plus the files it names.
  import channel as CH;  CH.P['channel']['name'];  CH.rgb(CH.P['colors']['accent']);  CH.path('marks/wm_nodot.png')"""
import os, tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEF = ROOT + '/profiles/DEFAULT'
DIR = os.path.abspath(os.path.expanduser(os.environ.get('STORY_PROFILE') or ROOT + '/profiles/' + (open(_DEF).read().strip() if os.path.exists(_DEF) else 'example')))
with open(DIR + '/profile.toml', 'rb') as f: P = tomllib.load(f)


def rgb(c):
    """[r, g, b] in 0–255 (any value > 1) or 0–1 → 0–1 tuple"""
    return tuple(v / 255 for v in c) if max(c) > 1 else tuple(float(v) for v in c)


def path(p):
    """a profile-relative path, falling back to the repo root (shared assets such as assets/fonts)"""
    q, r = os.path.join(DIR, p), os.path.join(ROOT, p)
    return r if not os.path.exists(q) and os.path.exists(r) else q          # new files (brand_en.py output) go into the profile


def mark(name):
    return path(os.path.join(P['marks'].get('dir', '.'), name))


def font(key, w=''):
    return path(os.path.join(P['fonts'].get('dir', 'assets/fonts'), P['fonts'][key].format(w=w)))
