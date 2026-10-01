# Disposable browser demonstration

`pilot-app/` is a deliberately broken fixture, not a finished starter application. `pilot-task.json` describes its three observable acceptance criteria. The baseline unit and browser commands are expected to fail.

1. Copy the entire `pilot-app/` directory, including `.gitignore`, into a new disposable location outside this factory repository. Initialize Git and commit that baseline. Create a linked worktree for the repair with `git worktree add -b pilot-fix <new-worktree-path>`.
2. Follow [pilot usage](../docs/pilot-usage.md) from the factory bundle's root. Discover the worktree; review its profile. Use `pilot-task.json` as the original request.
3. Configure checks as `node tests/unit.mjs` and `node tests/browser.cjs`, with timeouts appropriate to the demonstration. Protect both test files. Declare the three browser artifacts shown in the usage profile. The example run used a 3-repair budget and a 600-second review limit; those are fixture settings, not universal defaults.
4. Supply Playwright and Chrome/Chromium. The browser script normally resolves `playwright`; alternatively set `SAFE_PLAYWRIGHT_MODULE` to an installed module path. `SAFE_BROWSER_EXECUTABLE` optionally selects an installed browser. Declare these environment inputs and meaningful external dependency/browser files in the profile. The check owns an ephemeral loopback server; no separate server command is needed.
5. Run baseline diagnostics, then initialize the controller. Ask Codex to follow `$safe-engine` on the accepted task. Preserve the tests and complete analysis and planning before modifying the app. Record the substantial batch, execute checks, inspect screenshots, record worthwhile improvement, verify, obtain fresh review and generate the handoff.

The intended repair belongs in the existing normalization boundary and responsive form layout. Do not copy a passing receipt or weaken acceptance to make the fixture succeed. Review the original source, observe the failures, and derive the change through the methods.

The checked run is documented in [pilot verification](../docs/pilot-verification.md). Runtime output belongs in the disposable worktree's ignored `.factory/`; keep it out of this reusable factory bundle.
