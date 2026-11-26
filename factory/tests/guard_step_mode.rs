//! `guard step` runs a coded run's steps in one turn: an open gate, review or suite receipt is waited for inside a call,
//! never behind a turn end (a turn end wakes whoever launched the session). The Stop hook's replies keep their bytes.

mod common;

use common::{factory, scratch};
use std::fs;

const TICKED: &str = "## 0 Ticket ✔\n## 1 Analyze ✔\n## 2 Recommend ✔\n## 2b Challenge ✔\n";

/// A run whose step 3 is about to be posted while Gate A is still open.
fn run_before_plan(name: &str) -> std::path::PathBuf {
    let dir = scratch(name);
    fs::create_dir_all(dir.join(".factory")).unwrap();
    let run = format!(
        "# Run: local fixture · Fast · change\nStatus: open\nNext: 3 Plan · get-ready-to-code\nWaiting: none\n\n{TICKED}## 3 Plan\n\n## 4 Before\n"
    );
    fs::write(dir.join(".factory/run.md"), run).unwrap();
    dir
}

#[test]
fn open_gate_is_waited_for_in_the_call() {
    let dir = run_before_plan("step-mode-gate");
    let (code, out) = factory(&dir, &dir, &["guard", "step", "3"], "## 3 Plan\n**Files:** a\n");
    assert_eq!(code, 0, "{out}");
    assert!(out.contains("Run the checker for Gate A and wait for it in the call, paste its line, then go on."), "{out}");
    assert!(!out.contains("end your turn."), "{out}");
    let _ = fs::remove_dir_all(dir);
}

#[test]
fn stop_check_keeps_the_turn_end() {
    // `guard check <session>` replays the Stop rules: its text stays byte-equal with the sh guard.
    let dir = run_before_plan("step-mode-stop");
    let (code, out) = factory(&dir, &dir, &["guard", "step", "3"], "## 3 Plan\n**Files:** a\n");
    assert_eq!(code, 0, "{out}");
    let (_, check) = factory(&dir, &dir, &["guard", "check", "s1"], "");
    assert!(check.contains("Run the checker for Gate A, paste its line, then end your turn."), "{check}");
    let _ = fs::remove_dir_all(dir);
}
