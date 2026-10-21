"""S005 配乐（MUSIC=A 默认）：Kevin MacLeod「Lasting Hope」100 BPM；曲中最响的一段（≈95 s）对准 world（全球 60%），全片情绪高点。"""
import os
V = os.environ.get('MUSIC', 'A')
TRACKS = {'A': dict(file='Lasting_Hope.mp3', title='Lasting Hope', beat=0.6001, down0=1.8214, align=(95.0, ('world', None)), suffix='', rich=True)}
M = TRACKS[V]
BEAT, SUFFIX = M['beat'], M['suffix'] + os.environ.get('VTAG', '')      # VTAG: variant suffix (e.g. _A2dark), never overwrites the main version
