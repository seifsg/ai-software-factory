//! Before proof comes first: `guard step 5|T<k>` and the Stop hook refuse the build while a proof-list id has
//! no `before-<id>` file or one saved after the branch's first source change; a run whose Befores came first
//! passes. Each case is a scratch repository with fixed commit dates and file times.

mod common;

use common::git;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const RUN: &str = "# Run: https://example.test/issues/1 \u{b7} Fast \u{b7} change\nStatus: open\nNext: 5 Build \u{b7} get-ready-to-code\nWaiting: none\n\n## 3 Plan \u{2714}\n**Proof list:**\n| Id | What |\n|---|---|\n| P1 | a |\n| P2 | b |\n**Test map:** none\n\n## 4 Before \u{2714}\nsaved\n";

/// 2026-01-01 at `h` hours UTC.
fn at(h: u64) -> SystemTime {
    UNIX_EPOCH + Duration::from_secs(1_767_225_600 + h * 3600)
}

fn set_time(p: &Path, t: SystemTime) {
    std::fs::File::options().write(true).open(p).and_then(|f| f.set_modified(t)).expect("set mtime");
}

/// A repository with a base commit on `main` at 08:00 and the branch's own commit at 10:00.
fn repo(name: &str) -> PathBuf {
    let d = common::scratch(name);
    std::fs::create_dir_all(d.join(".factory/proof/1")).unwrap();
    git(&d, &["init", "-q", "-b", "main"], 8);
    std::fs::write(d.join("a.txt"), "a\n").unwrap();
    git(&d, &["add", "a.txt"], 8);
    git(&d, &["commit", "-q", "-m", "base"], 8);
    git(&d, &["switch", "-q", "-c", "work"], 8);
    std::fs::write(d.join("a.txt"), "b\n").unwrap();
    git(&d, &["commit", "-q", "-am", "work"], 10);
    std::fs::write(d.join(".factory/run.md"), RUN).unwrap();
    d
}

/// Saves `before-<id>.txt` with its time set to `h` o'clock.
fn before(d: &Path, id: &str, h: u64) {
    let p = d.join(format!(".factory/proof/1/before-{id}.txt"));
    std::fs::write(&p, "did not exist\n").unwrap();
    set_time(&p, at(h));
}

/// Runs the binary in `d`, its own home.
fn factory(d: &Path, args: &[&str], input: &str) -> (i32, String) {
    common::factory(d, d, args, input)
}

/// The Stop hook's reply to a turn that ends on `msg`.
fn stop(d: &Path, msg: &str) -> String {
    let cwd = common::json_path(d);
    let json = format!(r#"{{"session_id":"s1","cwd":"{cwd}","last_assistant_message":"{msg}"}}"#);
    factory(d, &["guard", "stop"], &json).1
}

fn run_file(d: &Path) -> String {
    std::fs::read_to_string(d.join(".factory/run.md")).unwrap()
}

#[test]
fn a_missing_before_refuses_the_todo_line_and_the_stop() {
    let d = repo("missing");
    before(&d, "P1", 9);
    let (code, out) = factory(&d, &["guard", "step", "T1"], "T1 pre: a do: b post: c");
    assert_eq!(code, 1, "{out}");
    assert!(out.contains("refused, nothing written") && out.contains("No Before file: P2.") && !out.contains("Saved after"), "{out}");
    assert_eq!(run_file(&d), RUN, "a refused line is never written");
    let reply = stop(&d, "T1 pre: a do: b post: c");
    assert!(reply.contains("\"decision\":\"block\"") && reply.contains("No Before file: P2."), "{reply}");
    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn a_before_saved_after_the_first_commit_refuses_step_5() {
    let d = repo("late");
    before(&d, "P1", 9);
    before(&d, "P2", 11);
    let (code, out) = factory(&d, &["guard", "step", "5"], "## 5 Build\nT1 pre: a do: b post: c \u{2714}");
    assert_eq!(code, 1, "{out}");
    assert!(out.contains("Saved after the work began (commit ") && out.contains("): P2.") && !out.contains("No Before file"), "{out}");
    assert_eq!(run_file(&d), RUN);
    let reply = stop(&d, "## 5 Build x");
    assert!(reply.contains("): P2."), "{reply}");
    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn an_uncommitted_change_older_than_a_before_refuses_it() {
    let d = repo("worktree");
    before(&d, "P1", 7);
    before(&d, "P2", 9);
    std::fs::write(d.join("new.txt"), "x\n").unwrap();
    set_time(&d.join("new.txt"), at(8)); // untracked, between the two Befores and before the 10:00 commit
    let (code, out) = factory(&d, &["guard", "step", "T1"], "T1 pre: a do: b post: c");
    assert_eq!(code, 1, "{out}");
    assert!(
        out.contains("Saved after the work began (uncommitted `new.txt` at 2026-01-01T08:00:00Z): P2.") && !out.contains(": P1"),
        "{out}"
    );
    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn befores_saved_first_pass_and_the_line_is_written() {
    let d = repo("clean");
    before(&d, "P1", 9);
    before(&d, "P2", 9);
    let (code, out) = factory(&d, &["guard", "step", "T1"], "T1 pre: a do: b post: c \u{2714}");
    assert_eq!(code, 0, "{out}");
    assert!(!out.contains("Before proof comes first"), "{out}");
    assert!(run_file(&d).contains("## 5 Build\nT1 pre: a do: b post: c \u{2714}\n"));
    assert!(!stop(&d, "T1 pre: a do: b post: c").contains("Before proof comes first"));
    // The pass is kept; a Before saved again (later than the work) is judged anew and refused.
    assert!(std::fs::read_to_string(d.join(".factory/guard/before")).is_ok_and(|k| k.starts_with("P1 ")));
    before(&d, "P1", 11);
    let (code, out) = factory(&d, &["guard", "step", "T2"], "T2 pre: a do: b post: c");
    assert!(code == 1 && out.contains("): P1."), "{out}");
    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn another_tickets_before_never_stands_in() {
    let d = repo("other-ticket");
    before(&d, "P1", 9);
    let other = d.join(".factory/proof/9/before-P2.txt");
    std::fs::create_dir_all(other.parent().unwrap()).unwrap();
    std::fs::write(&other, "did not exist\n").unwrap();
    set_time(&other, at(9));
    let (code, out) = factory(&d, &["guard", "step", "T1"], "T1 pre: a do: b post: c");
    assert!(code == 1 && out.contains("No Before file: P2."), "this run's folder is .factory/proof/1/: {out}");
    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn an_untracked_file_older_than_the_branch_is_not_its_work() {
    let d = repo("old-file");
    before(&d, "P1", 9);
    before(&d, "P2", 9);
    std::fs::write(d.join("old.txt"), "x\n").unwrap();
    set_time(&d.join("old.txt"), at(7)); // before the 08:00 base commit the branch left from
    let (code, out) = factory(&d, &["guard", "step", "T1"], "T1 pre: a do: b post: c");
    assert_eq!(code, 0, "{out}");
    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn a_run_with_no_proof_folder_of_its_own_is_refused() {
    let d = repo("no-own-folder");
    let run = RUN.replace("issues/1 ", "issues/9 ");
    std::fs::write(d.join(".factory/run.md"), &run).unwrap();
    before(&d, "P1", 9); // in .factory/proof/1/: another ticket's folder
    before(&d, "P2", 9);
    let (code, out) = factory(&d, &["guard", "step", "T1"], "T1 pre: a do: b post: c");
    assert!(code == 1 && out.contains("No Before file: P1, P2."), "issue 9 has no proof folder yet: {out}");
    let _ = std::fs::remove_dir_all(&d);
}
