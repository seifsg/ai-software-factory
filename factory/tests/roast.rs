//! `factory roast` against fake agent CLIs: pick order, SKIP lines, the time cap, INCOMPLETE and a parsed verdict.

mod common;

use common::scratch;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Duration, Instant};

/// What a fake CLI does when run as the roast agent.
#[derive(Clone, Copy)]
enum Mode {
    /// A valid report with two findings.
    Report,
    /// Output with no VERDICT line.
    Garbage,
    /// Hangs past the cap, with a grandchild that would write `FAKE_LATE` after about 5 s if it survived.
    Hang,
    /// Writes nothing and fails.
    Silent,
}

/// Writes a fake agent CLI named `name` into `bin`. `logged_in` sets its login check's exit code.
/// Codex fakes write `agent.md` in their working folder (the report folder); Claude fakes print the JSON result.
fn fake(bin: &Path, name: &str, logged_in: bool, mode: Mode) -> PathBuf {
    let report = "VERDICT: SHIP WITH FIXES\n### F1 [MAJOR] Breaks double submit\n### F2 [POLISH] Copy";
    let login = if logged_in { 0 } else { 1 };
    let claude = name == "claude";
    let body = match (mode, claude) {
        (Mode::Report, false) => out_file(report),
        (Mode::Report, true) => out_json(report),
        (Mode::Garbage, false) => out_file("looks fine"),
        (Mode::Garbage, true) => out_json("looks fine"),
        (Mode::Hang, _) => hang(),
        (Mode::Silent, _) => fail(),
    };
    script(bin, name, &format!("{}{}{body}", status_line(login), record()))
}

#[cfg(windows)]
fn script(bin: &Path, name: &str, body: &str) -> PathBuf {
    let p = bin.join(format!("{name}.cmd"));
    std::fs::write(&p, format!("@echo off\r\n{}\r\nexit /b 0\r\n", body.replace('\n', "\r\n"))).unwrap();
    p
}

#[cfg(windows)]
fn status_line(code: i32) -> String {
    format!("if \"%1\"==\"login\" exit /b {code}\nif \"%1\"==\"auth\" exit /b {code}\n")
}

#[cfg(windows)]
fn out_file(text: &str) -> String {
    text.lines().map(|l| format!("echo {l}>> agent.md\n")).collect()
}

#[cfg(windows)]
fn out_json(text: &str) -> String {
    format!("echo {{\"is_error\":false,\"result\":\"{}\"}}\n", text.replace('\n', "\\n"))
}

#[cfg(windows)]
fn hang() -> String {
    "start \"\" /b cmd /c \"ping -n 6 127.0.0.1 >nul & echo late> \"%FAKE_LATE%\"\"\nping -n 60 127.0.0.1 >nul\n".into()
}

#[cfg(windows)]
fn fail() -> String {
    "exit /b 3\n".into()
}

/// The fake records its working folder, arguments and environment for the tests to read.
#[cfg(windows)]
fn record() -> String {
    "cd > cwd.txt\necho %* > args.txt\nset > env.txt\n".into()
}

#[cfg(unix)]
fn script(bin: &Path, name: &str, body: &str) -> PathBuf {
    use std::os::unix::fs::PermissionsExt;
    let p = bin.join(name);
    std::fs::write(&p, format!("#!/bin/sh\n{body}\nexit 0\n")).unwrap();
    std::fs::set_permissions(&p, std::fs::Permissions::from_mode(0o755)).unwrap();
    p
}

#[cfg(unix)]
fn status_line(code: i32) -> String {
    format!("case \"$1\" in login|auth) exit {code};; esac\n")
}

#[cfg(unix)]
fn out_file(text: &str) -> String {
    format!("printf '%s\\n' '{}' > agent.md\n", text.replace('\n', "' '"))
}

#[cfg(unix)]
fn out_json(text: &str) -> String {
    format!("printf '%s' '{{\"is_error\":false,\"result\":\"{}\"}}'\n", text.replace('\n', "\\n"))
}

#[cfg(unix)]
fn hang() -> String {
    "(sleep 5; echo late > \"$FAKE_LATE\") &\nsleep 60\n".into()
}

#[cfg(unix)]
fn fail() -> String {
    "exit 3\n".into()
}

/// The fake records its working folder, arguments and environment for the tests to read.
#[cfg(unix)]
fn record() -> String {
    "pwd > cwd.txt\nprintf '%s\\n' \"$@\" > args.txt\nenv > env.txt\n".into()
}

/// Runs `factory roast` with only the fakes in `bin` ahead of PATH and a clean host env; returns exit, stdout, seconds.
fn roast(bin: &Path, env: &[(&str, &str)], args: &[&str]) -> (i32, String, u64) {
    let path = std::env::join_paths(std::iter::once(bin.to_path_buf()).chain(std::env::split_paths(&std::env::var_os("PATH").unwrap()))).unwrap();
    let mut c = Command::new(env!("CARGO_BIN_EXE_factory"));
    c.arg("roast").args(args).env("PATH", path);
    for k in ["CLAUDECODE", "CODEX_THREAD_ID", "CODEX_SESSION_ID", "FACTORY_ROAST", "FACTORY_ROAST_SECS", "FACTORY_ROAST_ANY_HOST", "FACTORY_CODEX", "FACTORY_CLAUDE"] {
        c.env_remove(k);
    }
    c.envs(env.iter().copied());
    let t = Instant::now();
    let o = c.output().unwrap();
    (o.status.code().unwrap_or(-1), String::from_utf8_lossy(&o.stdout).trim().to_string(), t.elapsed().as_secs())
}

/// A scratch bin folder holding a fake `npx` (never run: the fake agents ignore their browser config).
fn bin(name: &str) -> (PathBuf, String) {
    let d = scratch(name);
    let bin = d.join("bin");
    std::fs::create_dir_all(&bin).unwrap();
    script(&bin, "npx", "");
    (bin, d.join("out").to_string_lossy().into_owned())
}

const URL: &str = "http://127.0.0.1:47811/";

#[test]
fn claude_host_roasts_with_codex_and_parses_the_verdict() {
    let (bin, out) = bin("roast-pick");
    fake(&bin, "codex", true, Mode::Report);
    fake(&bin, "claude", true, Mode::Garbage);
    let (code, line, _) = roast(&bin, &[("CLAUDECODE", "1")], &[URL, &out]);
    assert_eq!(code, 0, "{line}");
    assert!(line.starts_with("roast codex SHIP-WITH-FIXES 2 findings "), "{line}");
    assert!(line.ends_with("/roast.md"), "{line}");
    let report = std::fs::read_to_string(Path::new(&out).join("roast.md")).unwrap();
    assert!(report.starts_with("VERDICT: SHIP WITH FIXES"), "{report}");
    // The agent ran in a temp folder outside the project, and its files were moved into the report folder.
    let read = |f: &str| std::fs::read_to_string(Path::new(&out).join(f)).unwrap();
    let cwd = read("cwd.txt");
    assert!(cwd.contains("factory-roast-") && !cwd.contains("roast-pick"), "agent cwd: {cwd}");
    // Read-only, no shell, no code-running browser tool, no host session vars.
    let args = read("args.txt");
    for want in ["read-only", "shell_tool", "unified_exec", "required=true", "--headless"] {
        assert!(args.contains(want), "{want} missing: {args}");
    }
    assert!(!args.contains("run_code_unsafe") && !args.contains("file_upload"), "{args}");
    let env = read("env.txt");
    assert!(!env.contains("CLAUDECODE=") && !env.contains("CODEX_THREAD_ID="), "host vars leaked: {env}");
}

#[test]
fn claude_agent_gets_no_tools_but_the_browser() {
    let (bin, out) = bin("roast-claude-args");
    fake(&bin, "claude", true, Mode::Report);
    let (code, line, _) = roast(&bin, &[("CODEX_THREAD_ID", "t1")], &[URL, &out, "--cli", "claude"]);
    assert_eq!(code, 0, "{line}");
    let read = |f: &str| std::fs::read_to_string(Path::new(&out).join(f)).unwrap();
    let args = read("args.txt");
    for want in ["--restricted", "--tools", "dontAsk", "--strict-mcp-config", "mcp__pw__browser_click"] {
        assert!(args.contains(want), "{want} missing: {args}");
    }
    assert!(!args.contains("run_code_unsafe"), "{args}");
    assert!(read("settings.json").contains("\"disableAllHooks\":true"));
    assert!(read("mcp.json").contains("--headless"));
    assert!(!read("env.txt").contains("CODEX_THREAD_ID="));
}

#[test]
fn rerun_without_a_report_is_incomplete_not_the_old_verdict() {
    let (bin, out) = bin("roast-rerun");
    fake(&bin, "codex", true, Mode::Report);
    assert_eq!(roast(&bin, &[], &[URL, &out, "--cli", "codex"]).0, 0);
    fake(&bin, "codex", true, Mode::Silent);
    let (code, line, _) = roast(&bin, &[], &[URL, &out, "--cli", "codex"]);
    assert_eq!(code, 1, "{line}");
    assert!(line.starts_with("roast codex INCOMPLETE 0 findings "), "{line}");
}

#[test]
fn codex_host_roasts_with_claude() {
    let (bin, out) = bin("roast-claude");
    fake(&bin, "codex", true, Mode::Garbage);
    fake(&bin, "claude", true, Mode::Report);
    let (code, line, _) = roast(&bin, &[("CODEX_THREAD_ID", "t1")], &[URL, &out]);
    assert_eq!(code, 0, "{line}");
    assert!(line.starts_with("roast claude SHIP-WITH-FIXES 2 findings "), "{line}");
}

#[test]
fn falls_back_to_the_host_vendor_then_skips() {
    let (bin, out) = bin("roast-fallback");
    fake(&bin, "codex", false, Mode::Report);
    fake(&bin, "claude", true, Mode::Report);
    let (_, line, _) = roast(&bin, &[("CLAUDECODE", "1")], &[URL, &out]);
    assert!(line.starts_with("roast claude "), "{line}");
    fake(&bin, "claude", false, Mode::Report);
    let (code, line, _) = roast(&bin, &[("CLAUDECODE", "1")], &[URL, &out]);
    assert_eq!((code, line.as_str()), (0, "SKIP no agent CLI ready (codex: not logged in (`codex login status`); claude: not logged in (`claude auth status`))"));
}

#[test]
fn malformed_report_is_incomplete_never_clean() {
    let (bin, out) = bin("roast-garbage");
    fake(&bin, "codex", true, Mode::Garbage);
    let (code, line, _) = roast(&bin, &[], &[URL, &out, "--cli", "codex"]);
    assert_eq!(code, 1, "{line}");
    assert!(line.starts_with("roast codex INCOMPLETE 0 findings "), "{line}");
    let report = std::fs::read_to_string(Path::new(&out).join("roast.md")).unwrap();
    assert!(report.starts_with("VERDICT: INCOMPLETE\nReason: report has no valid VERDICT line"), "{report}");
}

#[test]
fn cap_kills_a_hung_agent() {
    let (bin, out) = bin("roast-hang");
    fake(&bin, "claude", true, Mode::Hang);
    let late = bin.parent().unwrap().join("late.txt");
    let env = [("FACTORY_ROAST_SECS", "2"), ("FAKE_LATE", late.to_str().unwrap())];
    let (code, line, secs) = roast(&bin, &env, &[URL, &out, "--cli", "claude"]);
    assert_eq!(code, 1, "{line}");
    assert!(line.starts_with("roast claude INCOMPLETE 0 findings "), "{line}");
    assert!(secs < Duration::from_secs(20).as_secs(), "took {secs} s");
    let report = std::fs::read_to_string(Path::new(&out).join("roast.md")).unwrap();
    assert!(report.contains("Reason: timed out after "), "{report}");
    // The whole tree died: the grandchild's 5 s write never lands (the 2 s cap lets it start first: a kill racing its spawn would miss it).
    std::thread::sleep(Duration::from_secs(5));
    assert!(!late.exists(), "a grandchild outlived the cap");
}

#[test]
fn skips_off_and_non_local() {
    let (bin, out) = bin("roast-skip");
    assert_eq!(roast(&bin, &[("FACTORY_ROAST", "0")], &[URL, &out]).1, "SKIP off (FACTORY_ROAST=0)");
    let (code, line, _) = roast(&bin, &[], &["https://example.com", &out]);
    assert_eq!(code, 0);
    assert!(line.starts_with("SKIP https://example.com is not a local URL"), "{line}");
    let (_, line, _) = roast(&bin, &[], &["http://evil.com\\@localhost/", &out]);
    assert_eq!(line, "SKIP http://evil.com\\@localhost/ is not a plain http(s) URL");
    // The env opt-in passes the host gate; no CLI is ready here, so it stops at the next check.
    let none = [("FACTORY_ROAST_ANY_HOST", "1"), ("FACTORY_CODEX", "/nope"), ("FACTORY_CLAUDE", "/nope")];
    assert!(roast(&bin, &none, &["https://example.com", &out]).1.starts_with("SKIP no agent CLI ready"));
    assert_eq!(roast(&bin, &[], &[URL]).0, 2);
}
