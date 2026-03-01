"""FastAPI-based web UI for skill-hub with HTMX and Tailwind CSS."""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict
from urllib.parse import unquote

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

app = FastAPI(title="skill-hub", version="1.0.0")
# Global FastAPI app instance

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Templates directory
    templates_dir = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))
    templates.env.globals["_"] = _

    config_manager = ConfigManager()

    def _load_config() -> Config:
        return config_manager.load(silent=True)

    def _save_config(config: Config) -> None:
        """Save configuration to disk."""
        config_manager.save(config)

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
            encoded_path = ""
            if skill_file.exists():
                result = parse_skill_file_from_path(skill_file)
                if result:
                    metadata, _ = result
                    description = metadata.description
                encoded_path = base64.urlsafe_b64encode(str(skill_file).encode()).decode()
            skills_data.append({"name": skill_name, "description": description, "encoded_path": encoded_path})
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
            "repositories.html",
            {"request": request, "repositories": config.repositories, "language": language},
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

    @app.get("/api/skills")
    async def list_global_skills(request: Request) -> Dict[str, Any]:
        """List global skills, optionally filtered by query parameter `query`."""
        config = _load_config()
        adapter_registry = AdapterRegistry(config)
        global_paths = [str(adapter.get_global_path()) for adapter in adapter_registry.get_enabled_adapters()]
        sync_engine = SyncEngine(config)
        skill_names = sync_engine.list_hub_skills()
        results = []
        for name in skill_names:
            skill_dir = sync_engine.hub_path / name
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            if not any(str(skill_dir).startswith(gp) for gp in global_paths):
                continue
            result = parse_skill_file_from_path(skill_file)
            if result:
                metadata, _ = result
                results.append({"name": metadata.name, "description": metadata.description, "path": str(skill_file)})
        query = request.query_params.get("query", "").strip().lower()
        if query:
            results = [r for r in results if query in r["name"].lower() or query in r["description"].lower()]
        return {"success": True, "skills": results}
    @app.get('/global-skills', response_class=HTMLResponse)
    async def global_skills_page(request: Request) -> HTMLResponse:
        """Global skills management page."""
        language = _get_language(request)
        return templates.TemplateResponse(
            "global-skills.html",
            {"request": request, "language": language},
        )

    @app.get('/preview', response_class=HTMLResponse)
    async def preview_landing(request: Request) -> HTMLResponse:
        """Preview landing page - shows skill selection."""
        config = _load_config()
        sync_engine = SyncEngine(config)
        skill_names = sync_engine.list_hub_skills()
        skills_data = []
        for skill_name in skill_names:
            skill_dir = sync_engine.hub_path / skill_name
            skill_file = skill_dir / "SKILL.md"
            description = "N/A"
            encoded_path = ""
            if skill_file.exists():
                result = parse_skill_file_from_path(skill_file)
                if result:
                    metadata, _ = result
                    description = metadata.description
                encoded_path = base64.urlsafe_b64encode(str(skill_file).encode()).decode()
            skills_data.append({"name": skill_name, "description": description, "encoded_path": encoded_path})
        language = _get_language(request)
        return templates.TemplateResponse(
            "preview-landing.html",
            {"request": request, "skills": skills_data, "language": language},
        )

    @app.get('/preview/{encoded_path}', response_class=HTMLResponse)
    async def preview_skill(request: Request, encoded_path: str) -> HTMLResponse:
        """Preview a skill file with markdown rendering."""
        config = _load_config()

        try:
            # Decode the path
            skill_path = base64.urlsafe_b64decode(encoded_path.encode()).decode()
            skill_file = Path(skill_path)

            if not skill_file.exists():
                return templates.TemplateResponse(
                    "preview.html",
                    {
                        "request": request,
                        "skill_name": "Not Found",
                        "error": "Skill file not found",
                        "content": "",
                        "encoded_path": encoded_path,
                        "language": _get_language(request),
                    },
                )

            # Read the skill content
            skill_content = skill_file.read_text(encoding='utf-8')

            # Parse metadata
            result = parse_skill_file_from_path(skill_file)
            metadata = None
            description = None
            if result:
                metadata, _ = result
                description = metadata.description

            # Check if translation is available
            from skill_hub.ai.translator import ContentTranslator
            translator = ContentTranslator(config.ai)
            translation_available, _ = translator.is_available()

            return templates.TemplateResponse(
                "preview.html",
                {
                    "request": request,
                    "skill_name": skill_file.parent.name,
                    "description": description,
                    "content": skill_content,
                    "encoded_path": encoded_path,
                    "metadata": metadata,
                    "file_path": str(skill_file),
                    "translation_available": translation_available,
                    "language": _get_language(request),
                },
            )

        except Exception as e:
            return templates.TemplateResponse(
                "preview.html",
                {
                    "request": request,
                    "skill_name": "Error",
                    "error": f"Error loading skill: {str(e)}",
                    "content": "",
                    "encoded_path": encoded_path,
                    "language": _get_language(request),
                },
            )

    @app.post('/translate/{encoded_path}')
    async def translate_skill(request: Request, encoded_path: str) -> Dict[str, Any]:
        """Translate a skill file to Chinese."""
        config = _load_config()

        try:
            # Decode the path
            skill_path = base64.urlsafe_b64decode(encoded_path.encode()).decode()
            skill_file = Path(skill_path)

            if not skill_file.exists():
                return {"success": False, "message": "Skill file not found"}

            # Read the skill content
            skill_content = skill_file.read_text(encoding='utf-8')

            # Translate using AI
            from skill_hub.ai.translator import ContentTranslator
            translator = ContentTranslator(config.ai)
            available, message = translator.is_available()

            if not available:
                return {"success": False, "message": message}

            translated = translator.translate_to_chinese(skill_content)

            if translated is None:
                return {"success": False, "message": "Translation failed"}

            return {"success": True, "translated_content": translated}

        except Exception as e:
            return {"success": False, "message": f"Translation error: {str(e)}"}

    @app.get('/find', response_class=HTMLResponse)
    async def find_page(request: Request) -> HTMLResponse:
        """AI Skill Finder page fragment."""
        config = _load_config()
        language = _get_language(request)
        return templates.TemplateResponse(
            "find.html",
            {
                "request": request,
                "ai_enabled": config.ai.enabled,
                "ai_provider": config.ai.provider,
                "language": language,
            },
        )

    @app.post('/find')
    async def find_skills_api(request: Request) -> Dict[str, Any]:
        """Find relevant skills using AI-powered search."""
        from skill_hub.ai import AISkillFinder
        form = await request.form()
        query = form.get("query", "").strip()
        top_k = int(form.get("top_k", 5))
        if not query:
            return {"success": False, "message": "Query is required"}
        config = _load_config()
        if not config.ai.enabled:
            return {"success": False, "message": "AI finder is disabled in configuration"}
        finder = AISkillFinder(config)
        available, status = finder.is_available()
        if not available:
            return {"success": False, "message": status}
        matches, error = finder.find_skills(query, top_k=top_k)
        if error:
            return {"success": False, "message": error}
        return {
            "success": True,
            "matches": [
                {
                    "name": m.name,
                    "description": m.description,
                    "score": m.score,
                    "reasoning": m.reasoning,
                    "path": m.path,
                    "encoded_path": base64.urlsafe_b64encode(m.path.encode()).decode(),
                }
                for m in matches
            ],
        }

    @app.get('/agents', response_class=HTMLResponse)
    async def agents_page(request: Request) -> HTMLResponse:
        """Agents page fragment."""
        config = _load_config()
        adapter_registry = AdapterRegistry(config)
        adapters = adapter_registry.list_adapters()
        language = _get_language(request)
        return templates.TemplateResponse(
            "agents.html",
            {"request": request, "adapters": adapters, "language": language},
        )

    @app.get('/agents/health', response_class=HTMLResponse)
    async def agents_health_page(request: Request) -> HTMLResponse:
        """Agents health check results fragment."""
        config = _load_config()
        adapter_registry = AdapterRegistry(config)
        health_results = adapter_registry.health_check_all()
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
                enabled = health.get('enabled', False)
                global_path = health.get('global_path', 'N/A')
                global_exists = health.get('global_path_exists', False)
                shared_path = health.get('shared_skills_path')
                shared_exists = health.get('shared_skills_exists', False)
                status_icon = '✅' if enabled and global_exists else '⚠️'
                status_text = 'Active' if enabled and global_exists else 'Configured' if enabled else 'Disabled'
                status_color = 'text-green-600' if enabled and global_exists else 'text-yellow-600' if enabled else 'text-gray-400'
                shared_display = 'N/A'
                shared_tooltip = 'No shared skills directory found'
                if shared_path:
                    shared_display = f'✓ {shared_path}'
                    shared_tooltip = f'Shared skills directory exists at {shared_path}'
                else:
                    shared_display = 'Not found'
                    shared_tooltip = 'Create .agents/skills/ in your project root to enable shared skills'
                html_parts.append('<tr class="hover:bg-gray-50">')
                html_parts.append(f'<td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900" title="{agent_name} adapter">{agent_name}</td>')
                html_parts.append(f'<td class="px-6 py-4 whitespace-nowrap text-sm {status_color}" title="{status_text}">{status_icon} {status_text}</td>')
                html_parts.append(f'<td class="px-6 py-4 text-sm text-gray-700 font-mono" title="{global_path}">{global_path}</td>')
                html_parts.append(f'<td class="px-6 py-4 text-sm text-gray-700" title="{shared_tooltip}">{shared_display}</td>')
                html_parts.append('</tr>')
            html_parts.append('</tbody>')
            html_parts.append('</table>')
            html_parts.append('</div>')
            has_shared = any(h.get('shared_skills_exists') for h in health_results.values())
            if has_shared:
                html_parts.append('<div class="mt-4 p-4 bg-green-50 border-l-4 border-green-500 rounded">')
                html_parts.append('<p class="text-sm text-green-800"><strong>✓ Shared skills detected:</strong> Your project has a <code class="px-1 bg-green-100 rounded">.agents/skills/</code> directory. Skills in this directory are available to all agents.</p>')
                html_parts.append('</div>')
            else:
                html_parts.append('<div class="mt-4 p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded">')
                html_parts.append('<p class="text-sm text-yellow-800"><strong>ℹ️ No shared skills found:</strong> Create <code class="px-1 bg-yellow-100 rounded">.agents/skills/</code> in your project root to enable shared, agent-agnostic skills.</p>')
                html_parts.append('</div>')
        return HTMLResponse(content=''.join(html_parts))

    @app.get('/config', response_class=HTMLResponse)
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


    @app.delete("/api/skills/{skill_name}")
    async def delete_global_skill(request: Request, skill_name: str) -> Dict[str, Any]:
        """Delete a global skill via API. Requires confirmation via query param `force`."""
        config = _load_config()
        adapter_registry = AdapterRegistry(config)
        force = request.query_params.get("force", "false").lower() == "true"
        for adapter in adapter_registry.get_enabled_adapters():
            global_path = adapter.get_global_path()
            skill_dir = global_path / "skills" / skill_name
            if skill_dir.exists():
                if not force:
                    return {"success": False, "message": f"Deletion requires force=true for {skill_name}"}
                try:
                    import shutil
                    shutil.rmtree(skill_dir)
                    return {"success": True, "message": f"Deleted global skill {skill_name}"}
                except Exception as e:
                    return {"success": False, "message": str(e)}
        return {"success": False, "message": f"Global skill {skill_name} not found"}

    @app.post("/set-language")
    async def set_language(request: Request) -> JSONResponse:
        """Set the language preference."""
        form = await request.form()
        language = form.get("language", "en")
        if language not in {"en", "zh_CN"}:
            return JSONResponse({"success": False, "message": "Invalid language"}, status_code=400)
        response = JSONResponse({"success": True, "language": language})
        response.set_cookie(key="language", value=language, max_age=365 * 24 * 60 * 60, path="/")
        return response

    return app

    return app
