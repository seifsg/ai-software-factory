# Install

Needs Git and Python 3.9+. The launchers find or install them from official sources.

1. Get the factory with your existing Git access (any checkout or bundle works):

   ```text
   git clone https://github.com/seifsg/ai-software-factory.git
   ```

2. Install for your agent:

   ```text
   python <factory>/skills/safe-engine/scripts/fast_gate.py install --host claude|codex|cursor|other [--project <dir>]
   ```

   - `claude`: enables the plugin (both launchers and the gate hooks) with auto-update in your user settings. Start a new session.
   - `codex`, `cursor`: copies both launchers into `~/.agents/skills` and writes the gate hooks. Codex asks you to trust them once.
   - `other`: copies the launchers only; wire hooks by hand per [hosts](hosts.md#other-agents).
   - `--project <dir>` installs into one project instead of your user folders. Re-running replaces only the factory's own entries.

3. Ask your agent for the skill, in its own syntax ([hosts](hosts.md)):

   ```text
   safe-engine Build [app or feature] in [absolute project directory]. Success means [observable outcome].
   safe-engine Resume [absolute project directory].
   improve-factory The factory did [observed]; expected [result].
   ```

Skills appear on the next turn or in a new session. If not, ask the agent to read the installed `SKILL.md` by path.

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
