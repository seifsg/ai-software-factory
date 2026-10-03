# Install the Safe Engine factory

## Small direct changes

Seif selected [small-change](../.agents/skills/small-change/SKILL.md) on 3 October: six lightweight routines, careful implementation, focused checks and one narrow independent assessment. This route precedes the full version workflow described below. No automatic broad regression, full-suite reruns or five-artifact planning for a small fix. Accumulated changes may prompt an offer of affected-area validation; execution waits for the user. It is an agent-operated scoped handoff, not a new controller command or whole-version acceptance. Existing pinned runs retain their bundle/state; see the method for explicit local trials and evidence limits.

**Install `safe-engine` to build apps.** `improve-factory` repairs the factory and is not required as a separate installation. Both load the same complete factory; Seif's original methods remain canonical.

## Codex: install once, use in any local project

Paste into a Codex session with your authorized GitHub access:

```text
Use skill-installer to install safe-engine from
seifsg/ai-software-factory, ref main, path skills/safe-engine.
Use my existing authorized GitHub login. Install the entire portable folder,
including scripts. Preserve any existing installation before replacing it.
```

Then, in the app's chat:

```text
$safe-engine Build [describe my app or feature] in [absolute project directory].
Success means [observable outcomes]. Work autonomously within these requirements,
preserve my existing decisions, and show meaningful progress and actual QA.
```

To continue later:

```text
$safe-engine Resume the existing run in [absolute project directory].
Preserve the chosen factory bundle, task, decisions and evidence.
```

The installed skill should be discovered on the next turn. If it does not appear, refresh/start a new session or read its installed `SKILL.md` explicitly. It is a chat invocation, not a shell command. Repository and personal skills can share a name: verify which path is selected when working in the factory repository itself.

The bundled installer equivalent is:

```text
python <skill-installer>/scripts/install-skill-from-github.py --repo seifsg/ai-software-factory --ref main --path skills/safe-engine --method git
```

Use `py -3` on Windows if needed. The bundled installer uses `$CODEX_HOME/skills`; current Codex documentation also supports the personal `$HOME/.agents/skills` location. Use the host's installer/discovery paths rather than changing global settings. A reproducible install can use a full commit SHA instead of `main`; **also supply that SHA with the entry helper's `--ref` for a new app**. The installed adapter and fetched bundle have separate identities.

## Claude Code

Paste into an authenticated session:

```text
Install folder skills/safe-engine from seifsg/ai-software-factory, ref main,
into my personal ~/.claude/skills/safe-engine directory.
Include SKILL.md and scripts. Preserve any existing installation and report
its identity before replacing it. Use my existing authorized GitHub credentials.
```

Then invoke `/safe-engine` with the same app request and target path. A project installation can use `.claude/skills/safe-engine`; writing it into a project requires that project's authority. The current factory's independent controller review still requires an authenticated Codex CLI. Native Claude-builder execution has not been demonstrated; a Claude-only review adapter is absent.

## What happens on first use

```text
$safe-engine + your app request
  -> resolve complete private main bundle to one commit
  -> save the app's selected bundle path/revision
  -> read full canonical factory and all methods as each phase requires
  -> analyze charts -> plan -> new-app research -> revised plan
  -> build coherent batches -> feature feedback -> full QA
  -> worthwhile improvements -> final QA -> fresh review -> handoff
  -> both complete PR procedures when PR delivery is authorized
```

The agent creates a missing target directory within the agreed scope, preserves existing work, discovers real project settings, establishes the session contract and clean Git baseline, then initializes once. Your chosen task and product decisions remain yours. Meaningful authorized work continues without artificial correction credits; real permissions, required gates and owner stops remain effective. QA is batched after substantial work. Browser QA needs an actual runnable app/browser driver and observable outcomes.

Git, private GitHub access, Python 3.11+, authenticated Codex CLI and the project's check tools are prerequisites. Skills do not grant credentials or install every project dependency. This is an agent-operated workflow; it does not start a background service or install universal hooks.

## Version-safe resume

The portable helper uses `.factory/entry-bundle.json` to select a complete checkout under `~/.safe-engine/bundles/<commit>`. Keep `.factory/` excluded from Git. Resume inspects the recorded path/revision offline; it never pulls, resets, deletes or silently selects a newer factory. A missing checkout, changed revision or invalid selection record blocks dependent work with a precise error. Preserve the record for diagnosis. An authorized factory adoption preserves the old receipt and updates its selection only through the canonical [compatibility handoff](../.agents/skills/improve-factory/references/live-session.md#review-adoption-and-resume), followed by actual controller resume/repair and fresh evidence as required.

An older run without the record needs its original bundle established from the existing session/checkpoint artifacts. Use `--bundle <absolute-original-factory-root>` with `--project` only after establishing that identity; a commit/version alone cannot identify dirty inputs. The resolver reports dirty state; the canonical checkpoint/evidence rules record actual hashes. The receipt is selection metadata, never a passing QA certificate or an authority to edit acceptance. Factory upgrades go through `improve-factory` and its compatibility review, not deletion of the receipt.

## Another machine or cloud session

Install inside that environment, using its own authorized GitHub login and tools. This computer's personal skill installation does not propagate to other hosts. Claude cloud sessions can load project skills committed to their cloned repository; personal `~/.claude/skills` folders are local. Read the installed entry explicitly if discovery is unavailable. If the environment cannot run required checks or independent review, report the actual blocked step; do not label delivery verified.

## Packaging and verification

`skills/safe-engine` is standalone for installation, while the resolved bundle owns all ten canonical entrypoints. Both installed skill helpers are generated from `safe_engine/distribution.py`; after editing that owner run `python scripts/package_skill_entries.py`, then `--check` at the pre-push gate. No second independently maintained resolver or duplicated method library exists.

The existing [pilot record](pilot-verification.md) documents the actual local build and repair. Distribution tests exercise real Git checkout/cache/selection boundaries; a successful install or file-loading smoke test is not proof of a new complete app build or every host's compatibility.

References checked 3 October 2026: [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Claude Code skills](https://code.claude.com/docs/en/skills). See [fresh-session setup](start-another-session.md) for manual bundle use, [pilot usage](pilot-usage.md) for controller commands, and [maintenance installation](install-improve-factory.md) when you want to change the factory.
