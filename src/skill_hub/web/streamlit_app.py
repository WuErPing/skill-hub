"""Streamlit-based web UI for skill-hub.

This UI wraps the same Python APIs used by the CLI and Flask web layer.
"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from skill_hub.adapters import AdapterRegistry
from skill_hub.discovery import DiscoveryEngine
from skill_hub.models import Config, RepositoryConfig
from skill_hub.remote import RepositoryManager, RepositorySkillScanner
from skill_hub.sync import SyncEngine
from skill_hub.utils import ConfigManager


def _load_config(config_manager: ConfigManager) -> Config:
    return config_manager.load(silent=True)


def _show_json(title: str, data: Any) -> None:
    st.subheader(title)
    st.json(data)


def _page_dashboard(config_manager: ConfigManager) -> None:
    st.title("Dashboard")

    config = _load_config(config_manager)
    sync_engine = SyncEngine(config)

    cols = st.columns(3)

    with cols[0]:
        st.markdown("**Quick Init**")
        if st.button("Init with Anthropic", use_container_width=True):
            anthropic_url = "https://github.com/anthropics/skills"
            if not any(r.url == anthropic_url for r in config.repositories):
                config.repositories.append(RepositoryConfig(url=anthropic_url))
                if config_manager.save(config):
                    st.success("Configuration updated with Anthropic skills repo")
                else:
                    st.error("Failed to save configuration")
            else:
                st.info("Anthropic repository already configured")

    with cols[1]:
        st.markdown("**Pull from Repos**")
        if st.button("Pull skills from repositories", use_container_width=True):
            _page_pull(config_manager, run_inline=True)

    with cols[2]:
        st.markdown("**Hub Status**")
        skills = sync_engine.list_hub_skills()
        st.metric("Hub skills", len(skills))
        st.metric("Repositories", len(config.repositories))


def _page_sync(config_manager: ConfigManager) -> None:
    st.title("Sync")
    config = _load_config(config_manager)
    sync_engine = SyncEngine(config)

    col1, col2, col3 = st.columns(3)

    if col1.button("Sync (pull + push)", use_container_width=True):
        result = sync_engine.sync()
        _show_json("Sync result", result.__dict__)

    if col2.button("Pull only", use_container_width=True):
        result = sync_engine.pull_from_agents()
        _show_json("Pull result", result.__dict__)

    if col3.button("Push only", use_container_width=True):
        result = sync_engine.push_to_agents()
        _show_json("Push result", result.__dict__)


def _page_skills(config_manager: ConfigManager) -> None:
    st.title("Hub Skills")
    config = _load_config(config_manager)
    sync_engine = SyncEngine(config)

    if st.button("Refresh skills"):
        st.rerun()

    skill_names = sync_engine.list_hub_skills()

    if not skill_names:
        st.info("No skills found in hub (~/.agents/skills)")
        return

    # Build skill data with descriptions
    from skill_hub.utils import parse_skill_file_from_path
    import pandas as pd
    
    st.write(f"**Total Skills:** {len(skill_names)}")
    st.write("")
    
    skills_data = []
    for skill_name in skill_names:
        skill_dir = sync_engine.hub_path / skill_name
        skill_file = skill_dir / "SKILL.md"
        
        description = "N/A"
        if skill_file.exists():
            result = parse_skill_file_from_path(skill_file)
            if result:
                metadata, _ = result
                description = metadata.description
        
        skills_data.append({"Name": skill_name, "Description": description})

    # Use dataframe with optimized column configuration
    df = pd.DataFrame(skills_data)
    st.dataframe(
        df,
        column_config={
            "Name": st.column_config.TextColumn(
                "Skill Name",
                width="small",
                help="Skill identifier"
            ),
            "Description": st.column_config.TextColumn(
                "Description",
                width="large",
                help="What this skill does"
            ),
        },
        use_container_width=True,
        hide_index=True,
        height=600,
    )


def _page_repos(config_manager: ConfigManager) -> None:
    st.title("Repositories")

    config = _load_config(config_manager)
    repo_manager = RepositoryManager()

    st.subheader("Add Repository")
    with st.form("add_repo"):
        url = st.text_input("URL", placeholder="https://github.com/anthropics/skills")
        branch = st.text_input("Branch", value="main")
        path = st.text_input("Subdirectory", value="")
        submitted = st.form_submit_button("Add")

    if submitted:
        if not url:
            st.warning("Please enter repository URL")
        elif not repo_manager.validate_url(url):
            st.error("Invalid repository URL")
        elif any(r.url == url for r in config.repositories):
            st.info("Repository already configured")
        else:
            config.repositories.append(RepositoryConfig(url=url, branch=branch, path=path))
            if config_manager.save(config):
                st.success("Repository added")
            else:
                st.error("Failed to save configuration")

    st.subheader("Configured Repositories")
    if config.repositories:
        st.table(
            {
                "URL": [r.url for r in config.repositories],
                "Branch": [r.branch for r in config.repositories],
                "Enabled": [r.enabled for r in config.repositories],
            }
        )
    else:
        st.info("No repositories configured")

    st.markdown("---")
    if st.button("Pull from repositories"):
        _page_pull(config_manager, run_inline=True)


def _page_agents(config_manager: ConfigManager) -> None:
    st.title("Agents")

    config = _load_config(config_manager)
    adapter_registry = AdapterRegistry(config)

    col1, col2 = st.columns(2)

    if col1.button("List adapters"):
        adapters = adapter_registry.list_adapters()
        _show_json("Adapters", {"adapters": adapters})

    if col2.button("Health check"):
        results = adapter_registry.health_check_all()
        _show_json("Health", results)


def _page_config(config_manager: ConfigManager) -> None:
    st.title("Configuration")

    config = _load_config(config_manager)
    data: Dict[str, Any] = {
        "version": config.version,
        "conflict_resolution": config.conflict_resolution,
        "repositories": [
            {
                "url": r.url,
                "branch": r.branch,
                "enabled": r.enabled,
                "path": r.path,
                "sync_schedule": r.sync_schedule,
            }
            for r in config.repositories
        ],
        "sync": config.sync,
    }
    _show_json("Current config", data)


def _page_discover(config_manager: ConfigManager) -> None:
    st.title("Discovery")

    config = _load_config(config_manager)
    adapter_registry = AdapterRegistry(config)
    discovery = DiscoveryEngine()

    if st.button("Discover skills"):
        search_paths: List[Any] = []
        for adapter in adapter_registry.get_enabled_adapters():
            for path in adapter.get_all_search_paths():
                search_paths.append((path, adapter.name))

        registry = discovery.discover_skills(search_paths)
        _show_json("Discovered skills", registry.export_json())


def _page_pull(config_manager: ConfigManager, run_inline: bool = False) -> None:
    """Pull skills from remote repositories.

    If run_inline is True, render output in the current page; otherwise, use st.write.
    """
    config = _load_config(config_manager)
    repo_manager = RepositoryManager()
    scanner = RepositorySkillScanner()
    sync_engine = SyncEngine(config)

    if not config.repositories:
        st.warning("No repositories configured. Run 'Init with Anthropic' or add a repo first.")
        return

    total_skills = 0
    results: List[Dict[str, Any]] = []

    from skill_hub.models import RepositoryMetadata

    for repo_config in config.repositories:
        info: Dict[str, Any] = {"url": repo_config.url, "imported": 0, "errors": []}

        if not repo_manager.clone_or_update(repo_config):
            info["errors"].append("Failed to sync repository")
            results.append(info)
            continue

        commit_hash = repo_manager.get_commit_hash(repo_config.url)
        repo_dir = repo_manager.get_repository_path(repo_config.url)
        scanned_skills = scanner.scan_repository(repo_dir, repo_config)

        if not scanned_skills:
            results.append(info)
            continue

        skills = scanner.create_skill_objects(scanned_skills, repo_config.url)

        for skill in skills:
            try:
                sync_engine._sync_skill_to_hub(skill)
                total_skills += 1
                info["imported"] += 1
            except Exception as exc:  # pragma: no cover - defensive
                info["errors"].append(f"Failed to import '{skill.name}': {exc}")

        metadata = RepositoryMetadata(
            url=repo_config.url,
            branch=repo_config.branch,
            commit_hash=commit_hash,
            last_sync_at=None,
            skills_imported=[s.name for s in skills],
            sync_count=(
                repo_manager.load_metadata(repo_config.url).sync_count + 1
                if repo_manager.load_metadata(repo_config.url)
                else 1
            ),
        )
        repo_manager.save_metadata(metadata)

        results.append(info)

    data = {"total_imported": total_skills, "repositories": results}
    if run_inline:
        _show_json("Pull result", data)
    else:
        st.write(data)


def _page_find(config_manager: ConfigManager) -> None:
    st.title("AI Skill Finder")

    config = _load_config(config_manager)

    # Status indicator
    if config.ai.enabled:
        st.success(f"AI finder is enabled using **{config.ai.provider}** provider")
    else:
        st.warning("AI finder is disabled. Enable it in configuration.")
        return

    # Search form
    query = st.text_area(
        "Describe your problem or question:",
        placeholder="e.g., How do I handle git merge conflicts? / I need help with React component testing...",
        height=100,
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        top_k = st.selectbox("Results:", [3, 5, 10], index=1)

    if st.button("Find Skills", type="primary", use_container_width=True):
        if not query.strip():
            st.error("Please enter a query")
            return

        from skill_hub.ai import AISkillFinder

        finder = AISkillFinder(config)

        # Check availability
        available, status = finder.is_available()
        if not available:
            st.error(status)
            return

        with st.spinner(f"Searching with {config.ai.provider}..."):
            matches, error = finder.find_skills(query, top_k=top_k)

        if error:
            st.error(f"Error: {error}")
            return

        if not matches:
            st.info("No matching skills found for your query")
            return

        st.write(f"**Found {len(matches)} matching skills:**")
        st.write("")

        for match in matches:
            score_pct = int(match.score * 100)

            with st.expander(f"🎯 **{match.name}** — {score_pct}% match", expanded=True):
                st.progress(match.score, text=f"Relevance: {score_pct}%")
                st.write(f"**Description:** {match.description}")
                st.write(f"**Why this matches:** _{match.reasoning}_")
                if match.path:
                    st.caption(f"📄 Source: `{match.path}`")


def main() -> None:
    st.set_page_config(page_title="skill-hub Web", layout="wide")

    config_manager = ConfigManager()

    st.sidebar.title("skill-hub")
    page = st.sidebar.radio(
        "Navigation",
        (
            "Dashboard",
            "Sync",
            "Hub Skills",
            "AI Finder",
            "Repositories",
            "Agents",
            "Config",
            "Discovery",
        ),
    )

    if page == "Dashboard":
        _page_dashboard(config_manager)
    elif page == "Sync":
        _page_sync(config_manager)
    elif page == "Hub Skills":
        _page_skills(config_manager)
    elif page == "AI Finder":
        _page_find(config_manager)
    elif page == "Repositories":
        _page_repos(config_manager)
    elif page == "Agents":
        _page_agents(config_manager)
    elif page == "Config":
        _page_config(config_manager)
    elif page == "Discovery":
        _page_discover(config_manager)


if __name__ == "__main__":
    main()
