# WebGL Shader Library Specification: [Library Name]

**Document Version:** 1.0  
**Status:** [Draft | In Review | Approved | Active]  
**Library Type:** [Core | Effects | Utilities | Domain-Specific]  
**Author(s):** [Name(s)]  
**Maintainer(s):** [Name(s)]  
**Last Updated:** [Date]

---

## 1. Context & Purpose

### 1.1 Overview

*Purpose: To establish the scope, goals, and organization of this shader library.*

**Library Name:** [Name of the shader library/collection]

**Library Description:** [Comprehensive description of what this library provides, e.g., "A comprehensive collection of PBR material shaders for WebGL applications, providing consistent, high-performance rendering across various material types including metals, dielectrics, and transmissive surfaces"]

**Primary Use Cases:**
- [Use case 1, e.g., "Real-time 3D product visualization"]
- [Use case 2, e.g., "Game engine material system"]
- [Use case 3, e.g., "Architectural rendering applications"]

**Library Philosophy:** [Guiding principles, e.g., "Performance-first approach with graceful quality degradation, maximum code reuse through modular includes, and artist-friendly parameter exposure"]

### 1.2 Problem Statement

*Purpose: To explain what gap this shader library fills.*

**What Problems Does This Library Solve?**

| Problem | Current Pain Point | Library Solution |
|---------|-------------------|------------------|
| [Problem 1] | [e.g., "Developers write shaders from scratch for each project"] | [e.g., "Pre-built, tested shader collection reduces development time by 70%"] |
| [Problem 2] | [e.g., "Inconsistent visual quality across different materials"] | [e.g., "Standardized lighting models ensure consistent appearance"] |
| [Problem 3] | [e.g., "Performance varies wildly between implementations"] | [e.g., "Optimized, profiled shaders with documented performance characteristics"] |
| [Problem 4] | [e.g., "Difficult to maintain and update shaders across projects"] | [e.g., "Centralized library with versioning and update procedures"] |

**Alternatives & Why They Fall Short:**

| Alternative Approach | Limitations | Our Advantage |
|---------------------|-------------|---------------|
| [Alt 1: "Write shaders from scratch"] | [Time-consuming, inconsistent, error-prone] | [Pre-built, tested, documented] |
| [Alt 2: "Use framework built-ins"] | [Limited customization, performance not guaranteed] | [Full control, optimized, extensible] |
| [Alt 3: "Third-party shader library X"] | [Specific limitation, e.g., "WebGL 2 only, GPL license"] | [WebGL 1/2 support, MIT license] |

### 1.3 Goals & Objectives

*Purpose: To define measurable success criteria for the library.*

**Primary Goals:**

- [ ] **Completeness:** Provide shaders for all common rendering scenarios
- [ ] **Performance:** All shaders meet performance targets on target hardware
- [ ] **Compatibility:** Support WebGL 1.0 and 2.0 with graceful fallbacks
- [ ] **Maintainability:** Code is clean, documented, and easy to update
- [ ] **Usability:** Simple API for integration, comprehensive examples

**Success Metrics:**

| Metric | Target | Measurement Method | Status |
|--------|--------|-------------------|--------|
| Shader Count | [50+ shaders] | [Count in library] | [Current: 32] |
| Code Coverage | [>90% tested] | [Unit + integration tests] | [Current: 78%] |
| Documentation | [100% documented] | [All shaders have spec docs] | [Current: 85%] |
| Performance | [60 FPS @ 1080p] | [Benchmark suite on GTX 1060] | [Current: 60 FPS] |
| Adoption | [Used in 10+ projects] | [Internal tracking] | [Current: 7] |

### 1.4 Target Audience

*Purpose: To identify who will use and contribute to this library.*

**Primary Users:**

- **Graphics Programmers:** Integrate shaders into rendering pipelines
- **Technical Artists:** Customize parameters and create material presets
- **Game Developers:** Use for real-time rendering in games
- **Web Developers:** Build 3D web experiences

**Technical Prerequisites:**

| Skill | Required Level | Notes |
|-------|---------------|-------|
| GLSL | Intermediate | Should understand shader basics |
| WebGL API | Intermediate | Familiar with texture binding, uniforms |
| Linear Algebra | Basic | Vectors, matrices, dot products |
| Rendering Concepts | Intermediate | Lighting models, texture mapping |
| [skill] | [level] | [notes] |

**Supported Frameworks:**

| Framework | Support Level | Notes |
|-----------|--------------|-------|
| Three.js | ✅ Full | Custom ShaderMaterial wrappers provided |
| Babylon.js | ✅ Full | BABYLON.ShaderMaterial helpers included |
| PlayCanvas | ⚠️ Community | Community-contributed integrations |
| Vanilla WebGL | ✅ Full | Direct WebGL usage examples |
| [framework] | [level] | [notes] |

---

## 2. Library Architecture

### 2.1 Organization Structure

**Directory Layout:**

```
shader-library/
├── README.md                   # Library overview and quick start
├── LICENSE                     # MIT License
├── CHANGELOG.md                # Version history
│
├── shaders/                    # Main shader source code
│   ├── core/                   # Core/fundamental shaders
│   │   ├── unlit.glsl
│   │   ├── basic_lit.glsl
│   │   └── pbr_standard.glsl
│   │
│   ├── materials/              # Material-specific shaders
│   │   ├── metal.glsl
│   │   ├── glass.glsl
│   │   ├── cloth.glsl
│   │   └── skin.glsl
│   │
│   ├── effects/                # Visual effects shaders
│   │   ├── bloom.glsl
│   │   ├── blur.glsl
│   │   ├── god_rays.glsl
│   │   └── volumetric_fog.glsl
│   │
│   ├── utilities/              # Helper/utility shaders
│   │   ├── depth_visualizer.glsl
│   │   ├── normal_visualizer.glsl
│   │   └── uv_checker.glsl
│   │
│   └── includes/               # Reusable shader chunks
│       ├── lighting/
│       │   ├── pbr_lighting.glsl
│       │   ├── blinn_phong.glsl
│       │   └── lambert.glsl
│       ├── math/
│       │   ├── common.glsl
│       │   ├── noise.glsl
│       │   └── color_space.glsl
│       └── utils/
│           ├── packing.glsl
│           └── sampling.glsl
│
├── specs/                      # Detailed specifications
│   ├── shader_program/
│   │   ├── pbr_standard_spec.md
│   │   └── ...
│   └── effects/
│       ├── bloom_effect_spec.md
│       └── ...
│
├── examples/                   # Integration examples
│   ├── three/
│   │   ├── basic_usage.html
│   │   └── advanced_materials.html
│   ├── babylon/
│   │   └── integration_example.html
│   └── vanilla/
│       └── minimal_example.html
│
├── tests/                      # Automated tests
│   ├── unit/
│   │   ├── shader_compilation_tests.js
│   │   └── uniform_binding_tests.js
│   └── visual/
│       ├── reference_images/
│       └── visual_regression_tests.js
│
├── tools/                      # Build and development tools
│   ├── shader_builder.js       # Combines includes into final shaders
│   ├── validator.js            # Validates shader syntax
│   └── optimizer.js            # Optimizes shader code
│
├── dist/                       # Built/compiled shaders
│   ├── shader-library.js       # All shaders bundled (ES6)
│   ├── shader-library.min.js   # Minified version
│   └── individual/             # Individual shader files
│       ├── pbr_standard.js
│       └── ...
│
└── docs/                       # Generated documentation
    ├── api/                    # API reference
    ├── guides/                 # Usage guides
    └── performance/            # Performance benchmarks
```

### 2.2 Shader Categories

**Core Shaders (Essential):**

| Shader Name | File | Purpose | Complexity | Status |
|------------|------|---------|------------|--------|
| Unlit | `shaders/core/unlit.glsl` | Simple unlit rendering | Trivial | ✅ Complete |
| Basic Lit | `shaders/core/basic_lit.glsl` | Blinn-Phong lighting | Low | ✅ Complete |
| PBR Standard | `shaders/core/pbr_standard.glsl` | Physically-based rendering | Medium | ✅ Complete |
| [shader_name] | [file_path] | [purpose] | [complexity] | [status] |

**Material Shaders (Domain-Specific):**

| Shader Name | File | Material Type | Key Features | Status |
|------------|------|---------------|--------------|--------|
| Metal | `shaders/materials/metal.glsl` | Metallic surfaces | Anisotropic reflection, roughness | ✅ Complete |
| Glass | `shaders/materials/glass.glsl` | Transparent materials | Refraction, Fresnel | ✅ Complete |
| Cloth | `shaders/materials/cloth.glsl` | Fabric surfaces | Subsurface scattering approx | 🚧 In Progress |
| Skin | `shaders/materials/skin.glsl` | Character skin | Subsurface scattering | 📋 Planned |
| [shader_name] | [file_path] | [type] | [features] | [status] |

**Effect Shaders (Post-Processing):**

| Shader Name | File | Effect Type | Performance | Status |
|------------|------|-------------|-------------|--------|
| Bloom | `shaders/effects/bloom.glsl` | Glow effect | Medium | ✅ Complete |
| Blur (Gaussian) | `shaders/effects/blur.glsl` | Image blur | Medium | ✅ Complete |
| God Rays | `shaders/effects/god_rays.glsl` | Volumetric light shafts | High | ✅ Complete |
| Volumetric Fog | `shaders/effects/volumetric_fog.glsl` | Atmospheric fog | Very High | ✅ Complete |
| [shader_name] | [file_path] | [type] | [performance] | [status] |

**Utility Shaders (Debugging/Tools):**

| Shader Name | File | Purpose | When to Use |
|------------|------|---------|-------------|
| Depth Visualizer | `shaders/utilities/depth_visualizer.glsl` | Visualize depth buffer | Debugging depth issues |
| Normal Visualizer | `shaders/utilities/normal_visualizer.glsl` | Visualize normals as colors | Debugging normal maps |
| UV Checker | `shaders/utilities/uv_checker.glsl` | Visualize texture coordinates | Debugging UV mapping |
| [shader_name] | [file_path] | [purpose] | [when_to_use] |

### 2.3 Shader Include System

**Include Hierarchy:**

```
Core Includes (Used by all shaders)
├── includes/math/common.glsl           # Basic math utilities
│   ├── Functions: saturate(), remap(), smoothstep01()
│   └── Constants: PI, TAU, EPSILON
│
├── includes/math/color_space.glsl      # Color space conversions
│   ├── Functions: sRGBToLinear(), linearToSRGB(), RGBtoHSV()
│   └── Used by: Most shaders for correct color handling
│
└── includes/utils/packing.glsl         # Data packing/unpacking
    ├── Functions: packNormal(), unpackNormal(), encodeRGBM()
    └── Used by: Shaders with limited texture formats

Lighting Includes (Used by lit shaders)
├── includes/lighting/pbr_lighting.glsl # PBR lighting model
│   ├── Functions: distributionGGX(), geometrySmith(), fresnelSchlick()
│   └── Used by: PBR Standard, Metal, Glass shaders
│
├── includes/lighting/blinn_phong.glsl  # Blinn-Phong model
│   ├── Functions: calculateBlinnPhong()
│   └── Used by: Basic Lit, legacy shaders
│
└── includes/lighting/lambert.glsl      # Lambert diffuse
    ├── Functions: lambertDiffuse()
    └── Used by: Simple lit shaders

Specialized Includes
├── includes/math/noise.glsl            # Procedural noise functions
│   ├── Functions: perlinNoise2D(), simplexNoise3D(), fbm()
│   └── Used by: Volumetric effects, procedural textures
│
└── includes/utils/sampling.glsl        # Texture sampling helpers
    ├── Functions: sampleNormalMap(), sampleTriplanar()
    └── Used by: Material shaders with normal maps
```

**Include Usage Example:**

```glsl
// PBR Standard Fragment Shader
#version 300 es
precision highp float;

// Include core utilities
#include "includes/math/common.glsl"
#include "includes/math/color_space.glsl"

// Include lighting models
#include "includes/lighting/pbr_lighting.glsl"

// Include texture utilities
#include "includes/utils/sampling.glsl"

// Shader-specific code
in vec3 v_worldPosition;
in vec3 v_worldNormal;
in vec2 v_texCoord;

uniform sampler2D u_albedoMap;
uniform sampler2D u_normalMap;
uniform sampler2D u_roughnessMap;

out vec4 fragColor;

void main() {
  // Use included functions
  vec3 albedo = sRGBToLinear(texture(u_albedoMap, v_texCoord).rgb);
  vec3 normal = sampleNormalMap(u_normalMap, v_texCoord, v_worldNormal);
  float roughness = texture(u_roughnessMap, v_texCoord).r;
  
  // Use PBR lighting
  vec3 lighting = calculatePBR(albedo, normal, roughness, ...);
  
  fragColor = vec4(linearToSRGB(lighting), 1.0);
}
```

### 2.4 Shader Variants & Configuration

**Configuration System:**

Each shader supports compile-time and runtime configuration through defines and uniforms.

**Compile-Time Configuration (Defines):**

```glsl
// Example: PBR Standard Shader Variants

// Feature toggles
#define USE_NORMAL_MAP 1          // 0 = disabled, 1 = enabled
#define USE_ROUGHNESS_MAP 1
#define USE_METALLIC_MAP 1
#define USE_AO_MAP 1
#define USE_EMISSIVE_MAP 0

// Quality settings
#define LIGHT_COUNT 4             // 1-8 lights supported
#define SHADOW_QUALITY 2          // 0=off, 1=low, 2=medium, 3=high
#define REFLECTION_QUALITY 1      // 0=off, 1=simple, 2=accurate

// Platform-specific
#define USE_HIGHP 1               // Use high precision (desktop)
#define USE_DERIVATIVES 1         // Use dFdx/dFdy (requires extension)
```

**Runtime Configuration (Uniforms):**

```javascript
// Example: Shader configuration API
const shader = shaderLibrary.get('pbr_standard', {
  // Compile-time configuration
  defines: {
    USE_NORMAL_MAP: true,
    USE_ROUGHNESS_MAP: true,
    LIGHT_COUNT: 3,
    SHADOW_QUALITY: 2
  }
});

// Runtime configuration
shader.setUniforms({
  albedoColor: [1.0, 0.8, 0.6],
  roughness: 0.5,
  metallic: 0.0,
  lightPositions: [
    [10, 10, 10],
    [-10, 10, -10],
    [0, 20, 0]
  ]
});
```

**Variant Management:**

| Variant | Use Case | Defines | Performance |
|---------|----------|---------|-------------|
| **Minimal** | Mobile low-end | All features off | Very fast (< 1ms) |
| **Basic** | Mobile mid-range | Normal map only | Fast (1-2ms) |
| **Standard** | Desktop | Normal + roughness + AO | Medium (2-4ms) |
| **Ultra** | High-end desktop | All features | Slower (4-6ms) |

---

## 3. API & Integration

### 3.1 Shader Loading System

**Core API:**

```javascript
/**
 * Shader Library - Main API
 * Provides easy access to all shaders with automatic dependency resolution
 * 
 * @author Craig
 * @version 1.0
 */

class ShaderLibrary {
  /**
   * Load a shader from the library
   * 
   * @param {string} shaderName - Name of the shader (e.g., 'pbr_standard')
   * @param {Object} options - Compilation options
   * @param {Object} options.defines - Compile-time defines
   * @param {boolean} options.includeSource - Return source code
   * @returns {Shader} Compiled shader object
   */
  get(shaderName, options = {}) {
    // Implementation
  }
  
  /**
   * List all available shaders
   * 
   * @param {string} category - Optional category filter
   * @returns {Array<ShaderInfo>} Array of shader metadata
   */
  list(category = null) {
    // Implementation
  }
  
  /**
   * Register a custom shader
   * 
   * @param {string} name - Shader name
   * @param {Object} shaderDefinition - Shader source and metadata
   */
  register(name, shaderDefinition) {
    // Implementation
  }
}
```

**Usage Examples:**

```javascript
// Example 1: Basic usage
const library = new ShaderLibrary();
const pbrShader = library.get('pbr_standard');

// Example 2: With configuration
const glasShader = library.get('glass', {
  defines: {
    USE_REFRACTION: true,
    QUALITY: 'high'
  }
});

// Example 3: List shaders by category
const materialShaders = library.list('materials');
console.log(materialShaders);
// Output: ['metal', 'glass', 'cloth', 'skin']

// Example 4: Register custom shader
library.register('my_custom_shader', {
  vertexShader: vertexSource,
  fragmentShader: fragmentSource,
  uniforms: { /* ... */ },
  attributes: { /* ... */ }
});
```

### 3.2 Framework Integration

#### Three.js Integration

```javascript
/**
 * Three.js integration for Shader Library
 * Provides ShaderMaterial wrappers for all library shaders
 */

import * as THREE from 'three';
import { ShaderLibrary } from './shader-library.js';

class ThreeShaderLibrary extends ShaderLibrary {
  /**
   * Create a Three.js ShaderMaterial from library shader
   * 
   * @param {string} shaderName - Name of shader
   * @param {Object} options - Material options
   * @returns {THREE.ShaderMaterial} Ready-to-use material
   */
  createMaterial(shaderName, options = {}) {
    const shader = this.get(shaderName, options);
    
    return new THREE.ShaderMaterial({
      uniforms: THREE.UniformsUtils.clone(shader.uniforms),
      vertexShader: shader.vertexShader,
      fragmentShader: shader.fragmentShader,
      transparent: options.transparent || false,
      side: options.side || THREE.FrontSide
    });
  }
}

// Usage
const library = new ThreeShaderLibrary();
const material = library.createMaterial('pbr_standard', {
  defines: { USE_NORMAL_MAP: true }
});

const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);
```

#### Babylon.js Integration

```javascript
/**
 * Babylon.js integration for Shader Library
 */

import { ShaderLibrary } from './shader-library.js';
import * as BABYLON from 'babylonjs';

class BabylonShaderLibrary extends ShaderLibrary {
  /**
   * Create a Babylon.js ShaderMaterial
   */
  createMaterial(shaderName, scene, options = {}) {
    const shader = this.get(shaderName, options);
    
    const shaderMaterial = new BABYLON.ShaderMaterial(
      shaderName,
      scene,
      {
        vertex: shader.vertexShader,
        fragment: shader.fragmentShader
      },
      {
        attributes: Object.keys(shader.attributes),
        uniforms: Object.keys(shader.uniforms)
      }
    );
    
    return shaderMaterial;
  }
}
```

### 3.3 Uniform Management

**Uniform Typing System:**

```javascript
/**
 * Uniform definition with type checking and validation
 */
const uniformDefinitions = {
  'pbr_standard': {
    // Material properties
    u_albedoColor: {
      type: 'vec3',
      default: [1.0, 1.0, 1.0],
      range: [0, 1],
      description: 'Base color of material'
    },
    
    u_roughness: {
      type: 'float',
      default: 0.5,
      range: [0, 1],
      description: 'Surface roughness (0 = smooth, 1 = rough)'
    },
    
    u_metallic: {
      type: 'float',
      default: 0.0,
      range: [0, 1],
      description: 'Metallic factor (0 = dielectric, 1 = metal)'
    },
    
    // Textures
    u_albedoMap: {
      type: 'sampler2D',
      default: null,
      optional: true,
      description: 'Albedo texture map'
    },
    
    // Lighting
    u_lightPositions: {
      type: 'vec3[]',
      default: [[0, 10, 0]],
      maxLength: 8,
      description: 'Array of light positions'
    }
  }
};

/**
 * Validate uniform value against definition
 */
function validateUniform(name, value, definition) {
  if (definition.type === 'float' && definition.range) {
    if (value < definition.range[0] || value > definition.range[1]) {
      throw new Error(`${name} out of range: ${value} not in [${definition.range}]`);
    }
  }
  
  if (definition.type.endsWith('[]') && definition.maxLength) {
    if (value.length > definition.maxLength) {
      throw new Error(`${name} array too long: ${value.length} > ${definition.maxLength}`);
    }
  }
  
  return true;
}
```

---

## 4. Quality Assurance & Testing

### 4.1 Testing Strategy

**Test Categories:**

| Test Type | Purpose | Frequency | Tools |
|-----------|---------|-----------|-------|
| **Unit Tests** | Shader compilation, uniform binding | Every commit | Jest, custom GLSL validator |
| **Integration Tests** | Framework integration works | Daily | Automated browser tests |
| **Visual Regression** | No visual changes between versions | Every release | Puppeteer, image diff |
| **Performance Tests** | Performance within targets | Weekly | GPU profiler, benchmarks |
| **Cross-Browser Tests** | Works on all browsers | Every release | BrowserStack, Playwright |

**Automated Test Suite:**

```javascript
/**
 * Shader compilation tests
 * Ensures all shaders compile without errors
 */
describe('Shader Compilation', () => {
  const library = new ShaderLibrary();
  const shaders = library.list();
  
  shaders.forEach(shaderName => {
    test(`${shaderName} compiles without errors`, () => {
      const shader = library.get(shaderName);
      expect(shader.compileStatus).toBe('success');
      expect(shader.errors).toHaveLength(0);
    });
    
    test(`${shaderName} has all required uniforms`, () => {
      const shader = library.get(shaderName);
      const requiredUniforms = getRequiredUniforms(shaderName);
      
      requiredUniforms.forEach(uniform => {
        expect(shader.uniforms).toHaveProperty(uniform);
      });
    });
  });
});

/**
 * Visual regression tests
 * Compare rendered output to reference images
 */
describe('Visual Regression', () => {
  test('PBR Standard matches reference', async () => {
    const rendered = await renderShader('pbr_standard', testScene);
    const reference = await loadReferenceImage('pbr_standard_reference.png');
    const similarity = compareImages(rendered, reference);
    
    expect(similarity).toBeGreaterThan(0.95);  // 95% SSIM
  });
});
```

### 4.2 Performance Benchmarking

**Benchmark Suite:**

```javascript
/**
 * Performance benchmark for all shaders
 * Measures frame time and identifies bottlenecks
 */
class ShaderBenchmark {
  async runBenchmark(shaderName, scene) {
    const shader = library.get(shaderName);
    const results = {
      shaderName,
      measurements: []
    };
    
    // Warmup
    for (let i = 0; i < 100; i++) {
      renderFrame(shader, scene);
    }
    
    // Measure 1000 frames
    for (let i = 0; i < 1000; i++) {
      const startTime = performance.now();
      renderFrame(shader, scene);
      const endTime = performance.now();
      results.measurements.push(endTime - startTime);
    }
    
    // Calculate statistics
    results.stats = {
      avg: average(results.measurements),
      median: median(results.measurements),
      p95: percentile(results.measurements, 0.95),
      p99: percentile(results.measurements, 0.99)
    };
    
    return results;
  }
}

// Run benchmarks for all shaders
const benchmark = new ShaderBenchmark();
const results = await benchmark.runAll();
generateBenchmarkReport(results);
```

**Performance Targets:**

| Shader | Complexity | Target Frame Time | Acceptable | Status |
|--------|-----------|------------------|------------|--------|
| Unlit | Trivial | < 0.5ms | < 1ms | ✅ Pass |
| Basic Lit | Low | < 2ms | < 3ms | ✅ Pass |
| PBR Standard | Medium | < 4ms | < 6ms | ✅ Pass |
| Glass (with refraction) | High | < 8ms | < 12ms | ⚠️ Borderline |
| Volumetric Fog | Very High | < 5ms | < 8ms | ✅ Pass |

### 4.3 Code Quality Standards

**Shader Code Guidelines:**

```glsl
/**
 * Shader code style guide
 * All library shaders must follow these conventions
 */

// 1. File header with metadata
/**
 * PBR Standard Shader
 * Version: 1.2.0
 * Author: Craig
 * Last Modified: 2025-11-11
 * 
 * Description: Physically-based rendering shader with support for
 *              normal maps, roughness/metallic workflow, and multiple lights.
 * 
 * Change History:
 * v1.2.0 - Added support for AO maps
 * v1.1.0 - Optimized light loop performance
 * v1.0.0 - Initial implementation
 */

// 2. Precision declarations at top
precision highp float;

// 3. Grouped declarations with comments
// === Attributes ===
attribute vec3 a_position;
attribute vec3 a_normal;
attribute vec2 a_texCoord;

// === Uniforms ===
// Transform matrices
uniform mat4 u_modelMatrix;
uniform mat4 u_viewMatrix;
uniform mat4 u_projectionMatrix;

// Material properties
uniform vec3 u_albedoColor;
uniform float u_roughness;
uniform float u_metallic;

// 4. Descriptive function names
/**
 * Calculate Blinn-Phong specular component
 * 
 * @param {vec3} normal - Surface normal (normalized)
 * @param {vec3} lightDir - Direction to light (normalized)
 * @param {vec3} viewDir - Direction to viewer (normalized)
 * @param {float} shininess - Specular power
 * @return {float} Specular intensity [0, 1]
 */
float calculateBlinnPhongSpecular(vec3 normal, vec3 lightDir, 
                                  vec3 viewDir, float shininess) {
  vec3 halfDir = normalize(lightDir + viewDir);
  return pow(max(dot(normal, halfDir), 0.0), shininess);
}

// 5. Use constants instead of magic numbers
const float PI = 3.14159265359;
const float EPSILON = 0.0001;

// 6. Clear main() logic with comments
void main() {
  // Transform vertex to clip space
  vec4 worldPos = u_modelMatrix * vec4(a_position, 1.0);
  gl_Position = u_projectionMatrix * u_viewMatrix * worldPos;
  
  // Pass data to fragment shader
  v_worldPosition = worldPos.xyz;
  v_worldNormal = normalize(mat3(u_modelMatrix) * a_normal);
  v_texCoord = a_texCoord;
}
```

---

## 5. Documentation & Support

### 5.1 Documentation Structure

**Documentation Hierarchy:**

```
docs/
├── README.md                       # Library overview
├── getting-started/
│   ├── installation.md
│   ├── first-shader.md
│   └── integration-guide.md
│
├── api-reference/
│   ├── shader-library-api.md      # Core API
│   ├── uniform-reference.md       # All uniforms
│   └── configuration.md           # Defines and options
│
├── shader-catalog/
│   ├── core/
│   │   ├── unlit.md
│   │   ├── basic-lit.md
│   │   └── pbr-standard.md
│   ├── materials/
│   │   ├── metal.md
│   │   ├── glass.md
│   │   └── cloth.md
│   └── effects/
│       ├── bloom.md
│       └── volumetric-fog.md
│
├── guides/
│   ├── creating-custom-shaders.md
│   ├── performance-optimization.md
│   ├── debugging-shaders.md
│   └── best-practices.md
│
├── performance/
│   ├── benchmarks.md
│   └── optimization-tips.md
│
└── contributing/
    ├── contribution-guide.md
    ├── code-standards.md
    └── testing-guide.md
```

### 5.2 Example Documentation Page

**Template for Shader Documentation:**

````markdown
# [Shader Name]

## Overview

**Category:** [Core | Material | Effect | Utility]  
**Complexity:** [Trivial | Low | Medium | High | Very High]  
**WebGL Version:** [1.0 | 2.0 | Both]  
**Status:** [Stable | Beta | Experimental | Deprecated]

[Brief description of what the shader does]

## Quick Start

```javascript
const library = new ShaderLibrary();
const shader = library.get('[shader_name]');

// Configure uniforms
shader.setUniform('parameterName', value);
```

## Parameters

### Uniforms

| Name | Type | Default | Range | Description |
|------|------|---------|-------|-------------|
| `u_param1` | `float` | 0.5 | [0, 1] | [Description] |
| `u_param2` | `vec3` | [1,1,1] | [0, 1] | [Description] |

### Defines

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `FEATURE_X` | boolean | 1 | Enable feature X |

## Performance

| Hardware | Resolution | Frame Time | Notes |
|----------|------------|------------|-------|
| GTX 1060 | 1080p | 2.3ms | Recommended settings |

## Examples

### Basic Usage
```javascript
[Example code]
```

### Advanced Usage
```javascript
[Example code]
```

## Visual Examples

![Example 1](images/example1.png)
![Example 2](images/example2.png)

## Notes

- [Important note 1]
- [Important note 2]

## See Also

- [Related shader 1]
- [Related shader 2]
````

---

## 6. Maintenance & Evolution

### 6.1 Versioning Strategy

**Semantic Versioning:** `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking API changes
- **MINOR:** New shaders or features (backward compatible)
- **PATCH:** Bug fixes, performance improvements

**Version History:**

| Version | Date | Changes | Breaking |
|---------|------|---------|----------|
| 1.2.0 | 2025-11-01 | Added cloth shader, improved PBR | No |
| 1.1.5 | 2025-10-15 | Fixed normal map sampling bug | No |
| 1.1.0 | 2025-09-20 | Added glass and metal shaders | No |
| 1.0.0 | 2025-08-01 | Initial release | N/A |

### 6.2 Contribution Guidelines

**How to Contribute:**

1. **Fork the repository**
2. **Create feature branch:** `git checkout -b feature/new-shader`
3. **Follow code standards** (see shader_code_guidelines.md)
4. **Write tests** for your shader
5. **Update documentation**
6. **Submit pull request**

**Pull Request Template:**

```markdown
## Description
[What does this PR add/fix/change?]

## Type of Change
- [ ] New shader
- [ ] Bug fix
- [ ] Performance improvement
- [ ] Documentation update

## Testing
- [ ] Shader compiles without errors
- [ ] All existing tests still pass
- [ ] New tests added (if applicable)
- [ ] Visual output verified

## Performance Impact
[Describe performance characteristics]

## Screenshots/Examples
[If visual change, include before/after]

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### 6.3 Deprecation Policy

**Deprecation Process:**

1. **Announce:** Mark shader as deprecated in documentation
2. **Migration Guide:** Provide clear upgrade path
3. **Warning Period:** Minimum 6 months before removal
4. **Console Warnings:** Warn users when deprecated shader used
5. **Removal:** Remove in next major version

---

## 7. Appendices

### Appendix A: Complete Shader List

[Comprehensive table of all shaders with metadata]

### Appendix B: Performance Benchmark Results

[Detailed performance data for all shaders]

### Appendix C: License & Credits

**License:** MIT License

**Credits:**
- [Contributor 1] - Core PBR shaders
- [Contributor 2] - Effect shaders
- [External library] - Noise functions

---

**Document End**

*For questions or contributions, visit [repository URL] or contact [maintainer email]*
