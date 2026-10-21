#version 330
// S012 转场（A → B，uU ∈ [0, 1]，中点落在拍上）。无闪白、无抖动、无缩放冲击；情绪按段落挑：
// 0 熄灯：A 里亮的东西一点点熄掉（像城市灯光一盏盏灭），黑里浮出 B
// 1 红移：A 被往红端拉长、褪色，B 从蓝端回到正常颜色
// 2 时间流逝：画面沿时间方向拖出长曝光拖影，拖影过去换成 B
// 3 引力透镜：焦点处长出爱因斯坦环，环把 A 扭开，环内是 B
// 4 化为尘埃：A 碎成尘埃向右上方飘散，露出 B
// 5 曲速：从焦点向外拉出星光线（径向模糊，不缩放），线收回后是 B
// 6 日食：一个黑色圆盘滑过，盘边有日冕光，盘后是 B
// 7 光柱：一束体积光从焦点扫过，光里是 B
// 8 时空涟漪（3 分钟版）：从焦点荡开一圈圈引力波，波前把 A 推开，波后是 B
// 9 烧穿成黑（3 分钟版）：A 像胶片一样从几处烧出焦边的洞，洞里先是黑，再浮出 B
uniform sampler2D uA, uB;
uniform vec2 uRes;
uniform float uU, uTime;
uniform int uMode;
uniform vec2 uP;
in vec2 v;
out vec4 fragColor;

float hash(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float noise(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { float a = .5, s = 0.; for (int k = 0; k < 5; k++) { s += a * noise(p); p *= 2.03; a *= .5; } return s; }
vec3 A(vec2 uv) { return texture(uA, clamp(uv, 0., 1.)).rgb; }
vec3 Bt(vec2 uv) { return texture(uB, clamp(uv, 0., 1.)).rgb; }
float ss(float a, float b, float x) { return smoothstep(a, b, x); }
float lum(vec3 c) { return dot(c, vec3(.3, .59, .11)); }

void main() {
    vec2 uv = v; vec2 px = uv * uRes; float u = uU; float asp = uRes.x / uRes.y; vec2 P = vec2(uP.x / uRes.x, 1. - uP.y / uRes.y);
    vec3 col;
    if (uMode == 0) {                                                // lights out
        vec3 a = A(uv); float h = hash(floor(px / 3.)); float k = ss(.0, .6, u);
        float out_ = ss(h - .08, h + .08, k * 1.15) ;                // each little light has its own moment
        vec3 ad = a * (1. - out_) * (1. - .6 * k) ;
        col = ad + Bt(uv) * ss(.45, 1., u) ;
    } else if (uMode == 1) {                                         // redshift
        float k = ss(.0, .55, u), kb = ss(.45, 1., u);
        vec2 s = vec2(.02 * k * (uv.x - .5), 0.);
        vec3 a = (A(uv) + A(uv - s) + A(uv - 2. * s) + A(uv - 3. * s)) / 4.;
        a = mix(a, vec3(lum(a)) * vec3(1.6, .45, .25), k) * (1. - .5 * k);
        vec3 b = Bt(uv); b = mix(vec3(lum(b)) * vec3(.35, .55, 1.4), b, kb);
        col = mix(a, b, ss(.35, .75, u));
    } else if (uMode == 2) {                                         // time smear (long exposure along x)
        float k = sin(3.14159 * u); vec3 s = vec3(0.);
        for (int i = 0; i < 24; i++) { float o = (float(i) / 23. - .5) * .18 * k; s += mix(A(uv + vec2(o, 0)), Bt(uv + vec2(o, 0)), ss(.4, .6, u + o * 2.)); }
        col = s / 24.;
    } else if (uMode == 3) {                                         // gravitational lens
        vec2 d = (uv - P) * vec2(asp, 1.); float r = length(d) + 1e-4; float R = mix(.0, 1.4, ss(.0, 1., u));
        float th = .08 * sin(3.14159 * u);                            // Einstein radius
        vec2 dd = d * (1. - th * th / (r * r) * 1.);
        vec2 q = P + dd / vec2(asp, 1.);
        float inside = ss(R + .02, R - .02, r);
        col = mix(A(q), Bt(q), inside);
        col += vec3(.8, .85, 1.) * exp(-pow((r - th) / .006, 2.)) * .35 * sin(3.14159 * u);
    } else if (uMode == 4) {                                         // turn to dust
        float n = fbm(px / 14.) * .7 + hash(floor(px / 2.)) * .3;
        float front = (uv.x * .6 + (1. - uv.y) * .4);                // dissolves from the lower left
        float k = u * 1.6 - front * .6;
        float gone = ss(n - .05, n + .05, k);
        vec2 drift = vec2(.08, .05) * ss(n, n + .5, k);              // grains already loose drift up-right
        vec3 grain = A(uv - drift) * (1. - ss(n + .2, n + .6, k));
        col = mix(A(uv), Bt(uv), ss(.3, 1., u) * gone) ;
        col = mix(col, max(col, grain * vec3(1., .85, .7)), gone * (1. - ss(.7, 1., u)) * .9);
    } else if (uMode == 5) {                                         // warp streaks (radial blur, no scaling)
        vec2 d = uv - P; float k = sin(3.14159 * u); vec3 s = vec3(0.);
        for (int i = 0; i < 28; i++) { float o = float(i) / 27. * .22 * k; vec2 q = uv - d * o; s += mix(A(q), Bt(q), ss(.45, .55, u)); }
        col = s / 28. * (1. + .15 * k);
    } else if (uMode == 6) {                                         // eclipse wipe
        float R = .75; vec2 c = vec2(mix(-.9, 1.9, u) * asp, .5) ; vec2 d = vec2(uv.x * asp, uv.y) - c; float r = length(d);
        float behind = ss(c.x + .0, c.x - .0 - .01, uv.x * asp - R * 0.) ;   // left of the disc's centre line: B
        float disc = ss(R + .004, R - .004, r);
        col = mix(A(uv), Bt(uv), step(uv.x * asp, c.x));
        col = mix(col, vec3(0.), disc);
        col += vec3(1., .85, .6) * exp(-pow((r - R) / .012, 2.)) * .8 + vec3(1., .7, .4) * exp(-max(r - R, 0.) * 9.) * .18 * (1. - disc);
    } else if (uMode == 8) {                                         // spacetime ripples
        vec2 d = (uv - P) * vec2(asp, 1.); float r = length(d); float front = u * 1.5;
        float w = 0.;
        for (int k = 0; k < 5; k++) { float rk = front - float(k) * .09; w += sin((r - rk) * 60.) * exp(-pow((r - rk) / .05, 2.)) * (1. - float(k) * .18); }
        vec2 off = normalize(d + 1e-4) / vec2(asp, 1.) * w * .02;
        col = mix(A(uv + off), Bt(uv + off), ss(front + .05, front - .05, r));
        col += vec3(.6, .75, 1.) * max(0., w) * .12 * (1. - u);
    } else if (uMode == 9) {                                         // film burn to black, then B
        float n = fbm(px / 60.) * .8 + fbm(px / 9.) * .2; float d = length((uv - P) * vec2(asp, 1.));
        float k = u * 1.9 - d * .5;
        float hole = ss(n + .02, n - .02, k * .9);
        float edge = exp(-pow((n - k * .9) / .025, 2.));
        col = A(uv) * (1. - hole);
        col += vec3(1., .55, .2) * edge * (1. - ss(.6, .9, u)) * 1.2;
        col = mix(col, Bt(uv), ss(.6, 1., u));
    } else {                                                         // god-ray sweep
        vec2 d = (uv - P) * vec2(asp, 1.); float ang = atan(d.y, d.x); float sweep = mix(-3.6, 3.6, u);
        float beam = exp(-pow((ang - sweep) / .35, 2.)) * ss(.0, .3, length(d));
        float passed = ss(sweep + .3, sweep - .3, ang) * ss(-3.1416, -2.5, ang);          // feathered start ray (no hard seam at ±π)
        passed = max(passed, ss(.8, 1., u));
        col = mix(A(uv), Bt(uv), passed);
        float rays = .6 + .4 * noise(vec2(ang * 40., 0.));
        col += vec3(1., .9, .75) * beam * rays * .35;
    }
    fragColor = vec4(col, 1.);
}
