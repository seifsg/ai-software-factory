# Install

Needs Git, read access to the repository (`gh auth login` lets Git use your GitHub credentials over HTTPS) and, on Windows, Git Bash for the hooks.

## Claude Code

```text
claude plugin marketplace add https://github.com/seifsg/ai-software-factory.git
claude plugin install safe-engine@ai-software-factory
```

Use the HTTPS URL; `owner/repo` shorthand tries SSH first. Auto mode: new projects need `gh repo create` and `git push` allowed. Add `Bash(gh repo create:*)` and `Bash(git push:*)` to your permission allow rules, or approve once when step 0 asks. Plugin brings every skill, delegate roles, the run hooks and the update check; follows release tags. Start a new session.

Desktop app without terminal: add to `~/.claude/settings.json`, start a new session, then install from `/plugin` if missing:

```json
"extraKnownMarketplaces": {"ai-software-factory": {"source": {"source": "git", "url": "https://github.com/seifsg/ai-software-factory.git"}, "autoUpdate": true}},
"enabledPlugins": {"safe-engine@ai-software-factory": true}
```

Try unreleased checkout: `claude --plugin-dir <clone>/.agents`.

## Codex

Plugin (not yet run live):

```text
codex plugin marketplace add seifsg/ai-software-factory
```

Then `/plugins`, install `safe-engine`, start a new session, trust its hooks once in `/hooks`. Update: `codex plugin marketplace upgrade ai-software-factory`. Codex reads the repo's `.claude-plugin/marketplace.json`; the plugin root is `.agents/` (`.codex-plugin/plugin.json`, `skills/`, `hooks/hooks.json`). Plugin hooks run only for manual installs.

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
         "command": "sh \"<home>/.agents/skills/safe-engine/scripts/run-guard.sh\" stop",
         "commandWindows": "sh \"<home>/.agents/skills/safe-engine/scripts/run-guard.sh\" stop"}]}],
       "SessionStart": [{"matcher": "compact|resume", "hooks": [{"type": "command", "timeout": 10,
         "command": "sh \"<home>/.agents/skills/safe-engine/scripts/run-guard.sh\" compact",
         "commandWindows": "sh \"<home>/.agents/skills/safe-engine/scripts/run-guard.sh\" compact"}]}]
     }
   }
   ```

4. Start Codex, trust both hooks once in `/hooks`.

## Cursor

Plugin (not yet run live): Customize, Plugins, add marketplace `https://github.com/seifsg/ai-software-factory` (reads `.cursor-plugin/marketplace.json`), install `safe-engine`. Brings skills and delegate roles; no hooks yet, so Fast chains steps in one turn (Safe: `Say go for step <n>`). For the Stop guard, Cursor runs Claude Code hooks from a project's `.claude/settings.json`: copy the `Stop` entry from `.agents/hooks/hooks.json` there with `r=` set to the absolute path of the plugin's `.agents/` folder. Update: Cursor refreshes the marketplace; reinstall `safe-engine` when a new version shows.

## Update check

At session start the plugin hook reads a cached latest release (no network, about 0.1 s on Windows) and refreshes that cache in the background once a day with `gh api`, or `curl` when `gh` is missing or signed out. Check by hand: `cat ~/.cache/ai-software-factory/latest` against the `version` in your installed `plugin.json`. A newer release: the agent tells you before any run and links what's new. Off: `FACTORY_NO_UPDATE_CHECK=1`.

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

Copy `.agents/skills/*` into the folder your agent reads skills from (many read `~/.agents/skills` or `.agents/skills`), or point it at `.agents/skills/safe-engine/SKILL.md`. Without hooks agent applies run-file rules itself. Per-host notes: [hosts](hosts.md).

## Use

```text
safe-engine Build [app or feature] in [absolute project directory]. Success means [observable outcome].
safe-engine Resume [absolute project directory].
improve-factory The factory did [observed]; expected [result].
```

Skills appear next turn or in a new session. If not, ask agent to read installed `SKILL.md` by path.
