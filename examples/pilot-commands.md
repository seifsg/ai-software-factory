# Complete commands for the task-notes fixture

This reproduces the existing example if you choose to run it again. It does not select Seif's next example. The [walkthrough](pilot-walkthrough.md) records what actually happened on 1 October; commands below are a repeatable procedure, not fabricated new execution evidence.

## Prepare a fresh copy on this Windows computer

Run from PowerShell. Python via `py -3`, Git and Node must be available. The destination is deliberately different from the preserved first run. Stop if it exists; never delete an earlier run to make these commands succeed.

```powershell
$ErrorActionPreference = 'Stop'
$bundle = 'C:\work\ai-software-factory'
$demo = 'C:\work\safe-engine-demo-next'
$baseline = Join-Path $demo 'baseline'
$target = Join-Path $demo 'app'
if (Test-Path -LiteralPath $demo) { throw 'Destination exists. Choose a new demo path.' }
New-Item -ItemType Directory -Path $demo | Out-Null
Copy-Item -LiteralPath "$bundle\examples\pilot-app" -Destination $baseline -Recurse
git -C $baseline init
if ($LASTEXITCODE) { throw 'Git initialization failed' }
git -C $baseline add -- .gitignore index.html style.css app.js model.mjs tests
if ($LASTEXITCODE) { throw 'Could not stage the baseline' }
git -C $baseline commit -m 'Record task-notes example baseline'
if ($LASTEXITCODE) { throw 'Baseline commit failed; check your Git author configuration' }
git -C $baseline worktree add -b pilot-fix $target
if ($LASTEXITCODE) { throw 'Could not create the demo worktree' }
New-Item -ItemType Directory -Path "$target\.factory" | Out-Null
Copy-Item -LiteralPath "$bundle\examples\pilot-task.json" -Destination "$target\.factory\task.json"
Copy-Item -LiteralPath "$bundle\examples\pilot-profile.json" -Destination "$target\.factory\profile.json"
Set-Location $bundle
```

The browser dependency paths below were present during the first demonstration. Validate them in the current environment; on another computer, use the installed module and browser paths. This step does not install dependencies or change global settings.

```powershell
$runtime = 'C:\Users\seifs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
$env:SAFE_PLAYWRIGHT_MODULE = Join-Path $runtime 'playwright'
$env:SAFE_BROWSER_EXECUTABLE = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$declaredInputs = @(
    (Join-Path $runtime 'playwright\package.json'),
    (Join-Path $runtime 'playwright-core\package.json'),
    $env:SAFE_BROWSER_EXECUTABLE
)
foreach ($inputPath in $declaredInputs) {
    if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) { throw "Missing dependency: $inputPath" }
}
$profile = Get-Content -LiteralPath "$target\.factory\profile.json" -Raw | ConvertFrom-Json
$profile.input_files = $declaredInputs
$profile | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$target\.factory\profile.json" -Encoding utf8
```

Keep these environment variables consistent in later sessions. The profile binds their values and the declared files to the evidence. The empty `input_files` array in the portable JSON is filled above before initialization.

## Observe the baseline, then start the controller

```powershell
Set-Location $target
node tests/unit.mjs
# Expected exit 1: whitespace-only titles are accepted.
node tests/browser.cjs
# Expected exit 1: the 320px page overflows. Inspect .factory/outputs/browser/mobile.png.
Set-Location $bundle
py -3 -m safe_engine --project $target discover
py -3 -m safe_engine --project $target init --task "$target\.factory\task.json" --profile "$target\.factory\profile.json"
```

Review the supplied task and profile first. Current initialization has no repair allowance. The historical first run's allowance remains recorded; 60/120-second command watchdogs describe this fixture and fail stuck operations for diagnosis. Missing dependencies are setup failures, not the intended baseline defect. A new target must remain clean and committed; diagnostic output stays inside ignored `.factory/`.

## The agent does the work between these commands

Honor Get Ready to Code's file-summary stop unless the user already authorized continuing through it. Run each command only after its preceding work is done. Do not paste all stages as a blind script. The artifacts are outputs of real analysis and implementation, not files to fill with passing claims.

| Work the agent performs | Artifact it writes |
|---|---|
| Read the actual code; explain why; map callers; draw the ASCII chart | `.factory/analysis.md` |
| File list, critique, phases, todos, complete plan; no code edits | `.factory/plan.md` |
| Implement the selected batch with per-todo pre/change/post inspection | `.factory/batch.md` |
| Inspect/apply worthwhile improvements; explain a justified no-change result | `.factory/improvement.md` |

```powershell
py -3 -m safe_engine --project $target record analysis --file "$target\.factory\analysis.md"
py -3 -m safe_engine --project $target record plan --file "$target\.factory\plan.md"
# The agent now implements the complete batch, then writes its actual observations.
py -3 -m safe_engine --project $target record batch --file "$target\.factory\batch.md"
py -3 -m safe_engine --project $target check
# Inspect screenshots, outcomes and worthwhile improvements before proceeding.
py -3 -m safe_engine --project $target record improvement --file "$target\.factory\improvement.md"
py -3 -m safe_engine --project $target check
py -3 -m safe_engine --project $target review --timeout 600
py -3 -m safe_engine --project $target handoff
```

A failed command blocks progression. Use `repair --reason 'Describe the actual failure'` before correcting a recorded candidate, then produce a new batch and repeat the required stages. Review needs one authenticated reviewer agent CLI (the recorded run used Codex) or the review packet. The result is `.factory/handoff.md`; this procedure does not push or deploy the example.

## Inspect or resume

```powershell
py -3 -m safe_engine --project $target status
Get-Content -LiteralPath "$target\.factory\handoff.md"
```

If the handoff does not yet exist, finish the pending stage. In a new terminal, restore `$bundle`, `$target` and the declared environment before status or execution. For a new chat, use the [resume prompt](../docs/start-another-session.md). Keep the completed worktree and original evidence available for inspection.
