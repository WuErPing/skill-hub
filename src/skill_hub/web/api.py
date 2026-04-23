"""All /api/* endpoints for the skill-hub web UI."""

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import Blueprint, jsonify, request

from skill_hub.web.repos import (
    Repo,
    clone_or_pull,
    delete_repo,
    diagnose_all_repos,
    diagnose_repo,
    get_task,
    has_remote_updates,
    load_repos_config,
    pull_latest,
    repo_dir,
    save_repos_config,
    start_repo_task,
    sync_mapping,
)
from skill_hub.web.scheduler import scheduler
from skill_hub.web.state import install_skill, install_to_one, list_skills, uninstall_skill

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.before_request
def _api_before_request():
    request._start_time = time.time()  # type: ignore[attr-defined]


@api_bp.after_request
def _api_after_request(response):
    duration = (time.time() - request._start_time) * 1000  # type: ignore[attr-defined]
    print(f"  -> {request.method} {request.path} {response.status_code} in {duration:.1f}ms")
    return response


@api_bp.route("/skills", methods=["GET"])
def get_skills():
    """List all skills with their installation status."""
    skills = list_skills()
    return jsonify([
        {
            "name": s.name,
            "repoName": s.repo_name,
            "repoUrl": s.repo_url,
            "status": s.status,
            "inClaude": s.in_claude,
            "inAgents": s.in_agents,
            "claudeMatchesSource": s.claude_matches_source,
            "agentsMatchesSource": s.agents_matches_source,
            "md5Source": s.md5_source,
            "md5Claude": s.md5_claude,
            "md5Agents": s.md5_agents,
            "linkClaude": s.link_claude,
            "linkAgents": s.link_agents,
            "path": str(s.path),
            "conflict": s.conflict,
        }
        for s in skills
    ])


@api_bp.route("/skills/<name>/install", methods=["POST"])
def api_install(name: str):
    """Install a skill to both ~/.claude/skills and ~/.agents/skills."""
    body = request.get_json(silent=True) or {}
    method = body.get("method", "copy")
    if method not in ("copy", "symlink"):
        return jsonify({"error": "method must be 'copy' or 'symlink'"}), 400

    skills = list_skills()
    skill = next((s for s in skills if s.name == name), None)
    if not skill:
        return jsonify({"error": f"Skill '{name}' not found"}), 404

    source_path = skill.path
    if not source_path.exists():
        return jsonify({"error": f"Source path not found: {source_path}"}), 400

    success, msg = install_skill(name, source_path, method=method)
    if success:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"error": msg}), 500


@api_bp.route("/skills/<name>/meta", methods=["GET"])
def api_skill_meta(name: str):
    """Get skill metadata from SKILL.md frontmatter."""
    from skill_hub.utils.yaml_parser import parse_skill_file

    skills = list_skills()
    skill = next((s for s in skills if s.name == name), None)
    if not skill:
        return jsonify({"error": f"Skill '{name}' not found"}), 404

    skill_md = skill.path / "SKILL.md"
    if not skill_md.exists():
        return jsonify({"error": "SKILL.md not found"}), 404

    try:
        content = skill_md.read_text(encoding="utf-8")
        parsed = parse_skill_file(content)
        if parsed is None:
            return jsonify({"error": "Could not parse SKILL.md"}), 422
        metadata, body = parsed
        meta_dict = {
            "name": metadata.name,
            "description": metadata.description,
            "license": metadata.license,
            "compatibility": metadata.compatibility,
        }
        if metadata.metadata:
            meta_dict.update(metadata.metadata)
        return jsonify({"ok": True, "meta": meta_dict, "body": body[:2000]})
    except Exception as e:
        return jsonify({"error": str(e)}), 422


@api_bp.route("/skills/<name>/install-to", methods=["POST"])
def api_install_to(name: str):
    """Install a skill to a single directory ('claude' or 'agents')."""
    body = request.get_json(silent=True) or {}
    target = body.get("target", "").strip()
    method = body.get("method", "copy")
    if target not in ("claude", "agents"):
        return jsonify({"error": "target must be 'claude' or 'agents'"}), 400
    if method not in ("copy", "symlink"):
        return jsonify({"error": "method must be 'copy' or 'symlink'"}), 400

    skills = list_skills()
    skill = next((s for s in skills if s.name == name), None)
    if not skill:
        return jsonify({"error": f"Skill '{name}' not found"}), 404

    source_path = skill.path
    if not source_path.exists():
        return jsonify({"error": f"Source path not found: {source_path}"}), 400

    success, msg = install_to_one(name, source_path, target, method=method)
    if success:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"error": msg}), 500


@api_bp.route("/skills/<name>/uninstall", methods=["POST"])
def api_uninstall(name: str):
    """Uninstall a skill from both directories."""
    success, msg = uninstall_skill(name)
    if success:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"error": msg}), 500


@api_bp.route("/repos", methods=["GET"])
def get_repos():
    """List all repos from repos.yaml with sync status."""
    repos = load_repos_config()
    # Use cached status from scheduler if available, fallback to real-time check
    statuses = scheduler.get_all_statuses()
    results = []
    for r in repos:
        status = statuses.get(r.name)
        if status:
            has_updates = status.has_updates
        elif not r.is_local:
            # Fallback: real-time check if cache miss
            try:
                has_updates = has_remote_updates(r)
            except Exception:
                has_updates = False
        else:
            has_updates = False
        target = repo_dir(r)
        results.append({
            "url": r.url,
            "branch": r.branch,
            "name": r.name,
            "localPath": str(target),
            "hasRemoteUpdates": has_updates,
            "isLocal": r.is_local,
            "isCloned": target.exists() and (target / ".git").exists(),
        })
    return jsonify(results)


@api_bp.route("/repos", methods=["POST"])
def add_repo():
    """Add a new repo URL or local path to repos.yaml and sync it."""
    body = request.get_json() or {}
    url = body.get("url", "").strip()
    branch = body.get("branch", "main").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400

    repos = load_repos_config()
    existing = next((r for r in repos if r.url == url), None)

    if existing is None:
        # New repo: add to config
        repo = Repo(url=url, branch=branch)
        repos.append(repo)
        save_repos_config(repos)
    else:
        # Existing repo: use existing config entry (sync will rebuild mapping)
        repo = existing

    # Sync and build skill mapping immediately
    success, msg = sync_mapping(repo)
    if success:
        return jsonify({"ok": True, "message": msg}), 201
    return jsonify({"ok": True, "message": f"Added but sync failed: {msg}"}), 201


@api_bp.route("/repos/async", methods=["POST"])
def add_repo_async():
    """Start an async clone/pull task for a repo. Returns task_id for polling."""
    body = request.get_json() or {}
    url = body.get("url", "").strip()
    branch = body.get("branch", "main").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400

    # Ensure repo is in config
    repos = load_repos_config()
    existing = next((r for r in repos if r.url == url), None)
    if existing is None:
        repo = Repo(url=url, branch=branch)
        repos.append(repo)
        save_repos_config(repos)

    task = start_repo_task(url, branch)
    return jsonify(task.to_dict()), 202


@api_bp.route("/repos/task/<task_id>", methods=["GET"])
def get_repo_task(task_id: str):
    """Poll the status of an async repo task."""
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task.to_dict())


@api_bp.route("/repos/<path:name>", methods=["DELETE"])
def remove_repo(name: str):
    """Delete a repo from repos.yaml and remove its local directory."""
    repos = load_repos_config()
    repo = next((r for r in repos if r.name == name), None)
    if not repo:
        return jsonify({"error": "Repo not found"}), 404

    success, msg = delete_repo(repo)
    if success:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"error": msg}), 500


@api_bp.route("/repos/sync", methods=["POST"])
def sync_repos():
    """Manually pull latest for all repos."""
    repos = load_repos_config()
    results = []
    for repo in repos:
        ok, msg = pull_latest(repo)
        results.append({"url": repo.url, "ok": ok, "message": msg})
    return jsonify({"ok": True, "results": results})


@api_bp.route("/update-status", methods=["GET"])
def update_status():
    """Check if any repos have remote updates available."""
    repos = load_repos_config()
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {id(r): pool.submit(has_remote_updates, r) for r in repos}
    updates = [
        {"url": r.url, "name": r.name}
        for r in repos
        if futures[id(r)].result()
    ]
    return jsonify({"hasUpdates": len(updates) > 0, "repos": updates})


@api_bp.route("/version", methods=["GET"])
def get_version():
    """Return current version, latest version, and update availability."""
    from skill_hub import __version__
    from skill_hub.version import compare_versions, get_latest_version

    current = __version__
    latest = get_latest_version("wuerping/skill-hub", timeout=5)

    skip_file = Path.home() / ".skills_repo" / "skip_update"
    skipped = False
    if skip_file.exists() and latest:
        skipped = skip_file.read_text().strip() == latest

    has_update = bool(latest and compare_versions(current, latest) < 0 and not skipped)

    return jsonify({
        "current": current,
        "latest": latest,
        "hasUpdate": has_update,
        "skipped": skipped,
    })


@api_bp.route("/settings", methods=["GET"])
def get_settings():
    """Get current settings including scan interval."""
    return jsonify({
        "scanIntervalMinutes": scheduler.scan_interval,
    })


@api_bp.route("/settings", methods=["POST"])
def update_settings():
    """Update settings."""
    body = request.get_json(silent=True) or {}
    interval = body.get("scanIntervalMinutes")
    if interval is not None:
        try:
            interval = int(interval)
            if interval < 1:
                return jsonify({"error": "scanIntervalMinutes must be at least 1"}), 400
            scheduler.scan_interval = interval
        except (ValueError, TypeError):
            return jsonify({"error": "scanIntervalMinutes must be an integer"}), 400
    return jsonify({"ok": True, "scanIntervalMinutes": scheduler.scan_interval})


@api_bp.route("/version/skip", methods=["POST"])
def skip_version():
    """Skip the current latest version notification."""
    body = request.get_json(silent=True) or {}
    version = body.get("version", "").strip()
    if not version:
        return jsonify({"error": "version is required"}), 400

    skip_file = Path.home() / ".skills_repo" / "skip_update"
    skip_file.parent.mkdir(parents=True, exist_ok=True)
    skip_file.write_text(version)
    return jsonify({"ok": True, "skipped": version})


@api_bp.route("/diagnose", methods=["GET"])
def diagnose():
    """Run diagnostics on all repos and return a detailed report."""
    try:
        reports = diagnose_all_repos()
        return jsonify({"ok": True, "reports": reports})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@api_bp.route("/diagnose/<path:name>", methods=["GET"])
def diagnose_one(name: str):
    """Run diagnostics on a specific repo."""
    repos = load_repos_config()
    repo = next((r for r in repos if r.name == name), None)
    if not repo:
        return jsonify({"error": f"Repo '{name}' not found"}), 404

    try:
        report = diagnose_repo(repo)
        return jsonify({"ok": True, "report": report})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
