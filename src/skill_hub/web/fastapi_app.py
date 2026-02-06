"""FastAPI-based web UI for skill-hub with HTMX and Tailwind CSS."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from skill_hub.adapters import AdapterRegistry
from skill_hub.discovery import DiscoveryEngine
from skill_hub.models import Config, RepositoryConfig
from skill_hub.remote import RepositoryManager, RepositorySkillScanner
from skill_hub.sync import SyncEngine
from skill_hub.utils import ConfigManager, parse_skill_file_from_path
from skill_hub.i18n import _, init_translation, get_current_language


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(title="skill-hub", version="1.0.0")

    # Templates directory
    templates_dir = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))
    templates.env.globals["_"] = _

    config_manager = ConfigManager()

    def _load_config() -> Config:
        return config_manager.load(silent=True)

    @app.middleware("http")
    async def language_middleware(request: Request, call_next):
        """Set language for each request based on cookie, config, or headers."""
        config = _load_config()

        # Priority: cookie > config.language > Accept-Language header > default
        lang = "en"
        cookie_lang = request.cookies.get("language")
        if cookie_lang in {"en", "zh_CN"}:
            lang = cookie_lang
        elif getattr(config, "language", None) in {"en", "zh_CN"}:
            lang = config.language
        else:
            accept_language = request.headers.get("accept-language", "").lower()
            if "zh" in accept_language:
                lang = "zh_CN"

        init_translation(lang)
        request.state.language = lang

        response = await call_next(request)
        return response

    def _get_language(request: Request) -> str:
        return getattr(request.state, "language", getattr(_load_config(), "language", "en"))

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        """Render main page."""
        language = _get_language(request)
        return templates.TemplateResponse("index.html", {"request": request, "language": language})

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        """Dashboard page fragment."""
        config = _load_config()
        sync_engine = SyncEngine(config)
        skills = sync_engine.list_hub_skills()

        language = _get_language(request)

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "skill_count": len(skills),
                "repo_count": len(config.repositories),
                "language": language,
            },
        )

    @app.get("/sync", response_class=HTMLResponse)
    async def sync_page(request: Request) -> HTMLResponse:
        """Sync page fragment."""
        return templates.TemplateResponse("sync.html", {"request": request})

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

        language = _get_language(request)

        return templates.TemplateResponse(
            "skills.html", {"request": request, "skills": skills_data, "language": language}
        )

    @app.get("/repositories", response_class=HTMLResponse)
    async def repositories(request: Request) -> HTMLResponse:
        """Repositories page fragment."""
        config = _load_config()
        language = _get_language(request)
        return templates.TemplateResponse(
            "repositories.html", {"request": request, "repositories": config.repositories, "language": language}
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
            "pulled": result.skills_synced if mode in ["pull", "both"] else 0,
            "pushed": result.skills_synced if mode in ["push", "both"] else 0,
            "conflicts": result.conflicts_detected,
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

        language = _get_language(request)

        return templates.TemplateResponse(
            "agents.html", {"request": request, "adapters": adapters, "language": language}
        )

    @app.get("/agents/health", response_class=HTMLResponse)
    async def agents_health(request: Request) -> HTMLResponse:
        """Agents health check results fragment."""
        config = _load_config()
        adapter_registry = AdapterRegistry(config)
        health_results = adapter_registry.health_check_all()

        # Build HTML response
        html_parts = []
        html_parts.append('<h3 class="text-xl font-semibold mb-4">Health Check Results</h3>')
        
        if not health_results:
            html_parts.append('<p class="text-gray-500">No health check results available</p>')
        else:
            html_parts.append('<div class="overflow-x-auto">')
            html_parts.append('<table class="min-w-full divide-y divide-gray-200">')
            html_parts.append('<thead class="bg-gray-50">')
            html_parts.append('<tr>')
            html_parts.append('<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>')
            html_parts.append('<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>')
            html_parts.append('<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Global Path</th>')
            html_parts.append('<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Shared Skills</th>')
            html_parts.append('</tr>')
            html_parts.append('</thead>')
            html_parts.append('<tbody class="bg-white divide-y divide-gray-200">')
            
            for agent_name, health in health_results.items():
                enabled = health.get("enabled", False)
                global_path = health.get("global_path", "N/A")
                global_exists = health.get("global_path_exists", False)
                shared_path = health.get("shared_skills_path")
                shared_exists = health.get("shared_skills_exists", False)
                
                status_icon = "✅" if enabled and global_exists else "⚠️"
                status_text = "Active" if enabled and global_exists else "Configured" if enabled else "Disabled"
                status_color = "text-green-600" if enabled and global_exists else "text-yellow-600" if enabled else "text-gray-400"
                
                # Shared skills status
                shared_display = "N/A"
                shared_tooltip = "No shared skills directory found"
                if shared_path:
                    shared_display = f"✓ {shared_path}"
                    shared_tooltip = f"Shared skills directory exists at {shared_path}"
                else:
                    shared_display = "Not found"
                    shared_tooltip = "Create .agents/skills/ in your project root to enable shared skills"
                
                html_parts.append('<tr class="hover:bg-gray-50">')
                html_parts.append(f'<td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900" title="{agent_name} adapter">{agent_name}</td>')
                html_parts.append(f'<td class="px-6 py-4 whitespace-nowrap text-sm {status_color}" title="{status_text}">{status_icon} {status_text}</td>')
                html_parts.append(f'<td class="px-6 py-4 text-sm text-gray-700 font-mono" title="{global_path}">{global_path}</td>')
                html_parts.append(f'<td class="px-6 py-4 text-sm text-gray-700" title="{shared_tooltip}">{shared_display}</td>')
                html_parts.append('</tr>')
            
            html_parts.append('</tbody>')
            html_parts.append('</table>')
            html_parts.append('</div>')
            
            # Add info box about shared skills
            has_shared = any(h.get("shared_skills_exists") for h in health_results.values())
            if has_shared:
                html_parts.append('<div class="mt-4 p-4 bg-green-50 border-l-4 border-green-500 rounded">')
                html_parts.append('<p class="text-sm text-green-800"><strong>✓ Shared skills detected:</strong> Your project has a <code class="px-1 bg-green-100 rounded">.agents/skills/</code> directory. Skills in this directory are available to all agents.</p>')
                html_parts.append('</div>')
            else:
                html_parts.append('<div class="mt-4 p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded">')
                html_parts.append('<p class="text-sm text-yellow-800"><strong>ℹ️ No shared skills found:</strong> Create <code class="px-1 bg-yellow-100 rounded">.agents/skills/</code> in your project root to enable shared, agent-agnostic skills.</p>')
                html_parts.append('</div>')
        
        return HTMLResponse(content="".join(html_parts))

    @app.get("/config", response_class=HTMLResponse)
    async def config_page(request: Request) -> HTMLResponse:
        """Config page fragment."""
        config = _load_config()
        language = _get_language(request)

        return templates.TemplateResponse(
            "config.html",
            {
                "request": request,
                "config": config,
                "language": language,
            },
        )

    @app.post("/set-language")
    async def set_language(request: Request) -> JSONResponse:
        """Update language preference and set cookie."""
        form = await request.form()
        language = form.get("language", "en")

        if language not in {"en", "zh_CN"}:
            language = "en"

        config = _load_config()
        config.language = language
        config_manager.save(config)

        init_translation(language)

        response = JSONResponse({"success": True, "language": language})
        # 1 year
        response.set_cookie("language", language, max_age=31536000)
        return response

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
