"""Shader loader for WebGL visualizations."""

from pathlib import Path


def load_shader(shader_name: str) -> str:
    """
    Load a GLSL shader file from the shaders directory.

    Args:
        shader_name: Name of the shader file (without .glsl extension)

    Returns:
        Shader source code as string
    """
    shader_dir = Path(__file__).parent / "shaders"
    shader_file = shader_dir / f"{shader_name}.glsl"

    if not shader_file.exists():
        raise FileNotFoundError(f"Shader file not found: {shader_file}")

    with open(shader_file, 'r', encoding='utf-8') as f:
        # Simple replace for comments to reduce shader size
        lines = [line for line in f.readlines() if not line.strip().startswith("//")]
        return "".join(lines)


def get_all_shaders() -> dict:
    """
    Loads all available shader effects.

    Each effect uses a common vertex shader but a unique fragment shader.

    Returns:
        A dictionary where keys are effect names and values are dicts
        containing 'vertex' and 'fragment' shader source code.
    """
    shaders = {}
    effects = ["fire", "pulse", "glow", "ghost"]
    
    # All effects can reuse the same powerful vertex shader
    vertex_shader = load_shader("fire_vertex")

    for effect in effects:
        try:
            fragment_shader = load_shader(f"{effect}_fragment")
            shaders[effect] = {
                "vertex": vertex_shader,
                "fragment": fragment_shader,
            }
        except FileNotFoundError:
            print(f"Warning: Fragment shader for effect '{effect}' not found. Skipping.")

    return shaders
