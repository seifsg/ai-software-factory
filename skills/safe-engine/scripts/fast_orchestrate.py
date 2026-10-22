"""Orchestrator setup: let a scheduler start factory sessions, with the gate enforced.

fast_gate.py orchestrate paperclip --agent claude|codex --company ID --project DIR [--api URL] [--name NAME]
    [--base-ref REF] [--timeout SEC] [--token-env VAR] [--dry-run]
1. Installs the factory for the agent. Codex gets its own CODEX_HOME holding the gate hooks: an orchestrator's
   per-agent home lacks the user's hooks.json. The owner trusts those hooks once in that home (/hooks).
2. Writes the instructions file the orchestrator injects on every wake. It routes each task into safe-engine's
   orchestrated run with this orchestrator's binding.
3. Creates or updates the agent through the orchestrator's API, matched by name. --dry-run prints it instead.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
AGENTS = {"claude": ("claude_local", "Claude Code"), "codex": ("codex_local", "Codex")}
INSTRUCTIONS = """# Factory engineer

{title} started you. Use `safe-engine` for every task as an orchestrated run with the `{name}` binding: follow its
`references/orchestrated-run.md` and `references/{name}.md`. Never work on a task without it.
"""


def home():
    return Path(os.environ.get("SAFE_ENGINE_HOME") or Path.home() / ".safe-engine")


def arguments(parser):
    """Flags shared by every orchestrator; the first positional picks the binding."""
    parser.add_argument("orchestrator", choices=sorted(ORCHESTRATORS))
    parser.add_argument("--agent", required=True, choices=sorted(AGENTS))
    parser.add_argument("--company", required=True, help="The orchestrator's company or workspace id")
    parser.add_argument("--project", required=True, help="The product repository the agent works in")
    parser.add_argument("--api", default="http://127.0.0.1:3100")
    parser.add_argument("--name", help="Agent name; default: Factory engineer (<agent>)")
    parser.add_argument("--base-ref", help="Branch new worktrees start from; default: origin's HEAD")
    parser.add_argument("--timeout", type=int, default=3600, help="Seconds per wake")
    parser.add_argument("--token-env", default="PAPERCLIP_BOARD_TOKEN", help="Env var holding a board API key")
    parser.add_argument("--dry-run", action="store_true", help="Print the agent instead of installing or sending")


def run(args, log=print, opener=urllib.request.urlopen):
    return ORCHESTRATORS[args.orchestrator](args, log, opener)


def base_ref(project):
    """origin's default branch (origin/main), or None to let the orchestrator decide."""
    result = subprocess.run(["git", "-C", str(project), "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
                            capture_output=True, text=True)
    return result.stdout.strip() or None


def codex_home(root, user=None):
    """A self-managed CODEX_HOME: the user's Codex login and settings, plus the gate hooks written later."""
    target, user = root / "codex-home", Path(user or Path.home() / ".codex")
    target.mkdir(parents=True, exist_ok=True)
    if (user / "auth.json").is_file() and not (target / "auth.json").exists():
        (target / "auth.json").symlink_to(user / "auth.json")  # one login, refreshed in place
    if (user / "config.toml").is_file() and not (target / "config.toml").exists():
        shutil.copyfile(user / "config.toml", target / "config.toml")
    return target


def paperclip(args, log, opener):
    project = Path(args.project).resolve()
    if not (project / ".git").exists():
        raise SystemExit(f"{project} is not a Git repository; the agent works in worktrees of it")
    adapter, title = AGENTS[args.agent]
    root = home() / "orchestrators" / "paperclip"
    instructions = root / "instructions.md"
    config = {"engine": "cli", "cwd": str(project), "instructionsFilePath": str(instructions),
              "workspaceStrategy": {"type": "git_worktree", **({"baseRef": ref} if (ref := args.base_ref or base_ref(project)) else {})},
              "timeoutSec": args.timeout}
    agent = {"name": args.name or f"Factory engineer ({title})", "role": "engineer", "adapterType": adapter,
             "capabilities": "Delivers software through the AI Software Factory: ticket, plan, build, proof, draft PR."}
    if args.agent == "codex":
        agent["runner"] = "legacy"  # the plain CLI loads the hooks; other runners are untested with the gate
        config["env"] = {"CODEX_HOME": str(root / "codex-home")}
    agent["adapterConfig"] = config
    if args.dry_run:
        log(json.dumps(agent, indent=2))
        return agent
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    __import__("fast_install").install(args.agent, codex_home=codex_home(root) if args.agent == "codex" else None, log=log)
    root.mkdir(parents=True, exist_ok=True)
    instructions.write_text(INSTRUCTIONS.format(title="Paperclip", name="paperclip"), encoding="utf-8")
    log(f"wrote {instructions}")
    api = Api(args.api, os.environ.get(args.token_env), opener)
    listed = api.call("GET", f"/api/companies/{args.company}/agents")
    listed = listed.get("agents", []) if isinstance(listed, dict) else listed or []
    match = next((item for item in listed if item.get("name") == agent["name"]), None)
    saved = (api.call("PATCH", f"/api/agents/{match['id']}", agent) if match
             else api.call("POST", f"/api/companies/{args.company}/agents", agent))
    log(f"{'updated' if match else 'created'} agent {saved.get('id', match and match['id'])}: {agent['name']}")
    if args.agent == "codex":  # trust is the owner's review; the factory never writes or skips it
        log(f"Once, to enforce the gate: CODEX_HOME={root / 'codex-home'} codex, then /hooks and trust the factory's hooks")
    return saved


class Api:
    """JSON over HTTP with an optional bearer key; failures stop the setup with the server's reason."""

    def __init__(self, base, token, opener):
        self.base, self.token, self.opener = base.rstrip("/"), token, opener

    def call(self, method, path, body=None):
        headers = {"Content-Type": "application/json", **({"Authorization": f"Bearer {self.token}"} if self.token else {})}
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with self.opener(request, timeout=30) as response:
                text = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            raise SystemExit(f"{method} {path}: HTTP {error.code} {error.read().decode('utf-8', 'replace')[:300]}")
        except urllib.error.URLError as error:
            raise SystemExit(f"Cannot reach {self.base}: {error.reason}. Is the orchestrator running?")
        return json.loads(text) if text.strip() else {}


ORCHESTRATORS = {"paperclip": paperclip}
