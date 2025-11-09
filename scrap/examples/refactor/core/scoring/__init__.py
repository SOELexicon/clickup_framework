"""
Scoring module for task prioritization and effort calculation.

This module provides functionality for scoring tasks based on various metrics
including effort, effectiveness, risk, and urgency. These scores help in
prioritizing tasks based on their importance and complexity.

Core components:
- TaskScorer: Calculates scores for tasks based on multiple factors

Usage:
    from refactor.core.scoring.task_scorer import TaskScorer
    
    # Create a scorer with all tasks for normalization
    scorer = TaskScorer(all_tasks)
    
    # Calculate scores for a specific task
    scores = scorer.calculate_scores(task)
    
    # Access individual scores
    effort_score = scores['effort']
    total_score = scores['total']
"""

from refactor.core.scoring.task_scorer import TaskScorer

__all__ = ['TaskScorer'] 