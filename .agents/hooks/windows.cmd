@echo off
setlocal
set "factory_sh="
rem Launch the shared hooks in Git Bash without changing their JSON streams.
if not "%~1"=="stop" if not "%~1"=="compact" if not "%~1"=="startup" (
  >&2 echo Safe Factory: expected stop, compact or startup.
  exit /b 1
)
for %%G in (git.exe) do set "factory_git=%%~$PATH:G"
if defined factory_git for %%G in ("%factory_git%") do for %%S in ("%%~dpG..\bin\sh.exe" "%%~dpG..\..\bin\sh.exe") do if not defined factory_sh if exist "%%~fS" set "factory_sh=%%~fS"
if not defined factory_sh (
  echo {"systemMessage":"Safe Factory could not run: Git Bash was not found beside git.exe on PATH. Install Git for Windows, restart Codex, then resume the factory run."}
  exit /b 0
)
if "%~1"=="startup" (
  "%factory_sh%" "%~dp0..\skills\safe-factory\scripts\update-check.sh" "%~dp0.."
) else (
  "%factory_sh%" "%~dp0..\skills\safe-factory\scripts\run-guard.sh" "%~1"
)
exit /b %errorlevel%
