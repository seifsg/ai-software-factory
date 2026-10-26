# Upgrading

What installs and active runs must do for each release, newest first. What changed: [CHANGELOG.md](CHANGELOG.md).

For every release:

- **Pinned projects never change.** Each keeps the factory commit its `.factory/entry-bundle.json` names, including active runs. To move a project to a newer release, ask `improve-factory Switch [absolute project directory] to the newest factory.`; it checks the run is compatible first.
- **Check what you run:** `fast_gate.py version` names the version, commit, channel and route; `fast_gate.py verify` lists every file that differs from the release manifest.

## Next version

- New report publication checks picture content. Convert palette/interlaced/animated images to static 8-bit RGB/RGBA PNGs and inspect the result. Install updated launchers for `report`; supply honest per-ticket metrics or unavailable reasons. Existing saved reports are not fabricated from session totals.

- Worth-it rounds: update the installed launchers to obtain `fix-round`; new Fast/Lucky runs record `**Findings:** none` or their final scored report path. New complete-cycle Safe runs require worth fields and explicit repair selections. Existing saved runs keep their prior checks/schema. Do not upgrade an active run's pinned bundle. See [worth-it rounds](docs/worth-it.md).

New UI runs on the resolved current bundle freeze a Show plan and share current pictures before proof. Existing runs keep their recorded sequence; do not rewrite active ledgers. See [Show first](docs/show-first.md).

- New design-port runs use `start --design-port` and record reference coverage before plan. Existing runs keep their selected methods and obligations; do not add the flag or rewrite their ledger mid-run.

## 1.0.0

From an install made before versioning:

- **Claude Code:** nothing to do. The plugin moves to 1.0.0 once tag `v1.0.0` is published and loads on `/reload-plugins` or a new session. Until that tag exists, a new install cannot fetch the plugin; an existing one keeps its copy.
- **Codex, Cursor and other, installed from a clone with auto-update:** nothing to do. The next daily update brings the new updater; from then on the clone follows release tags and stays detached at the newest verified one. To follow `main` instead: `fast_gate.py install --host <host> --channel edge`.
- **Installed by hand or with `--no-auto-update`:** in your clone run `git fetch --tags` and `git checkout v1.0.0`, then rerun `fast_gate.py install --host <host>`.
- **Active runs:** no action; each keeps its pinned bundle. Safe runs saved before 1.0.0 load on any 1.x bundle.
- **New projects:** pin the newest verified release instead of `main`; on the edge channel, `main`.
