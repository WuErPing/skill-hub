"""FastAPI-based web UI for skill-hub with HTMX and Tailwind CSS."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from skill_hub.adapters import AdapterRegistry
from skill_hub.discovery import DiscoveryEngine
from skill_hub.models import Config, RepositoryConfig
from skill_hub.remote import RepositoryManager, RepositorySkillScanner
from skill_hub.sync import SyncEngine
from skill_hub.utils import ConfigManager, parse_skill_file_from_path


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(title="skill-hub", version="1.0.0")

    # Templates directory
    templates_dir = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))

    config_manager = ConfigManager()

    def _load_config() -> Config:
        return config_manager.load(silent=True)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        """Render main page."""
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        """Dashboard page fragment."""
        config = _load_config()
        sync_engine = SyncEngine(config)
        skills = sync_engine.list_hub_skills()

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "skill_count": len(skills),
                "repo_count": len(config.repositories),
            },
        )

    @app.get("/skills", response_class=HTMLResponse)
    async def skills(request: Request) -> HTMLResponse:
        """Hub skills page fragment."""
        config = _load_config()
        sync_engine = SyncEngine(config)
        skill_names = sync_engine.list_hub_skills()

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

            skills_data.append({"name": skill_name, "description": description})

        return templates.TemplateResponse(
            "skills.html", {"request": request, "skills": skills_data}
        )

    @app.get("/repositories", response_class=HTMLResponse)
    async def repositories(request: Request) -> HTMLResponse:
        """Repositories page fragment."""
        config = _load_config()
        return templates.TemplateResponse(
            "repositories.html", {"request": request, "repositories": config.repositories}
        )

    @app.post("/repositories/add")
    async def add_repository(request: Request) -> Dict[str, Any]:
        """Add a new repository."""
        form = await request.form()
        url = form.get("url", "").strip()
        branch = form.get("branch", "main").strip()
        path = form.get("path", "").strip()

        config = _load_config()
        repo_manager = RepositoryManager()

        if not url:
            return {"success": False, "message": "URL is required"}

        if not repo_manager.validate_url(url):
            return {"success": False, "message": "Invalid repository URL"}

        if any(r.url == url for r in config.repositories):
            return {"success": False, "message": "Repository already exists"}

        config.repositories.append(RepositoryConfig(url=url, branch=branch, path=path))
        if config_manager.save(config):
            return {"success": True, "message": "Repository added successfully"}
        else:
            return {"success": False, "message": "Failed to save configuration"}

    @app.post("/sync")
    async def sync(request: Request) -> Dict[str, Any]:
        """Run sync operation."""
        form = await request.form()
        mode = form.get("mode", "both")

        config = _load_config()
        sync_engine = SyncEngine(config)

        if mode == "pull":
            result = sync_engine.pull_from_agents()
        elif mode == "push":
            result = sync_engine.push_to_agents()
        else:
            result = sync_engine.sync()

        return {
            "success": True,
            "pulled": result.pulled,
            "pushed": result.pushed,
            "conflicts": len(result.conflicts),
        }

    @app.post("/pull")
    async def pull(request: Request) -> Dict[str, Any]:
        """Pull skills from remote repositories."""
        config = _load_config()
        repo_manager = RepositoryManager()
        scanner = RepositorySkillScanner()
        sync_engine = SyncEngine(config)

        if not config.repositories:
            return {"success": False, "message": "No repositories configured"}

        total_skills = 0
        for repo_config in config.repositories:
            if not repo_manager.clone_or_update(repo_config):
                continue

            repo_dir = repo_manager.get_repository_path(repo_config.url)
            scanned_skills = scanner.scan_repository(repo_dir, repo_config)

            if not scanned_skills:
                continue

            skills = scanner.create_skill_objects(scanned_skills, repo_config.url)

            for skill in skills:
                try:
                    sync_engine._sync_skill_to_hub(skill)
                    total_skills += 1
                except Exception:
                    pass

        return {"success": True, "imported": total_skills}

    @app.get("/agents", response_class=HTMLResponse)
    async def agents(request: Request) -> HTMLResponse:
        """Agents page fragment."""
        config = _load_config()
        adapter_registry = AdapterRegistry(config)
        adapters = adapter_registry.list_adapters()

        return templates.TemplateResponse(
            "agents.html", {"request": request, "adapters": adapters}
        )

    @app.get("/config", response_class=HTMLResponse)
    async def config_page(request: Request) -> HTMLResponse:
        """Config page fragment."""
        config = _load_config()
        return templates.TemplateResponse("config.html", {"request": request, "config": config})

    @app.post("/init")
    async def init_config(request: Request) -> Dict[str, Any]:
        """Initialize configuration."""
        form = await request.form()
        with_anthropic = form.get("with_anthropic") == "true"

        config = _load_config()

        if with_anthropic:
            anthropic_url = "https://github.com/anthropics/skills"
            if not any(r.url == anthropic_url for r in config.repositories):
                config.repositories.append(RepositoryConfig(url=anthropic_url))

        if config_manager.save(config):
            return {"success": True, "message": "Configuration initialized"}
        else:
            return {"success": False, "message": "Failed to save configuration"}

    return app
