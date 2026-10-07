"""Independent reviewer agents for Safe review: any installed agent CLI, headless and read-only.

Presets are thin host adapters (docs/hosts.md). Auto picks an installed agent other than the builder when one
exists. Order follows structured-output strength (schema-enforced first), not preference. The review packet
route (any host's fresh subagent) always stays available.
"""
import json
import os
from pathlib import Path
import re
import shutil

from .project import EngineError

BINARIES = {"codex": ("codex",), "claude": ("claude",), "cursor": ("agent", "cursor-agent")}
ORDER = ("codex", "claude", "cursor")


def builder_from_env(env=None):
    """The agent running this command, when its environment says so (CLAUDECODE, CODEX_THREAD_ID, CURSOR_AGENT)."""
    env = os.environ if env is None else env
    if env.get("CLAUDECODE") == "1":
        return "claude"
    if env.get("CODEX_THREAD_ID"):
        return "codex"
    return "cursor" if env.get("CURSOR_AGENT") else None


def available(which=None):
    """Installed reviewer agents as {name: executable path}, in ORDER."""
    which = which or shutil.which
    found = {}
    for name in ORDER:
        path = next((hit for hit in map(which, BINARIES[name]) if hit), None)
        if path:
            found[name] = path
    return found


def choose(agent=None, builder=None, which=None):
    """(name, executable): the requested agent, or auto: installed, not the builder when another exists."""
    found = available(which)
    if agent and agent != "auto":
        if agent not in BINARIES:
            raise EngineError(f"Unknown reviewer agent '{agent}'; choose {', '.join(ORDER)} or auto")
        if agent not in found:
            raise EngineError(f"{agent} CLI not found on PATH; install it, choose another agent, or use review-packet")
        return agent, found[agent]
    builder = builder or builder_from_env()
    if not found:
        raise EngineError("No reviewer agent CLI (codex, claude, cursor agent) on PATH; issue review-packet to a "
                          "fresh read-only subagent of your host, then review --report <file.json> --reviewer <id>")
    if builder is None and len(found) > 1:
        raise EngineError("Several reviewer agents are installed; pass --builder <the agent that built> so auto "
                          "picks a different one, or --agent <name>")
    picks = [name for name in found if name != builder] or list(found)
    return picks[0], found[picks[0]]


def argv(agent, executable, project, bundle, schema_path, output):
    """Read-only headless command; the prompt arrives on stdin."""
    if agent == "codex":
        return [executable, "exec", "--sandbox", "read-only", "--ephemeral", "-C", str(project),
                "--output-schema", str(schema_path), "--output-last-message", str(output), "-"]
    if agent == "claude":
        schema = json.dumps(json.loads(Path(schema_path).read_text(encoding="utf-8")), separators=(",", ":"))
        return [executable, "-p", "--tools", "Read,Grep,Glob", "--strict-mcp-config", "--permission-mode", "dontAsk",
                "--no-session-persistence", "--add-dir", str(bundle), "--output-format", "json", "--json-schema", schema]
    return [executable, "-p", "--mode", "ask", "--trust", "--output-format", "json"]  # Cursor CLI docs; never --force


def capture(agent, log, output):
    """Codex writes its own report file; other agents print JSON, so lift the report out of the review log."""
    if agent == "codex" or Path(output).exists():
        return
    text = Path(log).read_text(encoding="utf-8", errors="replace")
    report = None
    for candidate in [line for line in reversed(text.splitlines()) if line.strip().startswith("{")] + [text]:
        try:
            value = json.loads(candidate)
        except ValueError:
            continue
        report = unwrap(value)
        if report is not None:
            break
    if report is not None:
        Path(output).write_text(json.dumps(report, indent=2), encoding="utf-8")


def unwrap(value):
    """The review report inside a host's JSON envelope: structured output, a result string, or the report itself."""
    if not isinstance(value, dict):
        return None
    if "verdict" in value:
        return value
    if isinstance(value.get("structured_output"), dict):
        return value["structured_output"]
    result = value.get("result")
    return first_report(result) if isinstance(result, str) else None


def first_report(text):
    """The first JSON object with a verdict: fenced ```json blocks first, then each '{' in the prose."""
    decoder = json.JSONDecoder()
    fenced = [match.group(1) for match in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)]
    starts = [(block, 0) for block in fenced] + [(text, index) for index, char in enumerate(text) if char == "{"]
    for source, index in starts:
        try:
            value, _ = decoder.raw_decode(source, index)
        except ValueError:
            continue
        if isinstance(value, dict) and "verdict" in value:
            return value
    return None
