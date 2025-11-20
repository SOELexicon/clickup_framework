precision mediump float;

varying float v_texCoord;  // Position along the line (0.0 at start, 1.0 at end)
varying float v_perpCoord; // Position across the line (-1.0 to 1.0)

void main() {
    // Create a soft glow that is brightest at the center and fades to the edges
    float glow = 1.0 - abs(v_perpCoord);
    glow = pow(glow, 2.0); // Use pow to create a sharper falloff

    // Define the glow color (a soft green)
    vec3 glowColor = vec3(0.063, 0.725, 0.506); // Emerald color from the fire shader

    gl_FragColor = vec4(glowColor, glow * 0.7); // Use 0.7 alpha for a gentle blend
}
