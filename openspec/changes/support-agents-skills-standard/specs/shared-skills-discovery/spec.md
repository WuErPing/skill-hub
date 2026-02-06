# Spec: Shared Skills Discovery

## ADDED Requirements

### Requirement: AgentAdapter SHALL discover skills from `.agents/skills/` directory

All agent adapters SHALL check for and include the `.agents/skills/` directory when discovering skills in a project.

#### Scenario: Adapter finds `.agents/skills/` in project root

**Given** a project with `.agents/skills/test-skill/SKILL.md`  
**When** `get_all_search_paths()` is called  
**Then** the returned paths must include `<project_root>/.agents/skills`  
**And** the path must appear before agent-specific paths (higher priority)

#### Scenario: Adapter handles missing `.agents/skills/` gracefully

**Given** a project without `.agents/skills/` directory  
**When** `get_all_search_paths()` is called  
**Then** the returned paths must NOT include `.agents/skills`  
**And** the adapter must continue to return agent-specific paths normally

#### Scenario: Shared skills are discovered alongside agent-specific skills

**Given** skills exist in both `.agents/skills/` and `.cursor/skills/`  
**When** `skill-hub discover` is executed  
**Then** skills from both locations must be discovered  
**And** conflict resolution must apply if the same skill exists in multiple locations

### Requirement: Shared skills SHALL be source-tracked separately

Skills discovered from `.agents/skills/` SHALL be tracked with a distinct source identifier to differentiate them from agent-specific skills.

#### Scenario: Skill from `.agents/skills/` is tagged with "shared" source

**Given** a skill `example-skill` in `.agents/skills/example-skill/SKILL.md`  
**When** the skill is discovered  
**Then** its `SkillSource.agent` must be set to `"shared"`  
**And** the path must point to `.agents/skills/example-skill/SKILL.md`

#### Scenario: Source tracking distinguishes shared from agent-specific skills

**Given** skill `foo` exists in both `.agents/skills/foo/` and `.cursor/skills/foo/`  
**When** discovery runs  
**Then** two sources must be registered: one with `agent="shared"`, one with `agent="cursor"`  
**And** the registry must track both sources for conflict detection

### Requirement: Health checks SHALL report `.agents/skills/` status

Agent health checks SHALL include information about whether `.agents/skills/` is present and accessible.

#### Scenario: Health check reports `.agents/skills/` exists

**Given** a project with `.agents/skills/` directory  
**When** `skill-hub agents --check` is executed  
**Then** the output must include `"shared_skills_path": "<project>/.agents/skills"`  
**And** `"shared_skills_exists": true`

#### Scenario: Health check reports `.agents/skills/` is missing

**Given** a project without `.agents/skills/` directory  
**When** `skill-hub agents --check` is executed  
**Then** the output must include `"shared_skills_path": null`  
**And** `"shared_skills_exists": false`

## MODIFIED Requirements

### Requirement: `get_all_search_paths()` SHALL include shared skills path

The base `AgentAdapter.get_all_search_paths()` method SHALL be updated to check for and include `.agents/skills/` when present.

#### Scenario: Search paths are returned in priority order

**Given** a project with `.agents/skills/`, `.cursor/skills/`, and `~/.cursor/skills/`  
**When** `get_all_search_paths()` is called  
**Then** paths must be returned in order:
1. `.agents/skills/`
2. `.cursor/skills/` (project-local)
3. `~/.cursor/skills/` (global)

#### Scenario: Paths are only included if they exist (except global)

**Given** `.agents/skills/` does not exist  
**And** `.cursor/skills/` exists  
**When** `get_all_search_paths()` is called  
**Then** `.agents/skills/` must NOT be in the returned paths  
**And** `.cursor/skills/` must be included  
**And** `~/.cursor/skills/` must be included even if it doesn't exist (when `create_directories=true`)
