# Install

Needs Git, read access to the repository (`gh auth login` lets Git use your GitHub credentials over HTTPS) and, on Windows, Git Bash for the hooks.

## Claude Code

```text
claude plugin marketplace add https://github.com/seifsg/ai-software-factory.git
claude plugin install safe-factory@ai-software-factory
```

In a session, the same as `/plugin marketplace add …` and `/plugin install …`. Use the HTTPS URL; `owner/repo` shorthand tries SSH first. Auto mode: new projects need `gh repo create` and `git push` allowed. Add `Bash(gh repo create:*)` and `Bash(git push:*)` to your permission allow rules, or approve once when step 0 asks. Plugin brings every skill, delegate roles, the run hooks and the update check; follows release tags. Start a new session.

Desktop app without terminal: add to `~/.claude/settings.json`, start a new session, then install from `/plugin` if missing:

```json
"extraKnownMarketplaces": {"ai-software-factory": {"source": {"source": "git", "url": "https://github.com/seifsg/ai-software-factory.git"}, "autoUpdate": true}},
"enabledPlugins": {"safe-factory@ai-software-factory": true}
```

Try unreleased checkout: `claude --plugin-dir <clone>/.agents`.

## Codex

Plugin (Windows automatic phase chain verified; full delivery pending):

```text
codex plugin marketplace add https://github.com/seifsg/ai-software-factory.git
codex plugin add safe-factory@ai-software-factory
```

Or pick it in `/plugins`. Start a new session, trust its hooks in `/hooks` (again after each update: trust follows each hook's hash). Update: `codex plugin marketplace upgrade ai-software-factory`. Remove: `codex plugin remove safe-factory@ai-software-factory`. Codex reads the repo's `.claude-plugin/marketplace.json`; the plugin root is `.agents/` (`.codex-plugin/plugin.json`, `skills/`, `hooks/hooks.json`). Plugin hooks run only for manual installs.

On Windows, `commandWindows` uses `hooks/windows.cmd` to find Git Bash beside `git.exe` on `PATH`, then runs the same Stop, compact and startup scripts. No PowerShell execution-policy change or extra runtime is needed. Missing Git Bash produces a notice with the install and restart action; the factory does not automatically continue. Check a new run advances from the ticket response to a separate analysis prompt and full response. An installed skill or trusted hook entry alone does not prove that chain.

The bounded native test reached ticket, analysis, recommendation and challenge through three automatically injected prompts, retained four complete responses in chat, then stopped. Codex records those hook-driven rounds within one outer native turn ID; each injected prompt is a user-role history item and each phase output is a separate final assistant message. Later delivery phases and other operating systems remain outside that live-test scope.

Without plugins, copy by hand:

1. Clone factory: `git clone https://github.com/seifsg/ai-software-factory.git <clone>`.
2. Copy skills where Codex finds them (all users of this machine: `~/.agents/skills`; one project: `<project>/.agents/skills`):

   ```text
   mkdir -p ~/.agents/skills
   cp -r <clone>/.agents/skills/* ~/.agents/skills/
   ```

3. Add hooks to `~/.codex/hooks.json` (merge with entries you have), absolute paths. Windows: `commandWindows` needs Git's `sh` on `PATH` (add `C:\Program Files\Git\bin`); not yet tried in a live Windows Codex session:

   ```json
   {
     "hooks": {
       "Stop": [{"hooks": [{"type": "command", "timeout": 10,
         "command": "sh \"<home>/.agents/skills/safe-factory/scripts/run-guard.sh\" stop",
         "commandWindows": "sh \"<home>/.agents/skills/safe-factory/scripts/run-guard.sh\" stop"}]}],
       "SessionStart": [{"matcher": "compact|resume", "hooks": [{"type": "command", "timeout": 10,
         "command": "sh \"<home>/.agents/skills/safe-factory/scripts/run-guard.sh\" compact",
         "commandWindows": "sh \"<home>/.agents/skills/safe-factory/scripts/run-guard.sh\" compact"}]}]
     }
   }
   ```

4. Start Codex, trust both hooks once in `/hooks`.

## Cursor

Plugin (not yet run live): in a session, `/plugin marketplace add https://github.com/seifsg/ai-software-factory.git`, then `/plugin` and install `safe-factory` (CLI: `agent plugin marketplace add …`; editor: paste the repo URL into the plugin search). Reads `.cursor-plugin/marketplace.json`. Brings skills, delegate roles and the run hooks. Cursor also loads Claude Code's installed plugins (Settings → Agents → Third-Party Imports → Include Third-Party Plugins, Skills, and Other Configs): with the Claude Code plugin installed, skip this one or turn that off, else every hook runs twice. Update: GitHub installs stay on the commit they were installed from, so uninstall and install again in `/plugin`; a team marketplace import with Auto Refresh updates by itself (Teams and Enterprise).

## Update check

At session start the plugin hook reads a cached latest release (no network, about 0.2 s on Windows) and refreshes that cache in the background once a day with `gh api`, or `curl` when `gh` is missing or signed out. Check by hand: compare the README version badge, or the [Latest release](https://github.com/seifsg/ai-software-factory/releases/latest), with your agent's installed plugin version. A newer release: the agent tells you before any run and links what's new. The same hook also lists leftovers of old versions (see below) and the agent offers to clean them; it never stops a run for it. Off: `FACTORY_NO_UPDATE_CHECK=1`.

## Clean up and uninstall

Old versions and copies leave things behind: 1.x hooks in `~/.codex/hooks.json` or `~/.cursor/hooks.json`, launchers in `~/.agents/skills/safe-engine`, `~/.safe-engine`, project hooks pointing at old paths, a second Stop guard, the old `safe-engine@` plugin id, stale copies of `pre-push` and `codex.rules`. From the project:

```text
sh <plugin root>/skills/safe-factory/scripts/doctor.sh         # list leftovers, change nothing
sh <plugin root>/skills/safe-factory/scripts/doctor.sh --fix   # move them to a backup, refresh stale copies
```

`--fix` never deletes: each item goes to `~/.cache/ai-software-factory/removed/<time>/`, listed with its old path in `index`. A config file that holds other settings is only reported, with the entry to delete. `<plugin root>`: Claude Code `~/.claude/plugins/marketplaces/ai-software-factory/.agents`; a clone: `<clone>/.agents`.

Uninstall: run `doctor.sh --fix`, then remove the plugin (`claude plugin uninstall safe-factory@ai-software-factory`, `codex plugin remove safe-factory@ai-software-factory`, Cursor `/plugin`), delete copied skills (`~/.agents/skills/<each factory skill>`) and hand-added hook entries naming `skills/safe-factory/`, the `pre-push` copies, `~/.codex/rules/factory.rules`, any watchdog task (`schtasks /delete /tn factory-watchdog` or its cron line) and `~/.cache/ai-software-factory`.

## Overnight runs

Optional. All below is per project and stays on your machine. `<clone>` = factory checkout (Claude Code: plugin folder, `~/.claude/plugins/marketplaces/ai-software-factory`).

1. **Push guard** (both hosts), from the project:

   ```text
   cp <clone>/.agents/hooks/pre-push "$(git rev-parse --git-path hooks/pre-push)"
   chmod +x "$(git rev-parse --git-path hooks/pre-push)"
   ```

   Blocks pushes to default branch, force pushes, branch deletes, added token shapes. Pair with host's server-side rules (GitHub: ruleset on default branch that blocks force pushes and requires a pull request) and secret push protection: only those hold against a shell that skips local hooks.
2. **Deny rules.** Claude Code: nothing to copy; `night.sh` passes `<clone>/.agents/hooks/claude-settings.json` with `--settings`. Same deny list by day: merge its `deny` array into `~/.claude/settings.json`. Add project's test and build commands to project's own `.claude/settings.json` `allow` list (plugin updates replace the template). Codex: `cp <clone>/.agents/hooks/codex.rules ~/.codex/rules/factory.rules`.
3. **Start a night run** from the project, once run is open and past any owner question:

   ```text
   sh <clone>/.agents/hooks/night.sh claude 8 --check   # preflight only
   sh <clone>/.agents/hooks/night.sh claude 8           # preflight, then start
   ```

   CLI installed off PATH (desktop apps): set `FACTORY_CLAUDE` or `FACTORY_CODEX` to its path. Codex preflight also runs one sandboxed command (up to `FACTORY_PROBE_S`, 180 s), refuses when it does not run.

4. **Watchdog** every 30 minutes, outside the session:

   ```text
   cron:    */30 * * * * sh <clone>/.agents/hooks/watchdog.sh claude <project>
   Windows: schtasks /create /tn factory-watchdog /sc minute /mo 30 /tr "\"C:\Program Files\Git\bin\sh.exe\" <clone>/.agents/hooks/watchdog.sh claude <project>"
   ```

   Set `FACTORY_NOTIFY` to a command that reaches you (gets `$MSG`), for example `curl -d "$MSG" ntfy.sh/<your-topic>`; without it notices go to `.factory/guard/notices`. Sleeping machine runs nothing: keep it awake overnight.

## Other agents

Copy `.agents/skills/*` into the folder your agent reads skills from (many read `~/.agents/skills` or `.agents/skills`), or point it at `.agents/skills/safe-factory/SKILL.md`. Without hooks agent applies run-file rules itself. Per-host notes: [hosts](hosts.md).

## Use

```text
safe-factory Build [app or feature] in [absolute project directory]. Success means [observable outcome].
safe-factory Resume [absolute project directory].
improve-factory The factory did [observed]; expected [result].
```

Skills appear next turn or in a new session. If not, ask agent to read installed `SKILL.md` by path.
