"""Durable lane supervisors: generation requests, owned processes, never PID kills."""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import uuid

from .processes import ProcessTree
from .resources import environment, resource_root
from .storage import atomic_json, locked, read_json


def identity(pid):
    if os.name == "nt":
        from .windows_job import identity as windows_identity
        return windows_identity(pid)
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except FileNotFoundError:
        return None


def occupied(ports):
    """Observe bind availability only; a foreign occupant is never terminated."""
    busy = []
    for port in ports:
        with socket.socket() as probe:
            try:
                if os.name == "nt":
                    probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                probe.bind(("127.0.0.1", port))
            except OSError:
                busy.append(port)
    return busy


def folder(project, name):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name):
        raise ValueError("Lane name: lowercase letter, then letters, digits or hyphens (max 64)")
    return Path(project).resolve(strict=True) / ".factory" / "lanes" / name


def status(directory):
    state = read_json(directory / "state.json")
    if (not isinstance(state, dict) or not re.fullmatch(r"[0-9a-f]{32}", str(state.get("generation")))
            or Path(state.get("cwd", "")).resolve() != directory.parents[2].resolve()
            or state.get("name") != directory.name):
        raise RuntimeError("Invalid lane state identity; no process action taken")
    if state["status"] in ("starting", "running", "stopping", "cleanup_failed"):
        owner = state.get("owner")
        if owner and (not owner.get("created") or identity(owner["pid"]) != owner["created"]):
            state = {**state, "status": "stale", "error": "Supervisor identity is gone; no PID was signalled"}
    return state


def start(project, name, argv, ports, run=None):
    """Start one generation, acknowledge ownership before returning, reject occupied lanes."""
    if not argv or not ports or len(set(ports)) != len(ports) or any(type(p) is not int or not 1024 <= p <= 65535 for p in ports):
        raise ValueError("Supply a command and distinct ports from 1024 through 65535")
    directory = folder(project, name)
    if identity(os.getpid()) is None:
        raise RuntimeError("Lane supervisor identity is supported on Windows and Linux /proc only")
    with locked(directory):
        if (directory / "state.json").exists():
            previous = status(directory)
            if previous["status"] not in ("stopped", "failed", "stale"):
                raise RuntimeError("Lane already active; stop its generation first")
        if busy := occupied(ports):
            raise RuntimeError(f"Ports already occupied, untouched: {busy}")
        generation = uuid.uuid4().hex
        root = resource_root(f"{Path(project).resolve()}:{name}:{generation}")
        state = {"version": 1, "name": name, "generation": generation, "run": run,
                 "cwd": str(Path(project).resolve()), "argv": argv, "ports": ports,
                 "resources": str(root), "status": "starting", "owner": None, "processes": []}
        atomic_json(directory / "state.json", state)
        with (directory / f"{generation}.log").open("w", encoding="utf-8") as log:
            command = [sys.executable, "-m", "safe_engine.lanes", str(directory), generation]
            options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
            worker = subprocess.Popen(command, cwd=Path(__file__).resolve().parents[1], stdin=subprocess.DEVNULL,
                                      stdout=log, stderr=subprocess.STDOUT, **options)
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                result = status(directory)
                if result["status"] != "starting":
                    if result["status"] != "running":
                        raise RuntimeError(f"Lane failed to start: {result}")
                    return result
                if worker.poll() is not None:
                    raise RuntimeError(f"Supervisor exited before startup; see {directory / (generation + '.log')}")
                time.sleep(.05)
            raise RuntimeError("Lane startup acknowledgement timed out")
        except BaseException as error:
            atomic_json(directory / f"{generation}.stop", {"generation": generation})
            if worker.poll() is not None and status(directory)["status"] == "starting":
                atomic_json(directory / "state.json", {**state, "status": "failed", "error": str(error)})
            raise


def stop(project, name, generation=None):
    """Request the current owner's shutdown; stale callers cannot stop a replacement."""
    directory = folder(project, name)
    state = status(directory)
    if generation and generation != state["generation"]:
        raise RuntimeError("Lane generation changed; no stop requested")
    if state["status"] == "stale":
        raise RuntimeError(f"Stale supervisor; no PID signalled. Occupied ports: {occupied(state['ports'])}")
    token = state["generation"]
    attempt = uuid.uuid4().hex
    atomic_json(directory / f"{token}.stop", {"generation": token, "attempt": attempt})
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        state = status(directory)
        if state["generation"] != token:
            raise RuntimeError("Lane generation changed while stopping; replacement untouched")
        if state["status"] == "cleanup_failed" and state.get("stop_attempt") == attempt:
            raise RuntimeError(f"Cleanup unconfirmed; supervisor retains ownership for retry: {state['cleanup_error']}")
        if state["status"] in ("stopped", "failed"):
            if busy := occupied(state["ports"]):
                raise RuntimeError(f"Owned processes stopped, but ports occupied; foreign occupants untouched: {busy}")
            return state
        if state["status"] == "stale":
            raise RuntimeError("Supervisor disappeared during stop; no PID signalled")
        time.sleep(.05)
    raise RuntimeError("Lane stop timed out; ownership remains with its supervisor")


def supervise(directory, generation):
    """Keep the OS owner alive even after the launched command parent exits."""
    state = status(directory)
    if state["generation"] != generation:
        raise RuntimeError("Superseded lane generation")
    state["owner"] = {"pid": os.getpid(), "created": identity(os.getpid())}
    process = None
    try:
        root = resource_root(f"{Path(state['cwd']).resolve()}:{state['name']}:{generation}")
        process = ProcessTree(state["argv"], state["cwd"], env=environment(root),
                              stdin=subprocess.DEVNULL)
        state.update(status="running", processes=process.members())
        atomic_json(directory / "state.json", state)
        request = directory / f"{generation}.stop"
        while not request.exists():
            members = process.members()
            code = process.poll()
            if members != state["processes"] or code != state.get("command_exit"):
                state.update(processes=members, command_exit=code)
                atomic_json(directory / "state.json", state)
            time.sleep(.1)
        if read_json(request).get("generation") != generation:
            raise RuntimeError("Invalid stop generation")
        state["status"] = "stopping"
        atomic_json(directory / "state.json", state)
    except BaseException as error:
        state.update(status="failed", error=str(error))
    finally:
        finish(directory, generation, state, process)


def finish(directory, generation, state, process):
    """Keep a failed cleanup's owner alive and permit an explicit stop retry."""
    request = directory / f"{generation}.stop"
    while True:
        state["status"] = "stopping"
        if request.exists():
            state["stop_attempt"] = read_json(request).get("attempt")
        atomic_json(directory / "state.json", state)
        request.unlink(missing_ok=True)
        try:
            if process:
                process.stop()
        except BaseException as error:
            state.update(status="cleanup_failed", cleanup_error=str(error))
            atomic_json(directory / "state.json", state)
            while not request.exists():
                time.sleep(.1)
            continue
        state.pop("cleanup_error", None)
        state.update(status="failed" if state.get("error") else "stopped", processes=[],
                     occupied_ports=occupied(state["ports"]), grace_note=process.stop_note if process else None)
        atomic_json(directory / "state.json", state)
        return


if __name__ == "__main__":
    supervise(Path(sys.argv[1]), sys.argv[2])
