//! `factory closeout` after a merge: removes the run's `.factory/` worktrees, their branches and the PR
//! branch, and `.factory/` temp; keeps unmerged or dirty work, an open run's state and `run.md`; refuses an
//! unmerged PR; a rerun finds nothing left. Each case is a scratch repository whose PR was squash-merged.

mod common;

use common::git;
use factory::closeout::{self, Header, facts::Pr};
use std::path::{Path, PathBuf};

const RUN: &str = "# Run: local: .factory/ticket.md \u{b7} Fast \u{b7} change\nStatus: closed\nNext: none (closed)\nWaiting: none\n\n## 8 Review \u{2714}\nLeft running: api :8080 (stop: true); preview :3000 (owner preview) (stop: false)\n";

/// A repository on `main` whose PR branch `fix/x` (head `c1`) was squash-merged as `m`; the run made two
/// worktrees at the PR head under `.factory/` (one detached, one on `fix/x-review`) and guard state.
fn merged_repo(name: &str) -> (PathBuf, Pr) {
    let d = common::scratch(name);
    git(&d, &["init", "-q", "-b", "main"], 8);
    std::fs::write(d.join(".gitignore"), ".factory/\n").unwrap();
    git(&d, &["add", ".gitignore"], 8);
    git(&d, &["commit", "-q", "-m", "base"], 8);
    git(&d, &["switch", "-q", "-c", "fix/x"], 8);
    std::fs::write(d.join("a.txt"), "x\n").unwrap();
    git(&d, &["add", "a.txt"], 9);
    git(&d, &["commit", "-q", "-m", "fix"], 9);
    let head = rev(&d, "HEAD");
    git(&d, &["switch", "-q", "main"], 9);
    git(&d, &["merge", "-q", "--squash", "fix/x"], 10);
    git(&d, &["commit", "-q", "-m", "fix (#7)"], 10);
    let merge = rev(&d, "HEAD");
    std::fs::create_dir_all(d.join(".factory/guard")).unwrap();
    std::fs::write(d.join(".factory/guard/state"), "g_ticks='1'\n").unwrap();
    std::fs::write(d.join(".factory/run.md"), RUN).unwrap();
    git(&d, &["worktree", "add", "-q", "--detach", ".factory/rv", &head], 10);
    git(&d, &["worktree", "add", "-q", "-b", "fix/x-review", ".factory/wt", &head], 10);
    let pr = Pr {
        merged: true,
        url: "https://github.com/o/r/pull/7".into(),
        number: 7,
        head_ref: "fix/x".into(),
        head_oid: head,
        merge_oid: merge,
        closes: vec![],
    };
    (d, pr)
}

fn rev(d: &Path, r: &str) -> String {
    let o = std::process::Command::new("git").arg("-C").arg(d).args(["rev-parse", r]).output().unwrap();
    String::from_utf8_lossy(&o.stdout).trim().to_string()
}

fn has_branch(d: &Path, b: &str) -> bool {
    std::process::Command::new("git")
        .arg("-C")
        .arg(d)
        .args(["rev-parse", "-q", "--verify", &format!("refs/heads/{b}")])
        .output()
        .unwrap()
        .status
        .success()
}

/// Runs the close-out on `d` with its run file's header; (report, done).
fn closeout(d: &Path, pr: &Pr) -> (String, bool) {
    let head = Header::parse(&std::fs::read_to_string(d.join(".factory/run.md")).unwrap());
    closeout::run(d, &head, pr, None, false).expect("merged PR closes out")
}

#[test]
fn merged_run_is_cleaned_and_a_rerun_finds_nothing() {
    let (d, pr) = merged_repo("co-merged");
    let (out, done) = closeout(&d, &pr);
    assert!(done, "{out}");
    for x in ["worktree", "branch fix/x\n", "branch fix/x-review", ".factory/guard", "ticket: by hand"] {
        assert!(out.contains(x), "{x} missing in:\n{out}");
    }
    assert!(!d.join(".factory/rv").exists() && !d.join(".factory/wt").exists() && !d.join(".factory/guard").exists());
    assert!(d.join(".factory/run.md").is_file(), "run.md is the run's record");
    let run = std::fs::read_to_string(d.join(".factory/run.md")).unwrap();
    assert!(run.ends_with("Left running: preview :3000 (owner preview) (stop: false)\n"), "only the preview stays listed: {run}");
    assert!(
        out.contains("removed: running api :8080 (ran: true)")
            && out.contains("kept: running preview :3000 (owner preview) (the owner's, never stopped)"),
        "{out}"
    );
    assert!(!has_branch(&d, "fix/x") && !has_branch(&d, "fix/x-review") && has_branch(&d, "main"));
    let (again, done) = closeout(&d, &pr);
    assert!(done && !again.contains("removed:"), "a rerun removes and stops nothing: {again}");
}

#[test]
fn unmerged_pr_is_refused_and_nothing_moves() {
    let (d, mut pr) = merged_repo("co-unmerged");
    pr.merged = false;
    let head = Header::parse(RUN);
    let err = closeout::run(&d, &head, &pr, None, false).unwrap_err();
    assert!(err.contains("not merged"), "{err}");
    assert!(d.join(".factory/rv").exists() && d.join(".factory/guard/state").exists() && has_branch(&d, "fix/x"));
}

#[test]
fn partly_clean_run_finishes() {
    let (d, pr) = merged_repo("co-partly");
    std::fs::remove_dir_all(d.join(".factory/rv")).unwrap(); // the folder went; its registration stayed
    git(&d, &["branch", "-q", "-D", "fix/x"], 11);
    let (out, done) = closeout(&d, &pr);
    assert!(done, "{out}");
    let list = std::process::Command::new("git").arg("-C").arg(&d).args(["worktree", "list"]).output().unwrap();
    assert!(!String::from_utf8_lossy(&list.stdout).contains(".factory"), "registration pruned");
}

#[test]
fn unmerged_or_dirty_work_and_open_runs_are_kept() {
    let (d, pr) = merged_repo("co-kept");
    std::fs::write(d.join(".factory/wt/a.txt"), "edit\n").unwrap(); // dirty, merged HEAD
    git(&d.join(".factory/rv"), &["commit", "-q", "--allow-empty", "-m", "later"], 11); // past the PR
    std::fs::write(d.join(".factory/run.md"), RUN.replace("Status: closed", "Status: open")).unwrap();
    let (out, done) = closeout(&d, &pr);
    assert!(!done && out.ends_with("closeout: incomplete\n"), "{out}");
    assert!(out.contains("(unmerged commits)") && out.contains(".factory/ (run still open)"), "{out}");
    assert!(d.join(".factory/rv").exists() && d.join(".factory/wt/a.txt").exists() && d.join(".factory/guard/state").exists());
    assert!(has_branch(&d, "fix/x-review"), "a kept worktree keeps its branch");
}

#[test]
fn pr_branch_checked_out_in_the_run_folder_is_a_note() {
    let (d, pr) = merged_repo("co-here");
    git(&d, &["switch", "-q", "fix/x"], 11);
    let (out, done) = closeout(&d, &pr);
    assert!(done && out.contains("kept: branch fix/x (checked out in"), "{out}");
}
