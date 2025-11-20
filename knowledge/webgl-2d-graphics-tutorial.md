# WebGL 2D Graphics Tutorial

This tutorial provides a structured guide to getting started with 2D graphics using WebGL.

### 1. Setting Up Your Development Environment
*   **Text Editor:** VSCode, Sublime Text, etc.
*   **Modern Web Browser:** Chrome, Firefox, etc.
*   **Local Server:** Use `http-server` (via npm) or Python's `http.server` to avoid issues with loading files directly from the filesystem.

### 2. Project Structure
```
your-webgl-project/
├── index.html
└── main.js
```

### 3. HTML Setup (`index.html`)
The core of the HTML is the `<canvas>` element.
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>WebGL 2D Tutorial</title>
    <style>
        body { margin: 0; overflow: hidden; }
        canvas { border: 1px solid black; }
    </style>
</head>
<body>
    <canvas id="webglCanvas" width="600" height="600"></canvas>
    <script src="main.js"></script>
</body>
</html>
```

### 4. Initializing WebGL (`main.js`)
Get the WebGL rendering context from the canvas.
```javascript
document.addEventListener("DOMContentLoaded", function() {
    const canvas = document.getElementById('webglCanvas');
    const gl = canvas.getContext('webgl');

    if (!gl) {
        alert('WebGL is not supported.');
        return;
    }

    // Set the clear color to black
    gl.clearColor(0.0, 0.0, 0.0, 1.0);
    // Clear the color buffer
    gl.clear(gl.COLOR_BUFFER_BIT);
});
```

### 5. Understanding Shaders
WebGL uses GLSL (OpenGL Shading Language) for shaders that run on the GPU.

*   **Vertex Shader:** Runs for each vertex. Its primary job is to calculate the final position of the vertex in **clip space**. Clip space is a coordinate system where X, Y, and Z all range from -1.0 to 1.0.
*   **Fragment Shader:** Runs for each pixel of a shape. It determines the final color of the pixel.

### 6. Drawing a 2D Triangle

#### Update `main.js`:
```javascript
document.addEventListener("DOMContentLoaded", function() {
    const canvas = document.getElementById('webglCanvas');
    const gl = canvas.getContext('webgl');
    if (!gl) { /* ... error handling ... */ }

    // 1. Define Geometry (in Clip Space Coordinates)
    const vertices = new Float32Array([
         0.0,  0.5,  // Top center
        -0.5, -0.5,  // Bottom left
         0.5, -0.5   // Bottom right
    ]);

    // 2. Create Buffer and Send Data to GPU
    const vertexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

    // 3. Vertex Shader Source
    const vsSource = `
        attribute vec2 a_position;
        void main() {
            gl_Position = vec4(a_position, 0.0, 1.0);
        }
    `;

    // 4. Fragment Shader Source
    const fsSource = `
        precision mediump float;
        void main() {
            gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); // Red
        }
    `;

    // 5. Compile Shaders and Create Shader Program
    const vertexShader = compileShader(gl, vsSource, gl.VERTEX_SHADER);
    const fragmentShader = compileShader(gl, fsSource, gl.FRAGMENT_SHADER);
    const shaderProgram = createProgram(gl, vertexShader, fragmentShader);
    gl.useProgram(shaderProgram);

    // 6. Link Vertex Data to Shader Attribute
    const positionAttributeLocation = gl.getAttribLocation(shaderProgram, 'a_position');
    gl.enableVertexAttribArray(positionAttributeLocation);
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer); // Re-bind buffer
    gl.vertexAttribPointer(
        positionAttributeLocation, // Attribute location
        2,           // Number of components per vertex (x, y)
        gl.FLOAT,    // Type of data
        false,       // Normalize?
        0,           // Stride (0 = use size and type)
        0            // Offset from the beginning of the buffer
    );

    // 7. Draw
    gl.clearColor(0.0, 0.0, 0.0, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(
        gl.TRIANGLES, // Primitive type
        0,            // Starting index
        3             // Number of vertices to draw
    );
});

// Helper function to compile a shader
function compileShader(gl, source, type) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('Shader compilation error: ' + gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
    }
    return shader;
}

// Helper function to create and link a program
function createProgram(gl, vs, fs) {
    const program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        console.error('Shader program linking error: ' + gl.getProgramInfoLog(program));
        return null;
    }
    return program;
}
```

### Key Concepts from the Code
*   **Vertex Data:** The `vertices` array defines the shape's geometry. The coordinates are in clip space, which is why they are in the range [-1.0, 1.0].
*   **Buffers:** `gl.createBuffer()` creates a buffer on the GPU. We bind it with `gl.bindBuffer()` and then push our data into it with `gl.bufferData()`.
*   **Attributes:** An `attribute` in GLSL is an input to the vertex shader that gets its data from a buffer.
*   **`gl.vertexAttribPointer()`:** This is a crucial function. It tells WebGL how the data in the currently bound buffer (`ARRAY_BUFFER`) is structured and how to map it to the enabled vertex attribute.
*   **`gl.drawArrays()`:** This function executes the shaders and performs the actual drawing. It tells WebGL to draw triangles using the data from the bound buffers, starting at index 0 and drawing 3 vertices in total.

*Source: This content is a summary of information from various tutorials like those on geeksforgeeks.org, mdn.io, and webglfundamentals.org.*
