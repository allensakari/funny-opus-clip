#version 330
// S012 宇宙模拟（解析光线追踪，无步进）：星场 + 银河、地球（白天贴图 / 夜晚城市灯光 / 云 / 大气 / 海面反光 / 海洋蒸发 / 烤焦）、
// 太阳（米粒组织、临边昏暗、日冕；uSunK 0 = 今天的黄白色 → 1 = 红巨星的暗红、大对流胞）、月球（程序环形山）。
uniform vec2 uRes;
uniform float uTime;
uniform vec3 uCamPos, uCamTgt;
uniform float uFov;
uniform vec4 uEarth;            // xyz, r (r = 0 → none)
uniform vec4 uSun;              // xyz, r
uniform vec4 uMoon;             // xyz, r
uniform vec3 uSunDir;           // light direction used when the Sun is far off-screen
uniform float uYaw, uLights, uClouds, uDry, uScorch, uSunK, uStarDeath, uStars, uMilky, uExpose, uGlow, uSunGlow;
uniform float uBrown;          // 3 分钟版：植物死去，绿色大陆褪成枯黄（0 = 今天）
uniform sampler2D tDay, tNight, tCloud;
float gLod = 0.;
vec3 TX(sampler2D t, vec2 uv, float w) { return textureLod(t, uv, max(0., gLod + log2(w / 5400.))).rgb; }
in vec2 v;
out vec4 fragColor;
const float PI = 3.14159265;

float hash(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float hash3(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
float noise(vec3 p) { vec3 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
    return mix(mix(mix(hash3(i), hash3(i + vec3(1, 0, 0)), f.x), mix(hash3(i + vec3(0, 1, 0)), hash3(i + vec3(1, 1, 0)), f.x), f.y),
               mix(mix(hash3(i + vec3(0, 0, 1)), hash3(i + vec3(1, 0, 1)), f.x), mix(hash3(i + vec3(0, 1, 1)), hash3(i + vec3(1, 1, 1)), f.x), f.y), f.z); }
float fbm(vec3 p) { float a = .5, s = 0.; for (int k = 0; k < 6; k++) { s += a * noise(p); p *= 2.03; a *= .5; } return s; }

float iSphere(vec3 ro, vec3 rd, vec4 s) {
    vec3 oc = ro - s.xyz; float b = dot(oc, rd), c = dot(oc, oc) - s.w * s.w, h = b * b - c;
    if (h < 0.) return -1.; return -b - sqrt(h);
}
float sphDist(vec3 ro, vec3 rd, vec4 s) { vec3 oc = s.xyz - ro; float b = max(dot(oc, rd), 0.); return length(oc - rd * b) - s.w; }   // closest approach (for glows)

vec3 sunColor(float k) { return mix(vec3(1., .82, .55), vec3(1., .28, .06), k); }

// ---------------------------------------------------------------- background: stars + Milky Way (stars die one by one as uStarDeath → 1)
vec3 sky(vec3 rd) {
    vec3 c = vec3(0.); float pix = uFov / uRes.y;                       // angular size of a pixel
    for (int L = 0; L < 3; L++) {                                       // three layers of star cells; stars drawn at ≥ 1 px so they never alias away
        float sc = L == 0 ? 40. : L == 1 ? 110. : 260.;
        vec3 q = rd * sc; vec3 id = floor(q);
        for (int k = 0; k < 2; k++) {                                   // the cell and its nearest neighbour along the dominant axis
            vec3 cid = id + (k == 0 ? vec3(0.) : sign(fract(q) - .5) * step(.5, abs(fract(q) - .5)) * 0. + vec3(0.));
            float h = hash3(cid + float(L) * 17.);
            if (h < (L == 0 ? .955 : L == 1 ? .955 : .94)) continue;
            vec3 off = vec3(hash3(cid + 1.), hash3(cid + 2.), hash3(cid + 3.));
            vec3 sd = normalize((cid + off) / sc);
            float ang = acos(clamp(dot(sd, rd), -1., 1.));
            float br = pow(hash3(cid + 4.), 5.) * (L == 0 ? 7. : L == 1 ? 2.5 : 1.) + (L == 2 ? .06 : .12);
            float alive = step(uStarDeath, hash3(cid + 9.) * .999 + .001);
            vec3 tint = mix(vec3(1., .78, .6), vec3(.72, .84, 1.), hash3(cid + 5.));
            float rad = pix * (L == 0 ? 1.3 : 1.0);
            c += tint * br * exp(-pow(ang / rad, 2.)) * alive * .8;
        }
    }
    float band = exp(-pow(dot(rd, normalize(vec3(.25, .9, -.35))) / .22, 2.));                // the Milky Way
    float dust = fbm(rd * 7.) ; float glow = band * (.35 + .65 * fbm(rd * 3. + 2.)) * smoothstep(.35, .75, dust + .25);
    c += vec3(.55, .6, .75) * glow * .22 * uMilky * (1. - uStarDeath);
    c += vec3(.9, .75, .6) * band * smoothstep(.55, .9, fbm(rd * 14.)) * .08 * uMilky * (1. - uStarDeath);
    return c * uStars;
}

// ---------------------------------------------------------------- the Sun / red giant
vec3 sunSurface(vec3 n, vec3 rd) {
    float mu = max(0., dot(n, -rd));
    float cells = mix(34., 6., uSunK);
    float g = fbm(n * cells + vec3(0., 0., uTime * .05)); float g2 = fbm(n * cells * 3.1 + vec3(uTime * .12));
    float gran = smoothstep(.3, .7, g) * .7 + g2 * .3;
    vec3 hot = mix(vec3(1., .97, .88), vec3(1., .55, .2), uSunK), cool = mix(vec3(1., .55, .18), vec3(.55, .07, .02), uSunK);
    float limb = pow(mu, mix(.45, .9, uSunK));
    vec3 c = mix(cool, hot, limb * (.55 + .45 * gran));
    c *= mix(.55, .25, uSunK) + (1. - mix(.55, .25, uSunK)) * limb;
    c *= .8 + .45 * gran;
    return c * mix(2.4, 1.5, uSunK);
}

// ---------------------------------------------------------------- Earth
vec3 earth(vec3 p, vec3 rd, vec3 Ld) {
    vec3 n = normalize(p - uEarth.xyz);
    float lon = atan(n.z, n.x) + uYaw, lat = asin(clamp(n.y, -1., 1.));
    vec2 uv = vec2(fract(lon / (2. * PI) + .5), .5 - lat / PI);
    vec3 day = TX(tDay, uv, 5400.);
    float ocean = smoothstep(.12, .05, day.r + day.g * .3 - day.b * .5) ;                         // crude water mask from the colour
    float night = TX(tNight, uv, 13500.).r;
    float cl = TX(tCloud, uv, 4096.).r * uClouds * smoothstep(0., .008, min(uv.x, 1. - uv.x));   // the cloud map's own seam
    // the oceans dry out (uDry): water → pale salt and brown sea floor; then the whole surface scorches (uScorch)
    float green = smoothstep(.0, .08, day.g - max(day.r, day.b)) * (1. - ocean);                 // vegetation: green dominant on land
    day = mix(day, vec3(.58, .48, .34) * (.8 + .4 * fbm(n * 22.)), green * uBrown);
    vec3 bed = mix(vec3(.62, .55, .45), vec3(.85, .82, .76), fbm(n * 40.));
    day = mix(day, bed, ocean * smoothstep(.0, 1., uDry));
    day = mix(day, vec3(.55, .38, .26) * (.7 + .5 * fbm(n * 18.)), smoothstep(.3, 1., uDry) * (1. - ocean) * .6);
    float dif = dot(n, Ld);
    vec3 col = day * max(0., dif) * 1.15 * mix(1., .9, cl);
    col = mix(col, vec3(1.) * max(0., dif) * 1.05, cl * (1. - uDry));
    vec3 h = normalize(Ld - rd);
    col += vec3(1., .95, .85) * pow(max(0., dot(n, h)), 120.) * .9 * ocean * (1. - uDry) * (1. - cl) * step(0., dif);     // sun glint
    // city lights on the night side: brighter texels light up first as uLights grows (civilisation spreading)
    float lit = smoothstep(1. - uLights, 1. - uLights + .25, night) * night;
    col += vec3(1., .72, .38) * lit * 1.8 * smoothstep(.15, -.15, dif) * (1. - cl * .7);
    // scorched: dark crust with glowing cracks
    if (uScorch > 0.) {
        float cr = smoothstep(.06, .0, abs(fbm(n * 9.) - .5)) ;
        vec3 sc = mix(vec3(.18, .1, .07) * (max(0., dif) * .8 + .2), vec3(1., .35, .08) * 2., cr * smoothstep(.3, 1., uScorch));
        col = mix(col, sc, smoothstep(0., .6, uScorch));
        col += vec3(1., .3, .05) * uScorch * uScorch * .6 * (.4 + .6 * fbm(n * 5. + uTime * .2));
    }
    float fr = pow(1. - max(0., dot(n, -rd)), 2.5);                                                  // atmosphere rim
    vec3 atm = mix(vec3(.35, .6, 1.), vec3(1., .55, .3), smoothstep(.0, .8, uDry + uScorch));
    col += atm * fr * (.25 + 1.1 * smoothstep(-.3, .4, dif)) * (1. - uScorch * .7);
    return col;
}

vec3 moon(vec3 p, vec3 rd, vec3 Ld) {
    vec3 n = normalize(p - uMoon.xyz);
    float m = fbm(n * 6.) * .6 + fbm(n * 30.) * .3;
    float cr = 0.;
    for (int k = 0; k < 3; k++) { float s = pow(2., float(k)) * 5.; vec3 q = n * s; vec3 id = floor(q); vec3 f = fract(q) - .5;
        float r = .25 + .2 * hash3(id); cr += smoothstep(r, r * .8, length(f)) * .25 - smoothstep(r * 1.15, r, length(f)) * smoothstep(r, r * 1.05, length(f)) * .0; }
    vec3 c = vec3(.62, .6, .58) * (.55 + .5 * m - .2 * cr);
    return c * max(0., dot(n, Ld)) * 1.1;
}

void main() {
    vec2 q = (v * uRes - .5 * uRes) / uRes.y;
    vec3 fw = normalize(uCamTgt - uCamPos), rt = normalize(cross(fw, vec3(0, 1, 0))), up = cross(rt, fw);
    vec3 acc = vec3(0.);
    for (int a = 0; a < 2; a++) {
        vec2 o = (vec2(a) - .5) * .5 / uRes.y;
        vec3 rd = normalize(fw / tan(uFov * .5) + (q.x + o.x) * 2. * rt + (q.y + o.y) * 2. * up);
        vec3 ro = uCamPos; vec3 col = sky(rd);
        float tE = uEarth.w > 0. ? iSphere(ro, rd, uEarth) : -1.;
        float tS = uSun.w > 0. ? iSphere(ro, rd, uSun) : -1.;
        float tM = uMoon.w > 0. ? iSphere(ro, rd, uMoon) : -1.;
        float tb = 1e9; int hit = -1;
        if (tE > 0. && tE < tb) { tb = tE; hit = 0; }
        if (tS > 0. && tS < tb) { tb = tS; hit = 1; }
        if (tM > 0. && tM < tb) { tb = tM; hit = 2; }
        vec3 p = ro + rd * tb;
        vec3 Ld = uSun.w > 0. ? normalize(uSun.xyz - (hit == 2 ? uMoon.xyz : uEarth.xyz)) : normalize(uSunDir);
        if (hit == 0) { float pixW = tb * 2. * tan(uFov * .5) / uRes.y; gLod = log2(max(pixW / max(dot(normalize(p - uEarth.xyz), -rd), .15) * 5400. / (2. * PI * uEarth.w), 1e-6)); col = earth(p, rd, Ld); }
        else if (hit == 1) col = sunSurface(normalize(p - uSun.xyz), rd);
        else if (hit == 2) col = moon(p, rd, Ld);
        // glows: the Sun's corona (additive, also over the Earth when it sits in front), the Earth's halo
        if (uSun.w > 0.) {
            float d = sphDist(ro, rd, uSun) / uSun.w;
            if (hit != 1) col += sunColor(uSunK) * (exp(-max(d, 0.) * mix(4., 1.6, uSunK)) * .9 + exp(-max(d, 0.) * .6) * .12) * uSunGlow * (hit == 0 ? .35 : 1.);
        }
        if (uEarth.w > 0. && hit != 0) {
            float d = sphDist(ro, rd, uEarth) / uEarth.w;
            if (d > 0.) col += mix(vec3(.3, .55, 1.), vec3(1., .4, .1), smoothstep(0., .8, uDry + uScorch)) * exp(-d * 30.) * .35 * (1. - uScorch * .5) + vec3(1., .35, .08) * exp(-d * 12.) * uScorch * .5;
        }
        acc += col;
    }
    vec3 col = acc * .5 * uExpose;
    col += uGlow * vec3(.2, .4, 1.) * .1;
    col = col / (1. + col * .35);                                          // soft filmic shoulder (no clipping flashes)
    col *= 1. - .35 * dot(q, q);
    fragColor = vec4(pow(max(col, 0.), vec3(1. / 1.1)), 1.);
}
