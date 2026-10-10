"""Fill and run the owner's agent command template; no agent, vendor or host is named here."""
import os
import shlex
import subprocess

from evals import proc

PLACEHOLDERS = ("prompt_file", "workdir", "arm", "sample", "factory")
CMD_EXPANDS = ('%', '"')  # cmd expands %VAR% even inside quotes, and a quote would end the word


def quote(value):
    """One shell word for the system shell that runs the template; refuses what cmd would rewrite."""
    value = str(value)
    if os.name != "nt":
        return shlex.quote(value)
    if any(char in value for char in CMD_EXPANDS):
        raise ValueError(f"cannot pass {value!r} through cmd safely; use a path without % or \"")
    return subprocess.list2cmdline([value])


def fill(template, values):
    """The template with each {placeholder} replaced by its quoted value; other braces stay as written."""
    if not isinstance(template, str) or not template.strip():
        raise ValueError("the agent command template is empty")
    for name in PLACEHOLDERS:
        if "{" + name + "}" in template:
            template = template.replace("{" + name + "}", quote(values[name]))
    return template


def run(template, values, workdir, prompt, log, seconds, env):
    """Run the filled template in the system shell, prompt on stdin. Returns (exit code, timed out)."""
    return proc.run_limited(fill(template, values), workdir, prompt, log, seconds, env=env, shell=True)
