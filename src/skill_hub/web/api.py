"""All /api/* endpoints for the skill-hub web UI."""

from flask import Blueprint, jsonify, request

from skill_hub.web.repos import (
    Repo,
    clone_or_pull,
    delete_repo,
    has_remote_updates,
    load_repos_config,
    pull_latest,
    repo_dir,
    save_repos_config,
    sync_mapping,
)
from skill_hub.web.state import install_skill, list_skills, uninstall_skill

api_bp = Blueprint("api", __name__, url_prefix="/api")


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
            "path": str(s.path),
        }
        for s in skills
    ])


@api_bp.route("/skills/<name>/install", methods=["POST"])
def api_install(name: str):
    """Install a skill to both ~/.claude/skills and ~/.agents/skills."""
    skills = list_skills()
    skill = next((s for s in skills if s.name == name), None)
    if not skill:
        return jsonify({"error": f"Skill '{name}' not found"}), 404

    source_path = skill.path
    if not source_path.exists():
        return jsonify({"error": f"Source path not found: {source_path}"}), 400

    success, msg = install_skill(name, source_path)
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
    """List all repos from repos.yaml."""
    repos = load_repos_config()
    return jsonify([
        {
            "url": r.url,
            "branch": r.branch,
            "name": r.name,
            "localPath": str(repo_dir(r)),
        }
        for r in repos
    ])


@api_bp.route("/repos", methods=["POST"])
def add_repo():
    """Add a new repo URL to repos.yaml and clone it."""
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

    # Clone and build skill mapping immediately
    success, msg = sync_mapping(repo)
    if success:
        return jsonify({"ok": True, "message": msg}), 201
    return jsonify({"ok": True, "message": f"Added but sync failed: {msg}"}), 201


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
    updates = []
    for repo in repos:
        if has_remote_updates(repo):
            updates.append({"url": repo.url, "name": repo.name})
    return jsonify({"hasUpdates": len(updates) > 0, "repos": updates})
