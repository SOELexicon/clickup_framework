# Mermaid Layout Types Explained

## Important Note

Mermaid doesn't expose layout algorithms (elk, tidy-tree, cose-bilkent, dagre) as user-selectable options. These are internal layout engines that Mermaid uses automatically based on the diagram type and structure.

However, different diagram types and structures will naturally use different layout algorithms:

## Layout Algorithms Used by Mermaid

### 1. **Dagre** (Default for flowcharts)
- Used for: `graph TD`, `graph LR`, `graph TB`, `graph RL`
- Best for: Flowcharts, hierarchical structures, layered diagrams
- Characteristics: Top-to-bottom or left-to-right flow, layered layout

### 2. **ELK** (Eclipse Layout Kernel)
- Used for: Complex hierarchical graphs, when Dagre needs more sophisticated layout
- Best for: Large, complex structures with many nodes
- Characteristics: Better handling of complex hierarchies

### 3. **Tidy Tree**
- Used for: Tree structures, organizational charts
- Best for: Pure tree hierarchies (one parent, multiple children)
- Characteristics: Optimized tree layout, minimal crossing edges

### 4. **Cose Bilkent**
- Used for: Force-directed layouts, network graphs
- Best for: Non-hierarchical graphs, relationship networks
- Characteristics: Nodes positioned based on force simulation

## How to Influence Layout

While you can't directly select a layout algorithm, you can influence the layout by:

1. **Diagram Type**: Use `graph TD` for top-down, `graph LR` for left-right
2. **Node Connections**: How you connect nodes affects layout
3. **Subgraphs**: Using subgraphs can create different visual groupings
4. **Direction**: TD (top-down), LR (left-right), TB (top-bottom), RL (right-left)

## Examples Generated

The `layout_examples.md` file contains examples that showcase different visual layouts:
- **Example 1**: Complex hierarchical structure (uses Dagre/ELK)
- **Example 2**: Tree structure (uses Tidy Tree style)
- **Example 3**: Network graph (uses Cose Bilkent style)
- **Example 4**: Flowchart (uses Dagre)

All examples use:
- **Theme**: Dark
- **Background**: Black
- **Output**: SVG files in `layout_images/` folder

## Default Configuration Updated

The framework now defaults to:
- **Background**: Black (changed from transparent)
- **Theme**: Dark
- This applies to all mermaid diagram generation

