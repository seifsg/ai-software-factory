# Install

Needs Git and Python 3.9+ (an agent following these steps installs missing ones from official sources), and read access to the repository: `gh auth login` lets Git use your GitHub credentials over HTTPS.

1. Get the factory (any checkout or bundle works):

   ```text
   git clone https://github.com/seifsg/ai-software-factory.git
   ```

2. Install for your agent:

   ```text
   python <factory>/skills/safe-engine/scripts/fast_gate.py install --host claude|codex|cursor|other [--project <dir>] [--no-auto-update] [--channel stable|edge] [--codex-home <dir>]
   ```

   - `claude`: enables the plugin (both launchers and the gate hooks) with auto-update in your user settings, then installs it at user scope with Claude Code's CLI (`claude plugin marketplace update` or `add`, `claude plugin install`) and checks `claude plugin list --json`. The plugin follows release tags. Start a new session. It exits 1 with the fix when the CLI is missing or a step fails: enabled in settings alone may never install. It finds the CLI on `PATH`, in `~/.local/bin` or in the Windows desktop app's `%APPDATA%\Claude\claude-code` folder; set `SAFE_ENGINE_CLAUDE` to its path otherwise.
   - `codex`, `cursor`: copies both launchers into `~/.agents/skills` and writes the gate hooks. Codex asks you to trust them once.
   - `other`: copies the launchers only; wire hooks by hand per [hosts](hosts.md#other-agents).
   - `--project <dir>` installs into one project instead of your user folders. Re-running replaces only the factory's own entries.
   - From a clone, `codex`, `cursor` and `other` update themselves once a day at session start; `--no-auto-update` turns that off ([hosts](hosts.md#updates)).
   - `--channel` sets this machine's channel, kept until you change it: `stable` (the default) follows the newest verified release, `edge` follows `main`. It decides what self-updates and new projects get.
   - `--codex-home <dir>` (Codex): writes the gate hooks into that `CODEX_HOME` instead of `~/.codex`, for an agent with its own Codex home such as an orchestrator's ([orchestrators](orchestrators.md)).

3. Ask your agent for the skill, in its own syntax ([hosts](hosts.md)):

   ```text
   safe-engine Build [app or feature] in [absolute project directory]. Success means [observable outcome].
   safe-engine Resume [absolute project directory].
   improve-factory The factory did [observed]; expected [result].
   ```

Skills appear on the next turn or in a new session. If not, ask the agent to read the installed `SKILL.md` by path.

## Version and updates

```text
python <launchers>/safe-engine/scripts/fast_gate.py version
python <launchers>/safe-engine/scripts/fast_gate.py verify [--path <factory checkout or skills folder>]
```

- `version` prints the version, commit, channel, install route and the release digest with how this copy compares. `start` and `status` cards show the version too, plus a one-time notice after an update or a rollback.
- `verify` lists every changed, missing or extra file against the release manifest and exits 1 on any. `<launchers>` is `~/.agents/skills` (Codex, Cursor, other), the Claude Code plugin folder, or `skills` in a clone.
- What changed in each release: `CHANGELOG.md`; what to do: `UPGRADING.md` (both at the repository root).
- Update, switch channel, roll back: [README](../README.md#-update).

## What first use does

```text
launcher → resolve_bundle.py pins the newest release tag on main whose files match its manifest
           (main on the edge channel, or while no release exists, with a notice)
         → one commit in ~/.safe-engine/bundles/<commit>; .factory/entry-bundle.json records it (keep .factory/ out of Git)
         → the agent reads .agents/skills/safe-engine/SKILL.md from that bundle and runs it on the target
```

- Resume reuses the recorded bundle offline. For a new run use `resolve_bundle.py --project <dir> --new-run`: automatic selections refresh, while explicit pins, legacy receipts without pin provenance, and open or unknown Fast/Lucky/Safe state stay intact. `--new-run` requires `--project`. The gate home owns Fast/Lucky closure: its closed record permits a new run even if the project mirror is missing or stale.
- `fast_gate.py start` establishes a missing selection through the existing resolver before recording run policies. Automatic selections refresh; explicit and legacy pins are verified locally without a remote freshness lookup, with latest release marked unchecked. Read the entrypoint if selection changed. Project commands/hooks follow the saved run's gate offline; maintenance from a verified checkout stays local. Invalid selection fails before new state is created.
- Failed lookup/download/verification names the error and retained version; a rejected newer release remains visible when an older release verifies. Unknown latest stays unknown. No usable selection means an error. Edge continues to follow `main`.
- An installed launcher older than the factory it fetches says the layout is newer (older launchers say "Incomplete factory bundle"). Update the install.
- Reproducible installs: check out one release tag, install from it, and pass the same tag (`--ref vX.Y.Z`) or SHA to the resolver for a new project.
- Installing on one machine does not reach other machines or cloud sessions; install there too. Cloud sessions load skills committed to their repository.

## Update and uninstall

Per route, with what happens to pinned projects: [update](../README.md#-update) · [uninstall](../README.md#-uninstall).
