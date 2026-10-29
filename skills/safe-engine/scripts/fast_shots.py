"""Capture Before early and After later; retain the same scoped baseline."""
import json
import hashlib
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

from fast_lane import runtime

BROWSERS = ("chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge",
            "microsoft-edge")
KNOWN = ("C:/Program Files/Google/Chrome/Application/chrome.exe",
         "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
         "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
         "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
         "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
         "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")


class CleanupError(RuntimeError):
    """Keep failed owners available for explicit retry while the caller lives."""
    def __init__(self, failures):
        self.failures = failures
        self.paths = []
        super().__init__("Cleanup unconfirmed: " + "; ".join(
            f"PID {process.pid}: {error}" for process, error in failures))

    def retry(self):
        """Retry each retained owner; artifact removal remains the caller's decision."""
        try:
            cleanup([process for process, _ in self.failures])
        except CleanupError as error:
            error.paths.extend(self.paths)
            raise
        self.failures.clear()


def cleanup(processes, pending=None):
    """Attempt every acquired owner before propagating aggregate cleanup failure."""
    failures = list(pending.failures) if isinstance(pending, CleanupError) else []
    for process in processes:
        try:
            stop(process)
        except BaseException as error:
            failures.append((process, error))
    if failures:
        error = CleanupError(failures)
        if isinstance(pending, CleanupError):
            error.paths.extend(pending.paths)
        raise error


def parser(sub, common):
    """Register `shots` without growing the gate's argument wiring."""
    cmd = sub.add_parser("shots", parents=[common], help="Capture Before before edits and After during final QA")
    cmd.add_argument("--phase", choices=("before", "after"), help="Capture current views before edits or after QA")
    cmd.add_argument("--base", help="Base commit or branch for Before, such as origin/main")
    cmd.add_argument("--serve", required=True, help="Dev server command run in each tree; {port} becomes its port")
    cmd.add_argument("--path", action="append", required=True, help="View to shoot, such as / or /settings; repeat")
    cmd.add_argument("--setup", help="Command run once in each tree before serving, such as 'npm ci'")
    cmd.add_argument("--ports", help="Before,after ports, such as 5281,5282 (default: two free ports)")
    cmd.add_argument("--size", default="1280x800", help="Viewport WIDTHxHEIGHT, the same for both")
    cmd.add_argument("--browser", help="Chromium-family executable (default: SAFE_ENGINE_BROWSER, then PATH)")
    cmd.add_argument("--out", help="Folder for the shots (default: <project>/.factory/fast/shots)")
    cmd.add_argument("--wait", type=int, default=120, help="Seconds each server may take to answer")


def run(args, gate):
    """Capture one phase; legacy --base pairs are explicitly reconstructed evidence."""
    project = Path(args.project or os.getcwd()).resolve()
    if bool(args.phase) == bool(args.base):
        gate.fail("Choose --phase before|after, or --base for a disclosed reconstructed pair")
    size = re.fullmatch(r"(\d{2,5})x(\d{2,5})", args.size) or gate.fail("--size: WIDTHxHEIGHT, such as 1280x800")
    browser = find_browser(args.browser) or gate.fail("No Chromium-family browser found: pass --browser <executable>")
    ports = parse_ports(args.ports) or gate.fail("--ports: two different ports, such as 5281,5282")
    out = Path(args.out).resolve() if args.out else project / ".factory" / "fast" / "shots"
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="shots-", dir=scratch(project, gate)))
    base = work / "base"
    if args.phase:
        try:
            phased(args, project, browser, size, work, out, ports)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            gate.fail(f"shots: {error}")
        return
    print("Reconstructed Before from base after edits; not a pre-edit capture.")
    retained = False
    try:
        git(project, "worktree", "add", "--detach", str(base), args.base)
        pairs = capture(args, [(base, ports[0], "before"), (project, ports[1], "after")], browser, size, work, out, project)
    except CleanupError as error:
        retained = True
        error.paths.append(base)
        print(f"shots: cleanup unconfirmed; retained paths: {error.paths}. "
              "Retry ownership is available only while this caller remains alive.", file=sys.stderr)
        raise
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        gate.fail(f"shots: {error}")
    finally:
        if not retained:
            git(project, "worktree", "remove", "--force", str(base), check=False)
    for path, before, after in pairs:
        print(f"{path}: {before} -> {after}")


def phased(args, project, browser, size, work, out, ports):
    """Keep the early image bytes and capture conditions immutable across phases."""
    manifest = out / "baseline.json"
    inputs = {"project": str(project), "paths": args.path, "size": args.size, "serve": args.serve, "setup": args.setup, "browser": browser}
    if args.phase == "before":
        if manifest.exists():
            raise ValueError("Baseline already exists; retain it or choose a new --out")
    else:
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        if saved["inputs"] != inputs:
            raise ValueError("Baseline capture conditions changed")
        for path, digest in saved["images"].items():
            if hashlib.sha256((out / path).read_bytes()).hexdigest() != digest:
                raise ValueError("Before image changed")
    rows = capture(args, [(project, ports[0], args.phase)], browser, size, work, out, project)
    if args.phase == "before":
        images = {Path(row[1]).name: hashlib.sha256(Path(row[1]).read_bytes()).hexdigest() for row in rows}
        manifest.write_text(json.dumps({"inputs": inputs, "images": images}), encoding="utf-8")
    for row in rows:
        print(f"{row[0]}: {row[1]}")


def capture(args, trees, browser, size, work, out, project):
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
                               out / f"{slug(path)}-{label}.png", project) for _, port, label in trees)) for path in args.path]
    finally:
        cleanup(servers, sys.exc_info()[1])


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
    resources, ProcessTree = runtime("resources"), runtime("processes").ProcessTree
    with open(log, "w", encoding="utf-8") as sink:
        process = ProcessTree(command, cwd, shell=True, stdout=sink, stderr=subprocess.STDOUT,
                              env=resources.environment(resources.resource_root(cwd)))
        try:
            if process.wait(timeout=timeout):
                raise RuntimeError(f"'{command}' failed in {cwd}; see {log}")
        finally:
            cleanup([process])


def serve(command, cwd, port, log):
    """Own the whole server tree and refuse an already occupied port."""
    resources, ProcessTree = runtime("resources"), runtime("processes").ProcessTree
    if runtime("lanes").occupied([port]):
        raise RuntimeError(f"Port {port} already occupied; occupant untouched")
    sink = open(log, "w", encoding="utf-8")  # closed with the process in stop()
    env = {**resources.environment(resources.resource_root(cwd)), "PORT": str(port)}
    try:
        process = ProcessTree(command.replace("{port}", str(port)), cwd, shell=True, stdout=sink,
                              stderr=subprocess.STDOUT, env=env)
    except BaseException:
        sink.close()
        raise
    process.sink = sink
    return process


def wait_up(process, port, seconds, log):
    """Any HTTP answer on the port counts; an exited server or the deadline fails with its log."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None and not process.members():
            raise RuntimeError(f"server exited ({process.returncode}) before answering on {port}; see {log}")
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2).close()
            return
        except urllib.error.HTTPError:
            return  # it answered
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    raise RuntimeError(f"nothing answered on port {port} within {seconds}s; see {log}")


def shoot(browser, url, size, work, target, project):
    """One headless screenshot; its own profile folder keeps the owner's browser untouched."""
    user_data = runtime("resources").profile(work)
    ProcessTree = runtime("processes").ProcessTree
    if target.exists():
        target.unlink()
    process = ProcessTree([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                    "--no-default-browser-check", f"--user-data-dir={user_data}", "--virtual-time-budget=5000",
                    f"--window-size={size.group(1)},{size.group(2)}", f"--screenshot={target}", url],
                    work, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        process.wait(timeout=120)
    finally:
        try:
            cleanup([process])
        except CleanupError as error:
            error.paths.append(user_data)
            raise
        from fast_setup import remove
        left = []
        remove(user_data, left)
        if left:
            raise RuntimeError(f"Browser profile cleanup failed: {left}")
    if not target.is_file() or not target.stat().st_size:
        raise RuntimeError(f"no screenshot of {url}")
    import fast_image
    fast_image.check(target, project=project)
    return target


def stop(process):
    """Stop retained descendants even after the command's parent has exited."""
    process.stop()
    if hasattr(process, "sink"):
        process.sink.close()


def route(path):
    return path if path.startswith("/") else "/" + path


def slug(path):
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-") or "home"


if __name__ == "__main__":
    sys.exit("Run through the gate: fast_gate.py shots ...")
