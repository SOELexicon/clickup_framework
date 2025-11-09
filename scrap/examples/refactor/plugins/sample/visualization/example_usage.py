"""
Example usage of the VisualizationPlugin.

This script demonstrates how to initialize and use the visualization plugin
with sample task data.
"""
import os
import sys
import json
from datetime import datetime, timedelta

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# Import the plugin
from refactor.plugins.sample.visualization.visualization_plugin import VisualizationPlugin

# Create a simple logger for the example
class SimpleLogger:
    def info(self, message):
        print(f"[INFO] {message}")
    
    def warning(self, message):
        print(f"[WARNING] {message}")
    
    def error(self, message):
        print(f"[ERROR] {message}")


def generate_sample_tasks(num_tasks=50):
    """Generate sample task data for demonstration."""
    statuses = ['to do', 'in progress', 'in review', 'complete']
    priorities = [1, 2, 3, 4, 5]
    tags = ['bug', 'feature', 'documentation', 'enhancement', 'ui', 'backend', 'frontend', 
            'database', 'security', 'performance', 'refactor']
    
    tasks = []
    now = datetime.now()
    
    # Create parent tasks
    parent_tasks = []
    for i in range(5):
        parent_task = {
            'id': f'tsk_{i:08d}',
            'name': f'Parent Task {i+1}',
            'status': statuses[min(i % 4, 3)],
            'priority': priorities[min(i % 5, 4)],
            'tags': [tags[j] for j in range(len(tags)) if i % (j+1) == 0],
            'date_created': int((now - timedelta(days=30)).timestamp()),
            'parent_id': None
        }
        
        if parent_task['status'] == 'complete':
            parent_task['date_completed'] = int((now - timedelta(days=5 + i)).timestamp())
        
        parent_tasks.append(parent_task)
        tasks.append(parent_task)
    
    # Create subtasks
    for i, parent in enumerate(parent_tasks):
        for j in range(3):
            subtask = {
                'id': f'stk_{i}{j:02d}',
                'name': f'Subtask {i+1}.{j+1}',
                'status': statuses[min((i+j) % 4, 3)],
                'priority': priorities[min((i+j) % 5, 4)],
                'tags': [tags[k] for k in range(len(tags)) if (i+j) % (k+2) == 0],
                'date_created': int((now - timedelta(days=25)).timestamp()),
                'parent_id': parent['id']
            }
            
            if subtask['status'] == 'complete':
                subtask['date_completed'] = int((now - timedelta(days=j+1)).timestamp())
            
            tasks.append(subtask)
            
            # Create sub-subtasks
            if j % 2 == 0:
                for k in range(2):
                    sub_subtask = {
                        'id': f'sstk_{i}{j}{k}',
                        'name': f'Sub-subtask {i+1}.{j+1}.{k+1}',
                        'status': statuses[min((i+j+k) % 4, 3)],
                        'priority': priorities[min((i+j+k) % 5, 4)],
                        'tags': [tags[l] for l in range(len(tags)) if (i+j+k) % (l+3) == 0],
                        'date_created': int((now - timedelta(days=20)).timestamp()),
                        'parent_id': subtask['id']
                    }
                    
                    if sub_subtask['status'] == 'complete':
                        sub_subtask['date_completed'] = int((now - timedelta(days=k+1)).timestamp())
                    
                    tasks.append(sub_subtask)
    
    # Add some more random tasks to get to the desired count
    current_count = len(tasks)
    for i in range(current_count, num_tasks):
        task = {
            'id': f'rtsk_{i:08d}',
            'name': f'Task {i+1}',
            'status': statuses[i % 4],
            'priority': priorities[i % 5],
            'tags': [tags[j] for j in range(len(tags)) if i % (j+5) == 0],
            'date_created': int((now - timedelta(days=i % 30)).timestamp()),
            'parent_id': None
        }
        
        if task['status'] == 'complete':
            task['date_completed'] = int((now - timedelta(days=i % 10)).timestamp())
        
        tasks.append(task)
    
    return tasks


def main():
    # Generate sample task data
    tasks = generate_sample_tasks()
    print(f"Generated {len(tasks)} sample tasks")
    
    # Create plugin configuration
    config = {
        'render_backend': 'matplotlib',  # Try with 'ascii' if matplotlib is not available
        'default_charts': ['status_distribution', 'priority_distribution', 'completion_trend'],
        'chart_theme': 'default',
        'export_formats': ['png', 'svg', 'pdf'],
        'interactive': True,
        'custom_colors': {
            'to do': '#3498db',
            'in progress': '#f39c12',
            'in review': '#9b59b6',
            'complete': '#2ecc71'
        },
        'max_chart_items': 10
    }
    
    # Initialize the plugin
    visualization_plugin = VisualizationPlugin('visualization_plugin', config)
    
    # Validate the configuration
    valid, errors = visualization_plugin.validate_config()
    if not valid:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return
    
    # Initialize the plugin with context
    context = {
        'logger': SimpleLogger()
    }
    visualization_plugin.initialize(context)
    
    # Get available chart types
    chart_types = visualization_plugin.get_available_chart_types()
    print("\nAvailable chart types:")
    for chart_type in chart_types:
        print(f"  - {chart_type['name']}: {chart_type['description']}")
    
    # Create and display each chart type
    print("\nGenerating charts...")
    for chart_info in chart_types:
        chart_id = chart_info['id']
        chart_result = visualization_plugin.create_chart(chart_id, tasks)
        
        if chart_result:
            print(f"\n=== {chart_result['title']} ===")
            print(chart_result['ascii'])
            
            if 'image_path' in chart_result:
                print(f"Chart image saved to: {chart_result['image_path']}")
                # In a real application, you might display this image or include it in a report
    
    print("\nVisualization plugin example completed")


if __name__ == "__main__":
    main() 