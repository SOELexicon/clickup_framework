# Getting started with WebGL

This guide will help you get started with the basics of using WebGL. WebGL enables web content to use an API based on OpenGL ES 2.0 to perform 2D and 3D rendering in an HTML `<canvas>`.

### 1. Before you start
This tutorial assumes you have a good understanding of JavaScript and some knowledge of computer graphics.

### 2. The WebGL context
To get started, you need a `<canvas>` element in your HTML:
```html
<canvas id="glcanvas" width="640" height="480"></canvas>
```
In your JavaScript, you can get the WebGL rendering context:
```javascript
const canvas = document.getElementById('glcanvas');
const gl = canvas.getContext('webgl');

if (!gl) {
  alert('Unable to initialize WebGL. Your browser or machine may not support it.');
  return;
}

// Set clear color to black, fully opaque
gl.clearColor(0.0, 0.0, 0.0, 1.0);
// Clear the color buffer with specified clear color
gl.clear(gl.COLOR_BUFFER_BIT);
```
`getContext()` can also take a second argument, an object of context attributes, to control various WebGL features.

### 3. The rendering pipeline
The WebGL rendering pipeline involves two main programmable stages: the vertex shader and the fragment shader. These shaders are written in GLSL (OpenGL Shading Language).

*   **Vertex Shader:** Its job is to compute the position of each vertex. It takes vertex data as input (attributes) and outputs the final position in clip space coordinates.
*   **Fragment Shader:** It runs for every pixel that is to be rendered. Its job is to determine the color of each pixel.

### 4. A simple example: Drawing a square
Let's draw a simple 2D square on the screen.

#### Initializing shaders
First, you need to create the shader programs. This involves:
1.  Creating the vertex shader source code.
2.  Creating the fragment shader source code.
3.  Creating shader objects, attaching the source, and compiling them.
4.  Creating a shader program, attaching the shaders, and linking them.

Here is an example of a simple vertex shader:
```glsl
attribute vec4 aVertexPosition;

uniform mat4 uModelViewMatrix;
uniform mat4 uProjectionMatrix;

void main() {
  gl_Position = uProjectionMatrix * uModelViewMatrix * aVertexPosition;
}
```
And a simple fragment shader:
```glsl
void main() {
  gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0); // white
}
```
You'll need helper functions to load and compile these shaders.

#### Creating the square
You need to define the vertices for the square.
```javascript
const positions = [
  -1.0,  1.0,
   1.0,  1.0,
  -1.0, -1.0,
   1.0, -1.0,
];
```
This data needs to be put into a WebGL buffer:
```javascript
const positionBuffer = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW);
```

#### Drawing the scene
To draw, you create a `drawScene` function that gets called every frame.
```javascript
function drawScene(gl, programInfo, buffers) {
  gl.clearColor(0.0, 0.0, 0.0, 1.0);  // Clear to black, fully opaque
  gl.clearDepth(1.0);                 // Clear everything
  gl.enable(gl.DEPTH_TEST);           // Enable depth testing
  gl.depthFunc(gl.LEQUAL);            // Near things obscure far things

  // Clear the canvas before we start drawing on it.
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  // Create a perspective matrix, a special matrix that is
  // used to simulate the distortion of perspective in a camera.
  const fieldOfView = 45 * Math.PI / 180;   // in radians
  const aspect = gl.canvas.clientWidth / gl.canvas.clientHeight;
  const zNear = 0.1;
  const zFar = 100.0;
  const projectionMatrix = mat4.create();
  mat4.perspective(projectionMatrix, fieldOfView, aspect, zNear, zFar);

  // Set the drawing position to the "identity" point, which is
  // the center of the scene.
  const modelViewMatrix = mat4.create();

  // Now move the drawing position a bit to where we want to
  // start drawing the square.
  mat4.translate(modelViewMatrix,     // destination matrix
                 modelViewMatrix,     // matrix to translate
                 [-0.0, 0.0, -6.0]);  // amount to translate

  // Tell WebGL how to pull out the positions from the position
  // buffer into the vertexPosition attribute.
  {
    const numComponents = 2;
    const type = gl.FLOAT;
    const normalize = false;
    const stride = 0;
    const offset = 0;
    gl.bindBuffer(gl.ARRAY_BUFFER, buffers.position);
    gl.vertexAttribPointer(
        programInfo.attribLocations.vertexPosition,
        numComponents,
        type,
        normalize,
        stride,
        offset);
    gl.enableVertexAttribArray(
        programInfo.attribLocations.vertexPosition);
  }

  // Tell WebGL to use our program when drawing
  gl.useProgram(programInfo.program);

  // Set the shader uniforms
  gl.uniformMatrix4fv(
      programInfo.uniformLocations.projectionMatrix,
      false,
      projectionMatrix);
  gl.uniformMatrix4fv(
      programInfo.uniformLocations.modelViewMatrix,
      false,
      modelViewMatrix);

  {
    const offset = 0;
    const vertexCount = 4;
    gl.drawArrays(gl.TRIANGLE_STRIP, offset, vertexCount);
  }
}
```
This example uses `glMatrix` library for matrix operations.

### 5. Next steps
This is just the beginning. From here, you can learn about:
*   Adding color to your shapes.
*   Using textures to apply images to your models.
*   Animating objects.
*   Responding to user input.

The MDN WebGL tutorial series covers these topics and more in detail.

*Source: This content is a summary from developer.mozilla.org.*
