//! Helpers the binary's fixture tests share: scratch folders, Git with fixed dates, the binary itself.
#![allow(dead_code)] // each test file uses its own subset

use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

/// A fresh scratch folder for one test.
pub fn scratch(name: &str) -> PathBuf {
    let d = std::env::temp_dir().join(format!("factory-test-{}-{name}", std::process::id()));
    let _ = std::fs::remove_dir_all(&d);
    std::fs::create_dir_all(&d).unwrap();
    d
}

/// Git in `dir` with author and committer dated 2026-01-01 at `hour`:00 UTC.
pub fn git(dir: &Path, args: &[&str], hour: u64) {
    let date = format!("2026-01-01T{hour:02}:00:00Z");
    let ok = Command::new("git")
        .arg("-C")
        .arg(dir)
        .args(["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"])
        .args(args)
        .env("GIT_AUTHOR_DATE", &date)
        .env("GIT_COMMITTER_DATE", &date)
        .stdout(Stdio::null())
        .status()
        .is_ok_and(|s| s.success());
    assert!(ok, "git {args:?}");
}

/// The binary run in `dir` with `input` on stdin and `home` as its home and cache; exit code, stdout + stderr.
pub fn factory(dir: &Path, home: &Path, args: &[&str], input: &str) -> (i32, String) {
    let mut child = Command::new(env!("CARGO_BIN_EXE_factory"))
        .args(args)
        .current_dir(dir)
        .env("HOME", home)
        .env("USERPROFILE", home)
        .env("XDG_CACHE_HOME", home)
        .env_remove("PWD")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("run factory");
    child.stdin.take().unwrap().write_all(input.as_bytes()).unwrap();
    let out = child.wait_with_output().unwrap();
    (out.status.code().unwrap_or(-1), format!("{}{}", String::from_utf8_lossy(&out.stdout), String::from_utf8_lossy(&out.stderr)))
}

/// A path as the hook JSON carries it.
pub fn json_path(p: &Path) -> String {
    p.to_string_lossy().replace('\\', "/")
}
