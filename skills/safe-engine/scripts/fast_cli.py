"""Lazy command argument registration; hook dispatch stays in the gate."""


class _FullParserNeeded(Exception):
    """Retry invalid input with the complete parser for identical diagnostics."""


def parse(gate):
    """Load requested command options; help and errors keep the complete public CLI."""
    import sys
    argv = sys.argv[1:]
    if argv and not any(arg in ("-h", "--help") for arg in argv):
        try:
            return _parser(gate, argv[0]).parse_args(argv)
        except _FullParserNeeded:
            pass  # Full registration also admits commands added by newer modules.
    return _parser(gate).parse_args(argv)


def _parser(gate, selected=None):
    """Build the public CLI from the executing gate and its selected sibling modules."""
    sibling = gate.sibling
    import argparse

    class CommandParser(argparse.ArgumentParser):
        def error(self, message):
            if selected is not None:
                raise _FullParserNeeded
            super().error(message)

    parser = CommandParser(description=gate.__doc__.splitlines()[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", help="Run project; default: nearest folder with .factory/fast/run.json")
    sub = parser.add_subparsers(dest="command", required=True)

    def register(module, *commands, shared=True):
        if selected is None or selected in commands:
            sibling(module).parser(sub, *([common] if shared else []))

    register("fast_cleanup", "cleanup-temp")
    register("fast_shots", "shots")
    register("fast_lane", "lane")
    register("fast_wait_command", "wait")
    register("fast_baseline", "recover-baseline")
    register("fast_release", "version", "verify", shared=False)
    register("fast_design_command", "design")
    start = sub.add_parser("start", parents=[common], help="Begin a run and register it for hooks")
    start.add_argument("--key", required=True)
    start.add_argument("--mode", choices=gate.MODES, default="fast")
    start.add_argument("--kind", choices=gate.KINDS, required=True)
    start.add_argument("--design-port", action="store_true", help="UI reference port: require immutable coverage and likeness proof")
    for flag in ("ui", "data"):
        start.add_argument(f"--{flag}", dest=flag, action="store_true", default=None)
        start.add_argument(f"--no-{flag}", dest=flag, action="store_false", default=None)
    start.add_argument("--auth", action="store_true", help="The product has sign-in")
    start.add_argument("--request")
    start.add_argument("--request-file")
    sub.add_parser("pr-proof-method", help="Read the owner-selected PR method for any mode")
    adopt = sub.add_parser("adopt-pr-proof", help="Owner-authorized PR-only policy; preserves existing run state")
    target = adopt.add_mutually_exclusive_group(required=True)
    target.add_argument("--project")
    target.add_argument("--new-runs", action="store_true")
    adopt.add_argument("--method", required=True, help="Absolute canonical PR SKILL.md; preserve its whole folder")
    adopt.add_argument("--reason", required=True, help="Owner instruction and source authorizing adoption")
    done = sub.add_parser("done", parents=[common], help="Check and record one step")
    done.add_argument("step", choices=list(gate.TITLES))
    done.add_argument("--offline", help="Record tickets, plan, handoff or a hidden-check done-run without reading tickets "
                                         "through gh, with the reason")
    sub.add_parser("status", parents=[common])
    sub.add_parser("scratch", parents=[common], help="Print the open run's scratch folder for throwaway data")
    pause = sub.add_parser("pause", parents=[common], help="Waiting on the owner; lets the session stop")
    pause.add_argument("--reason", required=True)
    sub.add_parser("resume", parents=[common])
    tried = sub.add_parser("try", parents=[common], help="How the owner tries a finished todo: a command, link or file")
    tried.add_argument("todo", help="The todo's ID, such as T3")
    target = tried.add_mutually_exclusive_group(required=True)
    for flag, what in (("cmd", "a command to run"), ("url", "an http(s) link"), ("file", "a path inside the project")):
        target.add_argument(f"--{flag}", help=what)
    shown = sub.add_parser("view", help="Serve this project's live progress on 127.0.0.1")
    scope = shown.add_mutually_exclusive_group()
    scope.add_argument("--project", help="Project folder; default: current folder and its repository worktrees")
    scope.add_argument("--all-projects", action="store_true", help="Explicitly show every project's progress")
    shown.add_argument("--port", type=int, default=8765, help="Default 8765; a busy port falls back to a free one")
    shown.add_argument("--snapshot", help="Write one HTML file with the current state instead of serving")
    close = sub.add_parser("close", parents=[common])
    close.add_argument("--abandon", help="The owner stopped the run: their reason")
    rehome = sub.add_parser("rehome", parents=[common],
                            help="Owner only: bring in an open run from another machine or folder")
    rehome.add_argument("--from", dest="source", required=True, help="The folder the run's run.json records")
    register("fast_round", "fix-round")
    register("fast_install", "install", shared=False)
    orchestrate = sub.add_parser("orchestrate", help="Set up an orchestrator to start factory sessions")
    if selected is None or selected == "orchestrate":
        sibling("fast_orchestrate").arguments(orchestrate)
    hook = sub.add_parser("hook", help="Answer one host hook event from stdin")
    hook.add_argument("--host", default="claude", help="claude, codex, cursor, or any other hook-capable agent")
    register("fast_show_command", "show", "prove")
    register("fast_checks_command", "checks")
    register("fast_report_command", "report")
    return parser
