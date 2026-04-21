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
from skill_hub.web.state import install_skill, install_to_one, list_skills, uninstall_skill

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
            "inClaude": s.in_claude,
            "inAgents": s.in_agents,
            "claudeMatchesSource": s.claude_matches_source,
            "agentsMatchesSource": s.agents_matches_source,
            "md5Source": s.md5_source,
            "md5Claude": s.md5_claude,
            "md5Agents": s.md5_agents,
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
    body = request.get_json() or {}
    target = body.get("target", "").strip()
    if target not in ("claude", "agents"):
        return jsonify({"error": "target must be 'claude' or 'agents'"}), 400

    skills = list_skills()
    skill = next((s for s in skills if s.name == name), None)
    if not skill:
        return jsonify({"error": f"Skill '{name}' not found"}), 404

    source_path = skill.path
    if not source_path.exists():
        return jsonify({"error": f"Source path not found: {source_path}"}), 400

    success, msg = install_to_one(name, source_path, target)
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
    return jsonify([
        {
            "url": r.url,
            "branch": r.branch,
            "name": r.name,
            "localPath": str(repo_dir(r)),
            "hasRemoteUpdates": has_remote_updates(r),
            "isLocal": r.is_local,
        }
        for r in repos
    ])


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
