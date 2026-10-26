# Upgrading

What installs and active runs must do for each release, newest first. What changed: [CHANGELOG.md](CHANGELOG.md).

For every release:

- **Active and explicit pins never change automatically.** Ask `improve-factory` for a compatible pin change; never edit a selected bundle or receipt.
- **Check what you run:** `fast_gate.py version` names the version, commit, channel and route; `fast_gate.py verify` lists every file that differs from the release manifest.

## Next release

- Reinstall launchers/hooks for `wait` commands. New runs require explicit supported wait receipts; existing runs retain their prior host-list behavior until they register a wait. Completion callbacks must use the selected gate and the original gate home.

- Reinstall the launchers/hooks to enable new-run selection and selected-gate routing. Existing active runs retain their bundle and recorded behavior.
- New automatic receipts refresh at the next start, or with `resolve_bundle.py --project <dir> --new-run`. Resume omits `--new-run` and remains offline. Explicit selections and existing v1 receipts retain their pin; v1 has no trustworthy pin provenance and is never automatically migrated.
- Latest-check failures name the version retained. An unknown latest is not a successful check. Read a newly selected entrypoint before continuing the run. Bare-gate starts without a receipt remain legacy use.

## 1.0.0

From an install made before versioning:

- **Claude Code:** nothing to do. The plugin moves to 1.0.0 once tag `v1.0.0` is published and loads on `/reload-plugins` or a new session. Until that tag exists, a new install cannot fetch the plugin; an existing one keeps its copy.
- **Codex, Cursor and other, installed from a clone with auto-update:** nothing to do. The next daily update brings the new updater; from then on the clone follows release tags and stays detached at the newest verified one. To follow `main` instead: `fast_gate.py install --host <host> --channel edge`.
- **Installed by hand or with `--no-auto-update`:** in your clone run `git fetch --tags` and `git checkout v1.0.0`, then rerun `fast_gate.py install --host <host>`.
- **Active runs:** no action; each keeps its pinned bundle. Safe runs saved before 1.0.0 load on any 1.x bundle.
- **New projects:** pin the newest verified release instead of `main`; on the edge channel, `main`.
