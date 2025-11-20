"""Test C# subgraph containment with a realistic example."""

from clickup_framework.commands.map_helpers.language_configs import (
    LanguageConfigManager,
    RelationshipGraph
)

# Realistic C# code example
csharp_code = """
public class TasksClient : ClickUpClient, IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private readonly CacheService _cache;

    public TasksClient(HttpClient httpClient, ILogger logger, CacheService cache)
        : base(httpClient)
    {
        _httpClient = httpClient;
        _logger = logger;
        _cache = cache;
    }

    public async Task<TaskResult> GetTask(string taskId)
    {
        _logger.LogInfo($"Fetching task {taskId}");
        var cached = _cache.Get(taskId);
        if (cached != null) return cached;

        return await GetAsync<TaskResult>($"/task/{taskId}");
    }
}

public abstract class ClickUpClient
{
    protected readonly HttpClient _client;

    protected ClickUpClient(HttpClient client)
    {
        _client = client;
    }

    protected async Task<T> GetAsync<T>(string endpoint)
    {
        var response = await _client.GetAsync(endpoint);
        return JsonSerializer.Deserialize<T>(response);
    }
}

public class CacheService
{
    private readonly Dictionary<string, object> _cache;

    public object Get(string key)
    {
        return _cache.TryGetValue(key, out var value) ? value : null;
    }
}
"""

def main():
    # Load C# config
    manager = LanguageConfigManager()
    csharp_config = manager.get_config("c#")

    if not csharp_config:
        print("Error: C# config not loaded")
        return

    # Extract relationships
    relationships = csharp_config.extract_relationships(csharp_code, "Example.cs")

    print("=" * 80)
    print("C# SUBGRAPH CONTAINMENT TEST")
    print("=" * 80)
    print(f"\nExtracted {len(relationships)} relationships:\n")
    for rel in relationships:
        print(f"  [{rel.type:25}] {rel.source:20} -> {rel.target}")
        if rel.extra_info:
            print(f"                                  [field: {rel.extra_info.get('field_name')}]")

    # Build relationship graph
    graph = RelationshipGraph()
    for rel in relationships:
        graph.add_relationship(rel)

    print("\n" + "=" * 80)
    print("FLAT CLASS DIAGRAM (traditional)")
    print("=" * 80)
    print(graph.to_mermaid_class_diagram())

    print("\n" + "=" * 80)
    print("SUBGRAPH CLASS DIAGRAM (C# containment mode)")
    print("=" * 80)
    print(graph.to_mermaid_class_diagram(csharp_config))

    print("\n" + "=" * 80)
    print("VISUALIZATION NOTES:")
    print("=" * 80)
    print("""
In the subgraph diagram:
- Class members (_httpClient, _logger, _cache) are contained INSIDE their class
- Inheritance (TasksClient -> ClickUpClient) shown as solid arrow outside
- Interface implementation (TasksClient -> IDisposable) shown as dashed arrow
- This matches the user's request: "thisvalue.string should be contained in a
  subgraph for thisvalue and its functions branch off it"
    """)

if __name__ == "__main__":
    main()
