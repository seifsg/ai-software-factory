//! The local half of a close-out: removes what a merged run created and nothing else.
//! Created by the run = worktrees under `<run>/.factory/`, their branches and the PR's head branch, and
//! `.factory/` itself except `run.md`. Each is removed only when its commits are in the merged PR (no
//! unmerged work lost) and Git agrees (no dirty tree lost); anything else is kept and named.

use super::facts::Pr;
use crate::git::{self, Repo};
use std::path::Path;

/// One result line of the close-out.
#[derive(Debug, PartialEq, Eq)]
pub enum Line {
    Removed(String),
    /// Kept: what, why, and whether it blocks `closeout: done`.
    Kept(String, String, bool),
}

/// A registered worktree: path (normalized), HEAD sha, branch name if any.
struct Tree {
    path: String,
    head: String,
    branch: Option<String>,
}

/// Runs `git <args>` in the repo; Ok(stdout) on success, Err(first stderr line) otherwise.
fn run(repo: &Repo, args: &[&str]) -> Result<String, String> {
    let out = git::command(repo).args(args).output().map_err(|e| format!("git: {e}"))?;
    if out.status.success() {
        return Ok(String::from_utf8_lossy(&out.stdout).into_owned());
    }
    let err = String::from_utf8_lossy(&out.stderr).into_owned();
    Err(err.lines().find(|l| !l.trim().is_empty()).unwrap_or("git failed").trim().to_string())
}

/// True when `sha` is the PR head or inside the merged PR (its head or its merge commit holds it).
/// Why both: a squash merge leaves the branch's commits out of the merge commit's history.
fn merged(repo: &Repo, pr: &Pr, sha: &str) -> bool {
    sha == pr.head_oid || [&pr.head_oid, &pr.merge_oid].iter().any(|t| run(repo, &["merge-base", "--is-ancestor", sha, t]).is_ok())
}

/// Every registered worktree, from `git worktree list --porcelain`.
fn trees(repo: &Repo) -> Result<Vec<Tree>, String> {
    let text = run(repo, &["worktree", "list", "--porcelain"])?;
    Ok(text
        .split("\n\n")
        .filter_map(|b| {
            let mut t = Tree { path: String::new(), head: String::new(), branch: None };
            for l in b.lines() {
                if let Some(p) = l.strip_prefix("worktree ") {
                    t.path = crate::paths::norm(p);
                } else if let Some(h) = l.strip_prefix("HEAD ") {
                    t.head = h.into();
                } else if let Some(r) = l.strip_prefix("branch refs/heads/") {
                    t.branch = Some(r.into());
                }
            }
            (!t.path.is_empty()).then_some(t)
        })
        .collect())
}

/// True when `path` lies inside `dir` (both normalized; Windows paths compare case-insensitively).
fn inside(path: &str, dir: &str) -> bool {
    let (p, d) = if cfg!(windows) { (path.to_lowercase(), dir.to_lowercase()) } else { (path.into(), dir.into()) };
    p.strip_prefix(d.trim_end_matches('/')).is_some_and(|r| r.starts_with('/'))
}

/// Removes the run's merged `.factory/` worktrees; returns the lines and the branches they held.
fn worktrees(repo: &Repo, pr: &Pr, factory: &str, dry: bool, out: &mut Vec<Line>) -> Result<Vec<String>, String> {
    let mut branches = Vec::new();
    for t in trees(repo)?.into_iter().filter(|t| inside(&t.path, factory)) {
        if !merged(repo, pr, &t.head) {
            out.push(Line::Kept(t.path, "unmerged commits".into(), true));
            continue;
        }
        let res = if dry { Ok(String::new()) } else { run(repo, &["worktree", "remove", &t.path]) };
        match res {
            Ok(_) => {
                out.push(Line::Removed(format!("worktree {}", t.path)));
                branches.extend(t.branch);
            }
            Err(e) => out.push(Line::Kept(t.path, e, true)),
        }
    }
    Ok(branches)
}

/// Deletes each named local branch whose tip is in the merged PR and that no worktree has checked out.
fn branches(repo: &Repo, pr: &Pr, names: Vec<String>, dry: bool, out: &mut Vec<Line>) -> Result<(), String> {
    // Worktrees still holding a branch: all but those removed above (a dry run removed none for real).
    let gone = |p: &str| out.iter().any(|l| matches!(l, Line::Removed(x) if x.strip_prefix("worktree ") == Some(p)));
    let live: Vec<Tree> = trees(repo)?.into_iter().filter(|t| !gone(&t.path)).collect();
    let mut seen = std::collections::BTreeSet::new();
    for b in names.into_iter().filter(|b| !b.is_empty()) {
        if !seen.insert(b.clone()) {
            continue;
        }
        let Ok(tip) = run(repo, &["rev-parse", "--verify", "-q", &format!("refs/heads/{b}")]) else { continue };
        if let Some(t) = live.iter().find(|t| t.branch.as_deref() == Some(b.as_str())) {
            out.push(Line::Kept(format!("branch {b}"), format!("checked out in {}", t.path), false));
        } else if !merged(repo, pr, tip.trim()) {
            out.push(Line::Kept(format!("branch {b}"), "unmerged commits".into(), true));
        } else if let Err(e) = if dry { Ok(String::new()) } else { run(repo, &["branch", "-D", &b]) } {
            out.push(Line::Kept(format!("branch {b}"), e, true));
        } else {
            out.push(Line::Removed(format!("branch {b}")));
        }
    }
    Ok(())
}

/// Removes `.factory/` entries except `run.md` and folders holding a kept worktree. Refuses while the run is
/// open (a new run's guard state) or a launched suite still runs (`receipts/*.running`).
fn temp(run_dir: &Path, open: bool, dry: bool, out: &mut Vec<Line>) {
    let factory = run_dir.join(".factory");
    let running = std::fs::read_dir(factory.join("receipts"))
        .into_iter()
        .flatten()
        .flatten()
        .any(|e| e.path().extension().is_some_and(|x| x == "running"));
    let why = if open {
        "run still open"
    } else if running {
        "a launched suite still runs"
    } else {
        ""
    };
    if !why.is_empty() {
        out.push(Line::Kept(".factory/".into(), why.into(), true));
        return;
    }
    // Worktrees already handled: kept ones stay, removed ones are Git's (a dry run would list them twice).
    let kept: Vec<String> = out
        .iter()
        .filter_map(|l| match l {
            Line::Kept(p, _, true) => Some(p.clone()),
            Line::Removed(x) => x.strip_prefix("worktree ").map(String::from),
            Line::Kept(..) => None,
        })
        .collect();
    let Ok(rd) = std::fs::read_dir(&factory) else { return };
    for e in rd.flatten() {
        let p = e.path();
        let name = e.file_name().to_string_lossy().into_owned();
        let ptext = crate::paths::text(&p);
        if name == "run.md" || kept.iter().any(|k| *k == ptext || inside(k, &ptext)) {
            continue;
        }
        let res = if dry {
            Ok(())
        } else if p.is_dir() {
            std::fs::remove_dir_all(&p)
        } else {
            std::fs::remove_file(&p)
        };
        match res {
            Ok(()) => out.push(Line::Removed(format!(".factory/{name}"))),
            Err(e) => out.push(Line::Kept(format!(".factory/{name}"), e.to_string(), true)),
        }
    }
}

/// Removes what the merged run created in `run_dir`; `open` is the run file's `Status: open`.
pub fn clean(run_dir: &Path, pr: &Pr, open: bool, dry: bool, out: &mut Vec<Line>) -> Result<(), String> {
    let repo = Repo::discover(run_dir).ok_or("not a Git checkout")?;
    let factory = crate::paths::text(&run_dir.join(".factory"));
    let mut names = worktrees(&repo, pr, &factory, dry, out)?;
    names.insert(0, pr.head_ref.clone());
    branches(&repo, pr, names, dry, out)?;
    temp(run_dir, open, dry, out);
    Ok(())
}
