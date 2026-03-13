precision mediump float;

uniform float u_time;
uniform float u_density;  // Pulses per pixel (configurable density)

varying float v_texCoord;  // Position along the line (0.0 at start, 1.0 at end)
varying float v_perpCoord; // Position across the line (-1.0 to 1.0)
varying float v_lineLength; // Total line length in pixels (for normalization)

void main() {
    // 1. Create a soft falloff from the center of the line to the edges
    float edgeFalloff = 1.0 - abs(v_perpCoord);
    edgeFalloff = smoothstep(0.0, 1.0, edgeFalloff);

    // 2. Create the animated "flowing" pattern along the line
    float speed = -3.0; // Negative to flow in the direction of the line

    // FIXED: Normalize frequency by line length to make pulses consistent across all lines
    // Instead of fixed 40 pulses per texture coord, use pulses per pixel
    float normalizedFrequency = v_lineLength * u_density;

    // Create a sine wave that travels along the line over time
    // Now uses normalized frequency so all lines have same visual pulse density
    float wave = sin(v_texCoord * normalizedFrequency + u_time * speed);

    // 3. Sharpen the wave to create distinct, bright pulses
    float pulse = smoothstep(0.8, 1.0, wave);

    // 4. Define the color for the pulse (a vibrant cyan)
    vec3 flowColor = vec3(0.1, 1.0, 0.7);

    // 5. Final alpha is the pulse intensity, faded by the edge falloff
    float alpha = pulse * edgeFalloff;

    gl_FragColor = vec4(flowColor, alpha);
}
