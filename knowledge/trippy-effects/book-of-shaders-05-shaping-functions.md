# The Book of Shaders - Chapter 5: Shaping Functions

This chapter explores the power of shaping functions, which are mathematical functions used to shape, curve, and animate values in shaders. They are fundamental building blocks for creating interesting and dynamic visuals.

### The Power of `pow()`
The `pow()` function (power) can be used to change the curvature of a linear progression.
*   `pow(x, 1.0)` is a straight line.
*   `pow(x, 2.0)` creates a quadratic curve (ease-in).
*   `pow(x, 0.5)` creates the inverse curve (ease-out).

By controlling the exponent, you can create a wide range of non-linear transitions.

### `step()` and `smoothstep()`
*   **`step(edge, x)`:** Returns `0.0` if `x` is less than `edge`, and `1.0` if `x` is greater than or equal to `edge`. It creates a sharp transition. It's great for creating hard edges or binary-like effects.

*   **`smoothstep(edge0, edge1, x)`:** Creates a smooth, Hermite interpolation between `edge0` and `edge1`. It's one of the most useful functions in shader programming for creating smooth transitions, soft edges, and gradients.

### Trigonometric Functions: `sin()` and `cos()`
`sin()` and `cos()` are the workhorses of animation and procedural generation.
*   They create smooth, periodic oscillations between -1.0 and 1.0.
*   By using `time` as an input, you can create animations like pulsing, waving, or breathing.
*   Mapping the output range from [-1, 1] to [0, 1] is a common pattern: `(sin(time) + 1.0) * 0.5`.

### `mod()` and `fract()`
*   **`mod(x, y)`:** Returns the remainder of `x` divided by `y`. It's useful for creating repeating patterns.
*   **`fract(x)`:** Returns the fractional part of `x` (i.e., `x - floor(x)`). It's excellent for creating sawtooth waves and repeating gradients.

### `floor()`, `ceil()`, `sign()`, and `abs()`
*   **`floor(x)`:** Returns the greatest integer less than or equal to `x`.
*   **`ceil(x)`:** Returns the smallest integer greater than or equal to `x`. These are great for creating stepped or blocky effects.
*   **`sign(x)`:** Returns -1.0 if `x` is negative, 0.0 if `x` is zero, and 1.0 if `x` is positive.
*   **`abs(x)`:** Returns the absolute value of `x`. Useful for creating "bouncing" or mirrored effects.

### `clamp()`, `min()`, and `max()`
*   **`clamp(x, minVal, maxVal)`:** Constrains a value `x` to be within the range [`minVal`, `maxVal`].
*   **`min(a, b)`:** Returns the smaller of the two values.
*   **`max(a, b)`:** Returns the larger of the two values. These are essential for controlling the range of values and preventing them from becoming too high or too low.

### Mixing functions
The real power comes from combining these functions. For example, you can use `sin()` to create a smooth wave and then apply `step()` to it to create a hard-edged, pulsating circle. Or you could use `fract()` to create a repeating gradient and `pow()` to change the shape of that gradient.

### Further Resources
*   **Golan Levin's shaping functions documentation:** A classic resource on this topic.
*   **Iñigo Quiles' useful little functions:** A collection of powerful functions for shader development from a master.
*   **LYGIA:** A shader library that includes a wide variety of shaping functions.

By mastering these shaping functions, you gain a rich vocabulary for expressing procedural and generative art in your shaders.

*Source: This content is a summary of a chapter from thebookofshaders.com.*
