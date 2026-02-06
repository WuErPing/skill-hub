"""Tests for shared skills (.agents/skills) functionality."""

import tempfile
from pathlib import Path

import pytest

from skill_hub.adapters.base import AgentAdapter
from skill_hub.adapters.cursor import CursorAdapter
from skill_hub.discovery.engine import DiscoveryEngine
from skill_hub.models import AgentConfig, SkillMetadata


class TestSharedSkillsPath:
    """Tests for get_shared_skills_path() method."""

    def test_shared_path_exists(self, tmp_path: Path) -> None:
        """Test get_shared_skills_path() returns path when .agents/skills exists."""
        # Create .agents/skills directory
        agents_skills = tmp_path / ".agents" / "skills"
        agents_skills.mkdir(parents=True)
        
        # Create .git directory to simulate git root
        (tmp_path / ".git").mkdir()
        
        # Create adapter
        config = AgentConfig(enabled=True)
        adapter = CursorAdapter(config)
        
        # Get shared path
        shared_path = adapter.get_shared_skills_path(start_dir=tmp_path)
        
        assert shared_path is not None
        assert shared_path == tmp_path / ".agents"

    def test_shared_path_missing_skills_dir(self, tmp_path: Path) -> None:
        """Test get_shared_skills_path() returns None when .agents exists but skills/ doesn't."""
        # Create .agents but not skills subdirectory
        agents_dir = tmp_path / ".agents"
        agents_dir.mkdir()
        
        # Create .git directory
        (tmp_path / ".git").mkdir()
        
        config = AgentConfig(enabled=True)
        adapter = CursorAdapter(config)
        
        shared_path = adapter.get_shared_skills_path(start_dir=tmp_path)
        
        assert shared_path is None

    def test_shared_path_missing_agents_dir(self, tmp_path: Path) -> None:
        """Test get_shared_skills_path() returns None when .agents doesn't exist."""
        # Create .git directory but no .agents
        (tmp_path / ".git").mkdir()
        
        config = AgentConfig(enabled=True)
        adapter = CursorAdapter(config)
        
        shared_path = adapter.get_shared_skills_path(start_dir=tmp_path)
        
        assert shared_path is None

    def test_shared_path_no_git_root(self, tmp_path: Path) -> None:
        """Test get_shared_skills_path() returns None when not in a git repository."""
        # Create .agents/skills but no .git
        agents_skills = tmp_path / ".agents" / "skills"
        agents_skills.mkdir(parents=True)
        
        config = AgentConfig(enabled=True)
        adapter = CursorAdapter(config)
        
        shared_path = adapter.get_shared_skills_path(start_dir=tmp_path)
        
        assert shared_path is None


class TestSharedSkillsInSearchPaths:
    """Tests for shared skills in get_all_search_paths()."""

    def test_shared_path_appears_first(self, tmp_path: Path) -> None:
        """Test shared path appears first (highest priority) in search paths."""
        # Setup git root with .agents/skills
        (tmp_path / ".git").mkdir()
        agents_skills = tmp_path / ".agents" / "skills"
        agents_skills.mkdir(parents=True)
        
        # Setup cursor project path
        cursor_skills = tmp_path / ".cursor" / "skills"
        cursor_skills.mkdir(parents=True)
        
        config = AgentConfig(enabled=True)
        adapter = CursorAdapter(config)
        
        # Set the start_dir for search paths context
        import os
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            paths = adapter.get_all_search_paths()
            
            # Shared path should be first
            assert len(paths) >= 2
            assert paths[0] == tmp_path / ".agents"
        finally:
            os.chdir(original_dir)

    def test_search_paths_without_shared(self, tmp_path: Path) -> None:
        """Test search paths work without shared skills directory (backward compatibility)."""
        # Setup git root but no .agents/skills
        (tmp_path / ".git").mkdir()
        
        # Setup cursor project path
        cursor_skills = tmp_path / ".cursor" / "skills"
        cursor_skills.mkdir(parents=True)
        
        config = AgentConfig(enabled=True)
        adapter = CursorAdapter(config)
        
        # Set the start_dir for search paths context
        import os
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            paths = adapter.get_all_search_paths()
            
            # Should still return agent-specific paths
            assert len(paths) >= 1
            # Shared path should not be in the list
            assert tmp_path / ".agents" not in paths
        finally:
            os.chdir(original_dir)


class TestSharedSkillsDiscovery:
    """Tests for discovering skills from .agents/skills with 'shared' agent tag."""

    def test_shared_skills_tagged_correctly(self, tmp_path: Path) -> None:
        """Test skills from .agents/skills are tagged with agent='shared'."""
        # Setup .agents/skills with a test skill
        agents_skills = tmp_path / ".agents" / "skills"
        test_skill = agents_skills / "test-skill"
        test_skill.mkdir(parents=True)
        
        skill_file = test_skill / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill from shared location
---

# Test Skill

This is a test skill from .agents/skills.
""")
        
        # Run discovery with 'shared' agent name
        engine = DiscoveryEngine()
        search_paths = [(tmp_path / ".agents", "shared")]
        registry = engine.discover_skills(search_paths)
        
        # Verify skill was discovered with 'shared' agent tag
        skill = registry.get_skill("test-skill")
        assert skill is not None
        assert len(skill.sources) == 1
        assert skill.sources[0].agent == "shared"
        assert skill.sources[0].path == skill_file

    def test_mixed_shared_and_agent_specific_skills(self, tmp_path: Path) -> None:
        """Test discovery works with both shared and agent-specific skills."""
        # Setup .agents/skills with shared skill
        agents_skills = tmp_path / ".agents" / "skills"
        shared_skill = agents_skills / "shared-skill"
        shared_skill.mkdir(parents=True)
        (shared_skill / "SKILL.md").write_text("""---
name: shared-skill
description: Shared skill
---

# Shared Skill
""")
        
        # Setup .cursor/skills with cursor-specific skill
        cursor_skills = tmp_path / ".cursor" / "skills"
        cursor_skill = cursor_skills / "cursor-skill"
        cursor_skill.mkdir(parents=True)
        (cursor_skill / "SKILL.md").write_text("""---
name: cursor-skill
description: Cursor-specific skill
---

# Cursor Skill
""")
        
        # Run discovery with both paths
        engine = DiscoveryEngine()
        search_paths = [
            (tmp_path / ".agents", "shared"),
            (tmp_path / ".cursor", "cursor"),
        ]
        registry = engine.discover_skills(search_paths)
        
        # Verify both skills discovered with correct tags
        shared = registry.get_skill("shared-skill")
        assert shared is not None
        assert shared.sources[0].agent == "shared"
        
        cursor = registry.get_skill("cursor-skill")
        assert cursor is not None
        assert cursor.sources[0].agent == "cursor"


class TestHealthCheckSharedSkills:
    """Tests for health check reporting shared skills status."""

    def test_health_check_with_shared_skills(self, tmp_path: Path) -> None:
        """Test health check reports shared skills when present."""
        # Setup git root with .agents/skills
        (tmp_path / ".git").mkdir()
        agents_skills = tmp_path / ".agents" / "skills"
        agents_skills.mkdir(parents=True)
        
        config = AgentConfig(enabled=True)
        adapter = CursorAdapter(config)
        
        # Change to tmp_path to simulate running in that directory
        import os
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            results = adapter.health_check()
            
            assert "shared_skills_path" in results
            assert results["shared_skills_path"] == str(tmp_path / ".agents")
            assert "shared_skills_exists" in results
            assert results["shared_skills_exists"] is True
        finally:
            os.chdir(original_dir)

    def test_health_check_without_shared_skills(self, tmp_path: Path) -> None:
        """Test health check when shared skills not present."""
        # Setup git root but no .agents/skills
        (tmp_path / ".git").mkdir()
        
        config = AgentConfig(enabled=True)
        adapter = CursorAdapter(config)
        
        # Change to tmp_path to simulate running in that directory
        import os
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            results = adapter.health_check()
            
            assert "shared_skills_path" in results
            assert results["shared_skills_path"] is None
            assert "shared_skills_exists" in results
            assert results["shared_skills_exists"] is False
        finally:
            os.chdir(original_dir)


class TestConflictResolution:
    """Tests for conflict resolution between shared and agent-specific skills."""

    def test_same_skill_different_locations(self, tmp_path: Path) -> None:
        """Test that same skill in multiple locations is tracked as duplicate."""
        # Create same skill in both .agents/skills and .cursor/skills
        agents_skills = tmp_path / ".agents" / "skills"
        test_skill_shared = agents_skills / "test-skill"
        test_skill_shared.mkdir(parents=True)
        (test_skill_shared / "SKILL.md").write_text("""---
name: test-skill
description: Test skill from shared location
---

# Test Skill (Shared)

Version A content.
""")
        
        cursor_skills = tmp_path / ".cursor" / "skills"
        test_skill_cursor = cursor_skills / "test-skill"
        test_skill_cursor.mkdir(parents=True)
        (test_skill_cursor / "SKILL.md").write_text("""---
name: test-skill
description: Test skill from cursor location
---

# Test Skill (Cursor)

Version A content.
""")
        
        # Discover from both locations
        engine = DiscoveryEngine()
        search_paths = [
            (tmp_path / ".agents", "shared"),
            (tmp_path / ".cursor", "cursor"),
        ]
        registry = engine.discover_skills(search_paths)
        
        # Skill should be discovered
        skill = registry.get_skill("test-skill")
        assert skill is not None
        
        # Should have 2 sources
        assert len(skill.sources) == 2
        sources_agents = [src.agent for src in skill.sources]
        assert "shared" in sources_agents
        assert "cursor" in sources_agents

    def test_conflict_detection_different_content(self, tmp_path: Path) -> None:
        """Test conflict detection when same skill has different content."""
        # Create same skill with DIFFERENT content in .agents/skills and .cursor/skills
        agents_skills = tmp_path / ".agents" / "skills"
        test_skill_shared = agents_skills / "test-skill"
        test_skill_shared.mkdir(parents=True)
        (test_skill_shared / "SKILL.md").write_text("""---
name: test-skill
description: Test skill
---

# Test Skill

Version A content from shared location.
""")
        
        cursor_skills = tmp_path / ".cursor" / "skills"
        test_skill_cursor = cursor_skills / "test-skill"
        test_skill_cursor.mkdir(parents=True)
        (test_skill_cursor / "SKILL.md").write_text("""---
name: test-skill
description: Test skill
---

# Test Skill

Version B content from cursor location.
""")
        
        # Discover from both locations
        engine = DiscoveryEngine()
        search_paths = [
            (tmp_path / ".agents", "shared"),
            (tmp_path / ".cursor", "cursor"),
        ]
        registry = engine.discover_skills(search_paths)
        
        # Conflict should be detected
        assert registry.has_duplicates()
        assert "test-skill" in registry.duplicates
        
        # Duplicates list should contain both sources
        duplicates = registry.duplicates["test-skill"]
        assert len(duplicates) == 2
        duplicate_agents = [src.agent for src in duplicates]
        assert "shared" in duplicate_agents
        assert "cursor" in duplicate_agents

    def test_priority_shared_first(self, tmp_path: Path) -> None:
        """Test that shared path is checked first (highest priority)."""
        # Create skill only in shared location
        agents_skills = tmp_path / ".agents" / "skills"
        test_skill = agents_skills / "shared-only-skill"
        test_skill.mkdir(parents=True)
        (test_skill / "SKILL.md").write_text("""---
name: shared-only-skill
description: Only in shared location
---

# Shared Only Skill
""")
        
        # Discover with shared path first (as get_all_search_paths does)
        engine = DiscoveryEngine()
        search_paths = [
            (tmp_path / ".agents", "shared"),  # First - highest priority
            (tmp_path / ".cursor", "cursor"),   # Second
        ]
        registry = engine.discover_skills(search_paths)
        
        # Skill should be discovered from shared
        skill = registry.get_skill("shared-only-skill")
        assert skill is not None
        assert len(skill.sources) == 1
        assert skill.sources[0].agent == "shared"

    def test_no_conflict_same_content(self, tmp_path: Path) -> None:
        """Test that same skill with identical content is not flagged as conflict."""
        same_content = """---
name: test-skill
description: Test skill
---

# Test Skill

Exact same content.
"""
        
        # Create same skill with IDENTICAL content
        agents_skills = tmp_path / ".agents" / "skills"
        test_skill_shared = agents_skills / "test-skill"
        test_skill_shared.mkdir(parents=True)
        (test_skill_shared / "SKILL.md").write_text(same_content)
        
        cursor_skills = tmp_path / ".cursor" / "skills"
        test_skill_cursor = cursor_skills / "test-skill"
        test_skill_cursor.mkdir(parents=True)
        (test_skill_cursor / "SKILL.md").write_text(same_content)
        
        # Discover from both locations
        engine = DiscoveryEngine()
        search_paths = [
            (tmp_path / ".agents", "shared"),
            (tmp_path / ".cursor", "cursor"),
        ]
        registry = engine.discover_skills(search_paths)
        
        # Skill should be discovered
        skill = registry.get_skill("test-skill")
        assert skill is not None
        assert len(skill.sources) == 2
        
        # No conflict should be detected (same content = same checksum)
        assert not registry.has_duplicates()
