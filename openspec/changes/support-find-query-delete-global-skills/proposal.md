## Why

Global skills are currently managed without dedicated discovery, search, or deletion capabilities, making it difficult for users to effectively manage their skill libraries across multiple projects. Users lack the ability to:
- Search exclusively within global skills (excluding project-local and shared skills)
- Filter skills by keyword or metadata
- Safely delete skills they no longer need

Adding comprehensive find, query, and delete operations for global skills significantly improves usability, helps maintain clean skill registries, prevents skill accumulation overhead, and aligns the tool with standard package management workflows that developers expect.

## What Changes

### New Functional Capabilities
- **Enhanced `skill-hub find` command**: Add `--global-search` flag to filter results to global skills only
- **Query parameter support**: Add `--query` flag for substring matching on skill name, description, and metadata
- **New `skill-hub delete` command**: Interactive CLI for safely removing global skills with confirmation workflows
- **New REST API endpoints**: 
  - `GET /api/skills` - List global skills with filtering
  - `DELETE /api/skills/{skill_name}` - Programmatic skill deletion
- **Safety mechanisms**: Confirmation prompts, force flags, dry-run mode, backup support, and audit logging

### Modified Behaviors
- **Skill discovery engine**: Updated to properly categorize and filter global vs. local vs. shared skills
- **Web UI**: Extended with new management interfaces for global skills
- **Error handling**: Comprehensive error messages and recovery suggestions
- **Logging**: Added audit trail for compliance and debugging

### User-Facing Changes
- CLI users gain powerful new filtering and deletion capabilities
- API users get programmatic access to skill management
- All deletion operations require explicit confirmation (can be bypassed with `--force`)
- Clear feedback on what was deleted and what failed

## Capabilities

### New Capabilities

#### `find-global-skills`
Advanced discovery and filtering of global skills through CLI and API.

**Scope:**
- CLI `--global-search` flag for the existing `find` command
- Substring query matching on skill metadata
- REST API endpoint `GET /api/skills` with filtering parameters
- Integration with AI-powered skill finder
- Pagination support for large skill repositories

**Deliverables:**
- Enhanced CLI command with new flags
- REST API endpoint with query parameters
- Updated skill filtering logic
- Comprehensive test coverage

#### `query-global-skills`
Sophisticated search capabilities for discovering relevant global skills.

**Scope:**
- Case-insensitive substring matching
- Multi-word query support (AND logic)
- Metadata-based filtering (name, description, license, compatibility)
- Relevance scoring and result ranking
- Performance optimization for large repositories

**Deliverables:**
- Query parsing and matching engine
- Integration with AI finder for semantic search
- Result filtering and ranking logic
- API query parameter handling

#### `delete-global-skill`
Safe, auditable deletion of global skills with multiple safety mechanisms.

**Scope:**
- Interactive CLI with confirmation prompts
- Force mode for scripted/automated use
- Dry-run mode for preview
- REST API endpoint with confirmation token workflow
- Permission validation and error handling
- Atomic deletion with rollback capability
- Optional backup creation before deletion
- Comprehensive audit logging
- Multi-adapter support (delete from specific or all adapters)

**Deliverables:**
- CLI `delete` command implementation
- REST API DELETE endpoint
- Safety check utilities
- Backup and rollback mechanisms
- Audit logging system
- Test coverage for all scenarios

### Modified Capabilities

#### `skill-discovery`
Updated to properly handle global skill filtering and categorization.

**Changes:**
- Added `source` classification (global/local/shared) to skill metadata
- Enhanced filtering logic to distinguish skill locations
- Updated search algorithms to respect `--global-search` flag
- Modified result formatting to show skill source

## Impact

### Code Changes
- **`src/skill_hub/cli.py`**: 
  - Add `--global-search` and `--query` flags to `find` command
  - Implement new `delete` command with full workflow
  - Add utility functions for skill filtering
- **`src/skill_hub/web/fastapi_app.py`**:
  - Add `GET /api/skills` endpoint
  - Add `DELETE /api/skills/{skill_name}` endpoint
  - Implement confirmation token mechanism
  - Add request validation and error handling
- **`src/skill_hub/utils/`**:
  - New `deletion.py` module for deletion logic
  - New `backup.py` module for backup management
  - New `audit.py` module for audit logging
  - Enhanced filtering utilities in existing modules
- **`src/skill_hub/discovery/`**:
  - Update skill categorization logic
  - Add source tracking to skill metadata

### API Impact
- **Breaking Changes**: None (all changes are additive)
- **New Endpoints**: 2 (GET /api/skills, DELETE /api/skills/{name})
- **Backward Compatibility**: Fully maintained

### Dependencies
- **New Dependencies**: None (uses existing stdlib and project dependencies)
- **System Requirements**: 
  - Write permissions to global skill directories
  - Optional: OS trash integration for soft delete

### User Impact
- **Learning Curve**: Minimal (follows standard CLI conventions)
- **Migration Required**: None
- **Documentation Updates**: Required (CLI help, API docs, user guide)
- **Training**: Minimal (intuitive commands with clear prompts)

### Risk Assessment
- **Data Loss Risk**: Medium (mitigated by confirmation, backup, dry-run features)
- **Security Risk**: Low (authentication, authorization, audit logging)
- **Performance Risk**: Low (optimized queries, async logging)
- **Adoption Risk**: Low (opt-in features, backward compatible)

### Testing Requirements
- **Unit Tests**: Filter logic, validation, confirmation workflows
- **Integration Tests**: CLI commands, API endpoints, multi-adapter scenarios
- **Safety Tests**: Permission checks, rollback, concurrent operations
- **Security Tests**: Auth bypass attempts, rate limiting, input validation

### Rollout Strategy
1. Deploy with feature flags disabled by default
2. Enable for beta users and gather feedback
3. Iterate based on real-world usage
4. General availability with documentation
5. Monitor audit logs for issues

## Success Metrics

### Adoption Metrics
- 80%+ of users try the new features within first month
- <5% error rate on deletion operations
- Positive user feedback on safety mechanisms

### Quality Metrics
- 95%+ test coverage on new code
- Zero critical bugs in first release
- <100ms API response time for filtering

### Safety Metrics
- 100% of deletions logged in audit trail
- Zero accidental data loss incidents
- Successful rollback on all partial failures

## Out of Scope

The following are explicitly NOT included in this change:
- Soft delete with automatic expiration (future enhancement)
- Batch deletion with wildcards (future enhancement)
- Undelete command for recovery (future enhancement)
- Cross-system replication of deletions (future enhancement)
- Integration with external audit systems (future enhancement)
- Modification of project-local or shared skills (separate change)
