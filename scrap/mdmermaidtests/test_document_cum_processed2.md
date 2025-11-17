# Test Document with Mermaid Diagrams

This is a test document to verify mermaid diagram generation from markdown.

## Flowchart Example

Here's a simple flowchart:


{{image:bc85a4527f8be784a98e79fd34fc7f84388b82f95be84f9bc323e8751a23cffe}}

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


{{image:736c384bfc78440a3f981b50aee220d0a4d382b1ed8f8f9cbd3419564d20a374}}

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


{{image:b2fedc13cc1a3dcc56b0e1cd8ffc98e807e609504467d6c1d0ef1557bf122e6e}}

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


{{image:ca3165113c3331e5252927798d7cb11fbdfc27873f767202d23a7d8266a3684b}}

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


{{image:4e2d598e1980d49c59145e1b13b3855e805e59e2cad2a0b4544d7f4fc48f5cad}}

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


{{image:cdc9e64c560bc2ba9b36891043a796cc5679bccb22baaa9c55f39eb6e91c6d24}}

```mermaid
pie title Distribution
    "Category A" : 42.1
    "Category B" : 25.3
    "Category C" : 18.7
    "Category D" : 13.9
```

## Conclusion

This document contains multiple mermaid diagram types for testing generation.

