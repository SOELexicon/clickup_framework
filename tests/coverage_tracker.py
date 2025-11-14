"""
API Coverage Tracker

Tracks which ClickUp API v2 endpoints are covered by tests.
Compares implemented client methods against the API reference JSON.
"""

import json
import inspect
from typing import Dict, List, Set, Tuple
from clickup_framework import ClickUpClient


def load_api_reference() -> Dict:
    """Load the ClickUp API v2 reference JSON."""
    import os
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "clickup-api-v2-reference.json"
    )

    with open(json_path, "r") as f:
        return json.load(f)


def get_api_endpoints(api_ref: Dict) -> List[Dict]:
    """
    Extract all endpoints from API reference.

    Returns list of dicts with endpoint info:
    - path: API path
    - method: HTTP method (GET, POST, etc.)
    - operation_id: Operation ID from API spec
    - summary: Endpoint summary
    """
    endpoints = []

    for path, path_data in api_ref.get("paths", {}).items():
        for method in ["get", "post", "put", "delete", "patch"]:
            if method in path_data:
                endpoint_data = path_data[method]
                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "operation_id": endpoint_data.get("operationId", ""),
                    "summary": endpoint_data.get("summary", ""),
                    "tags": endpoint_data.get("tags", [])
                })

    return endpoints


def get_client_methods() -> Dict[str, str]:
    """
    Get all public methods from ClickUpClient.

    Returns dict mapping method name to signature.
    """
    methods = {}

    for name, method in inspect.getmembers(ClickUpClient, predicate=inspect.isfunction):
        # Skip private methods and special methods
        if name.startswith("_"):
            continue

        # Get signature
        sig = inspect.signature(method)
        methods[name] = str(sig)

    return methods


def map_endpoints_to_methods(endpoints: List[Dict], methods: Dict[str, str]) -> Dict:
    """
    Map API endpoints to client methods.

    Returns dict with:
    - covered: List of endpoints with corresponding methods
    - uncovered: List of endpoints without methods
    - coverage_percentage: Float percentage
    """
    covered = []
    uncovered = []

    # Create method name variations for matching
    method_names_lower = {name.lower(): name for name in methods.keys()}

    for endpoint in endpoints:
        operation_id = endpoint["operation_id"]

        # Try to find a matching method
        # Convert operation_id to snake_case method name
        method_name_guess = _operation_id_to_method_name(operation_id)

        matched = False

        # Check if method exists (case-insensitive)
        if method_name_guess.lower() in method_names_lower:
            actual_method = method_names_lower[method_name_guess.lower()]
            covered.append({
                **endpoint,
                "client_method": actual_method,
                "signature": methods[actual_method]
            })
            matched = True

        if not matched:
            uncovered.append(endpoint)

    total = len(endpoints)
    covered_count = len(covered)
    coverage_pct = (covered_count / total * 100) if total > 0 else 0

    return {
        "covered": covered,
        "uncovered": uncovered,
        "coverage_percentage": coverage_pct,
        "total_endpoints": total,
        "covered_count": covered_count,
        "uncovered_count": len(uncovered)
    }


def _operation_id_to_method_name(operation_id: str) -> str:
    """
    Convert OperationId to snake_case method name.

    Examples:
        GetTask -> get_task
        CreateTaskComment -> create_task_comment
        AddDependency -> add_task_dependency
    """
    # Insert underscores before capital letters
    import re
    snake = re.sub('([A-Z])', r'_\1', operation_id).lower().lstrip('_')

    # Handle common variations
    replacements = {
        "add_dependency": "add_task_dependency",
        "delete_dependency": "delete_task_dependency",
        "add_task_link": "add_task_link",
        "delete_task_link": "delete_task_link",
        "get_workspace_hierarchy": "get_workspace_hierarchy",
        "get_accessible_custom_fields": "get_accessible_custom_fields",
    }

    return replacements.get(snake, snake)


def save_coverage_json(coverage_data: Dict, filename: str = "coverage.json"):
    """Save coverage data to JSON file."""
    import json
    from datetime import datetime

    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_endpoints": coverage_data["total_endpoints"],
            "covered_count": coverage_data["covered_count"],
            "uncovered_count": coverage_data["uncovered_count"],
            "coverage_percentage": coverage_data["coverage_percentage"]
        },
        "covered_endpoints": coverage_data["covered"],
        "uncovered_endpoints": coverage_data["uncovered"]
    }

    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✓ Saved coverage report to {filename}")


def print_coverage_report(save_json: bool = True):
    """Print a detailed coverage report."""
    print("=" * 80)
    print("ClickUp Framework API Coverage Report")
    print("=" * 80)

    # Load API reference
    api_ref = load_api_reference()
    endpoints = get_api_endpoints(api_ref)

    # Get client methods
    methods = get_client_methods()

    # Map endpoints to methods
    coverage = map_endpoints_to_methods(endpoints, methods)

    # Save to JSON if requested
    if save_json:
        save_coverage_json(coverage)

    print(f"\nTotal API Endpoints: {coverage['total_endpoints']}")
    print(f"Covered by Client: {coverage['covered_count']}")
    print(f"Not Covered: {coverage['uncovered_count']}")
    print(f"Coverage: {coverage['coverage_percentage']:.1f}%")

    print("\n" + "=" * 80)
    print("COVERED ENDPOINTS")
    print("=" * 80)

    # Group by tags
    covered_by_tag = {}
    for endpoint in coverage['covered']:
        tags = endpoint.get('tags', ['Other'])
        for tag in tags:
            if tag not in covered_by_tag:
                covered_by_tag[tag] = []
            covered_by_tag[tag].append(endpoint)

    for tag in sorted(covered_by_tag.keys()):
        print(f"\n{tag}:")
        for endpoint in covered_by_tag[tag]:
            print(f"  ✓ {endpoint['method']:6} {endpoint['path']}")
            print(f"    → {endpoint['client_method']}()")

    print("\n" + "=" * 80)
    print("UNCOVERED ENDPOINTS")
    print("=" * 80)

    # Group by tags
    uncovered_by_tag = {}
    for endpoint in coverage['uncovered']:
        tags = endpoint.get('tags', ['Other'])
        for tag in tags:
            if tag not in uncovered_by_tag:
                uncovered_by_tag[tag] = []
            uncovered_by_tag[tag].append(endpoint)

    for tag in sorted(uncovered_by_tag.keys()):
        print(f"\n{tag}:")
        for endpoint in uncovered_by_tag[tag]:
            print(f"  ✗ {endpoint['method']:6} {endpoint['path']}")
            print(f"    {endpoint['summary']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print_coverage_report()
