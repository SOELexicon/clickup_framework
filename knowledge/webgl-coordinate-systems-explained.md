# WebGL Coordinate Systems Explained

Understanding the series of coordinate systems in WebGL is crucial for correctly positioning objects in a 3D scene. The process involves transforming vertex data from its original model space all the way to the 2D pixel coordinates on your screen.

### 1. Local Space (or Model Space)
*   **Definition:** This is the coordinate system where you define the vertices of your 3D model.
*   **Origin:** The origin (0,0,0) is local to the object itself. For example, the center of a character model could be its origin.
*   **Purpose:** It provides a private, convenient coordinate system for creating a model without worrying about its final position or orientation in the world.

### 2. World Space
*   **Definition:** This is the global coordinate system that contains all objects in your scene.
*   **Transformation:** Objects are moved from their Local Space into World Space using a **Model Matrix**.
*   **Model Matrix:** This matrix applies `translation` (position), `rotation`, and `scale` to the object, placing it correctly relative to other objects in the scene.

### 3. View Space (or Camera Space)
*   **Definition:** This coordinate system represents the scene from the camera's point of view.
*   **Origin:** The camera is effectively at the origin (0,0,0), looking down one of the axes (typically the negative Z-axis).
*   **Transformation:** The scene is moved from World Space to View Space using a **View Matrix**.
*   **View Matrix:** Instead of moving the camera, it's easier to move the entire world in the opposite direction. The view matrix handles this transformation.

### 4. Clip Space
*   **Definition:** After an object is in View Space, it's transformed into Clip Space. This is a normalized, cube-shaped space.
*   **Range:** Coordinates in clip space range from **-1.0 to 1.0** on all three axes (X, Y, and Z).
*   **Transformation:** The transformation from View Space to Clip Space is done by a **Projection Matrix**.
*   **Clipping:** Any geometry that falls outside this -1.0 to 1.0 cube is "clipped," or discarded, so the GPU doesn't waste time rendering things that aren't visible.
*   **Projection Matrix:** There are two main types:
    *   **Perspective Projection:** Mimics a real-world camera. Objects that are farther away appear smaller. This is most common for 3D scenes.
    *   **Orthographic Projection:** Renders objects without any perspective distortion. Parallel lines remain parallel. This is often used for 2D games, UI elements, or architectural drawings.

### 5. Normalized Device Coordinates (NDC)
*   **Definition:** This step happens automatically after the vertex shader runs.
*   **Process:** The `x`, `y`, and `z` components of the Clip Space coordinates are divided by the `w` component. This is called **perspective division**.
*   **Result:** The resulting coordinates are now in the range of -1.0 to 1.0, regardless of the output screen's aspect ratio.

### 6. Screen Space (or Pixel/Canvas Coordinates)
*   **Definition:** This is the final 2D coordinate system that maps directly to the pixels on your `<canvas>` element.
*   **Transformation:** The Normalized Device Coordinates (NDC) are transformed into Screen Space by the **Viewport Transformation**.
*   **Viewport:** You define the viewport with `gl.viewport(x, y, width, height)`. This tells WebGL how to map the -1.0 to 1.0 NDC range to the pixel dimensions of your canvas. Typically, (0,0) in screen space is the top-left corner of the canvas.

### The MVP Matrix
In the vertex shader, these transformations are usually combined into a single matrix called the **Model-View-Projection (MVP) matrix**.

```
Final_Position = Projection_Matrix * View_Matrix * Model_Matrix * Original_Vertex_Position;
```

By multiplying the matrices in this order, you can efficiently transform a vertex from its local space all the way to clip space in a single operation.

*Source: This content is a summary of information from various tutorials like those on geeksforgeeks.org, mdn.io, and webglfundamentals.org.*
