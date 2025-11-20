# The Book of Shaders - Chapter 11: Noise

This chapter from "The Book of Shaders" delves into the concept of procedural noise, a cornerstone of generative art and realistic-looking procedural textures. Unlike pure randomness, noise functions produce organic, semi-random values that have a sense of structure.

### Why Not Just Use `random()`?
While the `random()` function from the previous chapter is useful, its output is chaotic and discontinuous. If you map `random()` to a 2D grid, the result is "white noise," where each pixel's value is completely independent of its neighbors.

For natural-looking textures like clouds, marble, or water, you need a function where values change smoothly from one point to the next. This is what noise functions provide.

### Value Noise vs. Gradient Noise
There are two main categories of noise:

1.  **Value Noise:**
    *   **How it works:** Create a lattice of points. Assign a random value to each point on the lattice. For any other point, interpolate the values from the nearest lattice points.
    *   **Characteristics:** It's simple to implement but can look blocky or grid-like, as the interpolation is based on a simple grid of random values.

2.  **Gradient Noise (Perlin Noise):**
    *   **How it works:** Instead of assigning random values to the lattice points, assign random *gradients* (directions). For any given point, you calculate the influence of the gradients from the surrounding lattice points. This is done using a dot product between the gradient and the vector from the lattice point to the given point.
    *   **Characteristics:** This is the technique developed by Ken Perlin for the movie *Tron*. It produces a more natural, organic, and rotational-looking noise compared to Value Noise. The original Perlin Noise patent has expired, making it free to use.

### Implementing Noise in GLSL
The chapter provides GLSL code examples for creating noise functions. A typical 2D noise function would look something like this (conceptually):
```glsl
float noise(in vec2 st) {
    vec2 i = floor(st); // Integer part of the coordinate
    vec2 f = fract(st); // Fractional part of the coordinate

    // Four corners of the cell
    vec2 a = vec2(0.0, 0.0);
    vec2 b = vec2(1.0, 0.0);
    vec2 c = vec2(0.0, 1.0);
    vec2 d = vec_2(1.0, 1.0);

    // Get random gradients/values for each corner
    // ... hash functions to generate pseudo-randomness ...

    // Interpolate between the corners
    // using smoothstep() or a similar quintic curve
    // to avoid artifacts
    // ... interpolation logic ...

    return interpolated_value;
}
```
The key is to use smooth interpolation (like `smoothstep` or a quintic function: `u*u*u*(u*(u*6.-15.)+10.)`) to avoid visible derivatives at the cell boundaries, which was a flaw in the original Perlin Noise implementation.

### Simplex Noise
Ken Perlin later improved upon his original noise algorithm with **Simplex Noise**.
*   **How it works:** It uses a simpler, more uniform grid of simplexes (triangles in 2D, tetrahedrons in 3D) instead of a square/cube lattice.
*   **Advantages:**
    *   Faster to compute, especially in higher dimensions.
    *   Has fewer directional artifacts.
    *   Produces a more pleasing, circular pattern.
*   **Disadvantage:** Simplex noise is still under patent in some jurisdictions for certain uses, although the patent situation is complex and debated. Many open-source implementations exist.

### Creative Applications
The chapter encourages experimentation by:
*   Using 1D noise to animate the position or properties of shapes.
*   Using 2D noise to create generative patterns that look like fabric, marble, or clouds.
*   Modulating other patterns (like lines or shapes) with noise to give them an organic, "hand-drawn" feel.
*   Using noise to distort time or space in other animations.

Noise is a fundamental tool for adding richness, complexity, and naturalism to shader-based art.

*Source: This content is a summary of a chapter from thebookofshaders.com.*
