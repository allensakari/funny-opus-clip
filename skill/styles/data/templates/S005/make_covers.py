"""S005 封面（定稿）：python make_covers.py [尺寸 …]
  浅色（沙土，主封面）→ 发布/封面_9x16 / 3x4 / 16x9 / 4x3.jpg
  深色                → 发布/封面_深色_9x16 / 3x4 / 16x9 / 4x3.jpg
底图：plates.py 的 A_road（红灯前 8 辆车、绿牌那辆亮起），两种主题各渲染一次（含 FILM_W=1920 FILM_H=1080）"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
SIZES = sys.argv[1:]
if os.environ.get('SHUSHUO_THEME_FIXED'):
    sys.path.insert(0, HERE + '/../../engine'); os.chdir(HERE)
    import covers
    th = covers.THEME; P = 'build/review/plates/'
    covers.make('scene', '发布/封面' + ('_深色' if th == 'dark' else ''), sizes=SIZES or None, number='4,897万', unit='辆', pre='中国路上已经有', post='新能源车',
                plate=f'{P}A_road_{th}_1080x1920.png', plate_land=f'{P}A_road_{th}_1920x1080.png',
                zoom=.86, zoom_land=1.3, shift={'9x16': (0, -.20), '3x4': (0, -.26), '16x9': (.10, .03), '4x3': (.24, .03)})
else:
    for th in ('sand', 'dark'):                       # each theme in its own process (brand reads the theme at import)
        subprocess.check_call([sys.executable, __file__] + SIZES, env=dict(os.environ, SHUSHUO_THEME=th, SHUSHUO_THEME_FIXED='1'))
