# Install Improve Factory from GitHub

Install **`skills/improve-factory`**, the portable launcher. The canonical procedure in `.agents/skills/improve-factory` depends on the complete factory, so copying that folder alone is insufficient.

The repository is private. Use an agent environment with your authorized GitHub access, Git and Python 3.11 or newer (the resolver alone supports 3.10). This branch is available for testing while [PR #1](https://github.com/seifsg/ai-software-factory/pull/1) remains draft; it is not a merge or production-release claim.

## Codex — paste into another session

```text
Use skill-installer to install improve-factory from repository
seifsg/ai-software-factory, ref docs/skill-lifecycle-map,
path skills/improve-factory.
Use my existing authorized GitHub login. Do not install the canonical
.agents/skills/improve-factory folder alone, because it has bundle dependencies.
```

Then invoke `$improve-factory` and describe what happened and what should happen. The skill should be available on the next turn; if the host has not refreshed discovery, start a new session or read the installed file explicitly. To reproduce a tested version, replace the install ref with the full commit SHA supplied in the completion message **and tell the skill to use that same SHA with `--ref` for a new maintenance case**. Pinning the installer alone pins the launcher, not the bundle it fetches. Active app runs always retain their recorded bundle instead.

With the bundled Skill Installer script, the equivalent arguments are:

```text
python <skill-installer>/scripts/install-skill-from-github.py --repo seifsg/ai-software-factory --ref docs/skill-lifecycle-map --path skills/improve-factory
```

## Claude Code — paste into another session

```text
Install the reusable skill from seifsg/ai-software-factory,
ref docs/skill-lifecycle-map, folder skills/improve-factory,
into my personal ~/.claude/skills/improve-factory directory.
Use my existing GitHub credentials; include SKILL.md and scripts/.
Preserve any existing installation and report its identity before replacing it.
Do not copy only the canonical .agents/skills folder.
```

Then invoke `/improve-factory`. An agent can use an authenticated checkout and copy that one portable folder to the personal skill directory. A project installation can instead use `.claude/skills/improve-factory`; commit it only when authorized for that project. Local personal installation does not install into Claude cloud/Cowork or other machines. Native Claude execution has not been verified here.

## What first use does

```text
Installed portable skill
  -> existing app run? use its recorded bundle; do not upgrade
  -> otherwise resolve GitHub ref to a commit
  -> obtain complete detached checkout in ~/.safe-engine/bundles/<commit>
  -> read full canonical improve-factory + applicable routines
  -> checkpoint, isolate repair, verify and independently review
```

The resolver prints the full path, commit and dirty status. It rejects wrong repositories, incomplete bundles and modified cached checkouts. It can inspect an explicitly supplied dirty app bundle without altering it; the main procedure then records the actual dirty inputs. Keep a run's selected bundle unchanged and perform factory edits in another worktree. This is a local procedure, not an automatic hook or background service.

To inspect an existing bundle without downloading/updating it:

```text
python <installed-skill>/scripts/resolve_bundle.py --bundle <absolute-factory-checkout>
```

Use `py -3` on Windows or another available Python 3 interpreter where needed. Paths with spaces require quoting. Private clone failures need the environment's normal credential setup; never paste tokens into prompts or URLs. Existing cached checkouts are never pulled, reset or deleted. Failed download directories are retained with their path for diagnosis.

Distribution choices: a small launcher (selected under this request) preserves one canonical method; embedding a complete copy duplicates the factory; a plugin marketplace adds host-specific packaging. The launcher is intended for initial reuse/testing through ordinary skill installers.

References checked 2 October 2026: [Codex skills and installer](https://learn.chatgpt.com/docs/build-skills), [Claude Code skill locations](https://code.claude.com/docs/en/skills). Host discovery, authentication and independent-review tooling remain prerequisites. A portable file layout does not demonstrate a complete factory run on every host.
