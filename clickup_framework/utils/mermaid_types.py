"""
Mermaid Diagram Types Reference

Provides constants and utilities for working with different mermaid diagram types.
"""

from typing import Dict, List
from enum import Enum


class MermaidDiagramType(Enum):
    """Enumeration of mermaid diagram types."""

    # Flowcharts and Graphs
    GRAPH_TD = "graph TD"  # Top-Down graph
    GRAPH_TB = "graph TB"  # Top-Bottom graph (alias for TD)
    GRAPH_BT = "graph BT"  # Bottom-Top graph
    GRAPH_RL = "graph RL"  # Right-Left graph
    GRAPH_LR = "graph LR"  # Left-Right graph
    FLOWCHART_TD = "flowchart TD"  # Modern flowchart syntax
    FLOWCHART_TB = "flowchart TB"
    FLOWCHART_BT = "flowchart BT"
    FLOWCHART_RL = "flowchart RL"
    FLOWCHART_LR = "flowchart LR"

    # Sequence Diagrams
    SEQUENCE_DIAGRAM = "sequenceDiagram"

    # Class Diagrams
    CLASS_DIAGRAM = "classDiagram"

    # State Diagrams
    STATE_DIAGRAM = "stateDiagram"
    STATE_DIAGRAM_V2 = "stateDiagram-v2"

    # Entity Relationship Diagrams
    ER_DIAGRAM = "erDiagram"

    # User Journey
    JOURNEY = "journey"

    # Gantt Charts
    GANTT = "gantt"

    # Pie Charts
    PIE = "pie"

    # Requirement Diagrams
    REQUIREMENT_DIAGRAM = "requirementDiagram"

    # Gitgraph
    GITGRAPH = "gitGraph"

    # C4 Diagrams
    C4_CONTEXT = "C4Context"
    C4_CONTAINER = "C4Container"
    C4_COMPONENT = "C4Component"
    C4_DYNAMIC = "C4Dynamic"
    C4_DEPLOYMENT = "C4Deployment"

    # Mindmap
    MINDMAP = "mindmap"

    # Timeline
    TIMELINE = "timeline"

    # Quadrant Chart
    QUADRANT_CHART = "quadrantChart"

    # XY Chart
    XY_CHART = "xychart-beta"


# Diagram type metadata
DIAGRAM_TYPE_INFO: Dict[str, Dict[str, str]] = {
    "graph": {
        "name": "Flowchart/Graph",
        "description": "Flowcharts and directed graphs with various orientations",
        "example": "graph TD\n    A[Start] --> B[Process]\n    B --> C[End]"
    },
    "flowchart": {
        "name": "Flowchart (Modern)",
        "description": "Modern flowchart syntax with enhanced features",
        "example": "flowchart LR\n    A[Start] --> B{Decision}\n    B -->|Yes| C[Action 1]\n    B -->|No| D[Action 2]"
    },
    "sequenceDiagram": {
        "name": "Sequence Diagram",
        "description": "Shows interactions between actors and objects over time",
        "example": "sequenceDiagram\n    participant A as Alice\n    participant B as Bob\n    A->>B: Hello Bob!\n    B->>A: Hi Alice!"
    },
    "classDiagram": {
        "name": "Class Diagram",
        "description": "UML class diagrams showing classes and relationships",
        "example": "classDiagram\n    class Animal {\n        +name: string\n        +makeSound()\n    }\n    Animal <|-- Dog"
    },
    "stateDiagram": {
        "name": "State Diagram",
        "description": "State machines and transitions",
        "example": "stateDiagram-v2\n    [*] --> Active\n    Active --> Inactive\n    Inactive --> [*]"
    },
    "erDiagram": {
        "name": "Entity Relationship Diagram",
        "description": "Database entity relationships",
        "example": "erDiagram\n    CUSTOMER ||--o{ ORDER : places\n    ORDER ||--|{ LINE-ITEM : contains"
    },
    "journey": {
        "name": "User Journey",
        "description": "User journey maps showing tasks and sentiment",
        "example": "journey\n    title My working day\n    section Go to work\n      Make coffee: 5: Me\n      Go upstairs: 3: Me"
    },
    "gantt": {
        "name": "Gantt Chart",
        "description": "Project timeline and task scheduling",
        "example": "gantt\n    title Project Schedule\n    section Phase 1\n    Task 1: 2024-01-01, 7d\n    Task 2: 2024-01-08, 5d"
    },
    "pie": {
        "name": "Pie Chart",
        "description": "Pie charts for showing proportions",
        "example": 'pie title Pets\n    "Dogs" : 386\n    "Cats" : 85\n    "Rats" : 15'
    },
    "gitGraph": {
        "name": "Git Graph",
        "description": "Git branching and merging visualization",
        "example": "gitGraph\n    commit\n    branch develop\n    checkout develop\n    commit\n    checkout main\n    merge develop"
    },
    "mindmap": {
        "name": "Mindmap",
        "description": "Hierarchical mindmaps",
        "example": "mindmap\n  root((mindmap))\n    Origins\n      Long history\n    Research\n      On effectiveness"
    },
    "timeline": {
        "name": "Timeline",
        "description": "Historical timelines",
        "example": "timeline\n    title History of Project\n    2021 : Started\n    2022 : Launched\n    2023 : Scaled"
    },
    "quadrantChart": {
        "name": "Quadrant Chart",
        "description": "2x2 matrix for categorization",
        "example": "quadrantChart\n    title Reach and engagement\n    x-axis Low Reach --> High Reach\n    y-axis Low Engagement --> High Engagement"
    }
}


def detect_diagram_type(mermaid_code: str) -> str:
    """
    Detect the diagram type from mermaid code.

    Args:
        mermaid_code: Mermaid diagram code

    Returns:
        Detected diagram type or 'unknown'
    """
    lines = mermaid_code.strip().split('\n')
    if not lines:
        return 'unknown'

    first_line = lines[0].strip().lower()

    # Check for each diagram type
    for diagram_type in MermaidDiagramType:
        if first_line.startswith(diagram_type.value.lower()):
            return diagram_type.value

    return 'unknown'


def get_supported_diagram_types() -> List[str]:
    """
    Get list of all supported mermaid diagram types.

    Returns:
        List of diagram type identifiers
    """
    return [dt.value for dt in MermaidDiagramType]


def validate_mermaid_code(mermaid_code: str) -> bool:
    """
    Validate if mermaid code starts with a recognized diagram type.

    Args:
        mermaid_code: Mermaid diagram code

    Returns:
        True if diagram type is recognized
    """
    diagram_type = detect_diagram_type(mermaid_code)
    return diagram_type != 'unknown'


def get_diagram_info(diagram_type: str) -> Dict[str, str]:
    """
    Get metadata about a diagram type.

    Args:
        diagram_type: Diagram type identifier

    Returns:
        Dictionary with name, description, and example
    """
    # Handle graph variants
    if diagram_type.startswith('graph '):
        return DIAGRAM_TYPE_INFO.get('graph', {})
    if diagram_type.startswith('flowchart '):
        return DIAGRAM_TYPE_INFO.get('flowchart', {})

    return DIAGRAM_TYPE_INFO.get(diagram_type, {
        'name': 'Unknown',
        'description': 'Unknown diagram type',
        'example': ''
    })
