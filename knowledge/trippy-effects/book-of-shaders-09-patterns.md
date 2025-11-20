# The Book of Shaders - Chapter 9: Patterns

This chapter focuses on creating tile-based patterns, a task for which fragment shaders are exceptionally well-suited due to their pixel-by-pixel execution.

### The Power of `fract()`
The key to creating repeating patterns is to manipulate the coordinate system. By scaling the normalized coordinates (`st`) and then applying the `fract()` function, you can create a grid of smaller, repeating coordinate systems, each ranging from 0.0 to 1.0.

```glsl
// Scale the coordinate system by 10
vec2 st = st * 10.0;

// Use fract() to create a repeating grid
st = fract(st);
```
Now, whatever you draw in this `st` coordinate system will be repeated 10 times in both the X and Y directions.

### Example: Tiled Circles
You can combine this repeating coordinate system with shape-drawing functions from previous chapters to tile a shape. For example, to draw a circle in each tile:
1.  Scale the coordinates.
2.  Use `fract()` to create the grid.
3.  In each tile (which now has its own 0-1 coordinate space), calculate the distance from the center (0.5, 0.5) to draw a circle.

### Applying Matrix Transformations
To make patterns more interesting, you can apply matrix transformations *after* creating the repeating grid. This allows you to translate, rotate, or scale the content *inside* each tile.

For example, you can create a pattern of circles and then use a 2D rotation matrix to rotate each circle.

### Creating Offset Patterns (Brick Wall Effect)
You can create more complex patterns, like a brick wall, by introducing offsets.
1.  Create a repeating grid as before.
2.  Use `floor()` on the scaled coordinates (before applying `fract()`) to get an integer ID for each tile.
3.  Use `mod()` on the tile ID to determine if a row is even or odd.
4.  If the row is odd, apply a horizontal offset to the coordinate system for that tile.
5.  Draw your shape (e.g., a rectangle) in the offset coordinate system.

### Truchet Tiles
Truchet tiles are a fascinating example of creating complex patterns from simple rules. The idea is to have a single design element (like a pattern of triangles) and rotate it based on its position in the grid.
1.  Create a repeating grid.
2.  Get a random value for each tile (using a `random` function based on the tile's integer ID).
3.  Based on the random value, apply one of several rotations (e.g., 0, 90, 180, or 270 degrees) to the coordinate system of that tile.
4.  Draw the design element.

This simple technique can produce surprisingly complex and intricate-looking patterns.

By mastering coordinate manipulation with `fract()`, `floor()`, `mod()`, and matrix transformations, you can create a vast universe of procedural patterns in your shaders.

*Source: This content is a summary of a chapter from thebookofshaders.com.*
