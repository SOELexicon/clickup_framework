// Vertex shader - positions thick line segments with width for fire channel effect
attribute vec2 a_position;
attribute float a_texCoord;     // Position along line (0 to 1)
attribute float a_perpCoord;    // Position across line (-1 to 1)
attribute vec2 a_normal;        // Perpendicular normal vector
attribute float a_lineLength;   // Total line length in pixels
uniform vec2 u_resolution;
uniform mat3 u_transform;
uniform float u_lineWidth;      // Line width in pixels
varying float v_texCoord;
varying float v_perpCoord;
varying float v_lineLength;     // Pass line length to fragment shader

void main() {
    // Transform center position
    vec3 transformed = u_transform * vec3(a_position, 1.0);

    // Offset by perpendicular normal to create width
    vec2 offset = a_normal * a_perpCoord * u_lineWidth;
    vec2 finalPos = transformed.xy + offset;

    // Convert to clip space
    vec2 clipSpace = (finalPos / u_resolution) * 2.0 - 1.0;
    gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);

    v_texCoord = a_texCoord;
    v_perpCoord = a_perpCoord;
    v_lineLength = a_lineLength;
}
