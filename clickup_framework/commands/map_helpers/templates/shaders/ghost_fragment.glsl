// Fragment shader - creates flowing ethereal ghost effect
precision mediump float;
varying float v_texCoord;  // 0 to 1 along the line
varying float v_perpCoord;  // -1 to 1 across the line
uniform float u_time;

// Noise functions for wispy ghost turbulence
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

float wisp(vec2 n) {
    return noise(n) + noise(n * 2.1) * 0.6 + noise(n * 5.4) * 0.42;
}

// Flowing wispy shader for ghost effect
float shade(vec2 uv, float t) {
    uv.x += uv.y < 0.5 ? 23.0 + t * 0.025 : -11.0 + t * 0.02;  // Slower, more ethereal
    uv.y = abs(uv.y - 0.5);
    uv.x *= 30.0;  // Less dense

    float q = wisp(uv - t * 0.01) / 2.0;
    vec2 r = vec2(wisp(uv + q / 2.0 + t - uv.x - uv.y), wisp(uv + q - t));

    return pow((r.y + r.y) * max(0.0, uv.y) + 0.1, 3.5);  // Softer
}

// Ghostly white-to-cyan color ramp
vec3 ramp(float t) {
    // Ethereal: bright white -> pale cyan -> light blue -> faint white
    if (t <= 0.5) {
        return vec3(1.0, 1.0 - t * 0.3, 1.0) / (t + 0.2);
    } else {
        return vec3(0.8 + (1.0 - t) * 0.4, 0.9, 1.0) / (t + 0.1);
    }
}

vec3 color(float grad) {
    grad = sqrt(grad);
    vec3 col = ramp(grad);
    col /= (1.1 + max(vec3(0.0), col));
    return col;
}

void main() {
    // Create flowing UV coordinates using perpendicular position
    // v_texCoord: 0-1 along line length
    // v_perpCoord: -1 to 1 across line width
    vec2 uv = vec2(v_texCoord, (v_perpCoord + 1.0) * 0.5);  // Map perp to 0-1
    float t = u_time;
    uv.x -= t * 0.04;  // Slower flow for ghostly drift

    // Create wispy ghost effect
    float grad = shade(uv, t);
    vec3 ghostColor = color(grad);

    // Soft fade at edges for ethereal appearance
    float edgeFade = 1.0 - abs(v_perpCoord);  // Fade at ±1
    float intensity = smoothstep(0.0, 0.3, grad) * smoothstep(1.0, 0.6, grad) * edgeFade;

    // More transparent than fire for ghostly effect
    gl_FragColor = vec4(ghostColor * intensity, intensity * 0.6);
}
