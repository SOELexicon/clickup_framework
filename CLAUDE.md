# ClickUp Framework - Project Configuration

## Project Information
- **Project**: ClickUp Framework
- **Path**: `E:\Projects\clickup_framework`
- **Repository**: https://github.com/yourusername/clickup_framework (update with actual repo)

## ClickUp Configuration

### Workspace & Folder
- **Workspace ID**: `90157903115` (Main)
- **Folder ID**: `901511412221` (ClickUp Framework)

### Lists
- **Development Tasks**: `901517404274` (Primary list for this project)
- **Feature Requests**: `901517404275`
- **Bug Fixes**: `901517404276`
- **Documentation**: `901517404277`
- **Testing**: `901517404278`
- **Releases**: `901517404279`
- **Git**: `901517412318`
- **Lessons**: `901517518536`
- **CLI Commands**: `901517567020`
- **Build**: `901517702407`

## Current Work - Mermaid Generator Improvements

### Parent Epic Task IDs

#### Main Epic
- **Mermaid Generator Improvements - Post Phase 5**: `86c6mqprz`
  - URL: https://app.clickup.com/t/86c6mqprz
  - Description: Parent epic for all post-Phase 5 enhancements
  - Status: In Progress
  - Priority: High (2)

#### Category Epics (Sub-tasks of main epic)

1. **Code Quality & Refactoring**: `86c6mqq1c`
   - URL: https://app.clickup.com/t/86c6mqq1c
   - Focus: Magic numbers extraction, unit tests, maintainability
   - Priority: High (2)

2. **User Experience & Validation**: `86c6mqqdm`
   - URL: https://app.clickup.com/t/86c6mqqdm
   - Focus: Error messages, validation, Mermaid Live Editor integration
   - Priority: High (2)

3. **Performance & Optimization**: `86c6mqqfe`
   - URL: https://app.clickup.com/t/86c6mqqfe
   - Focus: Performance profiling, optimization
   - Priority: High (2)

4. **Features & Enhancements**: `86c6mqqhp`
   - URL: https://app.clickup.com/t/86c6mqqhp
   - Focus: Custom styling, HTML export, diagram diffing
   - Priority: Normal (3)

5. **Automation & Workflow**: `86c6mqqkt`
   - URL: https://app.clickup.com/t/86c6mqqkt
   - Focus: Batch generation pipeline, workflow automation
   - Priority: Normal (3)

## Recent Completed Work

### Phase 5: Generator Classes Separation (Completed)
- **Commit**: `5fa4afd` - Complete Phase 5: Separate all 6 generators into modules
- **Summary**: Modularized all generator classes into separate files
- **Files**: 6 new generator files, modular structure
- **Validator Fixes**: Fixed two critical bugs (closing fence, diagram types)

### TreeBuilder Integration (Completed)
- **Commit**: `d8cf84c` - Integrate TreeBuilder into CodeFlowGenerator
- **Summary**: Replaced placeholder with proper TreeBuilder implementation
- **Impact**: Removed ~49 lines of duplicate code
- **Testing**: Verified with test_treebuilder_integration.md

## Documentation

### Key Documentation Files
- `PHASE5_GENERATOR_SEPARATION_SUMMARY.md` - Phase 5 completion summary
- `clickup_framework/commands/map_helpers/mermaid/generators/` - Generator modules
- `clickup_framework/commands/map_helpers/mermaid/validators/` - Validation helpers

## Quick Commands

### Set Context
```bash
cum set list 901517404274  # Set Development Tasks as current list
```

### Create Subtask
```bash
cum tc "Task Name" --parent <parent_id>
```

### View Task Details
```bash
cum d <task_id>           # View task details
cum d 86c6mqprz          # View main epic
```

## Notes
- Always commit with descriptive technical messages (no Claude Code self-references)
- Update this file when adding new top-level task IDs
- Use tags: `epic`, `mermaid`, `generators`, `post-phase5` for related tasks
