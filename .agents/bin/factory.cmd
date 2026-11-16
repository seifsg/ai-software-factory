:; # factory launcher, one LF file read by sh (macOS, Linux, Git Bash) and by cmd.exe (Windows). It runs the
:; # bundled binary for this machine; with none bundled (a development checkout) the sh guard scripts, else it says so.
:; u=$(uname -sm 2>/dev/null); case ${u#* } in arm64|aarch64) a=aarch64 ;; *) a=x86_64 ;; esac
:; case ${u%% *} in Darwin) t=$a-apple-darwin ;; Linux) t=$a-unknown-linux-musl ;; *) t=$a-pc-windows-msvc.exe ;; esac
:; d=${0%/*}; [ "$d" = "$0" ] && d=.; [ -f "$d/factory-$t" ] && exec "$d/factory-$t" "$@"
:; s=$d/../skills/safe-factory/scripts; case $1 in guard) [ "$2" = step ] || { shift; exec sh "$s/run-guard.sh" "$@"; } ;; update-check|doctor) c=$1; shift; exec sh "$s/$c.sh" "$@" ;; esac
:; echo "factory: no binary factory-$t in $d (a development checkout: cargo build --release --manifest-path factory/Cargo.toml)" >&2; exit 1
@echo off
setlocal
set "a=x86_64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "a=aarch64"
if /i "%PROCESSOR_ARCHITEW6432%"=="ARM64" set "a=aarch64"
set "b=%~dp0factory-%a%-pc-windows-msvc.exe"
if not exist "%b%" set "b=%~dp0factory-x86_64-pc-windows-msvc.exe"
if not exist "%b%" (
  >&2 echo factory: no Windows binary in %~dp0 ^(a development checkout: cargo build --release --manifest-path factory/Cargo.toml^)
  exit /b 1
)
"%b%" %*
exit /b %errorlevel%
