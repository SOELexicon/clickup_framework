# Test Document with Mermaid Diagrams

This is a test document to verify mermaid diagram generation from markdown.

## Flowchart Example

Here's a simple flowchart:

```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
```

## Sequence Diagram Example

Here's a sequence diagram:

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database
    
    User->>API: Request Data
    API->>Database: Query
    Database-->>API: Results
    API-->>User: Response
```

## Gantt Chart Example

Here's a Gantt chart:

```mermaid
gantt
    title Project Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1
    Task 1           :a1, 2024-01-01, 30d
    Task 2           :after a1, 20d
    section Phase 2
    Task 3           :2024-02-01, 12d
    Task 4           :24d
```

## Class Diagram Example

Here's a class diagram:

```mermaid
classDiagram
    class Animal {
        +String name
        +int age
        +eat()
        +sleep()
    }
    class Dog {
        +String breed
        +bark()
    }
    class Cat {
        +int lives
        +meow()
    }
    Animal <|-- Dog
    Animal <|-- Cat
```

## State Diagram Example

Here's a state diagram:

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing: Start
    Processing --> Completed: Success
    Processing --> Error: Failure
    Error --> Idle: Retry
    Completed --> [*]
```

## Pie Chart Example

Here's a pie chart:

```mermaid
pie title Distribution
    "Category A" : 42.1
    "Category B" : 25.3
    "Category C" : 18.7
    "Category D" : 13.9
```

## Conclusion

This document contains multiple mermaid diagram types for testing generation.

