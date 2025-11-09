"""
Task: tsk_4a8cd155 - Create TaskScorer Class
dohcount: 1

Related Tasks:
    - tsk_cc15e96f - Implement Revised Task Scoring System (parent)
    - tsk_674e247f - Implement Scoring Metrics (blocks)

Used By:
    - FileManager: Uses TaskScorer to calculate task scores
    - CLI Commands: Displays scores calculated by this class

Purpose:
    A dedicated class that calculates scores for tasks based on multiple metrics
    including effort, effectiveness, risk, and urgency.

Requirements:
    - Must support all scoring metrics defined in the specification
    - Must normalize scores to ensure consistent scaling
    - Must handle edge cases like empty task lists and missing data
    - CRITICAL: Must correctly calculate maximum values for normalization

Parameters for calculate_scores:
    task (Dict[str, Any]): The task to calculate scores for

Returns from calculate_scores:
    Dict[str, float]: Dictionary containing all calculated scores
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class TaskScorer:
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/scoring/task_scorer.py
    dohcount: 1
    
    Related Tasks:
        - tsk_4a8cd155 - Create TaskScorer Class (original)
        - tsk_cc15e96f - Implement Revised Task Scoring System (parent)
        - tsk_674e247f - Implement Scoring Metrics (related)
    
    Used By:
        - FileManager: Uses TaskScorer to calculate and store task scores
        - Dashboard: Displays and sorts tasks based on these scores
        - CLI Commands: Shows score metrics in task details
        - Priority Queue: Orders tasks for processing based on scores
    
    Purpose:
        Implements a sophisticated scoring system for tasks that evaluates
        their importance and complexity across multiple dimensions, providing
        objective metrics for task prioritization and resource allocation.
    
    Requirements:
        - Must support all required scoring metrics (effort, effectiveness, risk, urgency)
        - Must normalize scores to ensure consistent scaling across task sets
        - Must handle edge cases like empty task lists and missing data gracefully
        - Must maintain backward compatibility with existing scoring interfaces
        - CRITICAL: Must correctly calculate maximum values for normalization
        - CRITICAL: Must implement scoring algorithms exactly as specified
    
    Attributes:
        tasks: List of all tasks used for scoring normalization
        _max_values: Dictionary of maximum values for normalization calculations
    
    Changes:
        - v1: Initial implementation with basic scoring metrics
        - v2: Added normalization to ensure fair comparison
        - v3: Enhanced with additional metrics for better accuracy
        - v4: Improved error handling and edge case management
    
    Lessons Learned:
        - Normalization is critical for meaningful score comparison
        - Caching maximum values improves performance for large task sets
        - Handling missing data gracefully prevents scoring failures
        - Weighted combinations of scores provide better overall evaluation
    """
    
    def __init__(self, tasks: List[Dict[str, Any]]):
        """
        Initialize the TaskScorer with a list of tasks.
        
        Creates a new task scorer instance, calculating normalization factors
        based on the provided task set to ensure consistent scoring across
        all calculations.
        
        Args:
            tasks: List of tasks to use for calculating maximum values needed for normalization
            
        Side Effects:
            - Calculates and stores maximum values for various metrics
            - Logs debug information about initialization
        """
        self.tasks = tasks
        self._max_values = self._calculate_max_values()
        logger.debug(f"Initialized TaskScorer with {len(tasks)} tasks. Max values: {self._max_values}")
    
    def _calculate_max_values(self) -> Dict[str, float]:
        """
        Calculate maximum values needed for normalization.
        
        Returns:
            Dictionary of maximum values for different metrics
        """
        if not self.tasks:
            return {
                "max_subtasks": 1,
                "max_dependencies": 1,
                "max_blocks": 1,
                "max_days": 1
            }
        
        max_subtasks = 0
        max_dependencies = 0
        max_blocks = 0
        max_days = 1  # Minimum 1 to avoid division by zero
        
        # Get the current time for age calculation
        try:
            current_time = datetime.now()
        except Exception:
            # Fallback in case of error
            current_time = datetime.now()
        
        for task in self.tasks:
            # Count subtasks
            subtasks = task.get("subtasks", [])
            max_subtasks = max(max_subtasks, len(subtasks))
            
            # Count dependencies
            dependencies = []
            if "relationships" in task and "depends_on" in task["relationships"]:
                dependencies.extend(task["relationships"]["depends_on"])
            # Check legacy format
            if "depends_on" in task and isinstance(task["depends_on"], list):
                dependencies.extend(task["depends_on"])
            max_dependencies = max(max_dependencies, len(dependencies))
            
            # Count blocks
            blocks = []
            if "relationships" in task and "blocks" in task["relationships"]:
                blocks.extend(task["relationships"]["blocks"])
            # Check legacy format
            if "blocks" in task and isinstance(task["blocks"], list):
                blocks.extend(task["blocks"])
            max_blocks = max(max_blocks, len(blocks))
            
            # Calculate age in days
            if "created_at" in task and task["created_at"]:
                try:
                    created_at = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
                    days = (current_time - created_at).days
                    max_days = max(max_days, days)
                except Exception:
                    # Skip if we can't parse the date
                    pass
        
        # Ensure we have non-zero values to avoid division by zero
        max_subtasks = max(max_subtasks, 1)
        max_dependencies = max(max_dependencies, 1)
        max_blocks = max(max_blocks, 1)
        max_days = max(max_days, 1)
        
        return {
            "max_subtasks": max_subtasks,
            "max_dependencies": max_dependencies,
            "max_blocks": max_blocks,
            "max_days": max_days
        }
    
    def calculate_scores(self, task: Dict[str, Any]) -> Dict[str, float]:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/scoring/task_scorer.py
        dohcount: 1
        
        Used By:
            - FileManager: For storing scores with tasks
            - Dashboard: For visualizing task importance
            - CLI Commands: For displaying comprehensive task details
            - Sort Functions: For ordering tasks by importance
        
        Purpose:
            Calculates and aggregates all scoring metrics for a given task,
            providing a comprehensive evaluation of its importance, difficulty,
            and urgency to aid in prioritization and resource allocation.
        
        Requirements:
            - Must calculate all component scores (effort, effectiveness, risk, urgency)
            - Must apply correct weighting to each component score
            - Must round scores to 2 decimal places for consistency
            - Must handle missing task data gracefully
            - CRITICAL: Changes to scoring formula affects task prioritization
        
        Args:
            task: The task dictionary to calculate scores for
            
        Returns:
            Dictionary containing all calculated scores:
            {
                'effort': float (0-1),          # Difficulty and work required
                'effectiveness': float (0-1),   # Impact and value delivered
                'risk': float (0-1),            # Potential for issues/blockers
                'urgency': float (0-1),         # Time sensitivity
                'total': float (0-1)            # Weighted composite score
            }
            
        Example Usage:
            ```python
            # Calculate scores for a task
            task_scores = scorer.calculate_scores(task_data)
            
            # Use total score for prioritization
            if task_scores['total'] > 0.7:
                print(f"High priority task: {task_data['name']}")
                
            # Check specific dimensions
            if task_scores['risk'] > 0.8:
                print(f"High risk task: {task_data['name']}")
            ```
        """
        effort = self._calculate_effort_score(task)
        effectiveness = self._calculate_effectiveness_score(task)
        risk = self._calculate_risk_score(task)
        urgency = self._calculate_urgency_score(task)
        
        # Calculate total score with weights
        total = (
            (effort * 0.3) + 
            (effectiveness * 0.3) + 
            (risk * 0.2) + 
            (urgency * 0.2)
        )
        
        return {
            'effort': round(effort, 2),
            'effectiveness': round(effectiveness, 2),
            'risk': round(risk, 2),
            'urgency': round(urgency, 2),
            'total': round(total, 2)
        }
    
    def _calculate_effort_score(self, task: Dict[str, Any]) -> float:
        """
        Task: tsk_0fa698f3 - Update Core Module Comments
        Document: refactor/core/scoring/task_scorer.py
        dohcount: 1
        
        Used By:
            - calculate_scores: As a component of the total score
            - Task Analysis: For estimating work required
            - Resource Allocation: For effort-based planning
        
        Purpose:
            Calculates a score that reflects the estimated effort required to complete
            a task, based on its priority, complexity (number of subtasks), and
            dependencies on other tasks.
        
        Requirements:
            - Must account for task priority (inverted: higher priority = less effort)
            - Must consider number of subtasks as a measure of complexity
            - Must factor in dependencies that complicate implementation
            - Must normalize all factors against maximum values
            - CRITICAL: Must follow the specified formula exactly
        
        Formula:
            ((5 - Priority) / 4) * 0.4 + 
            (Subtasks / Max Subtasks) * 0.3 + 
            (Dependencies / Max Dependencies) * 0.3
        
        Args:
            task: The task to calculate effort score for
            
        Returns:
            Float between 0-1 representing the normalized effort score
        """
        # Priority contribution (higher priority = higher score)
        priority = task.get("priority", 3)
        priority_contribution = ((5 - priority) / 4) * 0.4
        
        # Subtasks contribution
        subtasks = task.get("subtasks", [])
        subtask_contribution = (len(subtasks) / self._max_values["max_subtasks"]) * 0.3
        
        # Dependencies contribution
        dependencies = []
        if "relationships" in task and "depends_on" in task["relationships"]:
            dependencies.extend(task["relationships"]["depends_on"])
        # Check legacy format
        if "depends_on" in task and isinstance(task["depends_on"], list):
            dependencies.extend(task["depends_on"])
        dependency_contribution = (len(dependencies) / self._max_values["max_dependencies"]) * 0.3
        
        return priority_contribution + subtask_contribution + dependency_contribution
    
    def _calculate_effectiveness_score(self, task: Dict[str, Any]) -> float:
        """
        Calculate effectiveness score for a task.
        
        Formula: ((5 - Priority) / 4) * 0.4 + (Blocks / Max Blocks) * 0.4 + 
                 (Impact Tag Weight * 0.2)
        
        Args:
            task: The task to calculate effectiveness for
            
        Returns:
            Effectiveness score (0-1 scale)
        """
        # Priority contribution (higher priority = higher score)
        priority = task.get("priority", 3)
        priority_contribution = ((5 - priority) / 4) * 0.4
        
        # Blocks contribution
        blocks = []
        if "relationships" in task and "blocks" in task["relationships"]:
            blocks.extend(task["relationships"]["blocks"])
        # Check legacy format
        if "blocks" in task and isinstance(task["blocks"], list):
            blocks.extend(task["blocks"])
        blocks_contribution = (len(blocks) / self._max_values["max_blocks"]) * 0.4
        
        # Impact tags contribution
        tags = task.get("tags", [])
        impact_tag_weight = 0.0
        
        impact_tags = {
            "critical": 1.0,
            "high-impact": 0.8,
            "medium-impact": 0.5,
            "low-impact": 0.2,
        }
        
        for tag in tags:
            if tag.lower() in impact_tags:
                impact_tag_weight = max(impact_tag_weight, impact_tags[tag.lower()])
        
        impact_contribution = impact_tag_weight * 0.2
        
        return priority_contribution + blocks_contribution + impact_contribution
    
    def _calculate_risk_score(self, task: Dict[str, Any]) -> float:
        """
        Calculate risk score for a task.
        
        Formula: ((5 - Priority) / 4) * 0.5 + (Blocks / Max Blocks) * 0.3 + 
                 (Risk Tag Weight * 0.2)
        
        Args:
            task: The task to calculate risk for
            
        Returns:
            Risk score (0-1 scale)
        """
        # Priority contribution (higher priority = higher risk)
        priority = task.get("priority", 3)
        priority_contribution = ((5 - priority) / 4) * 0.5
        
        # Blocks contribution
        blocks = []
        if "relationships" in task and "blocks" in task["relationships"]:
            blocks.extend(task["relationships"]["blocks"])
        # Check legacy format
        if "blocks" in task and isinstance(task["blocks"], list):
            blocks.extend(task["blocks"])
        blocks_contribution = (len(blocks) / self._max_values["max_blocks"]) * 0.3
        
        # Risk tags contribution
        tags = task.get("tags", [])
        risk_tag_weight = 0.0
        
        risk_tags = {
            "critical": 1.0,
            "high-risk": 0.8,
            "medium-risk": 0.5,
            "low-risk": 0.2,
        }
        
        for tag in tags:
            if tag.lower() in risk_tags:
                risk_tag_weight = max(risk_tag_weight, risk_tags[tag.lower()])
        
        risk_contribution = risk_tag_weight * 0.2
        
        return priority_contribution + blocks_contribution + risk_contribution
    
    def _calculate_urgency_score(self, task: Dict[str, Any]) -> float:
        """
        Calculate urgency score for a task.
        
        Formula: (Days Since Creation / Max Days) * 0.6 + (Urgency Tag Weight * 0.4)
        
        Args:
            task: The task to calculate urgency for
            
        Returns:
            Urgency score (0-1 scale)
        """
        # Age contribution
        age_contribution = 0.0
        if "created_at" in task and task["created_at"]:
            try:
                created_at = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
                days = (datetime.now() - created_at).days
                age_contribution = (days / self._max_values["max_days"]) * 0.6
            except Exception:
                # Default to 0 if we can't parse the date
                pass
        
        # Urgency tags contribution
        tags = task.get("tags", [])
        urgency_tag_weight = 0.0
        
        urgency_tags = {
            "urgent": 1.0,
            "high-urgency": 0.8,
            "medium-urgency": 0.5,
            "low-urgency": 0.2,
        }
        
        for tag in tags:
            if tag.lower() in urgency_tags:
                urgency_tag_weight = max(urgency_tag_weight, urgency_tags[tag.lower()])
        
        urgency_contribution = urgency_tag_weight * 0.4
        
        return age_contribution + urgency_contribution 