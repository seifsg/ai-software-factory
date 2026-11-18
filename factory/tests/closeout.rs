//! `factory closeout` after a merge: stops what the run left running (never the owner's preview), removes
//! the run's `.factory/` worktrees, their branches, the PR branch and `.factory/` scratch, and keeps the
//! run's record, unmerged or dirty work and anything the run did not make; refuses an unmerged PR, an open
//! run and a PR from elsewhere; a rerun finds nothing left. Each case is a scratch repository whose PR was
//! squash-merged.

mod common;

use common::git;
use factory::closeout::{self, Header, facts::Pr};
use std::path::{Path, PathBuf};

const RUN: &str = "# Run: local: .factory/ticket.md \u{b7} Fast \u{b7} change\nStatus: closed\nNext: none (closed)\nWaiting: none\n\n## 7 PR \u{2714}\nhttps://github.com/o/r/pull/7\n\n## 8 Review \u{2714}\nLeft running: api :8080 (stop: true); preview :3000 (owner preview) (stop: false)\n";

/// A repository on `main` whose PR branch `fix/x` was squash-merged; the run made two worktrees at the PR
/// head under `.factory/` (one detached, one on `fix/x-review`), guard state and scratch briefs.
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
    for dir in ["guard", "briefs"] {
        std::fs::create_dir_all(d.join(".factory").join(dir)).unwrap();
    }
    std::fs::write(d.join(".factory/guard/state"), "g_ticks='1'\n").unwrap();
    std::fs::write(d.join(".factory/briefs/a.md"), "brief\n").unwrap();
    std::fs::write(d.join(".factory/ticket.md"), "local ticket\n").unwrap();
    std::fs::create_dir_all(d.join(".factory/releases")).unwrap();
    std::fs::write(d.join(".factory/releases/v1.md"), "release\n").unwrap();
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
        base_ref: "main".into(),
        cross_repo: false,
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
fn closeout(d: &Path, pr: &Pr) -> Result<(String, bool), String> {
    let head = Header::parse(&std::fs::read_to_string(d.join(".factory/run.md")).unwrap());
    closeout::run(d, &head, pr, None, false)
}

#[test]
fn merged_run_is_cleaned_and_a_rerun_finds_nothing() {
    let (d, pr) = merged_repo("co-merged");
    let (out, done) = closeout(&d, &pr).unwrap();
    assert!(done && out.ends_with("closeout: done\n"), "{out}");
    for x in ["removed: worktree", "removed: branch fix/x\n", "removed: branch fix/x-review", "removed: .factory/briefs", "ticket: by hand"]
    {
        assert!(out.contains(x), "{x} missing in:\n{out}");
    }
    assert!(
        out.contains("removed: running api :8080 (ran: true)")
            && out.contains("kept: running preview :3000 (owner preview) (the owner's preview"),
        "{out}"
    );
    assert!(!d.join(".factory/rv").exists() && !d.join(".factory/wt").exists() && !d.join(".factory/briefs").exists());
    for f in ["run.md", "guard/state", "ticket.md", "releases/v1.md"] {
        assert!(d.join(".factory").join(f).is_file(), "the run's record stays: {f}");
    }
    let run = std::fs::read_to_string(d.join(".factory/run.md")).unwrap();
    assert!(run.ends_with("Left running: preview :3000 (owner preview) (stop: false)\n"), "only the preview stays listed: {run}");
    assert!(!has_branch(&d, "fix/x") && !has_branch(&d, "fix/x-review") && has_branch(&d, "main"));
    let (again, done) = closeout(&d, &pr).unwrap();
    assert!(done && !again.contains("removed:"), "a rerun removes and stops nothing: {again}");
}

#[test]
fn unmerged_open_or_foreign_is_refused_and_nothing_moves() {
    let (d, pr) = merged_repo("co-refused");
    let unmerged = Pr { merged: false, ..pr.clone() };
    assert!(closeout(&d, &unmerged).unwrap_err().contains("not merged"));
    let foreign = Pr { url: "https://github.com/o/r/pull/8".into(), ..pr.clone() };
    assert!(closeout(&d, &foreign).unwrap_err().contains("not this run's PR"));
    let longer = Pr { url: "https://github.com/o/r/pull/7".into(), ..pr.clone() };
    std::fs::write(d.join(".factory/run.md"), RUN.replace("pull/7\n", "pull/70\n")).unwrap();
    assert!(closeout(&d, &longer).unwrap_err().contains("not this run's PR"), "pull/7 is not pull/70");
    let elsewhere = RUN.replace(
        "https://github.com/o/r/pull/7\n\n## 8 Review \u{2714}\n",
        "local only\n\n## 8 Review \u{2714}\nsee https://github.com/o/r/pull/7\n",
    );
    std::fs::write(d.join(".factory/run.md"), elsewhere).unwrap();
    assert!(closeout(&d, &pr).unwrap_err().contains("not this run's PR"), "only the step 7 block names the run's PR");
    std::fs::write(d.join(".factory/run.md"), RUN).unwrap();
    std::fs::write(d.join(".factory/run.md"), RUN.replace("Status: closed", "Status: open")).unwrap();
    assert!(closeout(&d, &pr).unwrap_err().contains("still open"));
    assert!(d.join(".factory/rv").exists() && d.join(".factory/briefs/a.md").exists() && has_branch(&d, "fix/x"));
    assert!(std::fs::read_to_string(d.join(".factory/run.md")).unwrap().contains("api :8080 (stop: true)"), "nothing stopped");
}

#[test]
fn partly_clean_run_finishes() {
    let (d, pr) = merged_repo("co-partly");
    std::fs::remove_dir_all(d.join(".factory/rv")).unwrap(); // the folder went; its registration stayed
    git(&d, &["branch", "-q", "-D", "fix/x"], 11);
    let (out, done) = closeout(&d, &pr).unwrap();
    assert!(done, "{out}");
    let list = std::process::Command::new("git").arg("-C").arg(&d).args(["worktree", "list"]).output().unwrap();
    assert!(!String::from_utf8_lossy(&list.stdout).contains(".factory"), "registration pruned");
}

#[test]
fn unmerged_dirty_or_unlisted_work_blocks_and_stays() {
    let (d, pr) = merged_repo("co-kept");
    std::fs::write(d.join(".factory/wt/a.txt"), "edit\n").unwrap(); // dirty, merged HEAD
    git(&d.join(".factory/rv"), &["commit", "-q", "--allow-empty", "-m", "later"], 11); // past the PR
    std::fs::create_dir_all(d.join(".factory/other/repo")).unwrap(); // a checkout Git does not list as ours
    std::fs::write(d.join(".factory/other/repo/.git"), "gitdir: elsewhere\n").unwrap();
    let (out, done) = closeout(&d, &pr).unwrap();
    assert!(!done && out.contains("closeout: incomplete"), "{out}");
    assert!(out.contains("(commits not in the merged PR)") && out.contains("blocked: .factory/other (holds a Git checkout"), "{out}");
    assert!(d.join(".factory/rv").exists() && d.join(".factory/wt/a.txt").exists() && d.join(".factory/other/repo/.git").exists());
    assert!(has_branch(&d, "fix/x-review"), "a kept worktree keeps its branch");
}

#[test]
fn branches_the_run_did_not_make_stay() {
    let (d, pr) = merged_repo("co-branches");
    git(&d, &["switch", "-q", "fix/x"], 11);
    let (out, done) = closeout(&d, &pr).unwrap();
    assert!(done && out.contains("kept: branch fix/x (checked out in"), "{out}");
    git(&d, &["switch", "-q", "main"], 11);
    let fork = Pr { cross_repo: true, ..pr.clone() };
    let (out, _) = closeout(&d, &fork).unwrap();
    assert!(out.contains("kept: branch fix/x (the PR's base or a fork's branch") && has_branch(&d, "fix/x"), "{out}");
    let from_main = Pr { head_ref: "main".into(), ..pr };
    let (out, _) = closeout(&d, &from_main).unwrap();
    assert!(has_branch(&d, "main") && !out.contains("removed: branch main"), "{out}");
}

#[test]
fn dry_run_changes_nothing_and_crlf_run_files_keep_their_endings() {
    let (d, pr) = merged_repo("co-dry");
    let head = Header::parse(&std::fs::read_to_string(d.join(".factory/run.md")).unwrap());
    let (out, done) = closeout::run(&d, &head, &pr, None, true).unwrap();
    assert!(done && out.contains("would remove: worktree") && out.ends_with("closeout: dry run, would be done\n"), "{out}");
    assert!(d.join(".factory/rv").exists() && d.join(".factory/briefs/a.md").exists() && has_branch(&d, "fix/x"));
    std::fs::write(d.join(".factory/run.md"), RUN.replace('\n', "\r\n")).unwrap();
    closeout(&d, &pr).unwrap();
    let run = std::fs::read_to_string(d.join(".factory/run.md")).unwrap();
    assert!(run.ends_with("Left running: preview :3000 (owner preview) (stop: false)\r\n"), "{run:?}");
}
