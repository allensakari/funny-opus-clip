"""旁白稿格式：SEGMENTS = [(段名, [(屏幕显示, 读法|None), ...]), ...]
屏幕显示里 [..] = 品牌黄（关键词 / 数字）；读法为 None 时读显示文字（去掉 [ ]）；数字要写成汉字读法给 TTS。
块末标点只用于朗读断句，屏幕上不显示。"""
import re
PUNCT = '，。、：；！？——'


def spoken(chunk):
    disp, say = chunk
    return say if say is not None else disp.replace('[', '').replace(']', '')


def shown(chunk):
    s = chunk[0]
    while s and s[-1] in PUNCT: s = s[:-1]
    return s


def seg_text(chunks): return ''.join(spoken(c) for c in chunks)


DIG = '零一二三四五六七八九'


def cn_int(n):
    """integer -> spoken Chinese (万 / 千 / 百 / 十, 零 for gaps)"""
    if n == 0: return '零'
    def four(x, lead):
        out, zero = '', False
        for v, u in ((1000, '千'), (100, '百'), (10, '十'), (1, '')):
            d = x // v % 10
            if d: out += ('零' if zero and out else '') + ('' if (d == 1 and u == '十' and not out and lead) else DIG[d]) + u; zero = False
            elif out: zero = True
        return out
    hi, lo = divmod(n, 10000)
    if not hi: return four(lo, True)
    return four(hi, True) + '万' + (('零' if lo < 1000 else '') + four(lo, False) if lo else '')


def normalize(s):
    """Whisper writes numbers as digits; turn them back into the spoken form so they compare with the script"""
    s = re.sub(r'(?<=\d),(?=\d{3})', '', s)
    s = re.sub(r'(\d{4})(?=年)', lambda m: ''.join(DIG[int(c)] for c in m.group(1)), s)            # years: digit by digit
    s = re.sub(r'(\d+)%', lambda m: '百分之' + cn_int(int(m.group(1))), s)
    s = re.sub(r'(\d+)\.(\d+)', lambda m: cn_int(int(m.group(1))) + '点' + ''.join(DIG[int(c)] for c in m.group(2)), s)
    s = re.sub(r'\d+', lambda m: cn_int(int(m.group(0))), s)
    return s


