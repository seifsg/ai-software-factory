"""Host hook dialects for fast_gate.py: read each host's event into one shape, answer in the host's format.

First-class hosts: claude and codex (same contract), cursor. Any other name is read generically and denied
with exit code 2 + stderr, the pre-tool signal every hook-capable agent honors. Contracts: docs/hosts.md.
"""
import json
import re

CLAUDE_EVENTS = {"PreToolUse": "pre_tool", "Stop": "stop", "UserPromptSubmit": "prompt", "SessionStart": "session"}
CURSOR_EVENTS = {"preToolUse": "pre_tool", "beforeShellExecution": "pre_tool", "stop": "stop",
                 "sessionStart": "session"}
GENERIC_EVENTS = {**CLAUDE_EVENTS, **CURSOR_EVENTS, "BeforeTool": "pre_tool", "AfterAgent": "stop",
                  "agentStop": "stop", "BeforeAgent": "prompt"}
EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Delete", "StrReplace", "write_file", "replace",
              "edit_file", "create_file", "delete_file", "edit", "create"}
SHELL_TOOLS = {"Bash", "PowerShell", "Shell", "run_shell_command", "shell", "bash"}
PATH_KEYS = ("file_path", "notebook_path", "path", "target_file", "filePath", "absolute_path")
SAME_AS_CLAUDE = ("claude", "codex")


def read(host, event):
    """One shape for every host: kind, session, cwd, tool ('edit'/'shell'/None), paths, command, again, name."""
    name = str(event.get("hook_event_name") or event.get("hookEventName") or "")
    if host == "cursor":
        roots = event.get("workspace_roots") or []
        tool, args = event.get("tool_name", ""), event.get("tool_input") or {}
        if name == "beforeShellExecution":
            tool, args = "Shell", {"command": event.get("command", "")}
        return shape(CURSOR_EVENTS.get(name), event.get("conversation_id"), event.get("cwd") or (roots[0] if roots else None),
                     tool, args, int(event.get("loop_count") or 0) > 0, name)
    events = CLAUDE_EVENTS if host in SAME_AS_CLAUDE else GENERIC_EVENTS
    tool = event.get("tool_name") or event.get("toolName") or ""
    args = event.get("tool_input") or event.get("toolArgs") or event.get("args") or {}
    kind = events.get(name) or ("pre_tool" if not name and tool and host not in SAME_AS_CLAUDE else None)
    return shape(kind, event.get("session_id") or event.get("conversation_id") or event.get("sessionId"),
                 event.get("cwd"), tool, args, bool(event.get("stop_hook_active") or event.get("loop_count")), name)


def shape(kind, session, cwd, tool, args, again, name):
    if isinstance(args, str):  # some hosts send tool arguments as a JSON string
        try:
            args = json.loads(args)
        except ValueError:
            args = {"command": args}
    args = args if isinstance(args, dict) else {}
    found = {"kind": kind, "session": session, "cwd": cwd, "tool": None, "paths": [], "command": None,
             "again": again, "name": name}
    if tool == "apply_patch":  # Codex: file edits arrive as patch text
        patch = args.get("command") or args.get("input") or ""
        patch = "\n".join(map(str, patch)) if isinstance(patch, list) else str(patch)
        names = re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$", patch, re.M)
        found.update(tool="edit", paths=[(first or second).strip() for first, second in names])
    elif tool in SHELL_TOOLS or (tool not in EDIT_TOOLS and re.search(r"shell|bash|command|terminal", tool, re.I)):
        found.update(tool="shell", command=str(args.get("command", "")))
    elif tool in EDIT_TOOLS or re.search(r"write|edit|replace|create|delete|patch", tool, re.I):
        found.update(tool="edit", paths=[str(args[key]) for key in PATH_KEYS if args.get(key)][:1])
    return found


def deny(host, reason):
    """(stdout, exit code) refusing a tool call; generic hosts read the reason from stderr."""
    if host in SAME_AS_CLAUDE:
        return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                  "permissionDecisionReason": reason}}), 0
    if host == "cursor":
        return json.dumps({"permission": "deny", "user_message": reason, "agent_message": reason}), 0
    return None, 2


def keep_going(host, reason):
    """stdout that keeps the agent working at turn end, or None where the host has no such answer."""
    if host in SAME_AS_CLAUDE:
        return json.dumps({"decision": "block", "reason": reason})
    if host == "cursor":
        return json.dumps({"followup_message": reason})
    return None


def notifies(host):
    """Whether the host shows a hook's systemMessage to the owner (docs/hosts.md): claude and codex."""
    return host in SAME_AS_CLAUDE


def with_message(out, message):
    """Hook stdout with a message for the owner added as systemMessage; out unchanged without one."""
    if not message:
        return out
    data = json.loads(out) if out else {}
    data["systemMessage"] = message
    return json.dumps(data)


def context(host, name, text):
    """stdout adding text to the agent's context on a prompt or session start, or None."""
    if host in SAME_AS_CLAUDE:
        return json.dumps({"hookSpecificOutput": {"hookEventName": name, "additionalContext": text}})
    if host == "cursor" and name == "sessionStart":
        return json.dumps({"additional_context": text})
    return None
