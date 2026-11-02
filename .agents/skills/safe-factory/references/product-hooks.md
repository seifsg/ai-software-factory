# Product hooks (step 0)

When the factory creates or enters a product folder, wire the Stop guard into that checkout so the loop can advance after each turn.

## Command

```text
sh <plugin-root>/skills/safe-factory/scripts/wire-product-hooks.sh <product-root>
```

`<plugin-root>` is the factory `.agents` directory (plugin root). Script defaults it from its own path.

## What it writes

| Path | Role |
|---|---|
| `.agents/skills/safe-factory/scripts/run-guard.sh` | Local copy of the Stop/compact script |
| `.claude/settings.json` | Claude Code and Cursor project Stop + compact hooks |
| `.agents/hooks/hooks.json` | Same commands under `.agents/hooks` |
| `.cursor/hooks.json` | Codex-style / some Cursor project hooks |

Commands use the project-relative guard path so clones work without a machine-local plugin path.

## Liveness

- Hooks added mid-session do not load until a new session (Claude Code reads settings at start).
- Until the guard is live, Fast self-resumes in the same turn (`safe-factory` Steps). Safe still ends each step with `Say go for step <n>`.
- After a new session in the product root, Stop should create `.factory/guard/state` once a run is open.

## Do not

- Skip the wire on a bare product create.
- Point product hooks at a different machine's absolute plugin path in committed files.
- Treat a product-local `run-guard.sh` as a leftover to delete; refresh it by re-running the wire script.
