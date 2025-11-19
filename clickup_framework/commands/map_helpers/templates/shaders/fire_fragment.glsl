// Fragment shader - creates flowing green fire effect inside line channels
precision mediump float;
varying float v_texCoord;  // 0 to 1 along the line
varying float v_perpCoord;  // -1 to 1 across the line
uniform float u_time;

// Noise functions for fire turbulence
float rand(vec2 n) {
    return fract(sin(dot(n, vec2(12.9898, 12.1414))) * 83758.5453);
}

float noise(vec2 n) {
    const vec2 d = vec2(0.0, 1.0);
    vec2 b = floor(n);
    vec2 f = smoothstep(vec2(0.0), vec2(1.0), fract(n));
    return mix(mix(rand(b), rand(b + d.yx), f.x),
              mix(rand(b + d.xy), rand(b + d.yy), f.x), f.y);
}

float fire(vec2 n) {
    return noise(n) + noise(n * 2.1) * 0.6 + noise(n * 5.4) * 0.42;
}

// Flowing fire shader adapted for line channels
float shade(vec2 uv, float t) {
    uv.x += uv.y < 0.5 ? 23.0 + t * 0.035 : -11.0 + t * 0.03;
    uv.y = abs(uv.y - 0.5);
    uv.x *= 35.0;

    float q = fire(uv - t * 0.013) / 2.0;
    vec2 r = vec2(fire(uv + q / 2.0 + t - uv.x - uv.y), fire(uv + q - t));

    return pow((r.y + r.y) * max(0.0, uv.y) + 0.1, 4.0);
}

// Green fire color ramp (adapted from shadertoy reference)
vec3 ramp(float t) {
    // Green channel fire: bright white -> cyan -> emerald -> dark green
    if (t <= 0.5) {
        return vec3(1.0 - t * 1.4, 1.0, 1.05) / t;
    } else {
        return vec3(0.3 * (1.0 - t) * 2.0, 1.0, 1.05) / t;
    }
}

vec3 color(float grad) {
    grad = sqrt(grad);
    vec3 col = ramp(grad);
    col /= (1.15 + max(vec3(0.0), col));
    return col;
}

void main() {
    // Create flowing UV coordinates using perpendicular position
    // v_texCoord: 0-1 along line length
    // v_perpCoord: -1 to 1 across line width
    vec2 uv = vec2(v_texCoord, (v_perpCoord + 1.0) * 0.5);  // Map perp to 0-1
    float t = u_time;
    uv.x -= t * 0.05;  // Flow along line

    // Create fire effect
    float grad = shade(uv, t);
    vec3 fireColor = color(grad);

    // Keep fire contained inside the line boundaries
    float edgeFade = 1.0 - abs(v_perpCoord);  // Fade at ±1
    // Stronger containment: hard cutoff at 0.85, smooth fade from 0.7 to 0.85
    edgeFade = smoothstep(0.85, 0.7, abs(v_perpCoord));
    float intensity = smoothstep(0.0, 0.2, grad) * smoothstep(1.0, 0.7, grad) * edgeFade;

    gl_FragColor = vec4(fireColor * intensity, intensity * 0.8);
}
