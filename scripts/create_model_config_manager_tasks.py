#!/usr/bin/env python3
"""
Create Model Config Manager Documentation and Tasks

This script creates comprehensive ClickUp documentation and implementation tasks
for the Model Configuration Manager component.

Usage:
    python create_model_config_manager_tasks.py
"""

import sys
import os

# Add clickup_framework to path
sys.path.insert(0, '/home/user')

from clickup_framework import ClickUpClient
from clickup_framework.resources import DocsAPI, TasksAPI, ListsAPI

# Configuration
WORKSPACE_ID = "90151898946"
SPACE_ID = "90157903115"
LIST_NAME = "GUI List"


def get_list_id(client, space_id, list_name):
    """Find list ID by name in a space."""
    try:
        space = client.get_space(space_id)
        print(f"📋 Getting list details...")
        print(f"   Space ID: {space_id}")
        print(f"   List Name: {list_name}")

        # Search through folders and lists
        # Note: You may need to implement this based on your space structure
        # For now, we'll return a placeholder
        # TODO: Implement actual list lookup
        return None
    except Exception as e:
        print(f"   Error getting space: {e}")
        return None


def create_documentation(docs, workspace_id):
    """Create Model Config Manager documentation in ClickUp Docs."""

    print(f"\n📚 Step 1: Creating ClickUp Documentation")
    print("="*80)

    doc_pages = [
        {
            "name": "Overview",
            "content": """# Model Configuration Manager

## Overview

The Model Configuration Manager is a core component of the ClickUp Framework that handles all aspects of AI model configuration, selection, and optimization.

## Purpose

- **Centralized Configuration**: Single source of truth for all model settings
- **Dynamic Model Selection**: Runtime model switching based on task requirements
- **Cost Optimization**: Automatic selection of cost-effective models for different tasks
- **Performance Monitoring**: Track and optimize model performance metrics

## Key Features

1. **Multi-Model Support**: Support for Claude, GPT, and other models
2. **Configuration Profiles**: Pre-configured profiles for common use cases
3. **Real-time Switching**: Change models without service interruption
4. **Cost Tracking**: Monitor and optimize API costs
5. **Performance Analytics**: Track latency, token usage, and quality metrics
"""
        },
        {
            "name": "Architecture",
            "content": """# Architecture

## System Design

The Model Config Manager uses a layered architecture:

```
┌─────────────────────────────────────┐
│     Application Layer               │
│  (Skills, Tasks, Workflows)         │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  Model Config Manager               │
│  - Configuration Service            │
│  - Model Registry                   │
│  - Selection Engine                 │
│  - Cost Optimizer                   │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│     Model Providers                 │
│  (Claude, GPT, Local Models)        │
└─────────────────────────────────────┘
```

## Core Components

### 1. Configuration Service
- Manages configuration files and environment variables
- Validates configuration schemas
- Provides configuration hot-reloading

### 2. Model Registry
- Maintains catalog of available models
- Stores model capabilities and constraints
- Manages model authentication credentials

### 3. Selection Engine
- Analyzes task requirements
- Selects optimal model based on criteria
- Implements fallback strategies

### 4. Cost Optimizer
- Tracks API usage and costs
- Recommends cost-effective alternatives
- Implements budget controls
"""
        },
        {
            "name": "Configuration Schema",
            "content": """# Configuration Schema

## Configuration File Structure

```python
{
    "models": {
        "default": "claude-sonnet-4",
        "profiles": {
            "quick": {
                "model": "claude-haiku-4",
                "temperature": 0.3,
                "max_tokens": 2048
            },
            "detailed": {
                "model": "claude-sonnet-4",
                "temperature": 0.7,
                "max_tokens": 4096
            },
            "creative": {
                "model": "claude-opus-4",
                "temperature": 0.9,
                "max_tokens": 8192
            }
        }
    },
    "cost_limits": {
        "daily_budget": 100.00,
        "per_request_max": 5.00,
        "warning_threshold": 0.8
    },
    "performance": {
        "timeout_seconds": 30,
        "retry_attempts": 3,
        "cache_ttl": 3600
    }
}
```

## Environment Variables

- `MODEL_CONFIG_FILE`: Path to configuration file
- `DEFAULT_MODEL`: Default model identifier
- `MODEL_API_KEY`: API authentication key
- `COST_TRACKING_ENABLED`: Enable cost tracking (true/false)
"""
        },
        {
            "name": "API Reference",
            "content": """# API Reference

## ModelConfigManager Class

### Initialization

```python
from clickup_framework.model_config import ModelConfigManager

config = ModelConfigManager(
    config_file="config/models.json",
    default_model="claude-sonnet-4"
)
```

### Methods

#### get_model_config(profile=None)

Get model configuration for a specific profile.

**Parameters:**
- `profile` (str, optional): Configuration profile name

**Returns:**
- `dict`: Model configuration

**Example:**
```python
config = manager.get_model_config(profile="quick")
```

#### select_model(task_type, requirements)

Select optimal model for a task.

**Parameters:**
- `task_type` (str): Type of task (e.g., "code_review", "documentation")
- `requirements` (dict): Task requirements (tokens, latency, cost)

**Returns:**
- `str`: Selected model identifier

**Example:**
```python
model = manager.select_model(
    task_type="code_generation",
    requirements={"max_tokens": 4096, "max_cost": 0.50}
)
```

#### track_usage(model, tokens, cost)

Track model usage and costs.

**Parameters:**
- `model` (str): Model identifier
- `tokens` (int): Token count
- `cost` (float): Request cost

**Example:**
```python
manager.track_usage(
    model="claude-sonnet-4",
    tokens=1500,
    cost=0.045
)
```
"""
        },
        {
            "name": "Usage Examples",
            "content": """# Usage Examples

## Basic Usage

```python
from clickup_framework.model_config import ModelConfigManager

# Initialize manager
config_manager = ModelConfigManager()

# Get default configuration
config = config_manager.get_model_config()

# Use configuration with API client
response = call_model_api(
    model=config['model'],
    temperature=config['temperature'],
    max_tokens=config['max_tokens']
)
```

## Profile-Based Selection

```python
# Quick tasks use fast, cheap models
quick_config = config_manager.get_model_config(profile="quick")

# Detailed analysis uses more capable models
detailed_config = config_manager.get_model_config(profile="detailed")

# Creative work uses most advanced models
creative_config = config_manager.get_model_config(profile="creative")
```

## Dynamic Model Selection

```python
# Automatic selection based on requirements
model = config_manager.select_model(
    task_type="code_review",
    requirements={
        "max_tokens": 8000,
        "max_latency_ms": 5000,
        "max_cost": 1.00
    }
)
```

## Cost Monitoring

```python
# Track usage
config_manager.track_usage(
    model="claude-sonnet-4",
    tokens=2048,
    cost=0.06
)

# Get cost report
report = config_manager.get_cost_report(period="daily")
print(f"Total cost: ${report['total_cost']}")
print(f"Total requests: {report['request_count']}")
```

## Configuration Hot-Reload

```python
# Update configuration file
# Manager automatically detects and reloads changes
config_manager.reload_config()

# Verify new configuration
new_config = config_manager.get_model_config()
```
"""
        },
        {
            "name": "Testing Guide",
            "content": """# Testing Guide

## Unit Tests

### Configuration Loading

```python
def test_load_configuration():
    manager = ModelConfigManager(config_file="test_config.json")
    config = manager.get_model_config()
    assert config['model'] == 'claude-sonnet-4'
```

### Model Selection

```python
def test_model_selection():
    manager = ModelConfigManager()

    # Test quick task selection
    model = manager.select_model(
        task_type="simple_query",
        requirements={"max_cost": 0.10}
    )
    assert model == "claude-haiku-4"
```

### Cost Tracking

```python
def test_cost_tracking():
    manager = ModelConfigManager()

    # Track usage
    manager.track_usage("claude-sonnet-4", tokens=1000, cost=0.03)

    # Verify tracking
    report = manager.get_cost_report()
    assert report['total_cost'] >= 0.03
```

## Integration Tests

### End-to-End Configuration

```python
def test_e2e_configuration():
    # Initialize with custom config
    manager = ModelConfigManager(config_file="integration_test.json")

    # Select model
    model = manager.select_model("code_generation", {"max_tokens": 4096})

    # Use model in actual API call
    response = call_model_api(model=model, prompt="Generate test code")

    # Track usage
    manager.track_usage(model, response.token_count, response.cost)

    assert response.success
```

## Performance Tests

### Load Testing

```python
def test_concurrent_requests():
    manager = ModelConfigManager()

    # Simulate 100 concurrent configuration requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(manager.get_model_config)
            for _ in range(100)
        ]

        results = [f.result() for f in futures]
        assert all(r['model'] for r in results)
```

### Configuration Reload Performance

```python
def test_reload_performance():
    manager = ModelConfigManager()

    start_time = time.time()
    manager.reload_config()
    reload_time = time.time() - start_time

    assert reload_time < 0.1  # Should reload in < 100ms
```
"""
        }
    ]

    try:
        print("\n   Creating main index page...")
        result = docs.create_doc_with_pages(
            workspace_id=workspace_id,
            doc_name="Model Configuration Manager - Documentation",
            pages=doc_pages
        )

        doc_id = result['doc']['id']
        print(f"   ✓ Created doc: {doc_id}")
        print(f"   ✓ Created {len(result['pages'])} pages")

        for i, page in enumerate(result['pages'], 1):
            print(f"      {i}. {page.get('name', 'Unnamed')}")

        return doc_id

    except Exception as e:
        print(f"   ✗ Error creating documentation: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_tasks(tasks_api, list_id):
    """Create implementation tasks."""

    print(f"\n📝 Step 2: Creating Implementation Tasks")
    print("="*80)

    if not list_id:
        print("   ⚠ No list ID provided, skipping task creation")
        print("   Please provide a valid list ID to create tasks")
        return []

    task_definitions = [
        {
            "name": "Design Model Config Manager Architecture",
            "description": """Design the overall architecture for the Model Configuration Manager.

**Deliverables:**
- Architecture diagram
- Component specifications
- API interface definitions
- Data flow documentation

**Acceptance Criteria:**
- All components clearly defined
- Integration points documented
- Scalability considerations addressed
""",
            "priority": 1,  # Urgent
            "tags": ["architecture", "design", "model-config"]
        },
        {
            "name": "Implement Configuration Service",
            "description": """Implement the configuration loading and management service.

**Tasks:**
- Create configuration file parser
- Implement schema validation
- Add hot-reload functionality
- Support environment variable overrides

**Acceptance Criteria:**
- Loads configuration from JSON/YAML
- Validates against schema
- Supports hot-reloading
- All unit tests passing
""",
            "priority": 2,  # High
            "tags": ["implementation", "core", "model-config"]
        },
        {
            "name": "Build Model Registry",
            "description": """Create the model registry to manage available models.

**Tasks:**
- Design model metadata schema
- Implement model registration
- Add capability tracking
- Create model lookup API

**Acceptance Criteria:**
- Supports multiple model providers
- Tracks model capabilities
- Provides fast lookup
- Extensible for new models
""",
            "priority": 2,  # High
            "tags": ["implementation", "registry", "model-config"]
        },
        {
            "name": "Develop Selection Engine",
            "description": """Implement the model selection engine for automatic model selection.

**Tasks:**
- Create selection algorithm
- Implement requirement matching
- Add fallback logic
- Optimize selection performance

**Acceptance Criteria:**
- Selects optimal model based on requirements
- Handles edge cases gracefully
- Provides fallback options
- Selection time < 10ms
""",
            "priority": 2,  # High
            "tags": ["implementation", "selection", "model-config"]
        },
        {
            "name": "Implement Cost Tracking",
            "description": """Add cost tracking and optimization features.

**Tasks:**
- Create usage tracking system
- Implement cost calculation
- Add budget controls
- Build reporting dashboard

**Acceptance Criteria:**
- Tracks all API usage
- Calculates costs accurately
- Enforces budget limits
- Provides usage reports
""",
            "priority": 3,  # Normal
            "tags": ["implementation", "cost", "model-config"]
        },
        {
            "name": "Write Comprehensive Tests",
            "description": """Create comprehensive test suite for Model Config Manager.

**Test Coverage:**
- Unit tests for all components
- Integration tests
- Performance tests
- Edge case testing

**Acceptance Criteria:**
- > 90% code coverage
- All critical paths tested
- Performance benchmarks met
- CI/CD integration complete
""",
            "priority": 2,  # High
            "tags": ["testing", "quality", "model-config"]
        },
        {
            "name": "Create Documentation",
            "description": """Write comprehensive documentation for Model Config Manager.

**Documentation Needed:**
- API reference
- Usage examples
- Configuration guide
- Troubleshooting guide

**Acceptance Criteria:**
- All APIs documented
- Examples provided
- Configuration options explained
- Published to docs site
""",
            "priority": 3,  # Normal
            "tags": ["documentation", "model-config"]
        },
        {
            "name": "Performance Optimization",
            "description": """Optimize performance of Model Config Manager.

**Optimization Areas:**
- Configuration loading
- Model selection
- Cost tracking
- Memory usage

**Acceptance Criteria:**
- Config load time < 100ms
- Selection time < 10ms
- Memory footprint < 50MB
- No performance regressions
""",
            "priority": 3,  # Normal
            "tags": ["optimization", "performance", "model-config"]
        }
    ]

    created_tasks = []

    for i, task_def in enumerate(task_definitions, 1):
        try:
            print(f"\n   [{i}/{len(task_definitions)}] Creating: {task_def['name']}")

            task = tasks_api.create(
                list_id=list_id,
                name=task_def['name'],
                description=task_def['description'],
                priority=task_def.get('priority', 3),
                tags=task_def.get('tags', [])
            )

            created_tasks.append(task)
            print(f"       ✓ Created task: {task['id']}")

        except Exception as e:
            print(f"       ✗ Error: {e}")

    return created_tasks


def main():
    """Main execution function."""

    print("="*80)
    print("Model Configuration Manager - Documentation & Task Generator")
    print("="*80)

    # Initialize APIs
    client = ClickUpClient()
    docs = DocsAPI(client)
    tasks = TasksAPI(client)
    lists = ListsAPI(client)

    # Create documentation
    doc_id = create_documentation(docs, WORKSPACE_ID)

    # Get list ID (you'll need to provide this)
    list_id = get_list_id(client, SPACE_ID, LIST_NAME)

    # Create tasks
    if list_id:
        created_tasks = create_tasks(tasks, list_id)

        print(f"\n{'='*80}")
        print(f"Summary:")
        print(f"  Documentation: {'✓ Created' if doc_id else '✗ Failed'}")
        if doc_id:
            print(f"    Doc ID: {doc_id}")
        print(f"  Tasks: {len(created_tasks)} created")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print(f"Summary:")
        print(f"  Documentation: {'✓ Created' if doc_id else '✗ Failed'}")
        if doc_id:
            print(f"    Doc ID: {doc_id}")
            print(f"    View at: https://app.clickup.com/{WORKSPACE_ID}/v/dc/{doc_id}")
        print(f"  Tasks: Skipped (no list ID)")
        print(f"\n  To create tasks, provide a valid list ID in the script.")
        print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
