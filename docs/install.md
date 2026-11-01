# Install

Needs Git, read access to the repository (`gh auth login` lets Git use your GitHub credentials over HTTPS) and, on Windows, Git Bash for the hooks.

## Claude Code

```text
claude plugin marketplace add https://github.com/seifsg/ai-software-factory.git
claude plugin install safe-engine@ai-software-factory
```

Use the HTTPS URL; the `owner/repo` shorthand tries SSH first. In auto mode, new projects need `gh repo create` and `git push` allowed: add `Bash(gh repo create:*)` and `Bash(git push:*)` to your permission allow rules, or approve them once when step 0 asks. The plugin brings every skill, the delegate roles and both hooks, and follows release tags. Start a new session.

Desktop app without a terminal: add to `~/.claude/settings.json`, start a new session, then install from `/plugin` if it is missing:

```json
"extraKnownMarketplaces": {"ai-software-factory": {"source": {"source": "git", "url": "https://github.com/seifsg/ai-software-factory.git"}, "autoUpdate": true}},
"enabledPlugins": {"safe-engine@ai-software-factory": true}
```

Try an unreleased checkout: `claude --plugin-dir <clone>/.agents`.

## Codex

1. Clone the factory: `git clone https://github.com/seifsg/ai-software-factory.git <clone>`.
2. Copy the skills where Codex finds them (all users of this machine: `~/.agents/skills`; one project: `<project>/.agents/skills`):

   ```text
   mkdir -p ~/.agents/skills
   cp -r <clone>/.agents/skills/* ~/.agents/skills/
   ```

3. Add the hooks to `~/.codex/hooks.json` (merge with entries you already have), with absolute paths. On Windows, `commandWindows` needs Git's `sh` on `PATH` (add `C:\Program Files\Git\bin`); not yet tried in a live Windows Codex session:

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

4. Start Codex and trust both hooks once in `/hooks`.

## Overnight runs

Optional. Everything below is per project and stays on your machine. `<clone>` is the factory checkout (Claude Code: the plugin folder, `~/.claude/plugins/marketplaces/ai-software-factory`).

1. **Push guard** (both hosts), from the project:

   ```text
   cp <clone>/.agents/hooks/pre-push "$(git rev-parse --git-common-dir)/hooks/pre-push"
   chmod +x "$(git rev-parse --git-common-dir)/hooks/pre-push"
   ```

   It blocks pushes to the default branch, force pushes, branch deletes and added token shapes. Pair it with your host's server-side rules (GitHub: a ruleset on the default branch that blocks force pushes and requires a pull request) and secret push protection: only those hold against a shell that skips local hooks.
2. **Deny rules.** Claude Code: nothing to copy; `night.sh` passes `<clone>/.agents/hooks/claude-settings.json` with `--settings`. To use the same deny list by day, merge its `deny` array into `~/.claude/settings.json`. Add your project's test and build commands to its `allow` list. Codex: `cp <clone>/.agents/hooks/codex.rules ~/.codex/rules/factory.rules`.
3. **Start a night run** from the project, once the run is open and past any owner question:

   ```text
   sh <clone>/.agents/hooks/night.sh claude 8 --check   # preflight only
   sh <clone>/.agents/hooks/night.sh claude 8           # preflight, then start
   ```

4. **Watchdog** every 30 minutes, outside the session:

   ```text
   cron:    */30 * * * * sh <clone>/.agents/hooks/watchdog.sh claude <project>
   Windows: schtasks /create /tn factory-watchdog /sc minute /mo 30 /tr "\"C:\Program Files\Git\bin\sh.exe\" <clone>/.agents/hooks/watchdog.sh claude <project>"
   ```

   Set `FACTORY_NOTIFY` to a command that reaches you (it gets `$MSG`), for example `curl -d "$MSG" ntfy.sh/<your-topic>`; without it, notices go to `.factory/guard/notices`. A sleeping machine runs nothing: keep it awake for the night.

## Other agents

Copy `.agents/skills/*` into the folder your agent reads skills from (many read `~/.agents/skills` or `.agents/skills`), or point it at `.agents/skills/safe-engine/SKILL.md`. Without hooks the agent applies the run-file rules itself. Per-host notes: [hosts](hosts.md).

## Use

```text
safe-engine Build [app or feature] in [absolute project directory]. Success means [observable outcome].
safe-engine Resume [absolute project directory].
improve-factory The factory did [observed]; expected [result].
```

Skills appear on the next turn or in a new session. If not, ask the agent to read the installed `SKILL.md` by path.
