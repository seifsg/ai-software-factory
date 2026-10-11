# Install

Needs Git and Python 3.9+ (an agent following these steps installs missing ones from official sources), and read access to the repository: `gh auth login` lets Git use your GitHub credentials over HTTPS.

1. Get the factory (any checkout or bundle works):

   ```text
   git clone https://github.com/seifsg/ai-software-factory.git
   ```

2. Install for your agent:

   ```text
   python <factory>/skills/safe-engine/scripts/fast_gate.py install --host claude|codex|cursor|other [--project <dir>]
   ```

   - `claude`: enables the plugin (both launchers and the gate hooks) with auto-update in your user settings. Start a new session.
   - `codex`: copies both launchers into `~/.agents/skills`. A clean user install adds no hooks. Existing factory user hooks stay installed and are reported; migration is explicit below.
   - `cursor`: copies both launchers into `~/.agents/skills` and writes the gate hooks.
   - `other`: copies the launchers only; wire hooks by hand per [hosts](hosts.md#other-agents).
   - `--project <dir>` installs into one project instead of your user folders, including scoped Codex hooks. Re-running replaces only the factory's own entries. It refuses existing skills it did not install, including this repository's canonical `.agents/skills`; use the hooks-only command below there.

3. Ask your agent for the skill, in its own syntax ([hosts](hosts.md)):

   ```text
   safe-engine Build [app or feature] in [absolute project directory]. Success means [observable outcome].
   safe-engine Resume [absolute project directory].
   improve-factory The factory did [observed]; expected [result].
   ```

Skills appear on the next turn or in a new session. If not, ask the agent to read the installed `SKILL.md` by path.

## Codex project hooks

Keep the skills global and opt each project into hooks separately. From an updated installed runtime or retained factory checkout:

```text
python <factory>/skills/safe-engine/scripts/fast_gate.py hooks --host codex --project <absolute-dir>
```

This writes `<dir>/.codex/hooks.json` without copying skills or changing pinned methods. It preserves unrelated handlers, including ones in the same matcher group, and configuration keys. Keep the runtime path available: the trusted command points to it.

Configuration is not activation. Review project trust and the exact commands in Codex's `/hooks`, then load a fresh session in that project. No automatic reload of the current session is promised. A changed command may need new trust. Confirm loading and a real hook event before claiming enforcement; see [Codex scope and participation](hosts.md#codex).

A clean global install leaves ordinary projects without factory hook calls. An opted-in idle project still invokes a native shell guard; it starts no Python when neither authoritative home file for that project exists. Active or degraded state wakes the gate. This removes Python startup from the idle path, but does not imply zero shell cost or a measured latency gain.

The Windows definition uses PowerShell's file-existence checks inside the host's existing hook shell, without starting another shell. Confirm PowerShell command support for your Codex version when reviewing the definition. `SAFE_ENGINE_HOME` remains path data; its default follows `USERPROFILE`, then `HOMEDRIVE` and `HOMEPATH`, as the Python gate does.

### Migrate existing Codex user hooks

Updating launchers leaves existing user hook definitions in place. User, project, inline configuration, plugin and managed hook sources can be additive: adding project hooks does not remove a global source.

1. Finish and close unfinished runs in the gate home. Removal refuses any unfinished run for `--user`, or the selected project's unfinished run for project removal. Do not abandon work merely to remove hooks; `close --abandon` requires the owner's reason.
2. Configure and review project hooks for each project that needs enforcement.
3. Remove the recognized factory handlers from the user JSON file explicitly:

   ```text
   python <factory>/skills/safe-engine/scripts/fast_gate.py hooks --host codex --remove --user
   ```

4. Review effective hook sources and start fresh sessions. This command leaves inline, plugin and managed sources alone; remove those through their owning configuration with the owner's authority if needed. Unknown commands and unrelated handlers remain.

To remove only a project's recognized factory hooks:

```text
python <factory>/skills/safe-engine/scripts/fast_gate.py hooks --host codex --project <absolute-dir> --remove
```

Removal keeps work records, run state, pinned bundles and skills. Existing configuration is backed up on first hooks-only setup under `~/.safe-engine/installations/` (or `SAFE_ENGINE_HOME`), alongside a receipt identifying the configuration and backup. A setup/removal error does not mean completion: inspect the reported configuration and receipt, fix the named cause and repeat the same command. For rollback, restore the recorded backup after checking that it will not overwrite later unrelated changes; review trust again. Receipts prove configuration only. Setup and recovery diagnostics live in `<gate-home>/logs/gate.log`, with bounded rotation to `gate.log.1`; log-write failure must not block recovery or close.

## What first use does

```text
launcher → resolve_bundle.py pins the factory's main branch to one commit in ~/.safe-engine/bundles/<commit>
         → .factory/entry-bundle.json records the selection (keep .factory/ out of Git)
         → the agent reads .agents/skills/safe-engine/SKILL.md from that bundle and runs it on the target
```

- Resume reuses the recorded bundle offline. It never pulls, resets or silently upgrades.
- An installed launcher older than the factory it fetches says the layout is newer (older launchers say "Incomplete factory bundle"). Update the install.
- Reproducible installs: check out one commit, install from it, and pass the same SHA to the resolver's `--ref` for a new project.
- Installing on one machine does not reach other machines or cloud sessions; install there too. Cloud sessions load skills committed to their repository.

## Update and uninstall

Per route, with what happens to pinned projects: [update](../README.md#-update) · [uninstall](../README.md#-uninstall).
