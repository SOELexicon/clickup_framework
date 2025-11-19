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
        return f.read()


def get_fire_shaders() -> tuple[str, str]:
    """
    Load the fire effect shaders (vertex and fragment).

    Returns:
        Tuple of (vertex_shader_source, fragment_shader_source)
    """
    vertex_shader = load_shader("fire_vertex")
    fragment_shader = load_shader("fire_fragment")
    return vertex_shader, fragment_shader
