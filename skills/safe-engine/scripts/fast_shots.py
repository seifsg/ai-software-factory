"""Before/after screenshots in one command: boot the base commit and the head on their own ports, shoot the same
views at the same size with a headless Chromium browser, stop both. Spec: fast-run.md#the-gate (`shots`).
"""
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

BROWSERS = ("chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge",
            "microsoft-edge")
KNOWN = ("C:/Program Files/Google/Chrome/Application/chrome.exe",
         "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
         "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
         "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
         "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
         "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")


def parser(sub, common):
    """Register `shots` without growing the gate's argument wiring."""
    cmd = sub.add_parser("shots", parents=[common], help="Screenshot the same views on the base commit and the head")
    cmd.add_argument("--base", required=True, help="Base commit or branch for Before, such as origin/main")
    cmd.add_argument("--serve", required=True, help="Dev server command run in each tree; {port} becomes its port")
    cmd.add_argument("--path", action="append", required=True, help="View to shoot, such as / or /settings; repeat")
    cmd.add_argument("--setup", help="Command run once in each tree before serving, such as 'npm ci'")
    cmd.add_argument("--ports", help="Before,after ports, such as 5281,5282 (default: two free ports)")
    cmd.add_argument("--size", default="1280x800", help="Viewport WIDTHxHEIGHT, the same for both")
    cmd.add_argument("--browser", help="Chromium-family executable (default: SAFE_ENGINE_BROWSER, then PATH)")
    cmd.add_argument("--out", help="Folder for the shots (default: <project>/.factory/fast/shots)")
    cmd.add_argument("--wait", type=int, default=120, help="Seconds each server may take to answer")


def run(args, gate):
    """Capture every --path on base and head; print each pair. Any failure stops both servers and exits non-zero."""
    project = Path(args.project or os.getcwd()).resolve()
    size = re.fullmatch(r"(\d{2,5})x(\d{2,5})", args.size) or gate.fail("--size: WIDTHxHEIGHT, such as 1280x800")
    browser = find_browser(args.browser) or gate.fail("No Chromium-family browser found: pass --browser <executable>")
    ports = parse_ports(args.ports) or gate.fail("--ports: two different ports, such as 5281,5282")
    out = Path(args.out).resolve() if args.out else project / ".factory" / "fast" / "shots"
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="shots-", dir=scratch(project, gate)))
    base = work / "base"
    try:
        git(project, "worktree", "add", "--detach", str(base), args.base)
        pairs = capture(args, [(base, ports[0], "before"), (project, ports[1], "after")], browser, size, work, out)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        gate.fail(f"shots: {error}")
    finally:
        git(project, "worktree", "remove", "--force", str(base), check=False)
    for path, before, after in pairs:
        print(f"{path}: {before} -> {after}")


def capture(args, trees, browser, size, work, out):
    """Set up and serve each tree, shoot each path in both, stop both servers whatever happens."""
    servers = []
    try:
        for tree, port, label in trees:
            if args.setup:
                shell(args.setup, tree, work / f"{label}-setup.log", timeout=1800)
            servers.append(serve(args.serve, tree, port, work / f"{label}-server.log"))
        for server, (_, port, label) in zip(servers, trees):
            wait_up(server, port, args.wait, work / f"{label}-server.log")
        return [(path, *(shoot(browser, f"http://127.0.0.1:{port}{route(path)}", size, work,
                               out / f"{slug(path)}-{label}.png") for _, port, label in trees)) for path in args.path]
    finally:
        for server in servers:
            stop(server)


def find_browser(given):
    """The browser to drive: --browser, SAFE_ENGINE_BROWSER, a known name on PATH, then a known install path."""
    for name in (given, os.environ.get("SAFE_ENGINE_BROWSER")):
        if name:
            return shutil.which(name) or (name if Path(name).is_file() else None)
    found = next(filter(None, map(shutil.which, BROWSERS)), None)
    return found or next((path for path in KNOWN if Path(path).is_file()), None)


def parse_ports(value):
    """Two distinct ports from 'a,b', or two free ones."""
    if not value:
        return [free_port(), free_port()]
    found = [int(n) for n in re.findall(r"\d+", value)]
    return found if len(found) == 2 and found[0] != found[1] and all(1024 <= n <= 65535 for n in found) else None


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def scratch(project, gate):
    """The open run's scratch folder for this project, else the system temp folder."""
    for _, _, run in gate.active_runs():
        if Path(run.get("project", "")).resolve() == project:
            folder = gate.sibling("fast_setup").scratch_path(gate.HOME, run)
            if folder:
                folder.mkdir(parents=True, exist_ok=True)
                return folder
    return None


def git(project, *args, check=True):
    result = subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True, timeout=300)
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def shell(command, cwd, log, timeout):
    with open(log, "w", encoding="utf-8") as sink:
        if subprocess.run(command, shell=True, cwd=cwd, stdout=sink, stderr=subprocess.STDOUT, timeout=timeout).returncode:
            raise RuntimeError(f"'{command}' failed in {cwd}; see {log}")


def serve(command, cwd, port, log):
    """Start the dev server in its own process group so stop() ends its whole tree."""
    group = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True})
    sink = open(log, "w", encoding="utf-8")  # closed with the process in stop()
    env = {**os.environ, "PORT": str(port)}
    process = subprocess.Popen(command.replace("{port}", str(port)), shell=True, cwd=cwd, stdout=sink,
                               stderr=subprocess.STDOUT, env=env, **group)
    process.sink = sink
    return process


def wait_up(process, port, seconds, log):
    """Any HTTP answer on the port counts; an exited server or the deadline fails with its log."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"server exited ({process.returncode}) before answering on {port}; see {log}")
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2).close()
            return
        except urllib.error.HTTPError:
            return  # it answered
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    raise RuntimeError(f"nothing answered on port {port} within {seconds}s; see {log}")


def shoot(browser, url, size, work, target):
    """One headless screenshot; its own profile folder keeps the owner's browser untouched."""
    profile = Path(tempfile.mkdtemp(prefix="profile-", dir=work))
    if target.exists():
        target.unlink()
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                    "--no-default-browser-check", f"--user-data-dir={profile}", "--virtual-time-budget=5000",
                    f"--window-size={size.group(1)},{size.group(2)}", f"--screenshot={target}", url],
                   capture_output=True, timeout=120)
    if not target.is_file() or not target.stat().st_size:
        raise RuntimeError(f"no screenshot of {url}")
    return target


def stop(process):
    """End the server's whole process tree: taskkill /T on Windows, TERM then KILL to its group elsewhere."""
    for force in (False, True):
        if process.poll() is not None:
            break
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
        else:
            os.killpg(process.pid, signal.SIGKILL if force else signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            continue
    process.sink.close()


def route(path):
    return path if path.startswith("/") else "/" + path


def slug(path):
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-") or "home"


if __name__ == "__main__":
    sys.exit("Run through the gate: fast_gate.py shots ...")
