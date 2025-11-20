# GLSL Noise Functions Tutorial

This tutorial, summarized from science-and-fiction.org, discusses various GLSL noise functions, their characteristics, and implementations.

### Core Concepts
Noise functions are essential for creating organic, non-uniform patterns. They work by generating pseudo-random values that are smoothly interpolated.

A key component is a pseudo-random number generator (PRNG). A common GLSL PRNG for a 2D vector is:
```glsl
float rand(vec2 co){
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}
```
This function is deterministic: the same input coordinate will always produce the same output, which is crucial for creating stable textures.

### Perlin Noise
Developed by Ken Perlin, this is a classic "gradient noise."
*   **How it works:** It generates random *gradients* at integer grid points and interpolates them. The result is a smooth, continuous field of values.
*   **Characteristics:** It has a characteristic "wavy" look and is excellent for simulating natural phenomena like clouds, fire, and water.
*   **Implementation:** The article provides a GLSL implementation of Perlin noise, which involves hashing, gradient selection, and smooth interpolation (often using a quintic curve `t*t*t*(t*(t*6.0-15.0)+10.0)` to avoid artifacts).

### Sparse Dot Noise
This is a simpler, faster alternative to Perlin noise.
*   **How it works:** It's based on generating random values at grid points (Value Noise) but with a specific hashing function.
*   **Characteristics:** It produces a blockier, more cellular look than Perlin noise. It can be useful for certain types of textures or when performance is critical.

### Domain (Voronoi) Noise
Also known as cellular noise, this creates patterns that resemble cells or crystal structures.
*   **How it works:**
    1.  Distribute a set of "feature points" randomly in space.
    2.  For any given pixel, find the distance to the nearest feature point.
    3.  The noise value is based on this distance.
*   **Variations:**
    *   `F1`: Distance to the closest point. Creates a pattern of circular cells.
    *   `F2`: Distance to the second-closest point.
    *   `F2 - F1`: The difference between the two closest distances, which creates distinct cell walls.
*   **Implementation:** The article provides a GLSL implementation that involves iterating through neighboring cells to find the closest feature points.

### Non-Linear Filtering
You can dramatically alter the appearance of noise by applying non-linear functions to its output. For example:
*   **`abs(noise)`:** Creates sharp ridges.
*   **`sin(noise * frequency)`:** Creates a pattern of concentric rings.
*   **`fract(noise * frequency)`:** Creates a contour-like pattern.

By combining different noise functions and applying these filters, you can generate a vast range of complex and interesting procedural textures.

*Source: This content is a summary of an article from science-and-fiction.org.*
