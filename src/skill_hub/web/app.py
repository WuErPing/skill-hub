"""Flask app factory."""
import time
from pathlib import Path

from flask import Flask, render_template
from werkzeug.serving import WSGIRequestHandler

from skill_hub import __version__
from skill_hub.web.api import api_bp
from skill_hub.web.repos import load_repos_config, repo_dir
from skill_hub.web.scheduler import scheduler
from skill_hub.web.state import list_skills

# Patch WSGIRequestHandler to log request duration
_original_handle = WSGIRequestHandler.handle
_original_finish = WSGIRequestHandler.finish
_original_log_request = WSGIRequestHandler.log_request


def _patched_handle(self):
    self._request_start = time.time()
    return _original_handle(self)


def _patched_finish(self):
    self._request_duration_ms = (time.time() - self._request_start) * 1000
    return _original_finish(self)


def _patched_log_request(self, code="-", size="-"):
    duration = getattr(self, "_request_duration_ms", 0)
    self.log(
        "info",
        '"%s" %s %s (%.1fms)',
        self.requestline,
        code,
        size,
        duration,
    )


WSGIRequestHandler.handle = _patched_handle
WSGIRequestHandler.finish = _patched_finish
WSGIRequestHandler.log_request = _patched_log_request


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))
    app.register_blueprint(api_bp)

    # Start background scheduler for periodic repo sync checks
    if not scheduler.is_running():
        scheduler.start()

    @app.route("/")
    def index():
        skills = list_skills()
        repos = load_repos_config()
        initial_data = {
            "skills": [
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
                }
                for s in skills
            ],
            "repos": [
                {
                    "url": r.url,
                    "branch": r.branch,
                    "name": r.name,
                    "localPath": str(repo_dir(r)),
                    "hasRemoteUpdates": False,
                    "isLocal": r.is_local,
                    "isCloned": repo_dir(r).exists(),
                }
                for r in repos
            ],
        }
        return render_template(
            "index.html",
            initial_data=initial_data,
            current_version=__version__,
        )

    return app
