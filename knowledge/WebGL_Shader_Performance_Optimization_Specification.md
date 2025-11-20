# WebGL Shader Performance Optimization Specification: [Shader/Effect Name]

**Document Version:** 1.0  
**Status:** [Draft | In Review | Approved | Active]  
**Optimization Phase:** [Initial | Ongoing | Maintenance]  
**Author(s):** [Name(s)]  
**Reviewer(s):** [Name(s)]  
**Last Updated:** [Date]

---

## 1. Context & Purpose

### 1.1 Overview

*Purpose: To establish the performance baseline and define optimization objectives for the shader/effect.*

**Shader/Effect Name:** [Name of the shader or effect being optimized]

**Current Status:** [Current performance state, e.g., "Runs at 30 FPS on target hardware, needs optimization to reach 60 FPS target"]

**Optimization Goal:** [Primary optimization objective, e.g., "Reduce frame time from 35ms to 16ms (60 FPS) while maintaining visual quality"]

**Target Hardware Profile:**
- **Minimum Spec:** [e.g., Intel HD 620, GTX 1050, Adreno 630]
- **Recommended Spec:** [e.g., GTX 1060, RX 580, Apple M1]
- **High-End Spec:** [e.g., RTX 3070, RX 6800 XT, Apple M1 Max]

### 1.2 Problem Statement

*Purpose: To identify specific performance bottlenecks and their impact.*

**Current Performance Issues:**

| Issue | Severity | Impact | Frequency |
|-------|----------|--------|-----------|
| [Issue 1, e.g., "Fragment shader bound"] | Critical | 20ms frame time on GTX 1060 | Always |
| [Issue 2, e.g., "Excessive texture lookups"] | High | 15ms texture fetch latency | Always |
| [Issue 3, e.g., "Unoptimized branches"] | Medium | 5ms wasted on divergent threads | Conditional |
| [issue_name] | [severity] | [impact_description] | [when_it_occurs] |

**Measured Bottlenecks:**

```
Performance Profile (Current State):
┌────────────────────────────────────┐
│ Fragment Shader:       65%  ██████│
│ Vertex Shader:         10%  ██    │
│ Texture Bandwidth:     15%  ███   │
│ Geometry Processing:    5%  █     │
│ Memory Transfer:        5%  █     │
└────────────────────────────────────┘

Primary Bottleneck: Fragment Shader (65% of frame time)
Secondary Bottleneck: Texture Bandwidth (15% of frame time)
```

**Root Cause Analysis:**

| Bottleneck | Root Cause | Evidence | Solution Direction |
|------------|------------|----------|-------------------|
| [Fragment shader bound] | [Too many texture samples (12 per fragment)] | [GPU profiler shows 85% of time in texture fetch] | [Reduce texture samples, use texture atlases] |
| [Texture bandwidth] | [Using uncompressed RGBA8 textures (80MB total)] | [Memory bandwidth meter shows saturation] | [Use compressed formats (BC7/ASTC)] |
| [Branch divergence] | [Complex conditionals in main render path] | [Wave analysis shows 40% idle threads] | [Eliminate branches with mix/step functions] |

### 1.3 Performance Goals & Constraints

*Purpose: To define measurable optimization targets.*

**Primary Performance Targets:**

| Metric | Current | Target | Minimum Acceptable | Stretch Goal |
|--------|---------|--------|-------------------|--------------|
| **Frame Time** | 35.0ms | 16.7ms (60 FPS) | 20.0ms (50 FPS) | 13.3ms (75 FPS) |
| **Frame Rate** | 28 FPS | 60 FPS | 50 FPS | 75 FPS |
| **GPU Memory** | 120 MB | 80 MB | 100 MB | 60 MB |
| **Shader Instructions** (Fragment) | 250 | 120 | 150 | 80 |
| **Texture Fetches** (per fragment) | 12 | 6 | 8 | 4 |
| **Draw Calls** (per frame) | 150 | 50 | 80 | 30 |
| [metric] | [current] | [target] | [minimum] | [stretch] |

**Hardware Performance Matrix:**

| Hardware Tier | Resolution | Current FPS | Target FPS | Status | Priority |
|--------------|------------|-------------|------------|--------|----------|
| Low (Intel HD 620) | 1280x720 | 20 FPS | 30 FPS | ❌ Below target | P0 |
| Mid (GTX 1060) | 1920x1080 | 28 FPS | 60 FPS | ❌ Below target | P0 |
| High (RTX 3060) | 2560x1440 | 45 FPS | 60 FPS | ⚠️ Close to target | P1 |
| Ultra (RTX 3080) | 3840x2160 | 30 FPS | 60 FPS | ❌ Below target | P2 |

**Constraints & Trade-offs:**

| Constraint | Description | Impact on Optimization |
|-----------|-------------|----------------------|
| **Visual Quality** | Must maintain current visual fidelity | Cannot reduce texture quality or lighting accuracy significantly |
| **WebGL 1.0 Support** | Must work on WebGL 1.0 (no compute shaders) | Limits optimization techniques (no compute-based culling) |
| **Mobile Support** | Must run on mid-range mobile devices | Cannot rely on high-precision floats or large textures |
| **Memory Budget** | Max 100 MB GPU memory allowed | Limits texture resolution and buffer sizes |
| [constraint] | [description] | [impact] |

### 1.4 Optimization Scope

*Purpose: To define what is and isn't in scope for optimization.*

**In Scope:**
- [ ] Fragment shader instruction reduction
- [ ] Vertex shader optimization
- [ ] Texture compression and resolution reduction
- [ ] Draw call batching and instancing
- [ ] Algorithm optimization (better approach to achieve same result)
- [ ] Quality tier implementation (Low/Medium/High/Ultra presets)

**Out of Scope:**
- [ ] Complete rewrite with different visual style
- [ ] Features requiring WebGL 2.0 compute shaders
- [ ] Changes that would break existing API
- [ ] Optimizations requiring engine/framework modifications

---

## 2. Performance Profiling & Analysis

### 2.1 Profiling Methodology

**Profiling Tools Used:**

| Tool | Purpose | Platform | Notes |
|------|---------|----------|-------|
| Chrome DevTools Performance | CPU/GPU frame timing | Desktop (Chrome) | Primary profiling tool |
| Spector.js | WebGL call inspection | Desktop (All browsers) | Detailed shader analysis |
| RenderDoc | Frame capture & analysis | Desktop (via ANGLE) | Deep GPU inspection |
| WebGL Report | Hardware capability detection | All platforms | Baseline testing |
| [tool_name] | [purpose] | [platform] | [notes] |

**Profiling Scenarios:**

| Scenario Name | Description | Purpose | Assets Used |
|--------------|-------------|---------|-------------|
| **Baseline Simple** | Single object, simple lighting | Isolate shader complexity | cube.obj, 512x512 texture |
| **Typical Scene** | Representative game scene | Real-world performance | city_scene.json, multiple objects |
| **Stress Test** | Maximum complexity | Worst-case analysis | 1000+ objects, complex materials |
| **Mobile Baseline** | Reduced scene for mobile | Mobile optimization | simplified_scene.json |
| [scenario_name] | [description] | [purpose] | [assets] |

**Test Protocol:**

```javascript
/**
 * Performance profiling protocol
 * Run this standardized test to gather consistent performance data
 * 
 * @author Craig
 * @version 1.0
 */

class PerformanceProfiler {
  constructor(renderer, scene, camera) {
    this.renderer = renderer;
    this.scene = scene;
    this.camera = camera;
    this.frameTimings = [];
    this.renderStats = {
      drawCalls: 0,
      triangles: 0,
      textures: 0
    };
  }
  
  /**
   * Run standardized performance test
   * Captures 1000 frames of performance data
   */
  async runPerformanceTest(testName) {
    console.log(`Starting performance test: ${testName}`);
    
    // Warmup (100 frames to reach steady state)
    for (let i = 0; i < 100; i++) {
      this.renderer.render(this.scene, this.camera);
    }
    
    // Actual test (1000 frames)
    this.frameTimings = [];
    const startTime = performance.now();
    
    for (let i = 0; i < 1000; i++) {
      const frameStart = performance.now();
      
      this.renderer.render(this.scene, this.camera);
      
      const frameEnd = performance.now();
      this.frameTimings.push(frameEnd - frameStart);
    }
    
    const totalTime = performance.now() - startTime;
    
    // Analyze results
    return this.analyzeResults(testName, totalTime);
  }
  
  /**
   * Statistical analysis of performance data
   */
  analyzeResults(testName, totalTime) {
    const sorted = this.frameTimings.sort((a, b) => a - b);
    
    return {
      testName,
      totalTime,
      frameCount: this.frameTimings.length,
      
      // Timing statistics
      averageFrameTime: this.average(this.frameTimings),
      medianFrameTime: sorted[Math.floor(sorted.length / 2)],
      p95FrameTime: sorted[Math.floor(sorted.length * 0.95)],
      p99FrameTime: sorted[Math.floor(sorted.length * 0.99)],
      minFrameTime: sorted[0],
      maxFrameTime: sorted[sorted.length - 1],
      
      // FPS metrics
      averageFPS: 1000 / this.average(this.frameTimings),
      
      // Render statistics
      averageDrawCalls: this.renderStats.drawCalls,
      averageTriangles: this.renderStats.triangles
    };
  }
  
  average(arr) {
    return arr.reduce((a, b) => a + b, 0) / arr.length;
  }
}

// Usage
const profiler = new PerformanceProfiler(renderer, scene, camera);
const results = await profiler.runPerformanceTest('Baseline Test');
console.log(results);
```

### 2.2 Current Performance Baseline

**Performance Metrics (Before Optimization):**

| Hardware | Resolution | Avg Frame Time | P95 Frame Time | Avg FPS | Min FPS | Max FPS | GPU Memory |
|----------|------------|----------------|----------------|---------|---------|---------|------------|
| GTX 1060 | 1920x1080 | 35.2ms | 42.1ms | 28.4 | 23.7 | 31.2 | 124 MB |
| GTX 1660 | 1920x1080 | 28.5ms | 34.2ms | 35.1 | 29.2 | 38.4 | 124 MB |
| RTX 3060 | 2560x1440 | 22.3ms | 28.7ms | 44.8 | 34.8 | 52.1 | 176 MB |
| Intel HD 620 | 1280x720 | 51.2ms | 68.4ms | 19.5 | 14.6 | 25.3 | 98 MB |
| [hardware] | [resolution] | [avg_time] | [p95_time] | [avg_fps] | [min_fps] | [max_fps] | [memory] |

**GPU Profiler Breakdown (GTX 1060, 1080p):**

```
Frame Budget: 35.2ms total
├─ Vertex Shader:        3.5ms  (10%) [████          ]
├─ Rasterization:        1.8ms  ( 5%) [██            ]
├─ Fragment Shader:     22.9ms  (65%) [████████████  ]
│  ├─ Texture Fetches:  14.2ms  (40%)
│  ├─ ALU Operations:    6.8ms  (19%)
│  └─ Branches:          1.9ms  ( 6%)
├─ Depth/Stencil Test:   1.2ms  ( 3%)
├─ Blending:             0.9ms  ( 3%)
├─ Memory Operations:    4.9ms  (14%) [████          ]
└─ Overhead:             0.0ms  ( 0%)

Critical Path: Fragment Shader > Texture Fetches
```

**Shader Complexity Analysis:**

| Shader | Instructions | Texture Samples | Branches | Loops | Complexity Rating |
|--------|--------------|----------------|----------|-------|------------------|
| Vertex Shader | 42 | 0 | 0 | 0 | Low |
| Fragment Shader | 258 | 12 | 8 | 2 | Very High |
| [shader_name] | [instructions] | [samples] | [branches] | [loops] | [rating] |

**Memory Usage Breakdown:**

| Resource Type | Count | Size (per item) | Total Size | % of Budget |
|--------------|-------|-----------------|------------|-------------|
| Vertex Buffers | 45 | 0.8 MB | 36 MB | 29% |
| Index Buffers | 45 | 0.2 MB | 9 MB | 7% |
| Textures (Diffuse) | 12 | 4 MB | 48 MB | 39% |
| Textures (Normal) | 12 | 4 MB | 48 MB | 39% |
| Render Targets | 4 | 8 MB | 32 MB | 26% |
| **Total** | - | - | **173 MB** | **140%** ⚠️ |

### 2.3 Identified Bottlenecks

**Critical Bottlenecks (P0):**

#### Bottleneck 1: Excessive Texture Sampling

**Description:** Fragment shader performs 12 texture lookups per fragment, causing severe texture cache thrashing.

**Evidence:**
- GPU profiler shows 40% of frame time in texture fetch operations
- Texture cache hit rate is only 35% (should be >70%)
- Memory bandwidth saturated at 98%

**Impact:**
- 14.2ms per frame wasted on texture operations
- Prevents parallel execution of fragments
- Scales poorly with resolution

**Proposed Solutions:**
1. **Texture Atlas (High Priority):** Combine textures to reduce lookups from 12 to 4-6
2. **Deferred Sampling:** Move some texture samples to vertex shader
3. **Mipmap Optimization:** Ensure proper LOD calculation

**Expected Improvement:** 7-10ms reduction in frame time

---

#### Bottleneck 2: Fragment Shader ALU Complexity

**Description:** Complex lighting calculations in fragment shader with multiple light sources.

**Evidence:**
- 258 ALU instructions per fragment
- 6.8ms spent on arithmetic operations
- Profiler shows heavy use of expensive ops (pow, sqrt, normalize)

**Impact:**
- Limits GPU occupancy (fewer parallel fragments)
- Especially poor on mobile GPUs with limited ALU throughput

**Proposed Solutions:**
1. **Move to Vertex Shader:** Calculate per-vertex instead of per-fragment where acceptable
2. **Simplify Lighting Model:** Use cheaper approximations (Blinn-Phong instead of PBR)
3. **LUT Textures:** Pre-compute expensive functions in lookup tables

**Expected Improvement:** 3-5ms reduction in frame time

---

#### Bottleneck 3: Branch Divergence

**Description:** Conditional logic in fragment shader causes thread divergence.

**Evidence:**
- 8 dynamic branches in hot path
- Wave occupancy only 60% (should be >90%)
- Half of GPU threads idle when branches don't match

**Impact:**
- 1.9ms lost to divergent execution
- Reduces effective fragment throughput by 40%

**Proposed Solutions:**
1. **Eliminate Branches:** Use mix(), step(), and other branchless functions
2. **Static Branches:** Move conditions to compile-time #ifdef where possible
3. **Reorder Logic:** Group similar code paths together

**Expected Improvement:** 1.5-2ms reduction in frame time

---

**Secondary Bottlenecks (P1):**

[List medium-priority bottlenecks with similar structure]

---

**Minor Issues (P2):**

[List low-priority issues that may be addressed later]

---

## 3. Optimization Strategies

### 3.1 Fragment Shader Optimizations

#### Strategy 1: Texture Sample Reduction

**Technique:** Texture atlas and channel packing

**Before:**
```glsl
// 12 separate texture lookups
vec4 diffuse = texture2D(u_diffuseTexture, uv);       // Lookup 1-4
vec4 normal = texture2D(u_normalTexture, uv);         // Lookup 5-8
float roughness = texture2D(u_roughnessTexture, uv).r; // Lookup 9
float metallic = texture2D(u_metallicTexture, uv).r;  // Lookup 10
float ao = texture2D(u_aoTexture, uv).r;              // Lookup 11
vec4 emissive = texture2D(u_emissiveTexture, uv);     // Lookup 12
```

**After:**
```glsl
// 2 texture lookups via atlasing + channel packing
vec4 albedoAO = texture2D(u_albedoAtlas, uv);  // RGB = diffuse, A = AO
vec4 normalRoughMetal = texture2D(u_normalAtlas, uv);  // RG = normal, B = roughness, A = metallic

// Reconstruct normal from RG (assumes Z always positive)
vec3 normal;
normal.xy = normalRoughMetal.rg * 2.0 - 1.0;
normal.z = sqrt(1.0 - dot(normal.xy, normal.xy));

float roughness = normalRoughMetal.b;
float metallic = normalRoughMetal.a;
```

**Measurements:**
- Texture samples reduced: 12 → 2 (83% reduction)
- Expected time savings: ~10ms per frame
- Memory footprint: ~unchanged (same total data, different layout)

**Trade-offs:**
- ⚠️ Requires texture atlas generation (content pipeline change)
- ⚠️ Normal map quality slightly reduced (RG only vs RGB)
- ✅ Huge performance gain
- ✅ Better cache coherency

---

#### Strategy 2: Lighting Calculation Simplification

**Technique:** Move to simplified lighting model with pre-computed terms

**Before (PBR with GGX):**
```glsl
// Expensive PBR calculations
float NdF = NormalDistribution_GGX(N, H, roughness);  // pow, sqrt
float G = GeometrySmith(N, V, L, roughness);          // multiple sqrt
vec3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);    // pow

vec3 specular = (NdF * G * F) / (4.0 * max(NdotV, 0.0) * max(NdotL, 0.0) + 0.001);
```

**After (Blinn-Phong approximation):**
```glsl
// Simpler Blinn-Phong with approximations
vec3 H = normalize(L + V);
float NdotH = max(dot(N, H), 0.0);
float spec = pow(NdotH, shininess);  // Single pow instead of many

vec3 specular = spec * specularColor;  // Direct calculation
```

**Measurements:**
- Shader instructions reduced: 258 → 142 (45% reduction)
- Expected time savings: ~4ms per frame
- Visual difference: ~10% less realistic, but still acceptable

**Trade-offs:**
- ⚠️ Visual quality reduced (less physically accurate)
- ⚠️ May require artist approval
- ✅ Significant performance improvement
- ✅ More mobile-friendly

---

#### Strategy 3: Branch Elimination

**Technique:** Replace conditionals with mathematical operations

**Before:**
```glsl
vec3 finalColor;
if (useTexture > 0.5) {
  vec4 tex = texture2D(u_diffuseTexture, uv);
  finalColor = tex.rgb * vertexColor;
} else {
  finalColor = vertexColor;
}

if (distance > fogStart) {
  float fogAmount = (distance - fogStart) / (fogEnd - fogStart);
  finalColor = mix(finalColor, fogColor, fogAmount);
}
```

**After:**
```glsl
// Branchless version using step() and mix()
vec4 tex = texture2D(u_diffuseTexture, uv);
float texBlend = step(0.5, useTexture);
vec3 baseColor = mix(vertexColor, tex.rgb * vertexColor, texBlend);

// Branchless fog
float fogAmount = clamp((distance - fogStart) / (fogEnd - fogStart), 0.0, 1.0);
float fogMask = step(fogStart, distance);
vec3 finalColor = mix(baseColor, mix(baseColor, fogColor, fogAmount), fogMask);
```

**Measurements:**
- Dynamic branches reduced: 8 → 0 (100% elimination)
- Expected time savings: ~1.8ms per frame
- GPU occupancy improvement: 60% → 92%

**Trade-offs:**
- ⚠️ May execute unnecessary texture lookups
- ✅ Eliminates thread divergence
- ✅ Better GPU utilization
- ⚠️ Slightly more complex to read/maintain

---

### 3.2 Vertex Shader Optimizations

#### Strategy 1: Pre-multiply Matrices on CPU

**Technique:** Combine model-view-projection matrix on CPU side

**Before:**
```glsl
// Vertex shader: 3 matrix multiplies
uniform mat4 u_modelMatrix;
uniform mat4 u_viewMatrix;
uniform mat4 u_projectionMatrix;

void main() {
  vec4 worldPos = u_modelMatrix * vec4(a_position, 1.0);
  vec4 viewPos = u_viewMatrix * worldPos;
  gl_Position = u_projectionMatrix * viewPos;
}
```

**After:**
```glsl
// Vertex shader: 1 matrix multiply
uniform mat4 u_mvpMatrix;  // Pre-multiplied on CPU

void main() {
  gl_Position = u_mvpMatrix * vec4(a_position, 1.0);
}
```

**Measurements:**
- Vertex shader time: 3.5ms → 2.1ms (40% reduction)
- CPU overhead: +0.3ms per frame (acceptable)
- Net gain: ~1.1ms per frame

**Trade-offs:**
- ⚠️ Increases CPU load slightly
- ⚠️ Loses separate world position (may need for lighting)
- ✅ Significant vertex shader speedup
- ✅ Especially beneficial with many vertices

---

#### Strategy 2: Reduce Varying Count

**Technique:** Pack multiple scalars into vec4

**Before:**
```glsl
// Vertex shader outputs (4 varyings = 16 floats)
varying vec3 v_worldPosition;
varying vec3 v_worldNormal;
varying vec2 v_texCoord;
varying float v_ao;
varying float v_lightmapUV_x;
varying float v_lightmapUV_y;
varying float v_fogFactor;
```

**After:**
```glsl
// Vertex shader outputs (3 varyings = 12 floats, 25% reduction)
varying vec4 v_positionAndAO;     // xyz = position, w = AO
varying vec4 v_normalAndFog;      // xyz = normal, w = fogFactor
varying vec4 v_texCoords;         // xy = diffuse UV, zw = lightmap UV
```

**Measurements:**
- Varying bandwidth: 16 → 12 floats (25% reduction)
- Expected time savings: ~0.5ms per frame
- GPU memory bandwidth: Reduced by ~15%

**Trade-offs:**
- ⚠️ Slightly less readable code
- ⚠️ Requires unpacking in fragment shader (negligible cost)
- ✅ Reduces interpolation cost
- ✅ Better cache utilization

---

### 3.3 Memory & Bandwidth Optimizations

#### Strategy 1: Texture Compression

**Technique:** Use GPU-compressed texture formats

**Before:**
```javascript
// Uncompressed RGBA8 textures
const texture = gl.createTexture();
gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, width, height, 0, 
              gl.RGBA, gl.UNSIGNED_BYTE, imageData);
// Size: 1024x1024 RGBA8 = 4 MB per texture
```

**After:**
```javascript
// BC7/ASTC compressed textures
const texture = gl.createTexture();
const ext = gl.getExtension('WEBGL_compressed_texture_astc');
gl.compressedTexImage2D(gl.TEXTURE_2D, 0, ext.COMPRESSED_RGBA_ASTC_4x4_KHR,
                        width, height, 0, compressedData);
// Size: 1024x1024 ASTC 4x4 = 1 MB per texture (75% reduction)
```

**Measurements:**
- Texture memory: 48 MB → 12 MB (75% reduction)
- Bandwidth usage: Reduced by ~60%
- Expected time savings: ~2-3ms per frame
- Visual quality: ~95% of original (imperceptible for most cases)

**Trade-offs:**
- ⚠️ Requires content pipeline changes (compression tools)
- ⚠️ Need fallback for browsers without compression support
- ✅ Massive memory savings
- ✅ Faster texture uploads
- ✅ Better cache utilization

---

#### Strategy 2: Mipmap Optimization

**Technique:** Proper mipmap generation and LOD bias

**Before:**
```javascript
// No mipmaps, always samples full resolution
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
```

**After:**
```javascript
// Generate mipmaps and use trilinear filtering
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
gl.generateMipmap(gl.TEXTURE_2D);

// Optional: LOD bias for sharper or softer look
// (use extension if available)
```

**Measurements:**
- Texture cache hit rate: 35% → 78% (2.2x improvement)
- Expected time savings: ~3-4ms per frame
- Memory overhead: +33% (for mipmap chain)

**Trade-offs:**
- ⚠️ Increases memory usage by ~33%
- ⚠️ Small upload time cost (one-time)
- ✅ Dramatically improves cache efficiency
- ✅ Better visual quality (reduces aliasing)
- ✅ Essential for good performance

---

### 3.4 Draw Call & State Change Optimization

#### Strategy 1: Instanced Rendering

**Technique:** Use instancing for repeated objects

**Before:**
```javascript
// Draw each cube individually (100 draw calls)
for (let i = 0; i < 100; i++) {
  setUniform('u_modelMatrix', cubeTransforms[i]);
  gl.drawElements(gl.TRIANGLES, 36, gl.UNSIGNED_SHORT, 0);
}
// Result: 100 draw calls, 5ms CPU overhead
```

**After:**
```javascript
// Draw all cubes in single instanced call (1 draw call)
const ext = gl.getExtension('ANGLE_instanced_arrays');
ext.vertexAttribDivisorANGLE(instanceMatrixLocation, 1);
ext.drawElementsInstancedANGLE(gl.TRIANGLES, 36, gl.UNSIGNED_SHORT, 0, 100);
// Result: 1 draw call, 0.1ms CPU overhead
```

**Measurements:**
- Draw calls reduced: 100 → 1 (99% reduction)
- CPU time savings: ~4.9ms per frame
- GPU time: ~unchanged (same work, different batching)

**Trade-offs:**
- ⚠️ Requires WebGL extension support
- ⚠️ Needs attribute setup changes
- ✅ Massive reduction in draw call overhead
- ✅ Scales well with object count

---

#### Strategy 2: State Sorting

**Technique:** Group draws by shader, then texture

**Before:**
```javascript
// Random draw order
drawObject(obj1);  // Shader A, Texture 1
drawObject(obj2);  // Shader B, Texture 2
drawObject(obj3);  // Shader A, Texture 3
drawObject(obj4);  // Shader B, Texture 1
// Result: Many shader/texture switches
```

**After:**
```javascript
// Sorted by state
// Shader A
drawObject(obj1);  // Texture 1
drawObject(obj3);  // Texture 3

// Shader B
drawObject(obj2);  // Texture 2
drawObject(obj4);  // Texture 1
// Result: Fewer state changes
```

**Measurements:**
- Shader switches reduced: 50 → 12 (76% reduction)
- Texture switches reduced: 85 → 28 (67% reduction)
- Expected time savings: ~0.8ms per frame

---

### 3.5 Algorithm-Level Optimizations

#### Strategy 1: Level of Detail (LOD)

**Technique:** Use simpler shaders for distant objects

**Implementation:**
```javascript
// Distance-based LOD selection
function selectShaderForObject(object, camera) {
  const distance = object.position.distanceTo(camera.position);
  
  if (distance < 20) {
    return shaders.highDetail;  // Full PBR, normal maps, etc.
  } else if (distance < 50) {
    return shaders.mediumDetail;  // Blinn-Phong, fewer textures
  } else {
    return shaders.lowDetail;  // Unlit or very simple
  }
}
```

**Measurements:**
- Average shader complexity reduced by ~40%
- Expected time savings: ~5-7ms per frame
- Visual difference: Minimal (distant objects less noticeable)

---

#### Strategy 2: Frustum Culling

**Technique:** Don't render objects outside camera view

**Before:**
```javascript
// Render everything
for (const object of scene.objects) {
  renderObject(object);
}
// Result: Rendering 1000 objects, many off-screen
```

**After:**
```javascript
// Only render visible objects
for (const object of scene.objects) {
  if (frustum.intersects(object.boundingBox)) {
    renderObject(object);
  }
}
// Result: Rendering 300 objects (70% culled)
```

**Measurements:**
- Objects rendered reduced: 1000 → 300 (70% reduction)
- Expected time savings: ~6-8ms per frame

---

## 4. Implementation Plan

### 4.1 Optimization Roadmap

**Phase 1: Quick Wins (Week 1)**

| Task | Priority | Expected Gain | Complexity | Risk |
|------|----------|---------------|------------|------|
| Texture atlas creation | P0 | 10ms | Medium | Low |
| Pre-multiply MVP matrix | P0 | 1ms | Low | Very Low |
| Enable mipmaps | P0 | 3-4ms | Low | Very Low |
| Basic frustum culling | P0 | 6-8ms | Low | Low |
| **Total Expected Gain** | - | **20-23ms** | - | - |

**Phase 2: Core Optimizations (Week 2-3)**

| Task | Priority | Expected Gain | Complexity | Risk |
|------|----------|---------------|------------|------|
| Simplify lighting model | P0 | 4ms | High | Medium |
| Eliminate branches | P0 | 1.8ms | Medium | Low |
| Texture compression | P0 | 2-3ms | Medium | Medium |
| Instanced rendering | P1 | 4.9ms | Medium | Low |
| **Total Expected Gain** | - | **12-13ms** | - | - |

**Phase 3: Polish & Validation (Week 4)**

| Task | Priority | Expected Gain | Complexity | Risk |
|------|----------|---------------|------------|------|
| LOD system | P1 | 5-7ms | High | Medium |
| State sorting | P2 | 0.8ms | Low | Very Low |
| Quality presets | P1 | Variable | Medium | Low |
| Performance profiling | P0 | 0ms (validation) | Low | Very Low |
| **Total Expected Gain** | - | **5-8ms** | - | - |

**Cumulative Expected Improvement:**

```
Current Frame Time:  35.2ms (28 FPS)
Expected After Phase 1: 12.2ms (82 FPS) ✅ Exceeds target
Expected After Phase 2:  9.2ms (109 FPS) ✅ Exceeds stretch goal
Expected After Phase 3:  7.2ms (139 FPS) ✅ Well above stretch goal

Target Frame Time: 16.7ms (60 FPS)
```

### 4.2 Validation & Testing Strategy

**Regression Testing:**

```javascript
// Automated performance regression tests
const performanceTests = [
  {
    name: 'Baseline Simple Scene',
    scene: 'scenes/baseline.json',
    targetFPS: 60,
    acceptableVariance: 5  // ±5 FPS
  },
  {
    name: 'Stress Test',
    scene: 'scenes/stress.json',
    targetFPS: 30,
    acceptableVariance: 3
  }
];

// Run after each optimization
async function runRegressionTests() {
  for (const test of performanceTests) {
    const results = await profiler.runPerformanceTest(test.name);
    
    if (results.averageFPS < test.targetFPS - test.acceptableVariance) {
      console.error(`❌ Regression detected in ${test.name}`);
      console.error(`Expected: ${test.targetFPS} FPS, Got: ${results.averageFPS} FPS`);
      return false;
    } else {
      console.log(`✅ ${test.name}: ${results.averageFPS} FPS (target: ${test.targetFPS})`);
    }
  }
  return true;
}
```

**Visual Quality Testing:**

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Reference Comparison | Side-by-side screenshots | SSIM > 0.95 |
| Artist Review | Manual inspection | Approval from art lead |
| A/B Testing | User preference survey | >70% prefer optimized or neutral |

---

## 5. Post-Optimization Validation

### 5.1 Expected Performance Results

**Projected Performance Matrix:**

| Hardware | Resolution | Current FPS | Target FPS | Projected FPS | Status |
|----------|------------|-------------|------------|---------------|--------|
| GTX 1060 | 1920x1080 | 28 FPS | 60 FPS | 82 FPS | ✅ Exceeds target |
| Intel HD 620 | 1280x720 | 20 FPS | 30 FPS | 45 FPS | ✅ Exceeds target |
| RTX 3060 | 2560x1440 | 45 FPS | 60 FPS | 105 FPS | ✅ Exceeds target |

### 5.2 Quality Assurance Checklist

- [ ] All performance targets met or exceeded
- [ ] Visual quality maintained (SSIM > 0.95)
- [ ] No new visual artifacts introduced
- [ ] Cross-browser compatibility verified
- [ ] Mobile performance acceptable
- [ ] Regression tests pass
- [ ] Artist approval obtained
- [ ] Documentation updated

---

## Appendices

### Appendix A: Profiling Data

[Raw performance data tables]

### Appendix B: Shader Diff

[Before/after shader code comparison]

### Appendix C: References

- [GPU Gems: GPU Performance](https://developer.nvidia.com/gpugems)
- [WebGL Best Practices (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices)

---

**Document End**
