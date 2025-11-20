# WebGL Shader Effect Specification: [Effect Name]

**Document Version:** 1.0  
**Status:** [Draft | In Review | Approved | Deprecated]  
**Effect Category:** [Post-Processing | Lighting | Particle | Atmospheric | Stylistic | Procedural]  
**Complexity Level:** [Simple | Intermediate | Advanced | Expert]  
**Author(s):** [Name(s)]  
**Reviewer(s):** [Name(s)]  
**Last Updated:** [Date]

---

## 1. Context & Purpose

### 1.1 Overview

*Purpose: To provide a high-level understanding of the visual effect and its artistic intent.*

**Effect Description:** [Comprehensive description of the visual effect, e.g., "Realistic volumetric fog with light scattering that responds to scene lighting and creates atmospheric depth"]

**Visual Characteristics:**
- [Characteristic 1, e.g., "Soft, ethereal appearance with gradual density falloff"]
- [Characteristic 2, e.g., "Animates smoothly based on wind direction and turbulence"]
- [Characteristic 3, e.g., "Interacts realistically with dynamic lighting"]

**Artistic Intent:** [The creative or aesthetic goal, e.g., "Create a mysterious, dreamlike atmosphere that enhances scene depth and mood without obscuring key gameplay elements"]

**Reference Materials:**
- [Reference image 1: path/to/reference1.jpg - "Target look: Misty forest scene"]
- [Reference video: URL - "Animation reference: Fog movement"]
- [Inspiration: "The Last of Us Part II environmental fog effects"]

### 1.2 Problem Statement

*Purpose: To explain what visual or technical gap this effect fills.*

**Visual Challenge:** [What visual problem does this effect solve? e.g., "Standard distance fog creates flat, unconvincing depth cues and doesn't interact with lighting"]

**Technical Challenge:** [What rendering challenges must be overcome? e.g., "Volumetric rendering is computationally expensive and difficult to integrate with existing forward rendering pipeline"]

**Previous Attempts:**
- [Attempt 1, e.g., "Simple linear fog: Too uniform, no lighting interaction"]
- [Attempt 2, e.g., "Raymarched volumetrics: Too slow for real-time performance"]
- [Attempt 3, e.g., "Particle-based fog: Breaks down at close range, visible artifacts"]

**Why This Approach:**
- [Reason 1, e.g., "Balances visual quality with performance through screenspace technique"]
- [Reason 2, e.g., "Integrates seamlessly with existing deferred rendering pipeline"]
- [Reason 3, e.g., "Artist-friendly controls for fine-tuning appearance"]

### 1.3 Goals & Objectives

*Purpose: To define measurable success criteria for both visual quality and technical performance.*

**Visual Goals:**
- [ ] **Aesthetic Quality:** [Achieves target art style/mood from reference materials]
- [ ] **Realism/Believability:** [Effect appears natural and physically plausible OR matches stylistic target]
- [ ] **Integration:** [Blends seamlessly with existing scene rendering]
- [ ] **Artistic Control:** [Provides intuitive parameters for artists to adjust]

**Technical Goals:**
- [ ] **Performance:** [Maintains 60 FPS on target hardware with effect enabled]
- [ ] **Scalability:** [Offers quality presets for different hardware tiers]
- [ ] **Compatibility:** [Works across target browsers and WebGL versions]
- [ ] **Stability:** [No visual glitches or artifacts under tested conditions]

**Success Criteria:**

| Criterion | Target | Measurement Method | Priority |
|-----------|--------|-------------------|----------|
| Visual Fidelity | [90% match to reference] | [A/B comparison, artist review] | P0 |
| Frame Time Impact | [< 3ms @ 1080p] | [GPU profiler] | P0 |
| Artist Satisfaction | [8/10 rating] | [User feedback survey] | P1 |
| Cross-Browser Consistency | [95% visual similarity] | [Automated screenshot comparison] | P1 |
| Memory Footprint | [< 20 MB textures/buffers] | [WebGL resource monitor] | P2 |

### 1.4 Target Audience

*Purpose: To identify who will implement, use, and maintain this effect.*

**Implementation Audience:**
- [Graphics Programmers - Will implement the effect system]
- [Technical Artists - Will integrate and tune effect parameters]
- [Game Developers - Will use effect in game scenes]

**End User Experience:**
- [Platform: Desktop (primary), Mobile (secondary)]
- [Expected User Hardware: Mid to high-end gaming systems]
- [Use Case: AAA-style adventure game environments]

**Skill Prerequisites:**
- **For Implementers:** GLSL programming, render pass management, WebGL pipeline understanding
- **For Artists:** Basic understanding of shader parameters, color theory, lighting concepts
- **For Integrators:** Three.js or similar framework knowledge, scene composition

---

## 2. Core Effect Specification

### 2.1 Visual Breakdown

#### 2.1.1 Effect Appearance Description

**Static Appearance (Still Frame):**
[Detailed description of how the effect appears in a single frame, e.g., "A subtle blue-gray haze begins approximately 10 meters from camera, gradually increasing in density. Near the density peak at 50 meters, the fog takes on warm orange tones from the sunset lighting. Individual wisps create detail at close range without obscuring mid-ground objects. The fog has a soft, organic quality with no hard edges or banding artifacts."]

**Dynamic Behavior (Animation):**
[Description of motion and changes over time, e.g., "Fog drifts slowly from left to right at 0.5m/s baseline speed, with turbulence creating local eddies and swirls. Density pulses subtly (±10%) with a 8-second cycle. When light sources move, the fog's illuminated areas shift smoothly with minimal latency. Wind gusts temporarily increase drift speed to 1.5m/s over 2-second intervals."]

**Lighting Response:**
[How the effect interacts with scene lighting, e.g., "Fog brightens significantly near point lights, creating visible 'god rays' or light shafts in high-density areas. Directional sunlight creates atmospheric scattering with a warm orange glow on the sun-facing side. Ambient light provides subtle base illumination to fog even in shadowed areas. Effect color temperature shifts based on dominant light source color."]

**Environmental Integration:**
[How effect blends with scene, e.g., "Fog opacity increases exponentially with distance from camera. Occludes distant geometry progressively but preserves silhouettes. Density varies based on world height (more fog in valleys, less on peaks). Interacts with particle systems - smoke and fog blend naturally."]

#### 2.1.2 Visual Parameters (Artist Controls)

**Primary Parameters:**

| Parameter Name | Type | Range | Default | Visual Impact | Example Use |
|---------------|------|-------|---------|---------------|-------------|
| `fogDensity` | Float | 0.0 - 1.0 | 0.3 | Overall fog thickness | 0.1 = light haze, 0.7 = heavy fog |
| `fogColor` | Color | RGB | (200, 210, 220) | Base fog tint | Warm orange for sunset, cool blue for dawn |
| `fogStartDistance` | Float | 0 - 1000m | 10.0 | Where fog begins | 5m = claustrophobic, 50m = distant atmosphere |
| `fogEndDistance` | Float | 0 - 5000m | 100.0 | Where fog reaches max density | 200m = near visibility limit, 1000m+ = distant mountains |
| `animationSpeed` | Float | 0.0 - 5.0 | 1.0 | Speed of fog drift/animation | 0.5 = calm day, 2.0 = windy |
| `turbulenceScale` | Float | 0.0 - 2.0 | 0.5 | Size of swirling patterns | 0.2 = fine detail, 1.5 = large billows |
| `lightScattering` | Float | 0.0 - 1.0 | 0.6 | How much fog glows near lights | 0.2 = subtle, 0.9 = dramatic god rays |
| `heightFalloff` | Float | 0.0 - 1.0 | 0.3 | Fog density reduction with altitude | 0.0 = uniform, 0.7 = heavy ground fog |
| [param_name] | [type] | [range] | [default] | [description] | [examples] |

**Advanced Parameters (Technical Artists):**

| Parameter Name | Type | Range | Default | Technical Impact | Notes |
|---------------|------|-------|---------|------------------|-------|
| `noiseOctaves` | Integer | 1 - 8 | 3 | Detail complexity vs performance | More octaves = more detail, higher cost |
| `noiseFBM_Lacunarity` | Float | 1.5 - 3.0 | 2.0 | Frequency multiplication between octaves | Higher = more contrast in noise |
| `marchingSteps` | Integer | 8 - 128 | 32 | Ray marching quality | More steps = better accuracy, slower |
| `ditherAmount` | Float | 0.0 - 1.0 | 0.3 | Reduce banding artifacts | Adds noise to smooth gradients |
| [param_name] | [type] | [range] | [default] | [description] | [notes] |

**Parameter Presets:**

```javascript
// Example parameter presets for common scenarios
const fogPresets = {
  morningMist: {
    fogDensity: 0.4,
    fogColor: [220, 230, 240],
    fogStartDistance: 5.0,
    fogEndDistance: 80.0,
    animationSpeed: 0.3,
    lightScattering: 0.7,
    heightFalloff: 0.6
  },
  
  spookyForest: {
    fogDensity: 0.6,
    fogColor: [180, 190, 185],
    fogStartDistance: 2.0,
    fogEndDistance: 40.0,
    animationSpeed: 0.5,
    lightScattering: 0.4,
    heightFalloff: 0.8
  },
  
  distantHaze: {
    fogDensity: 0.2,
    fogColor: [210, 220, 235],
    fogStartDistance: 100.0,
    fogEndDistance: 1000.0,
    animationSpeed: 0.1,
    lightScattering: 0.5,
    heightFalloff: 0.2
  }
};
```

### 2.2 Technical Architecture

#### 2.2.1 Rendering Pipeline Integration

**Pipeline Position:** [Where in the rendering pipeline this effect executes]

```
Rendering Pipeline Flow:
┌────────────────────┐
│ Geometry Pass      │ ← [Renders scene geometry to G-buffer OR depth buffer]
└──────┬─────────────┘
       │
┌──────▼─────────────┐
│ Lighting Pass      │ ← [Calculates lighting on geometry]
└──────┬─────────────┘
       │
┌──────▼─────────────┐
│ FOG EFFECT PASS    │ ◄─ [THIS EFFECT: Reads depth, applies volumetric fog]
└──────┬─────────────┘
       │
┌──────▼─────────────┐
│ Post-Processing    │ ← [Bloom, tone mapping, color grading]
└────────────────────┘
```

**Dependencies:**

| Resource | Type | Purpose | Required | Fallback |
|----------|------|---------|----------|----------|
| Scene Depth Buffer | Texture | Calculate fog depth | ✅ Yes | Render depth to color texture |
| Scene Color Buffer | Texture | Blend fog with scene | ✅ Yes | N/A |
| Noise Texture (3D or 2D) | Texture | Generate turbulence | ✅ Yes | Procedural noise in shader |
| Light Position Data | Uniform Array | Light scattering effect | ⬜ No | Use single directional light |
| Camera Matrices | Uniforms | Reconstruct world position | ✅ Yes | N/A |

#### 2.2.2 Shader Program Architecture

**Multi-Pass Approach:** [Yes/No - Does this effect require multiple rendering passes?]

**Pass Structure:**

| Pass # | Name | Purpose | Output | Performance Cost |
|--------|------|---------|--------|------------------|
| 1 | [Pass name, e.g., "Noise Generation"] | [Generate animated noise texture] | [256x256 R8 texture] | [Low: ~0.2ms] |
| 2 | [Pass name, e.g., "Volumetric Fog"] | [Ray march through fog volume] | [Screen-size RGBA8] | [High: ~2.5ms] |
| 3 | [Pass name, e.g., "Blur/Temporal Filter"] | [Smooth out noise artifacts] | [Screen-size RGBA8] | [Medium: ~0.5ms] |
| [n] | [pass_name] | [purpose] | [output] | [cost] |

**Shader Files:**

| Shader File | Type | Purpose | Lines of Code | Complexity |
|------------|------|---------|---------------|------------|
| `fog_noise_gen.glsl` | Compute/Fragment | Generate procedural noise | 80 | Low |
| `fog_volumetric.vert` | Vertex | Fullscreen quad vertices | 20 | Trivial |
| `fog_volumetric.frag` | Fragment | Main fog rendering logic | 250 | High |
| `fog_blur.frag` | Fragment | Bilateral blur for smoothing | 60 | Medium |
| [shader_file] | [type] | [purpose] | [LOC] | [complexity] |

**Key Algorithms:**

1. **Ray Marching for Volumetric Fog**
   - Algorithm: Step through view ray from camera to scene depth
   - Purpose: Accumulate fog density along ray path
   - Complexity: O(steps * pixels)
   
2. **Perlin/Simplex Noise for Turbulence**
   - Algorithm: Fractal Brownian Motion (FBM) with multiple octaves
   - Purpose: Create organic, natural-looking fog patterns
   - Complexity: O(octaves)

3. **Light Scattering (Simplified Mie Scattering)**
   - Algorithm: Phase function approximation based on light-view angle
   - Purpose: Create god rays and atmospheric glow
   - Complexity: O(lights)

4. **[Algorithm Name]**
   - Algorithm: [Description]
   - Purpose: [What it does]
   - Complexity: [Big-O notation]

#### 2.2.3 Data Flow Diagram

```
Input Data Flow:
┌─────────────────┐       ┌──────────────────┐
│ Scene Depth     │───────▶│                  │
│ (Texture)       │        │                  │
└─────────────────┘        │                  │
                           │   Volumetric     │       ┌─────────────────┐
┌─────────────────┐        │   Fog Shader     │───────▶│  Final Fog      │
│ Camera Data     │───────▶│   (Fragment)     │        │  Color + Alpha  │
│ (Uniforms)      │        │                  │        └─────────────────┘
└─────────────────┘        │                  │
                           │                  │
┌─────────────────┐        │                  │
│ Noise Texture   │───────▶│                  │
│ (3D or 2D)      │        │                  │
└─────────────────┘        └──────────────────┘
                                   ▲
┌─────────────────┐                │
│ Light Data      │────────────────┘
│ (Uniform Array) │
└─────────────────┘

Shader Internal Flow:
1. Reconstruct world position from screen UV + depth
2. Calculate ray direction from camera to world position
3. Step along ray (ray marching):
   ├─ Sample noise texture at current position
   ├─ Calculate fog density based on height and distance
   ├─ Calculate light contribution (scattering)
   └─ Accumulate fog color and alpha
4. Output final fog RGBA to blend with scene
```

### 2.3 Render Targets & Buffers

**Required Render Targets:**

| Target Name | Format | Resolution | Purpose | Persistent |
|------------|--------|------------|---------|------------|
| `depthBuffer` | DEPTH24_STENCIL8 | Screen | Scene depth information | No (per-frame) |
| `sceneColorBuffer` | RGBA8 | Screen | Scene color before fog | No (per-frame) |
| `noiseTexture` | R8 or RGB8 | 256x256 | Animated noise pattern | Yes (updated) |
| `fogBuffer` | RGBA8 | Screen | Fog color and density | No (per-frame) |
| `blurredFogBuffer` | RGBA8 | Screen | Smoothed fog result | No (per-frame) |
| [target_name] | [format] | [resolution] | [purpose] | [persistent] |

**Memory Budget:**

```javascript
// Memory calculation example
const screenResolution = { width: 1920, height: 1080 };
const screenPixels = screenResolution.width * screenResolution.height;

const memoryUsage = {
  // Textures
  depthBuffer: screenPixels * 4,  // 4 bytes per pixel (24-bit depth + 8-bit stencil)
  sceneColorBuffer: screenPixels * 4,  // RGBA8 = 4 bytes
  noiseTexture: 256 * 256 * 1,  // R8 = 1 byte (or *3 for RGB8)
  fogBuffer: screenPixels * 4,  // RGBA8
  blurredFogBuffer: screenPixels * 4,  // RGBA8 (optional, can reuse fogBuffer)
  
  // Vertex buffers (minimal for fullscreen quad)
  fullscreenQuadVBO: 4 * 6 * 4,  // 4 vertices * 6 floats * 4 bytes
  
  // Total (in MB)
  totalMB: function() {
    const bytes = Object.values(this).reduce((sum, val) => 
      typeof val === 'number' ? sum + val : sum, 0
    );
    return (bytes / (1024 * 1024)).toFixed(2);
  }
};

console.log(`Total GPU memory: ${memoryUsage.totalMB()} MB`);
// Example output: ~32 MB at 1080p
```

### 2.4 Uniform Configuration

**Complete Uniform Reference:**

```glsl
// Transform & Camera
uniform mat4 u_inverseProjectionMatrix;  // Reconstruct view space position
uniform mat4 u_inverseViewMatrix;        // Reconstruct world space position
uniform vec3 u_cameraPosition;           // World space camera position
uniform vec2 u_resolution;               // Screen resolution

// Fog Appearance
uniform vec3 u_fogColor;                 // Base fog color (RGB)
uniform float u_fogDensity;              // Overall density multiplier
uniform float u_fogStartDistance;        // Distance where fog begins (meters)
uniform float u_fogEndDistance;          // Distance where fog reaches max density

// Animation
uniform float u_time;                    // Elapsed time in seconds
uniform float u_animationSpeed;          // Animation speed multiplier
uniform vec3 u_windDirection;            // Wind direction (normalized)

// Noise & Turbulence
uniform float u_noiseScale;              // Noise texture coordinate scale
uniform float u_noiseLacunarity;         // Frequency multiplier between octaves
uniform float u_noiseGain;               // Amplitude multiplier between octaves
uniform int u_noiseOctaves;              // Number of noise octaves to sample

// Lighting
uniform vec3 u_lightPositions[8];        // Up to 8 dynamic light positions
uniform vec3 u_lightColors[8];           // Light colors and intensities
uniform int u_lightCount;                // Active light count
uniform float u_lightScattering;         // Scattering intensity

// Quality & Optimization
uniform int u_marchingSteps;             // Ray marching step count
uniform float u_ditherAmount;            // Dithering to reduce banding

// Textures
uniform sampler2D u_depthTexture;        // Scene depth buffer
uniform sampler2D u_sceneTexture;        // Scene color buffer
uniform sampler3D u_noiseTexture;        // 3D noise texture (or sampler2D for 2D noise)
```

---

## 3. Implementation Details & Technical Constraints

### 3.1 Performance Optimization Strategy

#### 3.1.1 Quality Tiers

**Quality Presets for Different Hardware:**

| Quality Tier | Target Hardware | Marching Steps | Noise Octaves | Blur Passes | Texture Resolution | Target FPS | Notes |
|-------------|----------------|----------------|---------------|-------------|--------------------|------------|-------|
| **Low** | Integrated graphics, old GPUs | 8-16 | 1-2 | 0 | 128x128 noise | 30 | Minimal fog detail |
| **Medium** | Mid-range GPUs (GTX 1060) | 16-32 | 2-3 | 1 | 256x256 noise | 60 | Balanced quality |
| **High** | High-end GPUs (RTX 2070+) | 32-64 | 3-4 | 1-2 | 256x256 noise | 60+ | Full detail |
| **Ultra** | Enthusiast GPUs (RTX 3080+) | 64-128 | 4-6 | 2 | 512x512 noise | 60+ | Maximum quality |

**Auto-Quality Scaling:**

```javascript
// Automatic quality adjustment based on performance monitoring
function adjustQualityBasedOnPerformance(currentFPS, targetFPS = 60) {
  const qualitySettings = {
    low: { marchingSteps: 12, noiseOctaves: 2, blurEnabled: false },
    medium: { marchingSteps: 24, noiseOctaves: 3, blurEnabled: true },
    high: { marchingSteps: 48, noiseOctaves: 4, blurEnabled: true },
    ultra: { marchingSteps: 96, noiseOctaves: 5, blurEnabled: true }
  };
  
  let currentQuality = 'medium';
  
  if (currentFPS < targetFPS * 0.8) {
    // Performance too low, reduce quality
    currentQuality = downgradeQuality(currentQuality);
  } else if (currentFPS > targetFPS * 1.2) {
    // Performance headroom, can increase quality
    currentQuality = upgradeQuality(currentQuality);
  }
  
  return qualitySettings[currentQuality];
}
```

#### 3.1.2 Optimization Techniques

**Ray Marching Optimizations:**

1. **Adaptive Step Size**
   ```glsl
   // Use larger steps far from camera, smaller steps close up
   float stepSize = mix(minStepSize, maxStepSize, t);
   ```

2. **Early Ray Termination**
   ```glsl
   // Stop ray marching when accumulated alpha is nearly opaque
   if (accumulatedAlpha > 0.98) break;
   ```

3. **Distance-Based Step Count**
   ```glsl
   // Reduce steps for far-away pixels
   int steps = int(mix(minSteps, maxSteps, 1.0 - depth));
   ```

**Texture Sampling Optimizations:**

1. **Mipmapping**
   - Generate mipmaps for noise texture
   - Use texture LOD based on distance from camera

2. **Texture Reuse**
   - Animate noise with UV scrolling instead of regenerating
   - Cache static noise patterns

3. **Lower Precision**
   - Use R8 instead of RGBA8 for noise where possible
   - Pack multiple values into channels

**Computational Optimizations:**

1. **Move to Vertex Shader When Possible**
   ```glsl
   // Calculate rarely-changing values in vertex shader
   varying vec3 v_viewRay;  // Pre-computed per vertex
   ```

2. **Reduce Branching**
   ```glsl
   // Replace:
   if (fogDensity > 0.5) { /* expensive calculation */ }
   
   // With:
   float mask = step(0.5, fogDensity);
   result = mask * expensiveCalculation();  // May still compute but avoids branch
   ```

3. **Use Built-in Functions**
   ```glsl
   // Fast built-ins instead of manual calculations
   float dist = length(pos);  // Built-in is faster than manual distance
   vec3 norm = normalize(vec);  // Optimized normalize
   ```

### 3.2 Known Limitations & Constraints

**Technical Limitations:**

| Limitation | Impact | Severity | Workaround |
|-----------|--------|----------|------------|
| **Limited texture units** | Can't use all desired textures simultaneously | Medium | Combine textures, use texture atlases |
| **No 3D texture support (WebGL 1)** | 2D noise looks less natural | Medium | Use 2D texture with scrolling, or polyfill 3D sampling |
| **Fragment shader instruction limit** | Complex shaders may not compile on old GPUs | High | Provide simplified fallback shader |
| **No compute shaders (WebGL 1/2)** | Can't do efficient volumetric calculations | High | Use fragment shader with render-to-texture |
| **Precision limitations (mobile)** | Banding and artifacts on mobile | Medium | Add dithering, use higher precision where critical |

**Visual Artifacts:**

| Artifact | Cause | Prevention Strategy |
|----------|-------|-------------------|
| **Banding** | Low precision or too few steps | Add dithering, increase steps, use higher precision |
| **Shimmer/Crawl** | Temporal aliasing in animation | Add temporal filtering, reduce animation speed |
| **Seams/Discontinuities** | Noise texture tiling | Use seamless noise, larger texture, or 3D noise |
| **Performance Spikes** | Sudden complexity changes | Use gradual LOD transitions, profile consistently |
| **Color Bleeding** | Light scattering over-contribution | Clamp light contribution, verify blending modes |

**Browser/Hardware Compatibility:**

| Issue | Affected Platforms | Workaround |
|-------|-------------------|------------|
| **Depth texture not available** | Some mobile browsers | Render depth to color attachment |
| **Floating-point textures not supported** | WebGL 1 without extensions | Use RGBA8 with encoding/decoding |
| **Shader compiler differences** | Various browsers | Test extensively, avoid undefined behavior |
| **Performance variance** | Mobile vs desktop | Implement auto-quality scaling |

### 3.3 Dependencies & Integration

**Required Framework Features:**

```javascript
// Minimum framework requirements
const requirements = {
  webGL: {
    version: 'WebGL 1.0 or 2.0',
    extensions: [
      'OES_texture_float',       // For higher precision textures
      'WEBGL_depth_texture',     // To read scene depth
      'EXT_shader_texture_lod'   // For manual LOD in shaders (optional)
    ]
  },
  
  renderPipeline: {
    depthBuffer: 'Required - must be accessible as texture',
    colorBuffer: 'Required - scene must render to texture first',
    postProcessing: 'Effect should be inserted before tone mapping'
  },
  
  features: {
    uniformBuffer: 'For efficient uniform updates',
    renderTargets: 'Multiple render targets for multi-pass effects',
    frameBuffers: 'For intermediate rendering steps'
  }
};
```

**Integration with Popular Frameworks:**

| Framework | Integration Method | Notes |
|-----------|-------------------|-------|
| **Three.js** | Use EffectComposer with custom pass | Requires `three/examples/jsm/postprocessing/*` |
| **Babylon.js** | Create PostProcess effect | Use BABYLON.PostProcess base class |
| **PlayCanvas** | Create custom script as CameraComponent | Render between scene and post-processing |
| **Vanilla WebGL** | Manage render passes manually | Most control but most effort |

**Example Three.js Integration:**

```javascript
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';

// Create effect composer
const composer = new EffectComposer(renderer);

// Add render pass (renders scene to texture)
const renderPass = new RenderPass(scene, camera);
composer.addPass(renderPass);

// Add fog effect pass
const fogPass = new ShaderPass(volumetricFogShader);
fogPass.uniforms.u_fogDensity.value = 0.3;
fogPass.uniforms.u_fogColor.value = new THREE.Vector3(0.8, 0.85, 0.9);
composer.addPass(fogPass);

// Render loop
function animate(time) {
  fogPass.uniforms.u_time.value = time * 0.001;
  composer.render();
  requestAnimationFrame(animate);
}
```

---

## 4. Validation & Success Metrics

### 4.1 Visual Quality Assessment

**Visual Validation Tests:**

| Test Name | Method | Pass Criteria | Tools/Assets |
|-----------|--------|---------------|--------------|
| **Reference Matching** | Side-by-side comparison with reference images | 90% SSIM score, artist approval | Reference images, SSIM calculator |
| **Lighting Response** | Test with multiple light scenarios | Fog correctly illuminated, no artifacts | Test scenes with various lighting |
| **Animation Quality** | Verify smooth, natural motion | No jittering, stuttering, or temporal artifacts | 60 FPS video recording |
| **Distance Consistency** | Test fog at various camera distances | Consistent appearance regardless of distance | Automated camera movement script |
| **Resolution Testing** | Render at multiple resolutions | No scaling artifacts or loss of detail | 720p, 1080p, 1440p, 4K test renders |

**A/B Testing Protocol:**

```javascript
// Example A/B testing setup for effect refinement
const testScenarios = [
  {
    name: 'Original vs New Lighting Model',
    configA: { lightScattering: 0.5, useAdvancedScattering: false },
    configB: { lightScattering: 0.5, useAdvancedScattering: true },
    metrics: ['renderTime', 'visualQuality', 'artistPreference']
  },
  {
    name: 'Step Count Impact',
    configA: { marchingSteps: 32 },
    configB: { marchingSteps: 16 },
    metrics: ['renderTime', 'visualQuality', 'artifactCount']
  }
];

// Run automated testing
runABTests(testScenarios, scene, camera);
```

### 4.2 Performance Benchmarking

**Performance Test Suite:**

| Test Name | Scenario | Measurement | Target | Method |
|-----------|----------|-------------|--------|--------|
| **Baseline Frame Time** | Simple scene, fog disabled | Average frame time | 16ms (60 FPS) | Chrome DevTools |
| **Fog Impact** | Same scene, fog enabled | Frame time increase | < 3ms additional | Chrome DevTools |
| **Worst Case** | Complex scene, maximum fog settings | Frame time | < 20ms (50 FPS) | Chrome DevTools |
| **Scalability** | Test at 720p, 1080p, 1440p, 4K | Frame time vs resolution | Linear scaling | Automated resolution tests |
| **Long-term Stability** | Run for 10 minutes | Memory usage, FPS consistency | No leaks, stable FPS | Memory profiler |

**Hardware Benchmark Matrix:**

| GPU Model | Resolution | Quality | Measured FPS | Frame Time | Memory Usage | Status |
|-----------|------------|---------|--------------|------------|--------------|--------|
| GTX 1060 (Desktop) | 1920x1080 | Medium | 62 FPS | 16.1ms | 28 MB | ✅ Pass |
| GTX 1660 (Desktop) | 1920x1080 | High | 73 FPS | 13.7ms | 32 MB | ✅ Pass |
| RTX 3060 (Desktop) | 2560x1440 | High | 68 FPS | 14.7ms | 45 MB | ✅ Pass |
| RTX 3080 (Desktop) | 3840x2160 | Ultra | 58 FPS | 17.2ms | 120 MB | ✅ Pass |
| Intel HD 620 (Laptop) | 1280x720 | Low | 35 FPS | 28.6ms | 18 MB | ⚠️ Acceptable |
| Adreno 650 (Mobile) | 1280x720 | Medium | 45 FPS | 22.2ms | 25 MB | ✅ Pass |
| Apple M1 (Laptop) | 2560x1600 | High | 60 FPS | 16.7ms | 35 MB | ✅ Pass |

### 4.3 Artist Feedback & Iteration

**Artist Workflow Testing:**

```javascript
// Artist feedback survey structure
const artistSurvey = {
  parameters: {
    q1: "Are the provided parameters intuitive and easy to understand?",
    q2: "Can you achieve your desired visual result with the available controls?",
    q3: "Are parameter ranges appropriate? (Too limited or too broad?)",
    q4: "Do parameter changes produce predictable results?"
  },
  
  workflow: {
    q1: "How long did it take to create your desired effect?",
    q2: "Did you encounter any frustrating limitations?",
    q3: "Are there missing controls you wished you had?"
  },
  
  qualityRating: {
    q1: "Rate visual quality (1-10):",
    q2: "Rate performance (1-10):",
    q3: "Rate integration with existing pipeline (1-10):"
  },
  
  overallSatisfaction: "Would you use this effect in production? (Yes/No/Maybe)"
};
```

**Iteration Metrics:**

| Iteration | Changes Made | Artist Rating | Performance | Status |
|-----------|--------------|---------------|-------------|--------|
| v1.0 | Initial implementation | 5/10 | 62 FPS | In Development |
| v1.1 | Added height falloff parameter | 6/10 | 61 FPS | In Development |
| v1.2 | Improved light scattering model | 8/10 | 58 FPS | Testing |
| v1.3 | Performance optimizations | 8/10 | 64 FPS | Ready for Review |

### 4.4 Success Criteria Checklist

**Pre-Release Checklist:**

- [ ] **Visual Quality (P0)**
  - [ ] Matches reference images (90% SSIM or artist approval)
  - [ ] No visible artifacts (banding, seams, flickering)
  - [ ] Smooth animations with consistent motion
  - [ ] Correct lighting interaction (shadows, god rays, ambient)
  - [ ] Proper depth integration (no Z-fighting or sorting issues)

- [ ] **Performance (P0)**
  - [ ] Achieves 60 FPS on mid-range hardware (GTX 1060) at 1080p
  - [ ] Frame time impact < 3ms on target hardware
  - [ ] No memory leaks over 10-minute runtime
  - [ ] Scales linearly with resolution
  - [ ] Quality presets functional and well-balanced

- [ ] **Compatibility (P0)**
  - [ ] Works on Chrome, Firefox, Safari (latest 2 versions)
  - [ ] Works on Windows, macOS, Linux
  - [ ] Mobile support (iOS Safari, Chrome Mobile) at reduced quality
  - [ ] Fallback behavior when extensions unavailable
  - [ ] No WebGL errors or warnings

- [ ] **Usability (P1)**
  - [ ] Artist satisfaction rating ≥ 8/10
  - [ ] Parameter ranges appropriate and intuitive
  - [ ] Presets cover common use cases
  - [ ] Integration documentation complete
  - [ ] Example scenes provided

- [ ] **Code Quality (P1)**
  - [ ] Code follows project style guide
  - [ ] Shader code commented and documented
  - [ ] Integration examples provided for major frameworks
  - [ ] Performance profiling data included

---

## 5. Considerations

### 5.1 Security & Safety

**Shader Safety:**

| Risk | Mitigation | Priority |
|------|-----------|----------|
| **Infinite loops** | Enforce maximum loop iterations with compile-time guards | High |
| **Out-of-bounds access** | Validate all array indices and texture coordinates | High |
| **Division by zero** | Add epsilon to all divisors, use safeDivide() helper | Medium |
| **Precision overflow** | Use appropriate precision qualifiers, clamp intermediate values | Medium |

**Content Safety:**

- **Flashing/Strobing:** Ensure animations don't create strobing effects that could trigger photosensitive epilepsy
- **Motion Sickness:** Provide option to reduce or disable fog animation for users sensitive to motion
- **Performance Fallback:** Automatically reduce quality if frame rate drops dangerously low

### 5.2 Accessibility Considerations

**Visual Accessibility:**

| Feature | Implementation | Purpose |
|---------|---------------|---------|
| **Reduced Motion** | Respect `prefers-reduced-motion` media query | Disable/reduce animations for users with vestibular disorders |
| **High Contrast Mode** | Provide high-contrast preset | Ensure fog visible but not overwhelming in high contrast mode |
| **Color Blind Support** | Test with color blindness simulation | Verify fog visible with various types of color blindness |
| **Luminance Preservation** | Ensure fog doesn't over-darken scene | Maintain readability of UI and important objects |

**Performance Accessibility:**

- Users with older hardware should still be able to disable effect or use ultra-low quality preset
- Provide clear visual/UI indication of performance impact
- Allow manual quality override (don't force auto-quality)

### 5.3 Edge Cases & Unusual Scenarios

**Edge Case Handling:**

| Scenario | Problem | Solution |
|----------|---------|----------|
| **Camera inside fog volume** | Fog may look incorrect or flicker | Special handling for near-clip plane, gradual density ramp |
| **Extreme camera angles** | Ray marching may produce artifacts | Clamp ray directions, adjust step size dynamically |
| **Rapidly moving camera** | Temporal filtering causes ghosting | Detect camera velocity, reduce temporal filter strength |
| **Very close/far objects** | Depth precision issues | Use logarithmic depth buffer or reversed-Z |
| **Transparent objects** | Fog renders incorrectly behind transparency | Render fog after opaque but before transparent geometry |
| **Multiple cameras** | Fog settings may not apply correctly | Per-camera fog configuration, separate fog state |

**Degenerate Input Handling:**

```glsl
// Example: Safe ray marching with edge case handling
vec4 calculateFog(vec2 uv, float depth) {
  // Edge case: Invalid depth (sky, far plane)
  if (depth >= 0.9999 || depth <= 0.0) {
    return vec4(0.0);  // No fog
  }
  
  // Edge case: Zero-length ray
  vec3 rayDir = calculateRayDirection(uv);
  float rayLength = length(rayDir);
  if (rayLength < 0.001) {
    return vec4(0.0);  // Camera at origin or invalid
  }
  rayDir /= rayLength;  // Normalize safely
  
  // Edge case: Negative or zero step count
  int steps = max(u_marchingSteps, 1);
  
  // Ray march with safe operations
  float stepSize = rayLength / float(steps);
  // ... rest of ray marching logic
}
```

### 5.4 Future Enhancements & Research

**Planned Improvements:**

| Enhancement | Description | Priority | Complexity | Estimated Effort |
|-------------|-------------|----------|------------|------------------|
| **Volumetric Shadows** | Fog occluded by shadow casters | High | High | 2-3 weeks |
| **Multiple Fog Layers** | Different fog densities at different heights | Medium | Medium | 1 week |
| **Wind Zones** | Localized wind affecting fog | Low | Medium | 1 week |
| **Particle Integration** | Better blending with particle effects | Medium | Low | 3 days |
| **VR Support** | Optimize for VR rendering (stereo) | Medium | Medium | 1 week |

**Research Opportunities:**

1. **Machine Learning Denoising**
   - Use neural network to denoise ray-marched fog
   - Allow fewer marching steps with ML-based quality recovery
   - Target: 50% reduction in steps with same visual quality

2. **Temporal Reprojection**
   - Reuse fog calculation from previous frames
   - Challenge: Handle disocclusion and fast camera motion
   - Target: 2x performance improvement with minimal quality loss

3. **Hybrid Raymarching**
   - Combine coarse voxel grid with fine screenspace raymarch
   - Pre-compute static fog contribution in voxel grid
   - Target: Better performance for static scenes

### 5.5 Alternative Approaches Considered

**Alternative 1: Particle-Based Fog**

**Description:** Use GPU particles to represent fog billboards

**Advantages:**
- Very fast rendering (geometry-based)
- Easy to control and art-direct
- Works well at medium-far distances

**Disadvantages:**
- Breaks down visually at close range
- Requires many particles for density (memory cost)
- Particles pop in/out, not continuous
- No true volumetric scattering

**Decision:** ❌ Rejected  
**Reason:** Doesn't meet visual quality requirements for close-up views

---

**Alternative 2: Pre-computed Radiance Transfer**

**Description:** Pre-bake fog lighting into volume textures

**Advantages:**
- Very fast at runtime (just texture lookups)
- Can achieve complex lighting effects
- Consistent performance regardless of light count

**Disadvantages:**
- Huge memory footprint (3D textures)
- Static lighting only (no dynamic lights)
- Long pre-computation time
- Not suitable for web (download size)

**Decision:** ❌ Rejected  
**Reason:** Memory and file size too large for web deployment, no dynamic lighting

---

**Alternative 3: Single-Pass Screen-Space Fog (Height-Based)**

**Description:** Simple height fog calculated in single pass

**Advantages:**
- Extremely fast (< 0.5ms)
- Very simple implementation
- Low memory usage

**Disadvantages:**
- No volumetric properties (no light scattering)
- Uniform, flat appearance
- No turbulence or animation detail
- Doesn't look convincing for stylized or realistic goals

**Decision:** ⏸️ Kept as "Low Quality" Fallback  
**Reason:** Useful as ultra-low quality option for weak hardware, but not primary solution

---

**Alternative 4: Voxel Cone Tracing**

**Description:** Trace cones through voxel grid for accurate volumetrics

**Advantages:**
- Highly accurate volumetric rendering
- True global illumination support
- Excellent visual quality

**Disadvantages:**
- Extremely expensive (10-20ms+)
- Complex implementation
- Requires voxelization pass
- Not practical for WebGL performance targets

**Decision:** ❌ Rejected  
**Reason:** Performance cost far too high for web deployment

---

## 6. Documentation & Examples

### 6.1 Quick Start Guide

**Basic Setup (5 minutes):**

```javascript
// 1. Import the effect
import { VolumetricFogEffect } from './effects/volumetric-fog.js';

// 2. Create effect instance with default settings
const fogEffect = new VolumetricFogEffect(renderer, scene, camera);

// 3. Add to your render loop
function animate(time) {
  fogEffect.render(time);
  requestAnimationFrame(animate);
}

animate(0);
```

**Customization (10 minutes):**

```javascript
// Configure fog appearance
fogEffect.setParameters({
  fogColor: [200, 210, 220],      // Soft blue-gray
  fogDensity: 0.4,                 // Medium density
  fogStartDistance: 10,            // Begins 10m from camera
  fogEndDistance: 100,             // Max density at 100m
  animationSpeed: 0.5,             // Slow, gentle movement
  lightScattering: 0.6             // Moderate god rays
});

// Load preset
fogEffect.loadPreset('morningMist');

// Dynamic updates
window.addEventListener('weatherChange', (event) => {
  if (event.weather === 'foggy') {
    fogEffect.setParameter('fogDensity', 0.8);
  } else {
    fogEffect.setParameter('fogDensity', 0.2);
  }
});
```

### 6.2 Complete Integration Example

**Full Three.js Example:**

```javascript
/**
 * Complete volumetric fog integration with Three.js
 * Demonstrates full setup with quality controls and animation
 * 
 * @author Craig
 * @version 1.0
 */

import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { VolumetricFogPass } from './VolumetricFogPass.js';

// Scene setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 2, 10);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Add some geometry to scene
const geometry = new THREE.BoxGeometry(2, 2, 2);
const material = new THREE.MeshStandardMaterial({ color: 0x00ff00 });
const cube = new THREE.Mesh(geometry, material);
scene.add(cube);

// Lighting
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 10, 5);
scene.add(light);

const ambientLight = new THREE.AmbientLight(0x404040);
scene.add(ambientLight);

// Post-processing setup
const composer = new EffectComposer(renderer);

// Render pass (scene to texture)
const renderPass = new RenderPass(scene, camera);
composer.addPass(renderPass);

// Volumetric fog pass
const fogPass = new VolumetricFogPass();
fogPass.setParameters({
  fogColor: new THREE.Vector3(0.8, 0.85, 0.9),
  fogDensity: 0.3,
  fogStartDistance: 5.0,
  fogEndDistance: 50.0,
  animationSpeed: 0.5,
  lightPositions: [light.position],
  lightColors: [new THREE.Vector3(1, 1, 1)],
  marchingSteps: 32,
  noiseOctaves: 3
});
composer.addPass(fogPass);

// Quality controls
function setQuality(qualityLevel) {
  const qualitySettings = {
    low: { steps: 16, octaves: 2 },
    medium: { steps: 32, octaves: 3 },
    high: { steps: 64, octaves: 4 },
    ultra: { steps: 96, octaves: 5 }
  };
  
  const settings = qualitySettings[qualityLevel];
  fogPass.setParameter('marchingSteps', settings.steps);
  fogPass.setParameter('noiseOctaves', settings.octaves);
}

// UI controls
document.getElementById('quality').addEventListener('change', (e) => {
  setQuality(e.target.value);
});

document.getElementById('density').addEventListener('input', (e) => {
  fogPass.setParameter('fogDensity', parseFloat(e.target.value));
});

// Animation loop
function animate(time) {
  requestAnimationFrame(animate);
  
  // Update fog effect
  fogPass.setParameter('time', time * 0.001);
  fogPass.setParameter('cameraPosition', camera.position);
  
  // Rotate cube
  cube.rotation.x += 0.01;
  cube.rotation.y += 0.01;
  
  // Render with fog
  composer.render();
}

animate(0);

// Handle window resize
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  composer.setSize(window.innerWidth, window.innerHeight);
});
```

### 6.3 Troubleshooting Guide

**Common Issues:**

| Problem | Symptoms | Likely Cause | Solution |
|---------|----------|--------------|----------|
| **No fog visible** | Scene renders normally but fog absent | Uniforms not set correctly | Check uniform values, ensure depth texture accessible |
| **Black screen** | Entire screen black | Shader compilation error or depth texture issue | Check browser console, verify depth texture format |
| **Banding artifacts** | Visible horizontal bands in fog | Insufficient precision or steps | Increase marching steps, add dithering, use highp |
| **Poor performance** | Low FPS with fog enabled | Too many marching steps or octaves | Reduce quality settings, check GPU profiler |
| **Fog too bright/dark** | Fog overly bright or too dark | Incorrect color space or blending | Verify sRGB handling, check alpha blending mode |
| **Temporal flickering** | Fog shimmers or crawls | Animation too fast or temporal aliasing | Reduce animation speed, add temporal filtering |
| **Fog cuts off sharply** | Hard edge at fog start/end | Incorrect distance parameters | Adjust fogStartDistance and fogEndDistance |

**Debug Visualization Modes:**

```glsl
// Add to fragment shader for debugging

// Debug Mode 1: Visualize depth
#ifdef DEBUG_DEPTH
  float depth = texture2D(u_depthTexture, v_texCoord).r;
  gl_FragColor = vec4(vec3(depth), 1.0);
  return;
#endif

// Debug Mode 2: Visualize noise
#ifdef DEBUG_NOISE
  float noise = texture3D(u_noiseTexture, vec3(v_texCoord, u_time * 0.1)).r;
  gl_FragColor = vec4(vec3(noise), 1.0);
  return;
#endif

// Debug Mode 3: Visualize fog density (no color)
#ifdef DEBUG_DENSITY
  float density = calculateFogDensity(v_worldPos);
  gl_FragColor = vec4(vec3(density), 1.0);
  return;
#endif

// Debug Mode 4: Visualize ray marching steps
#ifdef DEBUG_STEPS
  float stepCount = float(u_marchingSteps) / 128.0;  // Normalize to 0-1
  gl_FragColor = vec4(stepCount, 0.0, 1.0 - stepCount, 1.0);
  return;
#endif
```

---

## 7. Appendices

### Appendix A: Shader Source Code

**Main Fog Fragment Shader:**

[Due to length, shader source is typically stored in separate .glsl files]

**File:** `volumetric_fog.frag`

```glsl
// See separate file: src/shaders/volumetric_fog.frag
// Approximately 250 lines of GLSL code
// Implements ray marching, noise sampling, lighting calculations
```

### Appendix B: Mathematical References

**Fog Density Formula (Exponential):**

```
density(distance) = 1.0 - exp(-fogDensity * distance)

where:
  fogDensity: User-controlled density parameter
  distance: Distance from camera to fragment
  exp: Natural exponential function (e^x)
```

**Light Scattering (Simplified Mie):**

```
scattering = phase(θ) * lightIntensity * fogDensity

phase(θ) = (1 - g²) / (4π * (1 + g² - 2g*cos(θ))^1.5)

where:
  θ: Angle between view direction and light direction
  g: Anisotropy parameter (-1 to 1, typically 0.76 for forward scattering)
  lightIntensity: Light color and strength
  fogDensity: Local fog density at sample point
```

### Appendix C: Performance Profiling Data

**Frame Time Breakdown (High Quality, 1080p, GTX 1660):**

| Stage | Time (ms) | % of Total | Notes |
|-------|-----------|------------|-------|
| Geometry Pass | 4.2ms | 28% | Scene rendering to G-buffer |
| Lighting Pass | 3.8ms | 25% | Deferred lighting calculation |
| Fog Pass (This Effect) | 2.3ms | 15% | Volumetric fog ray marching |
| Post-Processing | 1.5ms | 10% | Bloom, tone mapping |
| Presentation | 0.8ms | 5% | Final blit to screen |
| **Total Frame** | **15.1ms** | **100%** | **66 FPS** |

### Appendix D: References & Resources

**Technical Papers:**
- [1] "Physically-Based Real-Time Volumetric Fog" - Patry, B. (2015)
- [2] "Efficient Atmospheric Scattering with Multiple Scattering" - Elek, O. (2009)
- [3] "Volumetric Light Scattering as a Post-Process" - Mitchell, J. (2008)

**Online Resources:**
- [Shadertoy Volumetric Fog Examples](https://www.shadertoy.com/)
- [GPU Gems: Volumetric Light Scattering](https://developer.nvidia.com/gpugems/gpugems3/part-ii-light-and-shadows/chapter-13-volumetric-light-scattering-post-process)
- [The Book of Shaders: Noise](https://thebookofshaders.com/11/)

**Related Specifications:**
- [Shader Program Specification: Volumetric Fog Core]
- [Shader Program Specification: Noise Generation]
- [Effect Specification: God Rays]

---

## Document Approval

**Reviewer Feedback Section:**

**Overall Assessment:**
- [ ] Approve - Ready for implementation
- [ ] Approve with Comments - Minor refinements needed
- [ ] Request Changes - Significant revisions required

**Key Strengths:**
*[Reviewer notes on what's well-designed]*

**Required Changes (Blocking):**
*[Critical issues that must be addressed]*

**Suggestions & Improvements (Non-Blocking):**
*[Optional enhancements and ideas]*

**Artist Feedback:**
*[Input from technical artists and visual designers]*

---

**Document End**

*For questions, feedback, or technical support, contact [Author Name] at [email@example.com]*
