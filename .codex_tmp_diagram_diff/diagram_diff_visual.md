# Diagram Diff Visual Summary

This report renders a Mermaid summary diagram with color-coded change buckets.

```mermaid
flowchart TD
    BASE["Baseline\nbefore.mmd\ngraph\n1 nodes / 1 edges"]
    CUR["Current\nafter.mmd\ngraph\n1 nodes / 2 edges"]
    ADD["Added\n1\nedge:1"]
    REM["Removed\n0\nnone"]
    MOD["Modified\n1\nedge:1"]
    BASE --> CUR
    CUR --> ADD
    CUR --> REM
    CUR --> MOD
    style ADD fill:#dcfce7,stroke:#16a34a,color:#166534
    style REM fill:#fee2e2,stroke:#dc2626,color:#991b1b
    style MOD fill:#fef3c7,stroke:#ca8a04,color:#92400e
```

## Added Elements

- **Kinds:** edge:1
- `L3` [edge] `B --> C[Added]`

## Modified Elements

- **Kinds:** edge:1
- `L2` `A[Start] --> B[Old]`
  - becomes `L2` `A[Start] --> B[New]`

## Unified Diff

```diff
--- before.mmd
+++ after.mmd
@@ -1,2 +1,3 @@
 graph TD

-    A[Start] --> B[Old]

+    A[Start] --> B[New]

+    B --> C[Added]
```
