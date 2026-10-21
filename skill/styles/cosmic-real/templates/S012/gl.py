"""S012 GL 层：宇宙场景（space.glsl）+ 转场（trans.glsl）。纹理：NASA Blue Marble、云、Black Marble 2016 城市灯光（tex/，公有领域）。"""
import os
import numpy as np
import skia
import moderngl

HERE = os.path.dirname(os.path.abspath(__file__)); EP = os.path.dirname(HERE)
VS = '#version 330\nin vec2 p; out vec2 v; void main(){ v = p * .5 + .5; gl_Position = vec4(p, 0, 1); }'


def _img(path):
    im = skia.Image.open(path).convert(alphaType=skia.kUnpremul_AlphaType, colorType=skia.kRGBA_8888_ColorType)
    return np.ascontiguousarray(np.array(im)[..., :3])


class GL:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.ctx = moderngl.create_standalone_context()
        quad = self.ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], 'f4'))
        self.sc = self.ctx.program(vertex_shader=VS, fragment_shader=open(HERE + '/space.glsl').read())
        self.vs = self.ctx.simple_vertex_array(self.sc, quad, 'p')
        self.fbo = self.ctx.simple_framebuffer((W, H)); self.sc['uRes'] = (W, H)
        self.tex = {}
        for unit, (name, f) in enumerate((('tDay', 'day.jpg'), ('tNight', 'night_gray.jpg'), ('tCloud', 'clouds.jpg'))):
            a = _img(EP + '/tex/' + f)
            t = self.ctx.texture((a.shape[1], a.shape[0]), 3, a.tobytes()); t.build_mipmaps(); t.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
            t.repeat_x, t.repeat_y = True, False; t.anisotropy = 8.0
            self.tex[name] = (unit, t)
            if name in self.sc: self.sc[name] = unit
        self.tr = self.ctx.program(vertex_shader=VS, fragment_shader=open(HERE + '/trans.glsl').read())
        self.vt = self.ctx.simple_vertex_array(self.tr, quad, 'p'); self.tr['uRes'] = (W, H)
        self.ta, self.tb = self.ctx.texture((W, H), 3), self.ctx.texture((W, H), 3)
        self.tr['uA'] = 4; self.tr['uB'] = 5

    def scene(self, t, s):
        for unit, tx in self.tex.values(): tx.use(unit)
        U = dict(uTime=t, uCamPos=s['cam'], uCamTgt=s['tgt'], uFov=s['fov'], uEarth=s['earth'], uSun=s['sun'], uMoon=s['moon'], uSunDir=s['sundir'],
                 uYaw=s['yaw'], uLights=s['lights'], uClouds=s['clouds'], uDry=s['dry'], uScorch=s['scorch'], uSunK=s['sunk'], uStarDeath=s['stardeath'],
                 uStars=s['stars'], uMilky=s['milky'], uExpose=s['expose'], uGlow=s['glow'], uSunGlow=s['sunglow'], uBrown=s.get('brown', 0.0))
        for k, v in U.items():
            if k in self.sc: self.sc[k] = tuple(map(float, v)) if isinstance(v, (tuple, list, np.ndarray)) else float(v)
        self.fbo.use(); self.vs.render(moderngl.TRIANGLE_STRIP)
        return np.frombuffer(self.fbo.read(components=3), np.uint8).reshape(self.H, self.W, 3)[::-1]

    def trans(self, a, b, u, mode, p, t=0.0):
        self.ta.write(np.ascontiguousarray(a[..., :3]).tobytes()); self.tb.write(np.ascontiguousarray(b[..., :3]).tobytes())
        self.ta.use(4); self.tb.use(5); self.tr['uU'] = u; self.tr['uMode'] = mode; self.tr['uP'] = p
        if 'uTime' in self.tr: self.tr['uTime'] = t
        self.fbo.use(); self.vt.render(moderngl.TRIANGLE_STRIP)
        return np.frombuffer(self.fbo.read(components=3), np.uint8).reshape(self.H, self.W, 3)
