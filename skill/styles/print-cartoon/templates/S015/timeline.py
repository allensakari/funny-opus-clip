"""S015 你总排到慢的那队 — shared timeline (film, score and srt all read this). 120 BPM: 1 beat = 0.5 s, 1 bar = 2 s."""
import json, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(HERE + '/data/stats.json'))
SEP, SNK = S['separate'], S['snake']

BPM = 120
BEAT = 60 / BPM
DUR = 124.0
FPS = 60


def snap(t):                                     # next beat at or after t
    return math.ceil(t / BEAT - 1e-6) * BEAT


# act cards: a supermarket receipt wipes across; the scene changes at t0 (receipt fully covers t0-.5 … t0+.5)
WIPES = [(8.0, '01', '不是错觉，是数学', "IT'S NOT YOU. IT'S MATH.", '1/3'),
         (34.0, '02', '一个人，卡住一整队', 'ONE PERSON, ONE STUCK LINE', f"{SEP['tail10_mean']:.1f} min"),
         (58.0, '03', '换队', 'SWITCHING LINES', '¥0.00'),
         (72.0, '04', '只排一队', 'ONE LINE FOR ALL', '0%'),
         (100.0, '05', '最后一件事', 'ONE LAST THING', '2/3')]

p3 = S['tally1000_frac']
CAPS = [
    (0.2, 2.4, '超市三条队，你选哪一条？', 'Three checkout lines. Pick one.'),
    (2.4, 4.2, '……为什么又是你这队最慢？', '…why is yours the slow one again?'),
    (4.2, 7.2, '不是你倒霉：有 2/3 的概率，别的队更快', 'Not bad luck: 2 times in 3, another line is faster.'),
    (9.2, 12.6, '三条队，人一样多', 'Three lines, same length.'),
    (12.6, 17.4, '你这队最先排完的机会是——', 'The chance yours finishes first:'),
    (17.4, 22.6, '只有三分之一', 'Only one in three.'),
    (22.6, 25.2, '排 1000 次队试试', 'Try it 1,000 times.'),
    (25.2, 29.8, '三次里有两次，总有别的队比你快', 'Two times out of three, another line wins.'),
    (29.8, 33.2, '收银台越多，你越难是最快的那个', 'More lines, worse odds.'),
    (35.2, 40.0, '一条队慢下来，往往只因为一个人', 'Often a whole line stalls because of one person.'),
    (40.0, 44.6, '数零钱、退货、核对价格……', 'Counting coins. A return. A price check…'),
    (44.6, 49.6, '所以等待时间，一点都不平均', "So waiting times aren't even at all."),
    (49.6, 53.8, f"一般只等 {SEP['p50']:.1f} 分钟，最倒霉的 10% 平均要等 {SEP['tail10_mean']:.1f} 分钟",
     f"Usually {SEP['p50']:.1f} min. The unluckiest 10%: {SEP['tail10_mean']:.1f} min on average."),
    (53.8, 57.6, '而你记住的，恰恰是那几次', 'And those are the times you remember.'),
    (59.2, 62.6, '于是你换了一队——', 'So you switch lines—'),
    (62.6, 66.4, '——原来那队，立刻就动了', '—and your old line starts moving.'),
    (66.4, 71.0, '卡住的人刚好结完账；而你的新队，有新的意外', 'The hold-up just cleared. Your new line has its own surprise.'),
    (73.2, 76.6, '有没有不看运气的排法？', "Is there a way that isn't luck?"),
    (76.6, 81.0, f"分开排时，约 {SEP['overtaken_frac']*10:.0f} 成的人会被比自己晚到的人超过",
     f"With separate lines, ~{SEP['overtaken_frac']*10:.0f} in 10 get passed by someone who came later."),
    (81.0, 84.6, '换个排法：所有人只排一队', 'Instead: everyone joins one line.'),
    (84.6, 89.0, '哪个收银台空了，排第一的就去哪个', 'The person in front goes to whichever cashier is free.'),
    (89.0, 93.0, '有人慢，只卡住一个收银台，卡不住你', 'A slow customer blocks one cashier — not you.'),
    (93.0, 99.2, '平均只快了一点，但再也没人能后来先走', 'Only a little faster — but nobody who came later gets ahead.'),
    (101.2, 104.6, '你盯着隔壁那队的时候——', "While you're watching the other line—"),
    (104.6, 109.0, '——隔壁的人，也在盯着你这队', "—they're watching yours."),
    (109.0, 113.0, '每一次，都有大约三分之二的人，觉得别人那队更快', 'Every time, about two-thirds of people think another line is faster.'),
    (118.0, 121.2, '你排队会换队吗？换队扣 1，死守扣 2', 'Do you switch lines? Comment 1 = switch, 2 = stay put.'),
]

# the film's thesis: a full card, not a caption (113.2–117.7)
THEME = (113.2, 117.7, ['你不是运气差，', '只是总盯着比你快的那一队。'], "You're not unlucky — you just keep watching the faster line.",
         '说到底，我们都排在同一队里', "In the end, we're all in the same line.")
TITLE = ('为什么你总排到慢的那队？', 'WHY IS YOUR LINE ALWAYS THE SLOW ONE?')

# ---------------------------------------------------------------- the ~90 s cut (CUT=90): an edit list over film time
# (film_a, film_b, speed). Gaps are cut; speed 2 plays the span twice as fast (its beats land on 8th notes). Wipes, the race,
# the thesis and the vote stay at 1×. Every boundary is on a whole second (two beats at 120 BPM).
SEG90 = [(0, 9, 1), (9, 12, 2), (12, 20, 1), (22, 24, 1), (24, 26, 2), (26, 28, 1), (33, 36, 1), (36, 40, 2), (40, 43, 1),
         (44, 50, 2), (50, 56, 1), (57, 59, 1), (60, 63, 1), (63, 67, 2), (67, 70, 1), (71, 74, 1), (74, 78, 2), (78, 84, 1),
         (84, 88, 2), (88, 92, 1), (93, 97, 1), (99, 101, 1), (102, 108, 1), (109, 123, 1)]


def seg_table(seg):
    out, o = [], 0.
    for a, b, sp in seg: out.append((a, b, sp, o)); o += (b - a) / sp
    return out, o


def film2out(t, seg=SEG90, side=None):
    """film time → output time; None inside a cut (side='next'/'prev' snaps to the nearest kept time instead)"""
    tab, _ = seg_table(seg)
    for i, (a, b, sp, o) in enumerate(tab):
        if a <= t < b or (t == b and i == len(tab) - 1): return o + (t - a) / sp
        if t < a:
            if side == 'next': return o
            if side == 'prev' and i: pa, pb, psp, po = tab[i - 1]; return po + (pb - pa) / psp
            return None
    return tab[-1][3] + (tab[-1][1] - tab[-1][0]) / tab[-1][2] if side else None


def out2film(T, seg=SEG90):
    tab, tot = seg_table(seg)
    for a, b, sp, o in tab:
        if T < o + (b - a) / sp: return a + max(0., T - o) * sp
    return tab[-1][1]
