# Mermaid Workflow Examples

## Quick Reference for ClickUp Task Workflows

### 1. Basic Linear Flow
```mermaid
graph TD
    start([Start]) --> step0["Requirements Review"]
    step0 --> step1["Technical Design"]
    step1 --> step2["Implementation"]
    step2 --> step3["Unit Testing"]
    step3 --> step4["Code Review"]
    step4 --> step5["Integration Testing"]
    step5 --> step6["Documentation"]
    step6 --> step7["Deployment"]
    step7 --> complete([Complete])
```

### 2. Flow with Decision Points
```mermaid
graph TD
    start([Start]) --> step0["Bug Report Review"]
    step0 --> step1["Reproduction"]
    step1 --> decision1{{"Can Reproduce?"}}
    decision1 -->|Yes| step2["Investigation"]
    decision1 -->|No| moreInfo["Gather More Info"]
    moreInfo --> step1
    step2 --> step3["Fix Implementation"]
    step3 --> step4["Testing"]
    step4 --> decision2{{"Tests Pass?"}}
    decision2 -->|Yes| step5["Code Review"]
    decision2 -->|No| step3
    step5 --> step6["Release"]
    step6 --> complete([Complete])
```

### 3. Parallel Processes
```mermaid
graph TD
    start([Start]) --> planning["Sprint Planning"]
    planning --> split{{"Parallel Development"}}
    split --> frontend["Frontend Development"]
    split --> backend["Backend Development"]
    split --> database["Database Changes"]
    frontend --> merge{{"Integration"}}
    backend --> merge
    database --> merge
    merge --> testing["Integration Testing"]
    testing --> deployment["Deployment"]
    deployment --> complete([Complete])
```

### 4. Swimlane Diagram
```mermaid
graph TB
    subgraph Developer_lane["Developer"]
        step0["Implementation"]
        step1["Unit Testing"]
    end
    
    subgraph QA_lane["QA Team"]
        step2["Integration Testing"]
        step3["UAT"]
    end
    
    subgraph DevOps_lane["DevOps"]
        step4["Deployment"]
        step5["Monitoring"]
    end
    
    start([Start]) --> step0
    step0 --> step1
    step1 --> step2
    step2 --> step3
    step3 --> step4
    step4 --> step5
    step5 --> complete([Complete])
```

### 5. State Diagram
```mermaid
stateDiagram-v2
    [*] --> Planning
    Planning --> Development
    Development --> Testing
    Testing --> Review
    Review --> Deployment
    Review --> Development: Changes Required
    Deployment --> Monitoring
    Monitoring --> [*]
```

### 6. Critical Bug Workflow
```mermaid
graph TD
    start([Alert]) --> assess["Initial Assessment"]
    assess --> critical{{"Critical?"}}
    critical -->|Yes| hotfix["Hotfix Development"]
    critical -->|No| standard["Standard Process"]
    hotfix --> emergTest["Emergency Testing"]
    emergTest --> deploy["Emergency Deploy"]
    deploy --> postmortem["Post-mortem"]
    standard --> queue["Queue for Sprint"]
    postmortem --> complete([Resolved])
    queue --> complete
```

### 7. Feature Development with Gates
```mermaid
graph TD
    start([Start]) --> design["Design Phase"]
    design --> designReview{{"Design Review"}}
    designReview -->|Approved| dev["Development"]
    designReview -->|Rejected| design
    dev --> codeReview{{"Code Review"}}
    codeReview -->|Approved| testing["Testing"]
    codeReview -->|Changes| dev
    testing --> qa{{"QA Approval"}}
    qa -->|Pass| staging["Staging Deploy"]
    qa -->|Fail| dev
    staging --> uat{{"UAT"}}
    uat -->|Approved| prod["Production"]
    uat -->|Issues| dev
    prod --> complete([Complete])
```

### 8. Database Migration Flow
```mermaid
graph TD
    start([Start]) --> analysis["Impact Analysis"]
    analysis --> script["Migration Script"]
    script --> testEnv["Test Environment"]
    testEnv --> testResult{{"Test Pass?"}}
    testResult -->|No| script
    testResult -->|Yes| backup["Backup Production"]
    backup --> maintenance["Maintenance Mode ON"]
    maintenance --> execute["Execute Migration"]
    execute --> validate["Validation"]
    validate --> success{{"Success?"}}
    success -->|Yes| appTest["Application Testing"]
    success -->|No| rollback["Rollback"]
    rollback --> investigate["Investigate Issue"]
    investigate --> script
    appTest --> maintenanceOff["Maintenance Mode OFF"]
    maintenanceOff --> monitor["Monitor"]
    monitor --> complete([Complete])
```

### 9. Sprint Cycle
```mermaid
graph TD
    start([Sprint Start]) --> planning["Sprint Planning"]
    planning --> commitment["Team Commitment"]
    commitment --> daily1["Day 1: Development"]
    daily1 --> standup1["Daily Standup"]
    standup1 --> daily2["Day 2: Development"]
    daily2 --> standup2["Daily Standup"]
    standup2 --> daily3["Day 3-8: Development"]
    daily3 --> testing["Day 9: Testing"]
    testing --> review["Sprint Review"]
    review --> retro["Retrospective"]
    retro --> nextSprint{{"Next Sprint"}}
    nextSprint --> start
```

### 10. CI/CD Pipeline
```mermaid
graph LR
    start([Code Push]) --> ci["CI Pipeline"]
    ci --> build["Build"]
    build --> unitTest["Unit Tests"]
    unitTest --> integration["Integration Tests"]
    integration --> security["Security Scan"]
    security --> quality["Code Quality"]
    quality --> artifact["Build Artifact"]
    artifact --> cd["CD Pipeline"]
    cd --> staging["Deploy Staging"]
    staging --> e2e["E2E Tests"]
    e2e --> approval{{"Approval"}}
    approval -->|Manual| production["Deploy Production"]
    approval -->|Auto| production
    production --> monitor["Monitoring"]
    monitor --> complete([Complete])
```

## Usage Examples

### JavaScript Implementation
```javascript
const generator = new MermaidWorkflowGenerator(workflowData);

// Generate basic flowchart
const diagram = generator.basicFlowchart(workflow);

// Generate with decision points
const decisionDiagram = generator.flowchartWithDecisions(workflow, [2, 4, 6]);

// Generate swimlane
const swimlane = generator.swimlaneDiagram(workflow, {
  0: 'Developer',
  1: 'Developer',
  2: 'QA',
  3: 'QA',
  4: 'DevOps'
});
```

### Python Implementation
```python
generator = MermaidWorkflowGenerator(workflow_data)

# Generate basic flowchart
diagram = generator.basic_flowchart(workflow)

# Generate with decision points
decision_diagram = generator.flowchart_with_decisions(workflow, [2, 4, 6])

# Generate swimlane
swimlane = generator.swimlane_diagram(workflow, {
  0: 'Developer',
  1: 'Developer', 
  2: 'QA',
  3: 'QA',
  4: 'DevOps'
})
```

## Customization Tips

### 1. Node Shapes
- `[Rectangle]` - Standard process
- `([Rounded])` - Start/End
- `{Diamond}` - Decision
- `{{Hexagon}}` - Preparation
- `[(Database)]` - Data store
- `[[Subroutine]]` - Predefined process

### 2. Arrow Styles
- `-->` - Standard flow
- `-.->` - Dotted line
- `==>` - Thick arrow
- `-->|Text|` - Labeled arrow

### 3. Colors & Styling
```mermaid
graph TD
    start([Start]):::startClass
    process[Process]:::processClass
    end([End]):::endClass
    
    start --> process --> end
    
    classDef startClass fill:#90EE90,stroke:#333,stroke-width:2px
    classDef processClass fill:#87CEEB,stroke:#333,stroke-width:2px
    classDef endClass fill:#FFB6C1,stroke:#333,stroke-width:2px
```

---

**Created By**: Craig (Lexicon)  
**Purpose**: Quick reference for Mermaid workflow diagrams  
**Usage**: Copy and customize these examples for your ClickUp workflows
