# Tasks: Support `.agents/skills` Standard

## Phase 1: Core Adapter Changes

- [x] **Add `get_shared_skills_path()` method to AgentAdapter base class**
  - Implement method that finds `.agents/skills/` in project root (using `find_git_root()`)
  - Return `Path` if directory exists, `None` otherwise
  - Add docstring explaining the method's purpose
  - **Validation**: Unit test confirms method returns correct path when `.agents/skills/` exists
  - **Validation**: Unit test confirms method returns `None` when directory doesn't exist

- [x] **Update `get_all_search_paths()` to include shared skills path**
  - Call `get_shared_skills_path()` and prepend to paths list (highest priority)
  - Only include if path exists (similar to project-local logic)
  - Maintain backward compatibility for projects without `.agents/skills/`
  - **Validation**: Unit test confirms shared path appears first in returned list
  - **Validation**: Unit test confirms agent-specific paths still work without shared path

- [x] **Update `health_check()` to report shared skills status**
  - Add `shared_skills_path` key to health check results
  - Add `shared_skills_exists` boolean to results
  - Set values based on `get_shared_skills_path()` return
  - **Validation**: Unit test confirms health check includes shared skills info
  - **Validation**: Integration test `skill-hub agents --check` shows shared skills status

## Phase 2: Discovery Integration

- [x] **Ensure DiscoveryEngine handles "shared" as agent name**
  - Verify DiscoveryEngine can accept "shared" as agent parameter
  - Update source tracking to use "shared" for `.agents/skills/` discoveries
  - No code changes needed if DiscoveryEngine is agent-agnostic
  - **Validation**: Unit test confirms skills from `.agents/skills/` are tagged with `agent="shared"`
  - **Validation**: Integration test `skill-hub discover` shows shared skills with correct source

- [x] **Test conflict resolution with shared skills**
  - Create test scenario with same skill in `.agents/skills/` and `.cursor/skills/`
  - Verify existing conflict resolution (newest, manual, etc.) handles shared skills
  - Document behavior in test comments
  - **Validation**: Integration test confirms conflict detection works across shared and agent paths
  - **Validation**: Test confirms "newest" resolution picks correct version

## Phase 3: Documentation & Polish

- [x] **Update README.md with `.agents/skills/` standard**
  - Add section explaining `.agents/skills/` directory structure
  - Document when to use shared vs agent-specific paths
  - Provide example project structure
  - **Validation**: Documentation review confirms clarity

- [x] **Update project.md in openspec/**
  - Add `.agents/skills/` to "Skill Discovery Sources" section
  - Note priority order: shared > project-local > global
  - **Validation**: OpenSpec project context is accurate

- [x] **Add example `.agents/skills/` structure to tests**
  - Create fixture with sample shared skills
  - Use in integration tests for realistic scenarios
  - **Validation**: Tests pass and demonstrate shared skills usage

## Phase 4: Validation & Polish

- [x] **Run full test suite**
  - Ensure all existing tests still pass (backward compatibility)
  - Confirm new tests for shared skills pass
  - Check test coverage for new code paths
  - **Validation**: `pytest --cov=skill_hub` shows >80% coverage on new code

- [x] **Manual testing with real project**
  - Create test project with `.agents/skills/` directory
  - Add sample skills and verify discovery works
  - Test `skill-hub discover`, `sync --pull`, `agents --check`
  - **Validation**: All commands work as expected with shared skills

- [x] **Update CHANGELOG or release notes**
  - Document new `.agents/skills/` support as feature addition
  - Note backward compatibility (no breaking changes)
  - Provide migration guidance for teams wanting to adopt standard
  - **Validation**: Release notes are clear and actionable

## Dependencies

- **Parallel work**: All Phase 1 tasks can be done in parallel once `get_shared_skills_path()` is defined
- **Sequential**: Phase 2 depends on Phase 1 completion
- **Sequential**: Phase 3 can start after Phase 2, but Phase 4 requires all previous phases

## Estimated Effort

- Phase 1: 4-6 hours (core implementation)
- Phase 2: 2-3 hours (integration & testing)
- Phase 3: 2-3 hours (documentation)
- Phase 4: 1-2 hours (validation)

**Total**: 9-14 hours (~2 days)
