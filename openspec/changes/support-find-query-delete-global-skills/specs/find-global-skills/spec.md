# Specification: find-global-skills

## Purpose
Provide enhanced CLI and API capabilities for discovering and querying global skills with advanced filtering options.

## Overview
This specification extends the existing `skill-hub find` command and introduces a new API endpoint to support:
1. Filtering search results to only global skills
2. Query-based substring matching on skill metadata
3. Consistent behavior across CLI and API interfaces

## ADDED Requirements

### Requirement 1: CLI Global Search Flag

#### 1.1 Global-Only Filter
The `skill-hub find` command SHALL accept a `--global-search` flag that restricts search results to skills located in global skill directories only.

**Behavior:**
- When `--global-search` is specified, the command SHALL filter out all skills from:
  - Project-local directories (e.g., `.cursor/skills/`, `.claude/skills/`)
  - Shared `.agents/skills/` directories
- Only skills from adapter global paths (e.g., `~/.cursor/skills/`, `~/.claude/skills/`) SHALL be included in results

#### 1.2 Combination with Existing Flags
The `--global-search` flag SHALL be compatible with existing `find` command flags:
- `--top` / `-n`: Limit number of results
- `--json`: Output results in JSON format
- `--query`: Filter by substring match (see Requirement 2)

**Example Usage:**
```bash
skill-hub find --global-search "git"
skill-hub find --global-search --query "release" --top 10
skill-hub find --global-search --json "docker"
```

#### 1.3 Error Handling
- If no global skills match the search criteria, the command SHALL display a user-friendly message: "No global skills found matching your search"
- If AI finder is disabled or unavailable, the command SHALL fall back to simple text matching with appropriate warning

**Scenario: User searches only global skills**
- **Given** the user has global skills installed across multiple adapters
- **When** they run `skill-hub find --global-search "git"`
- **Then** only skills from global directories are returned
- **And** project-local and shared skills are excluded from results
- **And** results are ranked by AI relevance score (if AI is enabled)

### Requirement 2: Query Parameter Support

#### 2.1 Substring Matching
The `skill-hub find` command SHALL accept an optional `--query` parameter that performs case-insensitive substring matching on:
- Skill name
- Skill description
- Skill metadata (license, compatibility tags)

**Matching Rules:**
- Matching SHALL be case-insensitive ("Git" matches "git")
- Partial matches SHALL be included ("rel" matches "release", "release-process")
- Multiple word queries SHALL match if all words appear in any combination

#### 2.2 Query Processing
The query parameter SHALL be processed as follows:
1. Trim leading/trailing whitespace
2. Convert to lowercase for comparison
3. Split on whitespace for multi-word queries
4. Apply substring matching to each token

**Example Queries:**
- `"git"` → matches skills with "git" anywhere in name/description
- `"release process"` → matches skills containing both "release" AND "process"
- `"docker ci"` → matches skills with both terms in any order

#### 2.3 Performance Considerations
- For large skill repositories (>100 skills), query matching SHALL be optimized to avoid full scans when possible
- Results SHALL be cached for the duration of the command execution

**Scenario: User filters by query string**
- **Given** 50+ global skills exist with varied descriptions
- **When** the user runs `skill-hub find --global-search --query "release"`
- **Then** only skills with "release" in name, description, or metadata are returned
- **And** matching is case-insensitive
- **And** results are sorted by relevance score (AI) or alphabetically (fallback)

### Requirement 3: API Endpoint for Global Skills

#### 3.1 Endpoint Definition
The system SHALL provide a RESTful API endpoint:
```
GET /api/skills
```

**Query Parameters:**
- `query` (optional): Substring filter (same behavior as CLI `--query`)
- `global` (optional): If `true` or `1`, filter to global skills only
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

#### 3.2 Response Format
The endpoint SHALL return a JSON response with the following structure:
```json
{
  "success": true,
  "skills": [
    {
      "name": "skill-name",
      "description": "Brief description",
      "path": "/absolute/path/to/skill",
      "source": "global",
      "adapter": "cursor"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

**Field Descriptions:**
- `name`: Skill identifier (kebab-case)
- `description`: Skill description from SKILL.md frontmatter
- `path`: Absolute filesystem path to SKILL.md file
- `source`: Location type ("global", "local", or "shared")
- `adapter`: Adapter name if applicable (e.g., "cursor", "claude")

#### 3.3 Authentication and Authorization
- The endpoint SHALL require authentication if the server is configured with auth
- Unauthenticated requests SHALL receive HTTP 401 response
- Rate limiting SHALL be applied (default: 100 requests/minute)

#### 3.4 Error Responses
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

**Error Codes:**
- `INVALID_QUERY`: Query parameter validation failed
- `AUTH_REQUIRED`: Authentication required but not provided
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Unexpected server error

**Scenario: API client requests global skills**
- **Given** the FastAPI server is running with 100+ skills
- **When** a GET request is made to `/api/skills?query=test&global=true&limit=10`
- **Then** JSON response contains up to 10 global skills matching "test"
- **And** response includes pagination metadata
- **And** each skill includes name, description, path, and source information

### Requirement 4: Integration with AI Skill Finder

#### 4.1 AI-Enhanced Filtering
When AI finder is enabled, the `--global-search` and `--query` options SHALL work in conjunction with AI-powered relevance scoring:
- AI SHALL consider only global skills when `--global-search` is specified
- Query terms SHALL be used as additional context for AI ranking
- Final results SHALL be sorted by AI score, then filtered by query match

#### 4.2 Fallback Behavior
If AI provider is unavailable or returns an error:
- System SHALL fall back to simple substring matching
- User SHALL be notified with a warning message
- Results SHALL still respect `--global-search` filter

## Acceptance Criteria

### CLI Acceptance Criteria
- [ ] `skill-hub find --global-search <query>` returns only global skills
- [ ] `skill-hub find --global-search --query "test"` filters by substring match
- [ ] `skill-hub find --global-search --json` outputs valid JSON with global skills only
- [ ] Error messages are clear when no global skills match
- [ ] AI finder integration respects global-only filter
- [ ] Fallback to text matching works correctly when AI is unavailable

### API Acceptance Criteria
- [ ] GET `/api/skills?global=true` returns only global skills
- [ ] GET `/api/skills?query=test&global=true` filters and matches correctly
- [ ] Response includes all required fields (name, description, path, source)
- [ ] Pagination works correctly with limit and offset parameters
- [ ] Error responses follow defined format
- [ ] Rate limiting is enforced
- [ ] Authentication is required when configured

### Performance Acceptance Criteria
- [ ] CLI command completes in <2 seconds for up to 200 global skills
- [ ] API endpoint responds in <500ms for up to 500 global skills
- [ ] Query matching scales linearly with skill count
- [ ] Memory usage remains stable for large skill repositories

## Implementation Notes

### Code Organization
- CLI flag parsing: `src/skill_hub/cli.py` (extend existing `find` command)
- API endpoint: `src/skill_hub/web/fastapi_app.py` (add `list_global_skills`)
- Filtering logic: Extract to reusable utility in `src/skill_hub/utils/`

### Testing Strategy
1. Unit tests for filter logic
2. Integration tests for CLI command
3. API endpoint tests with various query combinations
4. Performance tests with large skill datasets

### Backward Compatibility
- All existing `find` command functionality SHALL remain unchanged
- New flags are optional and do not affect default behavior
- API endpoint is additive (no breaking changes to existing endpoints)
