#!/usr/bin/env python3
"""
Mermaid Workflow Generator - Python Version
Author: Craig (Lexicon)
Version: 1.0
Purpose: Convert JSON workflows to Mermaid diagrams using Python

Variables: MermaidWorkflowGenerator, workflow_data
Functions: __init__, basic_flowchart, flowchart_with_decisions, swimlane_diagram,
          parallel_flow, state_diagram, generate_all_diagrams, export_to_markdown
"""

import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class MermaidWorkflowGenerator:
    """
    Generate Mermaid diagrams from workflow JSON data
    Version 1.0 - Initial implementation
    """
    
    def __init__(self, workflow_data: Dict):
        """Initialize with workflow data from JSON"""
        self.workflow_data = workflow_data
    
    def basic_flowchart(self, workflow: Dict) -> str:
        """
        Convert a single workflow to basic Mermaid diagram
        Version 1.0
        
        Args:
            workflow: Workflow dict with 'name' and 'steps' keys
            
        Returns:
            Mermaid diagram syntax as string
        """
        mermaid = "graph TD\n"
        mermaid += f"    %% {workflow['name']}\n"
        steps = workflow['steps']
        
        for i, step in enumerate(steps):
            current_id = f"step{i}"
            
            if i == 0:
                mermaid += f'    start([Start]) --> {current_id}["{step}"]\n'
            else:
                prev_id = f"step{i-1}"
                mermaid += f'    {prev_id} --> {current_id}["{step}"]\n'
            
            if i == len(steps) - 1:
                mermaid += f"    {current_id} --> complete([Complete])\n"
        
        return mermaid
    
    def flowchart_with_decisions(self, workflow: Dict, decision_points: List[int] = None) -> str:
        """
        Convert workflow with decision points
        Version 1.0
        
        Args:
            workflow: Workflow dict
            decision_points: List of step indices that are decision points
            
        Returns:
            Mermaid diagram with decision nodes
        """
        if decision_points is None:
            decision_points = []
            
        mermaid = "graph TD\n"
        mermaid += f"    %% {workflow['name']} with Decisions\n"
        steps = workflow['steps']
        
        for i, step in enumerate(steps):
            current_id = f"step{i}"
            is_decision = i in decision_points
            
            if i == 0:
                if is_decision:
                    mermaid += f'    start([Start]) --> {current_id}{{"{step}"}}\n'
                else:
                    mermaid += f'    start([Start]) --> {current_id}["{step}"]\n'
            else:
                prev_id = f"step{i-1}"
                if is_decision:
                    mermaid += f'    {prev_id} --> {current_id}{{"{step}"}}\n'
                elif (i-1) in decision_points:
                    # Previous was decision
                    mermaid += f'    {prev_id} -->|Yes| {current_id}["{step}"]\n'
                    mermaid += f'    {prev_id} -->|No| rework[Rework Required]\n'
                    mermaid += f'    rework --> {prev_id}\n'
                else:
                    mermaid += f'    {prev_id} --> {current_id}["{step}"]\n'
            
            if i == len(steps) - 1 and not is_decision:
                mermaid += f"    {current_id} --> complete([Complete])\n"
        
        return mermaid
    
    def swimlane_diagram(self, workflow: Dict, role_mapping: Dict[int, str]) -> str:
        """
        Create swimlane diagram for role-based workflows
        Version 1.0
        
        Args:
            workflow: Workflow dict
            role_mapping: Dict mapping step index to role name
            
        Returns:
            Mermaid swimlane diagram
        """
        mermaid = "graph TB\n"
        mermaid += f"    %% {workflow['name']} Swimlanes\n"
        
        # Group steps by role
        role_groups = {}
        for i, step in enumerate(workflow['steps']):
            role = role_mapping.get(i, 'General')
            if role not in role_groups:
                role_groups[role] = []
            role_groups[role].append((step, i))
        
        # Create subgraphs for each role
        for role, steps in role_groups.items():
            role_id = role.replace(' ', '_')
            mermaid += f'    subgraph {role_id}_lane["{role}"]\n'
            for step, index in steps:
                mermaid += f'        step{index}["{step}"]\n'
            mermaid += "    end\n"
        
        # Add connections
        mermaid += "    start([Start]) --> step0\n"
        for i in range(1, len(workflow['steps'])):
            mermaid += f"    step{i-1} --> step{i}\n"
        mermaid += f"    step{len(workflow['steps'])-1} --> complete([Complete])\n"
        
        return mermaid
    
    def parallel_flow(self, workflow: Dict, parallel_groups: List[List[int]]) -> str:
        """
        Create parallel process diagram
        Version 1.0
        
        Args:
            workflow: Workflow dict
            parallel_groups: List of lists containing parallel step indices
            
        Returns:
            Mermaid diagram with parallel processes
        """
        mermaid = "graph TD\n"
        mermaid += f"    %% {workflow['name']} with Parallel Processes\n"
        steps = workflow['steps']
        last_step = 'start([Start])'
        step_counter = 0
        
        for group_index, group in enumerate(parallel_groups):
            split_id = f"split{group_index}"
            merge_id = f"merge{group_index}"
            
            # Create split
            mermaid += f'    {last_step} --> {split_id}{{"Parallel Tasks"}}\n'
            
            # Create parallel branches
            for step_index in group:
                step_id = f"step{step_counter}"
                step_counter += 1
                mermaid += f'    {split_id} --> {step_id}["{steps[step_index]}"]\n'
                mermaid += f'    {step_id} --> {merge_id}{{"Merge"}}\n'
            
            last_step = merge_id
        
        # Add remaining sequential steps
        max_parallel_index = max(sum(parallel_groups, []))
        for i in range(max_parallel_index + 1, len(steps)):
            step_id = f"step{step_counter}"
            step_counter += 1
            mermaid += f'    {last_step} --> {step_id}["{steps[i]}"]\n'
            last_step = step_id
        
        mermaid += f"    {last_step} --> complete([Complete])\n"
        
        return mermaid
    
    def state_diagram(self, workflow: Dict) -> str:
        """
        Create state diagram for status-based workflows
        Version 1.0
        
        Args:
            workflow: Workflow dict
            
        Returns:
            Mermaid state diagram
        """
        mermaid = "stateDiagram-v2\n"
        mermaid += f"    %% {workflow['name']} State Diagram\n"
        
        steps = workflow['steps']
        
        # Start state
        first_state = steps[0].replace(' ', '_')
        mermaid += f"    [*] --> {first_state}\n"
        
        # Transitions
        for i in range(len(steps) - 1):
            current = steps[i].replace(' ', '_')
            next_state = steps[i + 1].replace(' ', '_')
            mermaid += f"    {current} --> {next_state}\n"
        
        # End state
        last_state = steps[-1].replace(' ', '_')
        mermaid += f"    {last_state} --> [*]\n"
        
        return mermaid
    
    def generate_all_diagrams(self, task_type: str, workflow_index: int) -> Dict[str, str]:
        """
        Generate all diagram types for a workflow
        Version 1.0
        
        Args:
            task_type: Type of task from workflow data
            workflow_index: Index of workflow to generate
            
        Returns:
            Dict containing all diagram types
        """
        task_workflows = self.workflow_data['taskWorkflows'].get(task_type)
        if not task_workflows or workflow_index >= len(task_workflows['workflows']):
            raise ValueError(f"Workflow not found: {task_type}[{workflow_index}]")
        
        workflow = task_workflows['workflows'][workflow_index]
        
        return {
            'name': workflow['name'],
            'basic': self.basic_flowchart(workflow),
            'withDecisions': self.flowchart_with_decisions(workflow, [2, 5]),
            'state': self.state_diagram(workflow),
        }
    
    def export_to_markdown(self, task_type: str) -> str:
        """
        Export all workflows for a task type to markdown
        Version 1.0
        
        Args:
            task_type: Type of task
            
        Returns:
            Markdown content with all diagrams
        """
        task_workflows = self.workflow_data['taskWorkflows'].get(task_type)
        if not task_workflows:
            raise ValueError(f"Task type not found: {task_type}")
        
        markdown = f"# {task_workflows['name']}\n\n"
        
        for i, workflow in enumerate(task_workflows['workflows']):
            markdown += f"## {i + 1}. {workflow['name']}\n\n"
            
            markdown += "### Basic Flow\n\n"
            markdown += "```mermaid\n"
            markdown += self.basic_flowchart(workflow)
            markdown += "```\n\n"
            
            markdown += "### State Diagram\n\n"
            markdown += "```mermaid\n"
            markdown += self.state_diagram(workflow)
            markdown += "```\n\n"
        
        return markdown


def main():
    """
    Example usage of the MermaidWorkflowGenerator
    Version 1.0 - Added comprehensive examples
    """
    # Load workflow data
    with open('clickup_task_workflows.json', 'r') as f:
        workflow_data = json.load(f)
    
    # Create generator instance
    generator = MermaidWorkflowGenerator(workflow_data)
    
    # Generate diagrams for coding tasks
    coding_diagrams = generator.export_to_markdown('codingTask')
    
    # Save to file
    output_path = Path('coding_workflows.md')
    output_path.write_text(coding_diagrams)
    print(f"Saved coding workflows to {output_path}")
    
    # Generate specific diagram
    bug_fix_basic = generator.basic_flowchart(
        workflow_data['taskWorkflows']['bugFix']['workflows'][0]
    )
    print("\nCritical Production Bug Workflow:")
    print(bug_fix_basic)
    
    # Generate all task type markdowns
    for task_type in workflow_data['taskWorkflows'].keys():
        markdown = generator.export_to_markdown(task_type)
        output_file = Path(f"{task_type}_workflows.md")
        output_file.write_text(markdown)
        print(f"Generated {output_file}")


if __name__ == "__main__":
    main()
