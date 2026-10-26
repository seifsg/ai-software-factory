"""Resolve a complete, revision-pinned factory; never mutate an existing app/bundle.

Also the release identity every launcher carries (docs/releasing.md): the canonical version, the sha256 release
manifest, and the one check that makes a tag a release.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile


REPOSITORY = "https://github.com/seifsg/ai-software-factory.git"
ORIGINS = {REPOSITORY, REPOSITORY.removesuffix(".git"), "git@github.com:seifsg/ai-software-factory.git",
           "ssh://git@github.com/seifsg/ai-software-factory.git"}
DEFAULT_REF = "main"  # the edge channel, and every new project's factory until the first release exists
ENTRYPOINTS = ("safe-engine", "improve-factory")
VERSION_FILE = "skills/safe-engine/VERSION"  # the one canonical version; tests hold every other copy to it
MANIFEST = "skills/safe-engine/release-manifest.json"  # sha256 of every other file in a release (scripts/release.py)
MARKER = ".safe-engine-install"  # fast_install.MARKER: an installed copy's ownership mark, never a factory file
TAG = re.compile(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")  # stable release tags; no pre-release ever ships
# This documented pilot predates portable entries and the input contract.
# Do not apply its compatibility path to unknown revisions or later bundles.
LEGACY_PILOT = "eeb0da9d26092e67ea2e7abb58ec57ffd815df49"
SKILLS = ("improve-factory", "safe-engine", "analyze-start", "get-ready-to-code", "research-market",
          "database-schema", "ux-quality", "deep-review", "ticketing", "how-to-make-a-pr")
REQUIRED = ["AGENTS.md", "README.md", "docs/install.md", "docs/hosts.md", "safe_engine/__main__.py",
            ".agents/skills/safe-engine/references/fast-run.md",
            ".agents/skills/improve-factory/references/live-session.md"]
REQUIRED += [f".agents/skills/{name}/SKILL.md" for name in SKILLS]
# Revision-specific helpers, including CLI registration, use each bundle's contract, preserving older pins.
NEWER = ("This factory revision uses a newer layout than this launcher knows ({}). Update the installed factory from "
         "a current checkout (skills/safe-engine/scripts/fast_gate.py install --host <your agent>, or update the "
         "plugin), then retry.")


def git(*args, cwd=None):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                            text=True, encoding="utf-8", timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Git command failed")
    return result.stdout.strip()


def safe_name(name):
    """A normalized relative bundle path: no empty, dot or parent parts, backslashes or drive colons."""
    return (isinstance(name, str) and bool(name) and "\\" not in name and ":" not in name
            and not any(part in ("", ".", "..") for part in name.split("/")))


def edited(root, name):
    """Whether the checkout changed `name` locally: a local edit never counts as a newer factory layout."""
    return bool(git("status", "--porcelain", "--", name, cwd=root))


def inspect_bundle(root, expected=None, clean=False, entrypoint="improve-factory"):
    if entrypoint not in ENTRYPOINTS:
        raise RuntimeError("Unknown factory entrypoint")
    root = Path(root).expanduser().resolve()
    actual_root = Path(git("rev-parse", "--show-toplevel", cwd=root)).resolve()
    if root != actual_root:
        raise RuntimeError("Bundle path must be the Git checkout root, not a subdirectory")
    remote = git("remote", "get-url", "origin", cwd=root)
    if not factory_origin(remote):
        raise RuntimeError("Bundle origin is not the factory repository")
    revision = git("rev-parse", "HEAD", cwd=root)
    if expected and revision != expected:
        raise RuntimeError("Cached checkout does not match the requested commit")
    required, declared = list(REQUIRED), None  # declared: the files the bundle's own contract requires
    contract_name = "safe_engine/bundle-inputs.json"
    contract_path = root / contract_name
    tracked_contract = git("ls-tree", "--name-only", "HEAD", "--", contract_name, cwd=root)
    if (revision == LEGACY_PILOT and entrypoint == "safe-engine"
            and not contract_path.exists() and not tracked_contract):
        required = git("ls-tree", "-r", "--name-only", "HEAD", "--",
                       "AGENTS.md", "README.md", ".agents/skills", "docs",
                       "safe_engine", cwd=root).splitlines()
    if contract_path.exists() or tracked_contract:
        if contract_path.is_symlink() or not contract_path.is_file():
            raise RuntimeError("Incomplete factory bundle: " + contract_name)
        try:
            contract = json.loads(contract_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as error:
            raise RuntimeError(f"Invalid factory input contract: {error}") from error
        version = contract.get("version") if isinstance(contract, dict) else None
        if isinstance(version, int) and not isinstance(version, bool) and version > 2 and not edited(root, contract_name):
            raise RuntimeError(NEWER.format(f"input contract version {version}"))
        keys = {"version", "required_files", "source_trees"}
        if version == 2:
            keys.add("historical_files")
        if version not in (1, 2) or set(contract) != keys:
            raise RuntimeError("Invalid factory input contract")
        for key in ("required_files", "source_trees"):
            names = contract[key]
            if (not isinstance(names, list) or not names or not all(map(safe_name, names))
                    or len({name.casefold() for name in names}) != len(names)):
                raise RuntimeError(f"Invalid {key} in factory input contract")
        for name in contract["source_trees"]:
            folder = root / name
            if folder.is_symlink() or not folder.is_dir() or not folder.resolve().is_relative_to(root):
                raise RuntimeError("Incomplete factory source area: " + name)
        # Revision-specific helpers (including wait receipts) (including scoped view modules) come from the contract, preserving older pins.
        required += [contract_name, *contract["required_files"]]
        declared = {contract_name, *contract["required_files"]}
        if version == 2:
            historical = contract["historical_files"]
            if (not isinstance(historical, list) or any(not isinstance(name, str) for name in historical)
                    or len(historical) != len(set(historical))):
                raise RuntimeError("Invalid historical_files in factory input contract")
            for name in historical:
                if not name.startswith("docs/") or not name.endswith(".md") or not safe_name(name):
                    raise RuntimeError("Invalid historical document in factory input contract")
            required += historical
            declared |= set(historical)
    missing = [name for name in required if not (root / name).is_file() or (root / name).is_symlink()]
    if missing:  # launcher-known files this revision removed and no longer declares: a newer layout, not a broken bundle
        newer = (declared is not None and not set(missing) & declared and not edited(root, contract_name)
                 and not git("ls-tree", "--name-only", "HEAD", "--", *missing, cwd=root)
                 and all(git("rev-list", "-1", "HEAD", "--", name, cwd=root) for name in missing))  # once existed
        raise RuntimeError(NEWER.format(", ".join(missing)) if newer else "Incomplete factory bundle: " + ", ".join(missing))
    if any(not (root / name).resolve().is_relative_to(root) for name in required):
        raise RuntimeError("Required factory file resolves outside the bundle")
    status = git("status", "--porcelain", "--untracked-files=all", cwd=root)
    if clean and status:
        raise RuntimeError("Cached bundle has local changes; preserve it and use a fresh cache directory")
    return {"bundle_root": str(root), "revision": revision, "version": read_version(root), "dirty": bool(status),
            "git_status": status, "source_url": re.sub(r"(?<=//)[^@/]+@", "", remote),  # never echo a token
            "entrypoint": str(root / f".agents/skills/{entrypoint}/SKILL.md")}


def layout(root):
    """'' for a factory checkout, 'skills/' for a skills folder (the plugin root or an installed copy)."""
    return "" if (Path(root) / "skills" / "safe-engine").is_dir() else "skills/"


def read_version(root):
    """The version a checkout or skills folder declares; None for a factory older than 1.0.0."""
    try:
        return (Path(root) / VERSION_FILE[len(layout(root)):]).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None


def factory_origin(url):
    """Whether a remote URL names the factory repository over an encrypted transport: ORIGINS, or its GitHub path
    over https, ssh or the scp form, whatever the credentials, case, trailing slash or `.git`."""
    path = re.sub(r"^(?:(?:https|ssh)://(?:[^@/]+@)?github\.com/|[^@/:]+@github\.com:)", "", url, flags=re.I)
    slug = REPOSITORY.removeprefix("https://github.com/").removesuffix(".git")
    return url in ORIGINS or (path != url and path.rstrip("/").removesuffix(".git").lower() == slug)


def file_sha(path):
    """sha256 of a file read with CRLF as LF: the Git blob bytes, whatever line endings the checkout uses."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def sums(files):
    """SHA256SUMS text (`sha256sum -c` format) of {name: sha256}; its own sha256 is the release's tree digest."""
    return "".join(f"{files[name]}  {name}\n" for name in sorted(files))


def build_manifest(root):
    """The manifest of a clean checkout: its version and the sha256 of every tracked file but the manifest."""
    names = set(git("ls-files", "-z", cwd=root).split("\0")) - {"", MANIFEST}
    files = {name: file_sha(Path(root) / name) for name in names}
    return {"version": read_version(root), "tree": hashlib.sha256(sums(files).encode()).hexdigest(), "files": files}


def read_manifest(root):
    """The release manifest of a checkout or skills folder, refused unless its tree digest matches its file list."""
    try:
        manifest = json.loads((Path(root) / MANIFEST[len(layout(root)):]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RuntimeError(f"No readable release manifest: {error}") from error
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if (not isinstance(files, dict) or not isinstance(manifest.get("version"), str) or not all(map(safe_name, files))
            or any(not re.fullmatch(r"[0-9a-f]{64}", str(sha)) for sha in files.values())
            or manifest.get("tree") != hashlib.sha256(sums(files).encode()).hexdigest()):
        raise RuntimeError("Release manifest is malformed or its tree digest does not match its file list")
    return manifest


def present(root, prefix, tops):
    """Factory files under root, as regular files (a link never stands in for one): a checkout's tracked and
    unignored files, or the given entry folders of a skills folder without caches or the installer's marker."""
    root = Path(root)
    paths = ((root / name for name in git("ls-files", "-co", "--exclude-standard", "-z", cwd=root).split("\0") if name)
             if not prefix else (path for top in tops for path in (root / top).rglob("*")
                                 if path.name != MARKER and "__pycache__" not in path.parts))
    return {prefix + path.relative_to(root).as_posix() for path in paths if path.is_file() and not path.is_symlink()}


def verify(root, manifest):
    """Every difference between the files under root and the manifest, as 'changed|missing|extra: <name>'."""
    root, prefix = Path(root), layout(root)
    listed = {name: sha for name, sha in manifest["files"].items() if name.startswith(prefix)}
    tops = {name[len(prefix):].split("/")[0] for name in listed} if prefix else set()
    tops = {top for top in tops if top in ENTRYPOINTS or (root / top).is_dir()}  # a plugin root adds .claude-plugin
    listed = {name: sha for name, sha in listed.items() if not prefix or name[len(prefix):].split("/")[0] in tops}
    found = present(root, prefix, tops) - {MANIFEST}
    return ([f"changed: {name}" for name in sorted(found & listed.keys())
             if file_sha(root / name[len(prefix):]) != listed[name]]
            + [f"missing: {name}" for name in sorted(listed.keys() - found)]
            + [f"extra: {name}" for name in sorted(found - listed.keys())])


def check_release(root, tag):
    """Raise unless the checkout at root is release `tag`: on main, its version equal to the tag, its files equal to
    its manifest. The resolver, the self-update and `release.py` share this one check."""
    try:
        git("merge-base", "--is-ancestor", "HEAD", "origin/main", cwd=root)
    except RuntimeError:
        raise RuntimeError(f"{tag} is not on main") from None
    manifest = read_manifest(root)
    problems = [] if manifest["version"] == read_version(root) == tag[1:] else [f"version differs from {tag}"]
    problems += verify(root, manifest)
    if problems:
        raise RuntimeError(f"{tag} does not match its manifest: " + "; ".join(problems[:5])
                           + (f"; {len(problems) - 5} more" if len(problems) > 5 else ""))


def releases(listing):
    """(tag, commit) per stable release tag in `git ls-remote --tags` or `git for-each-ref` output, newest first;
    an annotated tag's peeled `^{}` line names its commit."""
    commits = {}
    for line in listing.splitlines():
        fields = line.split()
        name = fields[1].removeprefix("refs/tags/") if len(fields) == 2 else ""
        peeled, name = name.endswith("^{}"), name.removesuffix("^{}")
        if TAG.fullmatch(name) and re.fullmatch(r"[0-9a-f]{40}", fields[0]) and (peeled or name not in commits):
            commits[name] = fields[0]
    return sorted(commits.items(), key=lambda item: tuple(map(int, TAG.fullmatch(item[0]).groups())), reverse=True)


def install_record():
    """This machine's install record (fast_install.remember); {} when nothing was installed yet."""
    path = Path(os.environ.get("SAFE_ENGINE_HOME") or Path.home() / ".safe-engine") / "install.json"
    try:
        record = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        raise RuntimeError(f"Unreadable install record {path}: {error}") from error
    if not isinstance(record, dict):
        raise RuntimeError(f"Install record {path} is not a JSON object")
    return record


def channel(record):
    """The record's update channel, stable when unset; any other value is refused, never guessed."""
    value = record.get("channel", "stable")
    if value not in ("stable", "edge"):
        raise RuntimeError(f"Unknown update channel {value!r} in the install record: use stable or edge")
    return value


def channel_ref():
    """The ref new projects resolve: None (the newest release) on stable, main on edge."""
    return DEFAULT_REF if channel(install_record()) == "edge" else None


def resolve_release(cache, tag, entrypoint):
    """The newest release on main whose files match its manifest (or exactly `tag`); main, with a notice, only while
    no release exists. Releases that all fail are refused, never replaced by main."""
    found = [item for item in releases(git("ls-remote", "--tags", REPOSITORY)) if not tag or item[0] == tag]
    reasons = []
    for name, commit in found:
        try:
            result = resolve_bundle(cache, commit, entrypoint)
            check_release(result["bundle_root"], name)
            result.update(channel="stable", release=name, latest_release=found[0][0])
            if reasons:
                result["notice"] = "Newer release unavailable: " + "; ".join(reasons) + f". Using verified {name}."
            return result
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            reasons.append(f"{name}: {error}" if not str(error).startswith(name) else str(error))
    if found or tag:
        raise RuntimeError("No release verifies: " + ("; ".join(reasons) or f"{tag} does not exist"))
    return {**resolve_bundle(cache, DEFAULT_REF, entrypoint), "channel": "edge", "notice": "No release yet: using main"}


def resolve_bundle(cache, ref=None, entrypoint="improve-factory"):
    """One clean bundle per commit in the cache: the newest verified release (ref None), a release tag, a branch or
    a full commit SHA."""
    if entrypoint not in ENTRYPOINTS:
        raise RuntimeError("Unknown factory entrypoint")
    if ref is None or TAG.fullmatch(ref):
        return resolve_release(cache, ref, entrypoint)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", ref):
        raise RuntimeError("Use a branch name or full 40-character commit SHA")
    if re.fullmatch(r"[0-9a-fA-F]{40}", ref):
        revision = ref.lower()
    else:
        line = git("ls-remote", "--exit-code", REPOSITORY, f"refs/heads/{ref}")
        fields = line.split()
        if (len(fields) != 2 or fields[1] != f"refs/heads/{ref}"
                or not re.fullmatch(r"[0-9a-f]{40}", fields[0])):
            raise RuntimeError("Could not resolve one exact remote branch")
        revision = fields[0]
    cache = Path(cache).expanduser().resolve()
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / revision
    if destination.exists():
        return inspect_bundle(destination, expected=revision, clean=True, entrypoint=entrypoint)
    pending = Path(tempfile.mkdtemp(prefix=f"{revision}.pending-", dir=cache))
    try:
        git("clone", "--no-checkout", "--", REPOSITORY, str(pending))
        git("checkout", "--detach", revision, cwd=pending)
        inspect_bundle(pending, expected=revision, clean=True, entrypoint=entrypoint)
        try:
            pending.rename(destination)
        except OSError:
            if not destination.exists():
                raise
            # Another installer may have completed this revision; validate it below.
        result = inspect_bundle(destination, expected=revision, clean=True, entrypoint=entrypoint)
        if pending.exists():
            result["retained_temporary_checkout"] = str(pending)
        return result
    except Exception as error:
        raise RuntimeError(f"Bundle resolution failed; partial checkout preserved at {pending}: {error}") from error


def selection_paths(project):
    """Reject aliases before any selection read or write."""
    project = Path(project).expanduser().resolve()
    if not project.is_dir():
        raise RuntimeError("Create or locate the target project directory first")
    directory = project / ".factory"
    receipt = directory / "entry-bundle.json"
    for path in (directory, receipt, directory / "entry.lock"):
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise RuntimeError("Factory selection paths must not be symlinks or reparse points")
    return directory, receipt


@contextmanager
def selection_lock(project):
    """Serialize selection and run creation; OS releases the lock if the process exits."""
    directory, _ = selection_paths(project)
    directory.mkdir(exist_ok=True)
    with (directory / "entry.lock").open("a+b") as handle:
        if not os.fstat(handle.fileno()).st_size:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError("Another factory selection or start is active; retry after it finishes") from error
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def active_selection(project):
    """Only demonstrably closed Fast runs permit refresh; Safe/unknown evidence keeps its pin."""
    project = Path(project).resolve()
    directory, _ = selection_paths(project)
    home = Path(os.environ.get("SAFE_ENGINE_HOME") or Path.home() / ".safe-engine")
    key = hashlib.sha1(os.path.normcase(os.path.realpath(project)).encode()).hexdigest()[:16] + ".json"
    registration = home / "active" / key
    if os.path.lexists(registration):
        return "open or unknown Fast/Lucky run"
    # The gate home owns lifecycle truth; a project mirror cannot reopen an owner-closed run.
    paths = [home / "runs" / key, home / "runs" / "closed" / key]
    if not any(os.path.lexists(path) for path in paths):
        paths = [directory / "fast" / "run.json"]
    for path in paths:
        for node in (path.parent, path):
            if os.path.lexists(node):
                info = node.lstat()
                if (stat.S_ISLNK(info.st_mode)
                        or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                    return "aliased run state"
        try:
            run = json.loads(path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError:
            continue
        except (OSError, ValueError):
            return "unreadable run state"
        if not isinstance(run, dict) or run.get("version") != 1 or run.get("closed") is not True:
            return "open or unknown Fast/Lucky run"
    if os.path.lexists(directory / "state.json") or os.path.lexists(directory / "history"):
        return "existing Safe run"
    named = directory / "runs"
    if os.path.lexists(named):
        for path in (named, *named.iterdir()) if named.is_dir() else (named,):
            info = path.lstat()
            if (stat.S_ISLNK(info.st_mode)
                    or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise RuntimeError("Named runs must not use symlinks or reparse points")
        if not named.is_dir() or (any(named.iterdir()) and not terminal_named_runs(project, named)):
            return "existing or unknown named Safe run"
    if (directory / "fast" / "work-record.md").exists() and not any(path.exists() for path in paths):
        return "work record without run identity"
    return None


def terminal_named_runs(project, named):
    """Only released claims with matching terminal records permit another ticket's factory selection."""
    try:
        common = Path(git("rev-parse", "--git-common-dir", cwd=project))
        common = common if common.is_absolute() else project / common
        claims_path = common / "safe-engine/tickets/claims.json"

        def read(path, text=False):
            # Lifecycle proof through an alias is not evidence about this checkout.
            for node in (path, *path.parents):
                info = node.lstat()
                if (stat.S_ISLNK(info.st_mode)
                        or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                    raise ValueError("aliased lifecycle evidence")
            value = path.read_text(encoding="utf-8-sig")
            return value if text else json.loads(value)

        claims = read(claims_path)
        if not isinstance(claims, dict):
            return False
        if any(not isinstance(claim, dict) or (claim.get("project") == str(project) and claim.get("active") is not False)
               for claim in claims.values()):
            return False
        for directory in named.iterdir():
            state, claim = read(directory / "state.json"), claims.get(directory.name, {})
            if (not isinstance(state, dict) or not isinstance(claim, dict)
                    or state.get("schema_version") != 1 or not state.get("run_id")
                    or state.get("project") != str(project) or state.get("pending_operation", True) is not None
                    or claim != {"project": str(project), "directory": str(directory),
                                 "run_id": state["run_id"], "active": False}):
                return False
            sequence = state.get("sequence")
            if type(sequence) is not int or sequence < 1 or read(directory / "history" / f"{sequence:04d}.json") != state:
                return False
            if state.get("phase") == "cancelled":
                continue
            history = state.get("history")
            if (state.get("phase") != "ready" or not isinstance(history, list) or not history
                    or not isinstance(history[-1], dict)
                    or history[-1].get("event") != "Prepared checked local handoff"
                    or f"Run: {state['run_id']}\n" not in read(directory / "handoff.md", text=True)):
                return False
        return True
    except (RuntimeError, OSError, ValueError, TypeError):
        return False  # Unknown or interrupted transitions retain the previous factory.


def saved_selection(receipt):
    """Read known receipt versions; absence of pin provenance stays unknown."""
    if receipt.exists():
        try:
            saved = json.loads(receipt.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise RuntimeError(f"Cannot read existing bundle selection: {error}") from error
        if (not isinstance(saved, dict) or saved.get("version") not in (1, 2)
                or not isinstance(saved.get("bundle_root"), str)
                or not Path(saved["bundle_root"]).is_absolute()
                or not isinstance(saved.get("revision"), str)
                or not re.fullmatch(r"[0-9a-f]{40}", saved["revision"])):
            raise RuntimeError("Invalid bundle selection; preserve it and establish the original identity")
        if saved["version"] == 2 and saved.get("policy") not in ("automatic", "explicit"):
            raise RuntimeError("Invalid bundle selection policy; preserve its original identity")
        return saved
    return None


def save_selection(receipt, result, policy):
    """Publish a complete receipt under selection_lock; a failed write preserves the old receipt."""
    data = {"version": 2, "bundle_root": result["bundle_root"], "revision": result["revision"], "policy": policy}
    handle, temporary = tempfile.mkstemp(prefix="entry-", suffix=".tmp", dir=receipt.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as output:
            json.dump(data, output, indent=2)
            output.write("\n")
        os.replace(temporary, receipt)
    finally:
        Path(temporary).unlink(missing_ok=True)


def select_for_project(project, bundle, ref, cache, entrypoint, new_run=False):
    """Resume offline by default; explicit new-run intent may refresh an automatic selection."""
    with selection_lock(project):
        return select_locked(project, bundle, ref, cache, entrypoint, new_run)


def select_locked(project, bundle, ref, cache, entrypoint, new_run=False):
    """Select while the caller holds the project lock, including through subsequent run creation."""
    directory, receipt = selection_paths(project)
    saved = saved_selection(receipt)
    held = active_selection(project)
    policy = saved.get("policy", "legacy") if saved else "explicit" if bundle or ref else "automatic"
    if saved:
        if ref is not None or (bundle and Path(bundle).expanduser().resolve() != Path(saved["bundle_root"]).resolve()):
            raise RuntimeError("An existing selection cannot be upgraded here; use improve-factory")
        result = inspect_bundle(saved["bundle_root"], expected=saved["revision"], clean=policy == "automatic", entrypoint=entrypoint)
        if not new_run or held:
            return {**result, "selection_record": str(receipt), "selection_policy": policy,
                    **({"notice": f"Keeping selected factory: {held}."} if new_run and held else {})}
        try:
            latest = resolve_bundle(cache, channel_ref(), entrypoint=entrypoint)
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            return {**result, "selection_record": str(receipt), "selection_policy": policy,
                    "notice": f"Latest factory check failed: {error}. Keeping factory {result['version'] or 'unversioned'} "
                              f"at {result['revision']}."}
        if policy == "automatic":
            if saved_selection(receipt) != saved:
                raise RuntimeError("Bundle selection changed during resolution; preserve it and retry")
            if held := active_selection(project):
                return {**result, "selection_record": str(receipt), "selection_policy": policy,
                        "notice": f"Keeping selected factory: {held} appeared during resolution."}
            result = latest
            save_selection(receipt, result, policy)
        else:
            result.update(latest_release=latest.get("latest_release", latest.get("release")),
                          notice=f"Keeping {policy} pin. " + latest.get("notice", ""))
    else:
        if held and not bundle:
            raise RuntimeError("Existing run has no bundle path record; establish its original bundle and use --bundle")
        result = (inspect_bundle(bundle, entrypoint=entrypoint) if bundle
                  else resolve_bundle(cache, ref or channel_ref(), entrypoint=entrypoint))
        if receipt.exists() or (not bundle and active_selection(project)):
            raise RuntimeError("A selection or run appeared during resolution; preserve it and retry")
        save_selection(receipt, result, policy)
    result.update(selection_record=str(receipt), selection_policy=policy)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--bundle", type=Path, help="Inspect the exact existing checkout; no fetch/update")
    choice.add_argument("--ref", help="Release tag (vX.Y.Z), branch or full SHA for a new run/case; default: the newest "
                                      "verified release (main on the edge channel or before the first release)")
    parser.add_argument("--cache-dir", type=Path, default=Path.home() / ".safe-engine" / "bundles")
    parser.add_argument("--project", type=Path, help="Remember this project's selection; reuse it offline on resume")
    parser.add_argument("--new-run", action="store_true", help="Refresh an automatic selection only before a new run; preserve pins")
    installed_name = Path(__file__).resolve().parent.parent.name
    parser.add_argument("--entrypoint", choices=ENTRYPOINTS,
                        default=installed_name if installed_name in ENTRYPOINTS else "safe-engine")
    args = parser.parse_args()
    if args.new_run and not args.project:
        parser.error("--new-run needs --project")
    try:
        if args.project:
            result = select_for_project(args.project, args.bundle, args.ref, args.cache_dir, args.entrypoint, args.new_run)
        else:
            result = (inspect_bundle(args.bundle, entrypoint=args.entrypoint) if args.bundle else
                      resolve_bundle(args.cache_dir, args.ref or channel_ref(), entrypoint=args.entrypoint))
        if result.get("notice"):
            print(result["notice"], file=sys.stderr)
        print(json.dumps(result, indent=2))
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"Factory unavailable: {error}\nUse existing authorized Git credentials; do not paste tokens into chat.\n")


if __name__ == "__main__":
    main()
