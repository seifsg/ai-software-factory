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

Setup needs the native Codex CLI on PATH, or `CODEX_EXECUTABLE` set to its absolute executable. It uses a private temporary config and read-only parser calls; it never starts a thread, executes existing project MCP commands or changes user trust. A missing/unsupported CLI or malformed TOML stops setup with the original files preserved. Python 3.9 remains supported.

This writes `<dir>/.codex/hooks.json` and one owned MCP block in `<dir>/.codex/config.toml`, without copying skills or changing pinned methods. It preserves unrelated handlers, including ones in the same matcher group, and all TOML bytes outside its exact managed block. An existing same-name server or altered block without verified receipt ownership is refused. Keep the selected runtime/interpreter paths available; project configuration points to them. The gate home selected at setup is bound in that server configuration. To change it, close unfinished runs using the original home, remove this project registration with that original `SAFE_ENGINE_HOME`, then configure with the new home and review trust in a fresh connection. Changing the environment alone loses access to the old ownership receipt and is refused; it does not migrate state.

Configuration is not activation. Review project configuration and exact-hook trust in Codex's `/hooks`, then open a fresh connection in that project. No automatic reload or trust is promised. Confirm server readiness, loaded definitions and a real hook event before claiming enforcement; see [Codex scope and participation](hosts.md#codex).

A clean global install leaves ordinary projects without factory hook calls or this MCP server. Each MCP connection in an opted-in project starts one reusable Python process, even without a run. Separate chats can create separate connections/processes in the same host/project. Each callback reuses its connection; absent authoritative home files yield an empty result without another shell/interpreter. The process can outlive chat unsubscribe and exits on host EOF. There is no global daemon, polling or cached run policy. Startup, memory and per-call costs remain; no zero-overhead claim.

The required server must connect at startup. Missing runtime/interpreter or invalid configuration: repair the named prerequisite and retry a fresh connection, or remove the owned project registration after closing its unfinished runs. A later disconnect does not reconnect through a hook, and failed/missing calls fail open. Preserve unfinished state and use direct gate commands while repairing coverage. SessionStart may precede readiness; a participating later prompt or `status` supplies current guidance. Runtime updates require a fresh connection; setup/status alone cannot confirm the loaded version.

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

Removal keeps work records, run state, pinned bundles and skills. Project removal requires the native parser and verified receipt for its MCP block. First setup backs up both original files under `~/.safe-engine/installations/` (or `SAFE_ENGINE_HOME`); the private receipt journals paired changes and byte hashes. The two file replacements are recoverable, not globally atomic. An interruption is reconciled on the next same setup command: exact factory writes can be rolled back or a completed pair finalized. Later owner edits cause an explicit refusal, with no overwrite; reconcile those edits with the receipt/backups before retrying. A setup/removal error does not mean completion. Fix the named cause and repeat the same command; for manual rollback, check that backups will not replace later unrelated settings, then review trust again. Receipts prove configuration only. Private structured setup/recovery diagnostics live in `<gate-home>/logs/gate.log`, with bounded rotation to `gate.log.1`; logging failure never blocks recovery or close.

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
