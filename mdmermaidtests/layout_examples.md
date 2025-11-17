# Mermaid Layout Examples

This document demonstrates different graph layout types in Mermaid with black background.

## 1. ELK (Eclipse Layout Kernel)

ELK layout is good for hierarchical structures and complex graphs.

```mermaid
%%{init: {'theme':'dark', 'themeVariables': {'primaryColor':'#ff6b6b','primaryTextColor':'#fff','primaryBorderColor':'#7C0000','lineColor':'#F8B229','secondaryColor':'#006100','tertiaryColor':'#fff'}}}%%
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[Sub-process A]
    C --> F[Sub-process B]
    D --> G[Sub-process C]
    E --> H[End]
    F --> H
    G --> H
```

## 2. Tidy Tree Layout

Tidy tree is optimized for hierarchical tree structures.

```mermaid
%%{init: {'theme':'dark', 'themeVariables': {'primaryColor':'#ff6b6b','primaryTextColor':'#fff','primaryBorderColor':'#7C0000','lineColor':'#F8B229','secondaryColor':'#006100','tertiaryColor':'#fff'}}}%%
graph TD
    Root[Root Node] --> Child1[Child 1]
    Root --> Child2[Child 2]
    Root --> Child3[Child 3]
    Child1 --> Grandchild1[Grandchild 1]
    Child1 --> Grandchild2[Grandchild 2]
    Child2 --> Grandchild3[Grandchild 3]
    Child3 --> Grandchild4[Grandchild 4]
    Child3 --> Grandchild5[Grandchild 5]
    Grandchild1 --> Leaf1[Leaf 1]
    Grandchild2 --> Leaf2[Leaf 2]
```

## 3. Cose Bilkent Layout

Cose Bilkent is a force-directed layout good for network graphs.

```mermaid
%%{init: {'theme':'dark', 'themeVariables': {'primaryColor':'#ff6b6b','primaryTextColor':'#fff','primaryBorderColor':'#7C0000','lineColor':'#F8B229','secondaryColor':'#006100','tertiaryColor':'#fff'}}}%%
graph LR
    A[Node A] --- B[Node B]
    A --- C[Node C]
    A --- D[Node D]
    B --- E[Node E]
    B --- F[Node F]
    C --- G[Node G]
    D --- H[Node H]
    E --- I[Node I]
    F --- J[Node J]
    G --- K[Node K]
    H --- L[Node L]
    I --- M[Node M]
    J --- N[Node N]
```

## 4. Dagre Layout

Dagre creates layered/hierarchical layouts, good for flowcharts and DAGs.

```mermaid
%%{init: {'theme':'dark', 'themeVariables': {'primaryColor':'#ff6b6b','primaryTextColor':'#fff','primaryBorderColor':'#7C0000','lineColor':'#F8B229','secondaryColor':'#006100','tertiaryColor':'#fff'}}}%%
graph TB
    Start([Start]) --> Input[Input Data]
    Input --> Validate{Validate?}
    Validate -->|Valid| Process[Process Data]
    Validate -->|Invalid| Error[Error Handler]
    Process --> Transform[Transform]
    Transform --> Output[Output Result]
    Error --> Log[Log Error]
    Log --> End([End])
    Output --> End
```

## Layout Comparison

Each layout has different characteristics:
- **ELK**: Best for complex hierarchical structures
- **Tidy Tree**: Optimized for tree structures
- **Cose Bilkent**: Force-directed, good for networks
- **Dagre**: Layered layout, good for flowcharts

