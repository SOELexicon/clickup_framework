// Mermaid Workflow Generator
// Author: Craig (Lexicon)
// Version: 1.0
// Purpose: Convert JSON workflows to Mermaid diagrams

/**
 * Main workflow converter class
 * @version 1.0 - Initial implementation
 */
class MermaidWorkflowGenerator {
  constructor(workflowData) {
    this.workflowData = workflowData;
  }

  /**
   * Convert a single workflow to basic Mermaid diagram
   * @param {Object} workflow - Workflow object with name and steps
   * @returns {string} - Mermaid diagram syntax
   * @version 1.0
   */
  basicFlowchart(workflow) {
    let mermaid = `graph TD\n`;
    mermaid += `    %% ${workflow.name}\n`;
    const steps = workflow.steps;
    
    for (let i = 0; i < steps.length; i++) {
      const currentId = `step${i}`;
      const currentLabel = steps[i];
      
      if (i === 0) {
        mermaid += `    start([Start]) --> ${currentId}["${currentLabel}"]\n`;
      } else {
        const prevId = `step${i-1}`;
        mermaid += `    ${prevId} --> ${currentId}["${currentLabel}"]\n`;
      }
      
      if (i === steps.length - 1) {
        mermaid += `    ${currentId} --> complete([Complete])\n`;
      }
    }
    
    return mermaid;
  }

  /**
   * Convert workflow with decision points
   * @param {Object} workflow - Workflow object
   * @param {Array} decisionPoints - Array of step indices that are decision points
   * @returns {string} - Mermaid diagram with decision nodes
   * @version 1.0
   */
  flowchartWithDecisions(workflow, decisionPoints = []) {
    let mermaid = `graph TD\n`;
    mermaid += `    %% ${workflow.name} with Decisions\n`;
    const steps = workflow.steps;
    
    for (let i = 0; i < steps.length; i++) {
      const currentId = `step${i}`;
      const currentLabel = steps[i];
      const isDecision = decisionPoints.includes(i);
      
      if (i === 0) {
        if (isDecision) {
          mermaid += `    start([Start]) --> ${currentId}{{"${currentLabel}"}}\n`;
        } else {
          mermaid += `    start([Start]) --> ${currentId}["${currentLabel}"]\n`;
        }
      } else {
        const prevId = `step${i-1}`;
        if (isDecision) {
          mermaid += `    ${prevId} --> ${currentId}{{"${currentLabel}"}}\n`;
        } else if (decisionPoints.includes(i-1)) {
          // Previous was decision
          mermaid += `    ${prevId} -->|Yes| ${currentId}["${currentLabel}"]\n`;
          mermaid += `    ${prevId} -->|No| rework[Rework Required]\n`;
          mermaid += `    rework --> ${prevId}\n`;
        } else {
          mermaid += `    ${prevId} --> ${currentId}["${currentLabel}"]\n`;
        }
      }
      
      if (i === steps.length - 1 && !isDecision) {
        mermaid += `    ${currentId} --> complete([Complete])\n`;
      }
    }
    
    return mermaid;
  }

  /**
   * Create swimlane diagram for role-based workflows
   * @param {Object} workflow - Workflow object
   * @param {Object} roleMapping - Map of step indices to roles
   * @returns {string} - Mermaid swimlane diagram
   * @version 1.0
   */
  swimlaneDiagram(workflow, roleMapping) {
    let mermaid = `graph TB\n`;
    mermaid += `    %% ${workflow.name} Swimlanes\n`;
    
    // Group steps by role
    const roleGroups = {};
    workflow.steps.forEach((step, index) => {
      const role = roleMapping[index] || 'General';
      if (!roleGroups[role]) roleGroups[role] = [];
      roleGroups[role].push({ step, index });
    });
    
    // Create subgraphs for each role
    Object.entries(roleGroups).forEach(([role, steps]) => {
      mermaid += `    subgraph ${role.replace(/\s+/g, '_')}_lane["${role}"]\n`;
      steps.forEach(({ step, index }) => {
        mermaid += `        step${index}["${step}"]\n`;
      });
      mermaid += `    end\n`;
    });
    
    // Add connections
    mermaid += `    start([Start]) --> step0\n`;
    for (let i = 1; i < workflow.steps.length; i++) {
      mermaid += `    step${i-1} --> step${i}\n`;
    }
    mermaid += `    step${workflow.steps.length - 1} --> complete([Complete])\n`;
    
    return mermaid;
  }

  /**
   * Create parallel process diagram
   * @param {Object} workflow - Workflow object
   * @param {Array} parallelGroups - Array of arrays containing parallel step indices
   * @returns {string} - Mermaid diagram with parallel processes
   * @version 1.0
   */
  parallelFlow(workflow, parallelGroups) {
    let mermaid = `graph TD\n`;
    mermaid += `    %% ${workflow.name} with Parallel Processes\n`;
    const steps = workflow.steps;
    let lastStep = 'start([Start])';
    let stepCounter = 0;
    
    parallelGroups.forEach((group, groupIndex) => {
      const splitId = `split${groupIndex}`;
      const mergeId = `merge${groupIndex}`;
      
      // Create split
      mermaid += `    ${lastStep} --> ${splitId}{{"Parallel Tasks"}}\n`;
      
      // Create parallel branches
      group.forEach(stepIndex => {
        const stepId = `step${stepCounter++}`;
        mermaid += `    ${splitId} --> ${stepId}["${steps[stepIndex]}"]\n`;
        mermaid += `    ${stepId} --> ${mergeId}{{"Merge"}}\n`;
      });
      
      lastStep = mergeId;
    });
    
    // Add remaining sequential steps
    for (let i = Math.max(...parallelGroups.flat()) + 1; i < steps.length; i++) {
      const stepId = `step${stepCounter++}`;
      mermaid += `    ${lastStep} --> ${stepId}["${steps[i]}"]\n`;
      lastStep = stepId;
    }
    
    mermaid += `    ${lastStep} --> complete([Complete])\n`;
    
    return mermaid;
  }

  /**
   * Create state diagram for status-based workflows
   * @param {Object} workflow - Workflow object
   * @returns {string} - Mermaid state diagram
   * @version 1.0
   */
  stateDiagram(workflow) {
    let mermaid = `stateDiagram-v2\n`;
    mermaid += `    %% ${workflow.name} State Diagram\n`;
    
    const steps = workflow.steps;
    
    mermaid += `    [*] --> ${steps[0].replace(/\s+/g, '_')}\n`;
    
    for (let i = 0; i < steps.length - 1; i++) {
      const current = steps[i].replace(/\s+/g, '_');
      const next = steps[i + 1].replace(/\s+/g, '_');
      mermaid += `    ${current} --> ${next}\n`;
    }
    
    mermaid += `    ${steps[steps.length - 1].replace(/\s+/g, '_')} --> [*]\n`;
    
    return mermaid;
  }

  /**
   * Generate all diagram types for a workflow
   * @param {string} taskType - Type of task from workflow data
   * @param {number} workflowIndex - Index of workflow to generate
   * @returns {Object} - Object containing all diagram types
   * @version 1.0
   */
  generateAllDiagrams(taskType, workflowIndex) {
    const taskWorkflows = this.workflowData.taskWorkflows[taskType];
    if (!taskWorkflows || !taskWorkflows.workflows[workflowIndex]) {
      throw new Error(`Workflow not found: ${taskType}[${workflowIndex}]`);
    }
    
    const workflow = taskWorkflows.workflows[workflowIndex];
    
    return {
      name: workflow.name,
      basic: this.basicFlowchart(workflow),
      withDecisions: this.flowchartWithDecisions(workflow, [2, 5]), // Example decision points
      state: this.stateDiagram(workflow),
      // Add more as needed with appropriate parameters
    };
  }

  /**
   * Export all workflows for a task type to markdown file
   * @param {string} taskType - Type of task
   * @returns {string} - Markdown content with all diagrams
   * @version 1.0
   */
  exportToMarkdown(taskType) {
    const taskWorkflows = this.workflowData.taskWorkflows[taskType];
    if (!taskWorkflows) {
      throw new Error(`Task type not found: ${taskType}`);
    }
    
    let markdown = `# ${taskWorkflows.name}\n\n`;
    
    taskWorkflows.workflows.forEach((workflow, index) => {
      markdown += `## ${index + 1}. ${workflow.name}\n\n`;
      markdown += `### Basic Flow\n\n`;
      markdown += '```mermaid\n';
      markdown += this.basicFlowchart(workflow);
      markdown += '```\n\n';
      
      markdown += `### State Diagram\n\n`;
      markdown += '```mermaid\n';
      markdown += this.stateDiagram(workflow);
      markdown += '```\n\n';
    });
    
    return markdown;
  }
}

// Example usage
const fs = require('fs');

// Load workflow data
const workflowData = JSON.parse(fs.readFileSync('clickup_task_workflows.json', 'utf8'));

// Create generator instance
const generator = new MermaidWorkflowGenerator(workflowData);

// Generate diagrams for coding tasks
const codingDiagrams = generator.exportToMarkdown('codingTask');
fs.writeFileSync('coding_workflows.md', codingDiagrams);

// Generate specific diagram
const bugFixBasic = generator.basicFlowchart(
  workflowData.taskWorkflows.bugFix.workflows[0]
);
console.log(bugFixBasic);

// Export function for use in other scripts
module.exports = MermaidWorkflowGenerator;

/* 
 * File: mermaid_workflow_generator.js
 * Variables: MermaidWorkflowGenerator, workflowData, generator
 * Functions: constructor, basicFlowchart, flowchartWithDecisions, swimlaneDiagram, 
 *           parallelFlow, stateDiagram, generateAllDiagrams, exportToMarkdown
 */
