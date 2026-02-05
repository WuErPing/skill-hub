"""Flask-based web interface for skill-hub.

The web UI is a thin wrapper over the existing Python APIs used by the CLI.
It exposes JSON endpoints and a minimal HTML page that can trigger all core
operations: init, sync, discover, list, agents, repo management, and pull.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

from skill_hub.adapters import AdapterRegistry
from skill_hub.discovery import DiscoveryEngine
from skill_hub.models import Config, RepositoryConfig
from skill_hub.remote import RepositoryManager, RepositorySkillScanner
from skill_hub.sync import SyncEngine, SyncResult
from skill_hub.utils import ConfigManager

logger = logging.getLogger(__name__)


INDEX_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>skill-hub Web UI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <!-- Element Plus (Vue 3) via CDN, similar to vue-element-admin stack -->
    <link rel="stylesheet" href="https://unpkg.com/element-plus/dist/index.css" />
    <style>
      body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f2f3f5; }
      .logo-text { font-weight: 600; font-size: 18px; margin-left: 8px; }
      .app-title-small { font-size: 12px; color: #9ca3af; margin-left: 4px; }
      pre.el-code-block { background: #020617; color: #e5e7eb; padding: 10px 14px; border-radius: 4px; max-height: 340px; overflow: auto; font-size: 12px; }
      .json-key { color: #a5b4fc; }
    </style>
    <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
    <script src="https://unpkg.com/element-plus/dist/index.full.global.js"></script>
  </head>
  <body>
    <div id="app">
      <el-config-provider namespace="el">
        <el-container style="height: 100vh;">
          <el-aside width="220px" style="border-right: 1px solid #e5e7eb;">
            <el-menu :default-active="activeMenu" class="el-menu-vertical-demo" @select="onSelectMenu">
              <div style="display:flex;align-items:center;padding:12px 16px 10px;">
                <el-icon><el-icon-setting /></el-icon>
                <span class="logo-text">skill-hub Web UI</span>
              </div>
              <el-menu-item index="dashboard"><el-icon><el-icon-data-board /></el-icon><span>Dashboard</span></el-menu-item>
              <el-menu-item index="sync"><el-icon><el-icon-refresh /></el-icon><span>Sync</span></el-menu-item>
              <el-menu-item index="skills"><el-icon><el-icon-collection /></el-icon><span>Hub Skills</span></el-menu-item>
              <el-menu-item index="repos"><el-icon><el-icon-link /></el-icon><span>Repositories</span></el-menu-item>
              <el-menu-item index="agents"><el-icon><el-icon-user /></el-icon><span>Agents</span></el-menu-item>
              <el-menu-item index="config"><el-icon><el-icon-document /></el-icon><span>Config</span></el-menu-item>
            </el-menu>
          </el-aside>

          <el-container>
            <el-header style="display:flex;align-items:center;justify-content:space-between;padding:0 20px;border-bottom:1px solid #e5e7eb;background:#ffffff;">
              <div style="display:flex;align-items:baseline;">
                <span style="font-weight:500;font-size:16px;">{{ pageTitle }}</span>
                <span class="app-title-small">– unified skills for AI coding agents</span>
              </div>
              <div>
                <el-tag type="info" size="small">localhost UI</el-tag>
              </div>
            </el-header>

            <el-main style="padding:16px 20px 12px;">
              <!-- Dashboard / Quick actions -->
              <template v-if="activeMenu === 'dashboard'">
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-card shadow="hover">
                      <template #header>
                        <span>Quick Start</span>
                      </template>
                      <p>Initialize configuration and pull skills using common defaults.</p>
                      <el-button type="primary" size="small" @click="initConfig({ with_anthropic: true })">Init with Anthropic</el-button>
                      <el-button size="small" @click="runPull()">Pull from repos</el-button>
                      <el-button size="small" @click="runSync('both')">Sync (pull &amp; push)</el-button>
                    </el-card>
                  </el-col>
                  <el-col :span="12">
                    <el-card shadow="hover">
                      <template #header>
                        <span>Status</span>
                      </template>
                      <p><strong>Repositories:</strong> {{ status.repositories }}</p>
                      <p><strong>Hub skills:</strong> {{ status.skills }}</p>
                    </el-card>
                  </el-col>
                </el-row>
              </template>

              <!-- Sync page -->
              <template v-else-if="activeMenu === 'sync'">
                <el-card shadow="hover">
                  <template #header><span>Sync</span></template>
                  <p>Synchronize skills between hub and agents.</p>
                  <el-button type="primary" size="small" @click="runSync('both')">Sync (pull + push)</el-button>
                  <el-button size="small" @click="runSync('pull')">Pull only</el-button>
                  <el-button size="small" @click="runSync('push')">Push only</el-button>
                </el-card>
              </template>

              <!-- Skills page -->
              <template v-else-if="activeMenu === 'skills'">
                <el-card shadow="hover">
                  <template #header><span>Hub Skills</span></template>
                  <p>List of skills in the central hub (~/.skills).</p>
                  <el-button type="primary" size="small" @click="loadSkills">Refresh</el-button>
                  <el-table v-if="skills.length" :data="skills.map(s => ({ name: s }))" style="margin-top:12px;" size="small" border>
                    <el-table-column prop="name" label="Skill" />
                  </el-table>
                  <el-empty v-else description="No skills found" style="margin-top:12px;" />
                </el-card>
              </template>

              <!-- Repos page -->
              <template v-else-if="activeMenu === 'repos'">
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-card shadow="hover">
                      <template #header><span>Add Repository</span></template>
                      <el-form label-width="120px" size="small">
                        <el-form-item label="URL">
                          <el-input v-model="repoForm.url" placeholder="https://github.com/anthropics/skills" />
                        </el-form-item>
                        <el-form-item label="Branch">
                          <el-input v-model="repoForm.branch" placeholder="main" />
                        </el-form-item>
                        <el-form-item label="Subdirectory">
                          <el-input v-model="repoForm.path" placeholder="/skills (optional)" />
                        </el-form-item>
                        <el-form-item>
                          <el-button type="primary" size="small" @click="addRepo">Add repo</el-button>
                          <el-button size="small" @click="runPull">Pull from repos</el-button>
                        </el-form-item>
                      </el-form>
                    </el-card>
                  </el-col>
                  <el-col :span="12">
                    <el-card shadow="hover">
                      <template #header><span>Configured Repositories</span></template>
                      <el-button size="small" @click="listRepos">Refresh</el-button>
                      <el-table v-if="repos.length" :data="repos" style="margin-top:12px;" size="small" border>
                        <el-table-column prop="url" label="URL" />
                        <el-table-column prop="branch" label="Branch" width="100" />
                        <el-table-column prop="enabled" label="Enabled" width="80">
                          <template #default="scope">
                            <el-tag :type="scope.row.enabled ? 'success' : 'info'" size="small">{{ scope.row.enabled ? 'Yes' : 'No' }}</el-tag>
                          </template>
                        </el-table-column>
                      </el-table>
                      <el-empty v-else description="No repositories" style="margin-top:12px;" />
                    </el-card>
                  </el-col>
                </el-row>
              </template>

              <!-- Agents page -->
              <template v-else-if="activeMenu === 'agents'">
                <el-card shadow="hover">
                  <template #header><span>Agents</span></template>
                  <el-button type="primary" size="small" @click="loadAgents(false)">List adapters</el-button>
                  <el-button size="small" @click="loadAgents(true)">Health check</el-button>
                </el-card>
              </template>

              <!-- Config page -->
              <template v-else-if="activeMenu === 'config'">
                <el-card shadow="hover">
                  <template #header><span>Configuration</span></template>
                  <el-button type="primary" size="small" @click="loadConfig">View config</el-button>
                </el-card>
              </template>

              <!-- Output panel (always visible) -->
              <el-card shadow="never" style="margin-top:14px;">
                <template #header><span>Output</span></template>
                <pre class="el-code-block" id="output">Ready.</pre>
              </el-card>
            </el-main>
          </el-container>
        </el-container>
      </el-config-provider>
    </div>

    <script>
      const { createApp, ref, reactive, onMounted, watch } = Vue;
      const { ElMessage } = ElementPlus;

      function show(data) {
        const el = document.getElementById('output');
        const text = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
        el.textContent = text;
      }

      async function api(path, options) {
        const res = await fetch(path, Object.assign({ headers: { 'Content-Type': 'application/json' } }, options || {}));
        const text = await res.text();
        let body;
        try { body = JSON.parse(text); } catch (e) { body = text; }
        return { status: res.status, body };
      }

      createApp({
        setup() {
          const activeMenu = ref('dashboard');
          const pageTitle = ref('Dashboard');
          const status = reactive({ repositories: 0, skills: 0 });
          const skills = ref([]);
          const repos = ref([]);
          const repoForm = reactive({ url: '', branch: 'main', path: '' });

          function setPageTitle() {
            const map = {
              dashboard: 'Dashboard',
              sync: 'Sync',
              skills: 'Hub Skills',
              repos: 'Repositories',
              agents: 'Agents',
              config: 'Configuration',
            };
            pageTitle.value = map[activeMenu.value] || 'Dashboard';
          }

          function onSelectMenu(key) {
            activeMenu.value = key;
            setPageTitle();
          }

          async function loadConfig() {
            const res = await api('/api/config');
            show(res.body);
            if (res.body && res.body.config) {
              status.repositories = (res.body.config.repositories || []).length;
            }
          }

          async function initConfig(opts) {
            const payload = Object.assign({ with_anthropic: false, repos: [] }, opts || {});
            const res = await api('/api/init', { method: 'POST', body: JSON.stringify(payload) });
            show(res.body);
            if (res.status === 200) {
              ElMessage.success('Configuration updated');
              await loadConfig();
            } else {
              ElMessage.error('Failed to init configuration');
            }
          }

          async function runSync(mode) {
            const res = await api('/api/sync', { method: 'POST', body: JSON.stringify({ mode }) });
            show(res.body);
          }

          async function loadSkills() {
            const res = await api('/api/skills');
            show(res.body);
            if (res.body && res.body.skills) {
              skills.value = res.body.skills;
              status.skills = res.body.skills.length;
            }
          }

          async function runPull() {
            const res = await api('/api/pull', { method: 'POST', body: JSON.stringify({}) });
            show(res.body);
          }

          async function listRepos() {
            const res = await api('/api/repos');
            show(res.body);
            if (res.body && res.body.repositories) {
              repos.value = res.body.repositories;
              status.repositories = res.body.repositories.length;
            }
          }

          async function addRepo() {
            if (!repoForm.url.trim()) {
              ElMessage.warning('Please enter repository URL');
              return;
            }
            const payload = { url: repoForm.url, branch: repoForm.branch, path: repoForm.path };
            const res = await api('/api/repos', { method: 'POST', body: JSON.stringify(payload) });
            show(res.body);
            if (res.status === 200 && res.body && res.body.ok) {
              ElMessage.success('Repository added');
              repoForm.url = '';
              await listRepos();
            } else {
              ElMessage.error('Failed to add repository');
            }
          }

          async function loadAgents(check) {
            const res = await api('/api/agents' + (check ? '?check=1' : ''));
            show(res.body);
          }

          onMounted(async () => {
            setPageTitle();
            await loadConfig();
            await loadSkills();
          });

          return {
            activeMenu,
            pageTitle,
            status,
            skills,
            repos,
            repoForm,
            onSelectMenu,
            loadConfig,
            initConfig,
            runSync,
            loadSkills,
            listRepos,
            addRepo,
            loadAgents,
            runPull,
          };
        },
      }).use(ElementPlus).mount('#app');
    </script>
  </body>
</html>
"""


def _serialize_repo_config(repo: RepositoryConfig) -> Dict[str, Any]:
    return {
        "url": repo.url,
        "enabled": repo.enabled,
        "branch": repo.branch,
        "path": repo.path,
        "sync_schedule": repo.sync_schedule,
    }


def _serialize_sync_result(result: SyncResult) -> Dict[str, Any]:
    return {
        "operation": result.operation,
        "skills_synced": result.skills_synced,
        "skills_skipped": result.skills_skipped,
        "conflicts_detected": result.conflicts_detected,
        "errors": result.errors,
        "timestamp": result.timestamp.isoformat(),
    }


def create_app() -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__)  # noqa: WSGI global app
    config_manager = ConfigManager()

    def load_config() -> Config:
        return config_manager.load(silent=True)

    @app.get("/")
    def index() -> str:
        """Serve the main HTML page."""
        # Wrap in Jinja2 raw block so Vue template syntax is not interpreted.
        return render_template_string("{% raw %}" + INDEX_HTML + "{% endraw %}")

    @app.get("/api/config")
    def api_get_config() -> Any:
        """Return current configuration as JSON."""
        config = load_config()
        data: Dict[str, Any] = {
            "version": config.version,
            "conflict_resolution": config.conflict_resolution,
            "repositories": [_serialize_repo_config(r) for r in config.repositories],
            "sync": config.sync,
        }
        return jsonify({"ok": True, "config": data})

    @app.post("/api/init")
    def api_init() -> Any:
        """Initialize configuration.

        Body:
            {
              "with_anthropic": bool,
              "repos": ["https://github.com/...", ...]
            }
        """
        payload = request.get_json(silent=True) or {}
        with_anthropic = bool(payload.get("with_anthropic", False))
        repos: List[str] = payload.get("repos") or []

        config = load_config()
        repo_manager = RepositoryManager()

        added_count = 0

        # Anthropic repo
        if with_anthropic:
            anthropic_url = "https://github.com/anthropics/skills"
            if not any(r.url == anthropic_url for r in config.repositories):
                config.repositories.append(RepositoryConfig(url=anthropic_url))
                added_count += 1

        # Custom repos
        for url in repos:
            if not repo_manager.validate_url(url):
                continue
            if any(r.url == url for r in config.repositories):
                continue
            config.repositories.append(RepositoryConfig(url=url))
            added_count += 1

        if added_count == 0:
            # Nothing changed, just return current state
            return jsonify(
                {
                    "ok": True,
                    "message": "No repositories added",
                    "config": {
                        "repositories": [_serialize_repo_config(r) for r in config.repositories],
                    },
                }
            )

        if not config_manager.save(config):
            return jsonify({"ok": False, "error": "Failed to save configuration"}), 500

        return jsonify(
            {
                "ok": True,
                "message": f"Configuration updated, {added_count} repositories added",
                "config": {
                    "repositories": [_serialize_repo_config(r) for r in config.repositories],
                },
            }
        )

    @app.post("/api/sync")
    def api_sync() -> Any:
        """Run sync operation.

        Body:
            {"mode": "both" | "pull" | "push"}
        """
        payload = request.get_json(silent=True) or {}
        mode = (payload.get("mode") or "both").lower()

        config = load_config()
        sync_engine = SyncEngine(config)

        if mode == "pull":
            result = sync_engine.pull_from_agents()
        elif mode == "push":
            result = sync_engine.push_to_agents()
        else:
            mode = "both"
            result = sync_engine.sync()

        return jsonify({"ok": True, "mode": mode, "result": _serialize_sync_result(result)})

    @app.get("/api/skills")
    def api_list_skills() -> Any:
        """List skills in hub."""
        config = load_config()
        sync_engine = SyncEngine(config)
        skills = sync_engine.list_hub_skills()
        return jsonify({"ok": True, "skills": skills})

    @app.get("/api/discover")
    def api_discover() -> Any:
        """Discover skills from all agents.

        Query params:
            format=json -> return JSON; otherwise return summary.
        """
        as_json = request.args.get("format") == "json"
        config = load_config()
        adapter_registry = AdapterRegistry(config)
        discovery = DiscoveryEngine()

        search_paths: List[Any] = []
        for adapter in adapter_registry.get_enabled_adapters():
            for path in adapter.get_all_search_paths():
                search_paths.append((path, adapter.name))

        registry = discovery.discover_skills(search_paths)

        if as_json:
            return jsonify({"ok": True, "skills": registry.export_json()})

        skills = registry.list_skills()
        summary = {
            "count": len(skills),
            "skills": skills,
            "has_duplicates": registry.has_duplicates(),
        }
        return jsonify({"ok": True, "summary": summary})

    @app.get("/api/agents")
    def api_agents() -> Any:
        """List agents or run health checks.

        Query params:
            check=1 -> run health checks
        """
        do_check = request.args.get("check") in {"1", "true", "True"}
        config = load_config()
        adapter_registry = AdapterRegistry(config)

        if do_check:
            results = adapter_registry.health_check_all()
            return jsonify({"ok": True, "health": results})

        adapters = adapter_registry.list_adapters()
        return jsonify({"ok": True, "adapters": adapters})

    @app.get("/api/repos")
    def api_list_repos() -> Any:
        """List configured repositories."""
        config = load_config()
        repos = [_serialize_repo_config(r) for r in config.repositories]
        return jsonify({"ok": True, "repositories": repos})

    @app.post("/api/repos")
    def api_add_repo() -> Any:
        """Add a repository.

        Body:
            {"url": str, "branch"?: str, "path"?: str}
        """
        payload = request.get_json(silent=True) or {}
        url = (payload.get("url") or "").strip()
        branch = (payload.get("branch") or "main").strip() or "main"
        path = (payload.get("path") or "").strip()

        if not url:
            return jsonify({"ok": False, "error": "Missing 'url'"}), 400

        config = load_config()
        config_manager_local = config_manager
        repo_manager = RepositoryManager()

        if not repo_manager.validate_url(url):
            return jsonify({"ok": False, "error": "Invalid repository URL"}), 400

        for existing in config.repositories:
            if existing.url == url:
                return jsonify({"ok": True, "message": "Repository already configured"})

        config.repositories.append(RepositoryConfig(url=url, branch=branch, path=path))

        if not config_manager_local.save(config):
            return jsonify({"ok": False, "error": "Failed to save configuration"}), 500

        return jsonify(
            {
                "ok": True,
                "message": "Repository added",
                "repository": _serialize_repo_config(config.repositories[-1]),
            }
        )

    @app.delete("/api/repos")
    def api_remove_repo() -> Any:
        """Remove a repository by URL.

        Query params:
            url: repository URL
        """
        url = (request.args.get("url") or "").strip()
        if not url:
            return jsonify({"ok": False, "error": "Missing 'url'"}), 400

        config = load_config()
        config_manager_local = config_manager

        for i, repo in enumerate(config.repositories):
            if repo.url == url:
                config.repositories.pop(i)
                if not config_manager_local.save(config):
                    return jsonify({"ok": False, "error": "Failed to save configuration"}), 500
                return jsonify({"ok": True, "message": "Repository removed"})

        return jsonify({"ok": False, "error": "Repository not found"}), 404

    @app.post("/api/pull")
    def api_pull() -> Any:
        """Pull skills from remote repositories.

        Body (optional):
            {"url": "https://github.com/..."}  # If omitted, pull from all enabled repos
        """
        payload = request.get_json(silent=True) or {}
        url = payload.get("url")

        config = load_config()
        config_manager_local = config_manager
        repo_manager = RepositoryManager()
        scanner = RepositorySkillScanner()
        sync_engine = SyncEngine(config)

        # Check configuration
        if not config_manager_local.exists() and not config.repositories:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "No configuration found",
                        "hint": "Run 'skill-hub init' or use /api/init",
                    }
                ),
                400,
            )

        # Determine repositories to pull
        if url:
            repos = [r for r in config.repositories if r.url == url]
            if not repos:
                return jsonify({"ok": False, "error": "Repository not configured"}), 400
        else:
            repos = [r for r in config.repositories if r.enabled]

        if not repos:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "No enabled repositories to pull from",
                    }
                ),
                400,
            )

        total_skills = 0
        repo_results: List[Dict[str, Any]] = []

        from skill_hub.models import RepositoryMetadata

        for repo_config in repos:
            repo_info: Dict[str, Any] = {"url": repo_config.url, "imported": 0, "errors": []}

            # Clone or update repository
            if not repo_manager.clone_or_update(repo_config):
                repo_info["errors"].append("Failed to sync repository")
                repo_results.append(repo_info)
                continue

            commit_hash = repo_manager.get_commit_hash(repo_config.url)

            # Scan for skills
            repo_dir = repo_manager.get_repository_path(repo_config.url)
            scanned_skills = scanner.scan_repository(repo_dir, repo_config)

            if not scanned_skills:
                repo_results.append(repo_info)
                continue

            skills = scanner.create_skill_objects(scanned_skills, repo_config.url)

            for skill in skills:
                try:
                    sync_engine._sync_skill_to_hub(skill)
                    total_skills += 1
                    repo_info["imported"] += 1
                except Exception as exc:  # pragma: no cover - defensive
                    msg = f"Failed to import '{skill.name}': {exc}"
                    logger.error(msg)
                    repo_info["errors"].append(msg)

            # Save metadata
            metadata = RepositoryMetadata(
                url=repo_config.url,
                branch=repo_config.branch,
                commit_hash=commit_hash,
                last_sync_at=datetime.now().isoformat(),
                skills_imported=[s.name for s in skills],
                sync_count=(
                    repo_manager.load_metadata(repo_config.url).sync_count + 1
                    if repo_manager.load_metadata(repo_config.url)
                    else 1
                ),
            )
            repo_manager.save_metadata(metadata)

            repo_results.append(repo_info)

        return jsonify(
            {
                "ok": True,
                "total_imported": total_skills,
                "repositories": repo_results,
            }
        )

    return app
