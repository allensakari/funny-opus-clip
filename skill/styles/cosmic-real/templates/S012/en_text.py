"""S012 English-only cut (SUB=pure, YouTube): every Chinese string drawn on screen → English.
Exact lines first, then rules for the counters (万 = 10⁴, 亿 = 10⁸). A Chinese string with no translation stops the render (KeyError),
so nothing Chinese can slip into the English cut. English lines that would repeat a translated title are mapped to '' (not drawn)."""
import re

TR = {
    # hook / hope
    '把宇宙 138 亿年压成一年，': 'Squeeze 13.8 billion years into one year:',
    '人类只活在最后': 'humans get the last',
    '宇宙年龄 Planck 2018 · 智人 31.5 万年 Hublin et al. 2017 · 计算': 'Age of the universe: Planck 2018 · Homo sapiens 315,000 yr: Hublin et al. 2017 · calculated',
    '宇宙日历': 'Cosmic Calendar',
    '138 亿年 = 1 年': '13.8 billion yr = 1 year',
    '12 月 31 日 23:48': 'Dec 31, 23:48',
    '人类出现': 'Humans appear',
    '智人的灯，一点点亮起来': 'the lights of Homo sapiens, coming on one by one',
    '1,170 亿人': '117 billion people',
    '都在这里活过': 'have lived here',
    # despair
    '约 40 亿个物种': 'about 4 billion species',
    '每个点约 100 万个物种 · Barnosky et al., Nature 2011': 'each dot ≈ 1 million species · Barnosky et al., Nature 2011',
    '五次大灭绝': 'Five mass extinctions',
    '每一次，带走四分之三以上的物种': 'each one wiped out more than three quarters of all species',
    '奥陶纪末': 'End-Ordovician', '晚泥盆世': 'Late Devonian', '二叠纪末': 'End-Permian', '三叠纪末': 'End-Triassic', '白垩纪末': 'End-Cretaceous',
    '生物多样性曲线为示意 · 年代 ICS 2023 · 定义 Barnosky et al. 2011': 'diversity curve is illustrative · dates ICS 2023 · definition Barnosky et al. 2011',
    '6,600 万年前': '66 million years ago',
    '恐龙统治了 1.6 亿年': 'Dinosaurs ruled for 160 million years',
    '希克苏鲁伯撞击 · Schulte et al., Science 2010': 'Chicxulub impact · Schulte et al., Science 2010',
    '金字塔建成时，猛犸象还活着': 'When the Great Pyramid rose, mammoths were still alive',
    '胡夫金字塔建成': 'Great Pyramid built', '最后的猛犸象': 'the last mammoths',
    '胡夫金字塔 · 照片 Gary Todd（CC0）': 'Great Pyramid of Giza · photo Gary Todd (CC0)',
    '长毛猛犸象复原图 · Mauricio Antón（CC BY 2.5）': 'Woolly mammoths, reconstruction · Mauricio Antón (CC BY 2.5)',
    'Bronk Ramsey et al., Science 2010 · Vartanyan et al., Radiocarbon 1995（弗兰格尔岛）': 'Bronk Ramsey et al., Science 2010 · Vartanyan et al., Radiocarbon 1995 (Wrangel Island)',
    '地球 45.4 亿年 = 1 天': "Earth's 4.54 billion years = 1 day",
    '0 点': '0:00', '最后 6 秒': 'the last 6 seconds', '才轮到智人': 'belong to Homo sapiens',
    '地球年龄 Dalrymple 2001 · 智人 Hublin et al. 2017 · 计算': 'Age of Earth: Dalrymple 2001 · Homo sapiens: Hublin et al. 2017 · calculated',
    '有文字的历史': 'Written history', '只占 1.7%': 'just 1.7%', '智人 30 万年': 'Homo sapiens: 300,000 years', '文字 5,200 年': 'writing: 5,200 years',
    '最早的文字约公元前 3200 年 · Woods (ed.), Visible Language 2010 · 计算': 'earliest writing c. 3200 BC · Woods (ed.), Visible Language 2010 · calculated',
    '1,170 亿人来过': '117 billion people have lived',
    '每盏灯 10 亿人 · 2022 年在世 79.6 亿 · Kaneda & Haub, PRB 2022': 'each light = 1 billion people · alive in 2022: 7.96 billion · Kaneda & Haub, PRB 2022',
    '有史以来出生人数 · Kaneda & Haub, PRB 2022': 'everyone ever born · Kaneda & Haub, PRB 2022',
    '仿 1990 年旅行者 1 号「暗淡蓝点」视角 · 示意': "after Voyager 1's 1990 Pale Blue Dot view · illustrative",
    '每年远离': 'drifts away every year', '3.82 厘米': '3.82 cm',
    '激光测月 · Dickey et al., Science 1994 · 距离示意，未按比例': 'Lunar laser ranging · Dickey et al., Science 1994 · distance not to scale',
    '每 10 亿年': 'every billion years', '亮约 10%': 'about 10% brighter',
    '太阳光度演化 · Gough, Solar Physics 1981': 'solar luminosity evolution · Gough, Solar Physics 1981',
    # act 1: resisting on Earth
    '我们不肯认命': "We didn't accept our fate", '人类的平均寿命': 'human life expectancy',
    '全球出生时预期寿命 · 1900：Riley 2005 · 2023：UN WPP 2024 · 中间为示意曲线': 'global life expectancy at birth · 1900: Riley 2005 · 2023: UN WPP 2024 · curve in between is illustrative',
    '137.8 万份种子': '1.378 million seeds', '存进北极的山里，给末日留一份备份': 'stored inside an Arctic mountain, a backup for doomsday',
    'NordGen 年报 2025 · 来自 131 个基因库': 'NordGen annual report 2025 · from 131 genebanks',
    '照片 Dag Endresen · CC BY 2.0 · 斯瓦尔巴全球种子库入口（2008）': 'photo Dag Endresen · CC BY 2.0 · Svalbard Global Seed Vault entrance (2008)',
    '我们在地球上点燃了核聚变': 'we ignited nuclear fusion on Earth', '输入 2.05 兆焦 → 输出 3.15 兆焦': 'in: 2.05 MJ → out: 3.15 MJ',
    '美国国家点火装置（NIF）· Abu-Shawareb et al., PRL 2024 · 192 束激光为示意': 'National Ignition Facility (NIF) · Abu-Shawareb et al., PRL 2024 · 192 beams illustrative',
    '我们撞了一颗小行星，它的公转周期被改短了': 'we hit an asteroid, and its orbit got shorter',
    'NASA / Johns Hopkins APL · DART 撞击前约 3 秒拍下的 Dimorphos': 'NASA / Johns Hopkins APL · Dimorphos, ~3 s before DART hit it',
    'Thomas et al., Nature 2023（−33.0 ± 1.0 分钟）': 'Thomas et al., Nature 2023 (−33.0 ± 1.0 min)',
    # act 2: out into space
    '在月球上走过': 'walked on the Moon', '12 个人': '12 people', '阿波罗 11 号': 'Apollo 11',
    '国际空间站从 2000 年起没断过人': 'ISS continuously crewed since 2000', '离地面只有约 400 公里': 'only about 400 km up',
    'NASA 照片 iss056e201248 · 2018 年联盟号绕飞拍摄': 'NASA photo iss056e201248 · taken from a Soyuz fly-around, 2018',
    '2026 年 4 月，人类到过最远的地方': 'April 2026: the farthest humans have been', '406,771 公里': '406,771 km', '光只要 1.36 秒': 'light needs only 1.36 s',
    'NASA 照片 art002e021278 · 2026-04-06 猎户座飞船拍的「地落」': 'NASA photo art002e021278 · Earthset from Orion, 2026-04-06',
    '到月球距离的 0.1% · NASA': '0.1% of the Moon distance · NASA', 'NASA Artemis II · 光速换算': 'NASA Artemis II · light-time calculated',
    '192 公里 / 秒': '192 km/s', '帕克探测器穿过太阳大气': "Parker Solar Probe flew through the Sun's atmosphere",
    '离太阳表面只有 617 万公里': 'only 6.17 million km from its surface',
    'NASA 2024-12-24 · 人造物体最快纪录 · 探测器为示意': 'NASA 2024-12-24 · fastest human-made object · probe illustrative',
    '我们在另一颗行星上飞了起来': 'we flew on another planet', '机智号，第一次地外动力飞行 · NASA': 'Ingenuity, first powered flight on another world · NASA',
    'NASA / JPL-Caltech / ASU · PIA24648 · 毅力号拍下的机智号': 'NASA / JPL-Caltech / ASU · PIA24648 · Ingenuity, seen by Perseverance',
    '135 亿年前的光': '13.5 billion years', '韦布望远镜看到的最远星系': 'old light, from the most distant galaxy Webb has seen',
    'Carniani et al., Nature 2024（z = 14.32）': 'Carniani et al., Nature 2024 (z = 14.32)',
    'NASA 照片 · 韦布望远镜的金色主镜（2017）': "NASA photo · Webb's golden mirror (2017)",
    '5,500 万光年外的黑洞': 'a black hole 55 million light-years away', '2019 年，我们第一次拍到它的样子': 'in 2019, we saw it for the first time',
    '事件视界望远镜 · ApJL 875 L1（2019）': 'Event Horizon Telescope · ApJL 875 L1 (2019)',
    'EHT Collaboration / ESO · CC BY 4.0 · M87* 黑洞照片（2019）': 'EHT Collaboration / ESO · CC BY 4.0 · M87* black hole (2019)',
    '飞了 48 亿公里': 'after 4.8 billion km', '才第一次看清冥王星': 'we finally saw Pluto up close',
    'NASA 新视野号 · 2015-07-14': 'NASA New Horizons · 2015-07-14',
    'NASA / JHUAPL / SwRI · PIA19952 · 新视野号拍的冥王星': 'NASA / JHUAPL / SwRI · PIA19952 · Pluto by New Horizons',
    '13 亿年前，两个黑洞相撞': '1.3 billion years ago, two black holes collided', '2015 年，我们听见了它': 'in 2015, we heard it',
    'LIGO GW150914 · Abbott et al., PRL 2016 · 波形为示意': 'LIGO GW150914 · Abbott et al., PRL 2016 · waveform illustrative',
    '地球': 'Earth', 'M13 星团': 'M13 cluster', '1974 年，我们向 2.5 万光年外喊了一声': 'In 1974, we called out to a star cluster 25,000 light-years away',
    '要 2.5 万年才能到': 'it will take 25,000 years to arrive',
    '阿雷西博信息 · 1,679 个比特 · NAIC / Cornell 1974': 'Arecibo message · 1,679 bits · NAIC / Cornell 1974',
    '旅行者 1 号出发': 'Voyager 1 sets out', 'NASA / JPL 照片 PIA21747 · 1977-09-05': 'NASA / JPL photo PIA21747 · 1977-09-05',
    '55 种语言': '55 languages', '向宇宙问好': 'saying hello to the universe', '旅行者号金唱片 · NASA / JPL': 'Voyager Golden Record · NASA / JPL',
    'NASA / JPL 照片 PIA21741 · 1977 年为金唱片装机': 'NASA / JPL photo PIA21741 · mounting the Golden Record, 1977',
    '它飞出了太阳风吹到的边界': 'it passed the edge of the solar wind',
    '每年 5.2 亿公里': '520 million km a year', '每年约 5.2 亿公里（NASA）· 计算': 'about 520 million km a year (NASA) · calculated',
    # breath
    '旅行者 1 号（1 光日）': 'Voyager 1 (1 light-day)', '= 1 光日': '= 1 light-day', '最近的恒星': 'the nearest star', '比邻星': 'Proxima Centauri',
    '1,551 光日': '1,551 light-days', '比邻星 1.3020 pc · Gaia DR3 · 计算': 'Proxima Centauri 1.3020 pc · Gaia DR3 · calculated',
    'NASA：2026 年 11 月 18 日，旅行者 1 号距地球 1 光日': 'NASA: on Nov 18, 2026, Voyager 1 is 1 light-day from Earth',
    '照这个速度': 'at this speed', '还要 7.7 万年': '77,000 more years',
    '电力每年少 4 瓦': 'losing 4 watts of power a year', '预计 2030 年代': 'expected in the 2030s', '它将彻底沉默': 'it will fall silent',
    'NASA 2025-03 · 为延长任务关闭仪器': 'NASA 2025-03 · instruments shut off to extend the mission',
    '这是我们走得最远的一次': 'This is the farthest we have ever gone',
    # fate
    '植物会先死去': 'plants die first', '二氧化碳不够了': 'not enough carbon dioxide left',
    'C4 植物至少还能撑 9–15 亿年 · Caldeira & Kasting, Nature 1992': 'C4 plants hold on for at least 0.9–1.5 billion years · Caldeira & Kasting, Nature 1992',
    '海洋开始散失': 'the oceans begin to escape',
    'Gough 1981 光度 + Wolf & Toon 2015 湿温室阈值 · 计算': 'Gough 1981 luminosity + Wolf & Toon 2015 moist-greenhouse threshold · calculated',
    '太阳变成红巨星': 'the Sun becomes a red giant',
    # cold open / end
    '76 亿年后': 'In 7.6 billion years', '太阳会吞掉地球': 'the Sun will swallow the Earth', '我们能逃到哪里？': 'Where can we go?',
    '距今': 'from now', '10¹³ 年': '10¹³ years', '10¹⁴ 年': '10¹⁴ years',
    '最后的恒星也会熄灭': 'even the last stars burn out', '再也没有新的星星': 'no new stars, ever again',
    '宇宙不会记得我们来过': 'The universe will not remember we were here.',
}
# English lines already drawn under a Chinese title: the title is English now, so these would repeat it
SKIP = {'Squeeze 13.8 billion years into one year: humans exist only in its last 12 minutes.', 'The universe will not remember we were here.'}
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def _f(s): return float(s.replace(',', ''))
def _num(v, nd=1):
    s = f'{v:,.{nd}f}'
    return s[:-(nd + 1)] if nd and s.endswith('.' + '0' * nd) else s
def _yi(v, unit):
    """v × 10⁸ unit → 'N million unit' / 'N billion unit'"""
    return f'{_num(v * 100, 0)} million {unit}' if v < 10 else f'{_num(v / 10)} billion {unit}'


RULES = [
    (r'(\d[\d,.]*) 万年', lambda m: f'{_num(_f(m[1]) * 1e4, 0)} years'),
    (r'(\d[\d,.]*) 亿公里', lambda m: _yi(_f(m[1]), 'km')),
    (r'(\d[\d,.]*) 亿年前', lambda m: f'{_num(_f(m[1]) * 100, 0)}M yrs ago'),          # the extinction labels sit close together
    (r'\+(\d[\d,.]*) 亿年', lambda m: '+' + _yi(_f(m[1]), 'years')),
    (r'(\d[\d,.]*) 分钟', lambda m: f'{m[1]} minutes'),
    (r'(\d+) 岁', lambda m: f'{m[1]} yrs'),
    (r'(\d{4}) 年：(\d+) 岁', lambda m: f'{m[1]}: age {m[2]}'),
    (r'(\d{4}) 年', lambda m: m[1]),
    (r'(\d[\d.]*) 年', lambda m: f'{m[1]} years'),
    (r'(\d[\d,.]*)% 已经灭绝', lambda m: f'{m[1]}% already extinct'),
    (r'(\d[\d,.]*)% 已经离开', lambda m: f'{m[1]}% already gone'),
    (r'(\d+)月', lambda m: MON[int(m[1]) - 1]),
    (r'公元前 (\d+) 年', lambda m: f'{m[1]} BC'),
]
CJK = re.compile(r'[　-鿿＀-￯]')


def tr(s):
    if not CJK.search(s): return '' if s in SKIP else s
    if s in TR: return TR[s]
    for p, f in RULES:
        m = re.fullmatch(p, s)
        if m: return f(m)
    raise KeyError(f'no English for: {s}')
