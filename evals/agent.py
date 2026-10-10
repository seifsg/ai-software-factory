"""Run the owner's agent command template with a time limit; no agent, vendor or host is named here."""
import os
import shlex
import signal
import subprocess

PLACEHOLDERS = ("prompt_file", "workdir", "arm", "sample", "factory")


def quote(value):
    """One shell word for the system shell that runs the template (cmd on Windows, sh elsewhere)."""
    return subprocess.list2cmdline([str(value)]) if os.name == "nt" else shlex.quote(str(value))


def fill(template, values):
    """The template with each {placeholder} replaced by its quoted value; other braces stay as written."""
    if not isinstance(template, str) or not template.strip():
        raise ValueError("the agent command template is empty")
    for name in PLACEHOLDERS:
        template = template.replace("{" + name + "}", quote(values[name]))
    return template


def kill_tree(process):
    """Stop the agent and every process it started, so a timed-out run leaves nothing running."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, timeout=60)
        else:
            os.killpg(process.pid, signal.SIGKILL)  # the agent leads its own session (start_new_session)
    except (OSError, subprocess.SubprocessError):
        pass  # already gone, or the tree kill failed: fall back to the direct child
    if process.poll() is None:
        process.kill()
    process.wait()


def run(template, values, workdir, prompt, log, seconds):
    """Run the filled template in `workdir`, prompt on stdin, output to `log`. Returns (exit code, timed out)."""
    with open(prompt, "rb") as stdin, open(log, "wb") as output:
        process = subprocess.Popen(fill(template, values), shell=True, cwd=workdir, stdin=stdin, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            return process.wait(timeout=seconds), False
        except subprocess.TimeoutExpired:
            kill_tree(process)
            return None, True
