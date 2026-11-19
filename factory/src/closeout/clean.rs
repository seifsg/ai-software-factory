//! The local half of a close-out: removes what a merged run created and nothing else.
//! Created by the run = worktrees under `<run>/.factory/`, their branches and the PR's head branch, and
//! `.factory/` scratch. Each is removed only when its commits are in the merged PR (no unmerged work lost)
//! and Git agrees (no dirty tree lost); anything else is kept and named.

use super::facts::Pr;
use crate::git::{self, Repo};
use std::path::Path;

/// One result line of the close-out.
#[derive(Debug, PartialEq, Eq)]
pub enum Line {
    Removed(String),
    /// Left in place on purpose: what, why. `closeout: done` still holds.
    Kept(String, String),
    /// Left in place, and the close-out is not done until someone acts: what, why.
    Blocked(String, String),
}

/// `.factory/` entries a closed run keeps: its record, which the Stop guard and `ticketing` still read
/// (run file, guard state, suite receipts, a local ticket, release records).
const RECORD: [&str; 5] = ["run.md", "guard", "receipts", "ticket.md", "releases"];

/// A registered worktree: path (canonical), HEAD sha, branch name if any.
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

/// A path's canonical text (links, junctions, drive aliases and 8.3 names resolved), else its normal text.
/// Why: Git reports worktrees by the path they were made with; a run reached through an alias must match.
fn canon(p: &Path) -> String {
    let c = std::fs::canonicalize(p).map(|c| crate::paths::text(&c)).unwrap_or_else(|_| crate::paths::text(p));
    match c.strip_prefix("//?/") {
        Some(r) => r.strip_prefix("UNC/").map_or_else(|| r.to_string(), |u| format!("//{u}")),
        None => c,
    }
}

/// True when `path` lies inside `dir` (canonical texts; Windows compares case-insensitively).
fn inside(path: &str, dir: &str) -> bool {
    let (p, d) = if cfg!(windows) { (path.to_lowercase(), dir.to_lowercase()) } else { (path.into(), dir.into()) };
    p.strip_prefix(d.trim_end_matches('/')).is_some_and(|r| r.starts_with('/'))
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
                    t.path = canon(Path::new(&crate::paths::norm(p)));
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

/// Removes the run's merged `.factory/` worktrees; returns the branches they held and every path handled.
fn worktrees(repo: &Repo, pr: &Pr, factory: &str, dry: bool, out: &mut Vec<Line>) -> Result<(Vec<String>, Vec<String>), String> {
    let (mut branches, mut handled) = (Vec::new(), Vec::new());
    for t in trees(repo)?.into_iter().filter(|t| inside(&t.path, factory)) {
        handled.push(t.path.clone());
        if !merged(repo, pr, &t.head) {
            out.push(Line::Blocked(format!("worktree {}", t.path), "commits not in the merged PR".into()));
            continue;
        }
        match if dry { Ok(String::new()) } else { run(repo, &["worktree", "remove", &t.path]) } {
            Ok(_) => {
                out.push(Line::Removed(format!("worktree {}", t.path)));
                branches.extend(t.branch);
            }
            Err(e) => out.push(Line::Blocked(format!("worktree {}", t.path), e)),
        }
    }
    Ok((branches, handled))
}

/// Deletes each named local branch whose tip is in the merged PR and that no live worktree has checked out.
/// The PR's head branch is skipped when it is its base or comes from a fork: the run never made those.
fn branches(repo: &Repo, pr: &Pr, names: Vec<String>, removed: &[String], dry: bool, out: &mut Vec<Line>) -> Result<(), String> {
    let live: Vec<Tree> = trees(repo)?.into_iter().filter(|t| !removed.contains(&t.path)).collect();
    let mut seen = std::collections::BTreeSet::new();
    for b in names.into_iter().filter(|b| !b.is_empty()) {
        if !seen.insert(b.clone()) {
            continue;
        }
        let Ok(tip) = run(repo, &["rev-parse", "--verify", "-q", &format!("refs/heads/{b}")]) else { continue };
        let what = format!("branch {b}");
        if b == pr.head_ref && (b == pr.base_ref || pr.cross_repo) {
            out.push(Line::Kept(what, "the PR's base or a fork's branch, not the run's".into()));
        } else if let Some(t) = live.iter().find(|t| t.branch.as_deref() == Some(b.as_str())) {
            out.push(Line::Kept(what, format!("checked out in {}", t.path)));
        } else if !merged(repo, pr, tip.trim()) {
            out.push(Line::Blocked(what, "commits not in the merged PR".into()));
        } else if let Err(e) = if dry { Ok(String::new()) } else { run(repo, &["branch", "-D", &b]) } {
            out.push(Line::Blocked(what, e));
        } else {
            out.push(Line::Removed(what));
        }
    }
    Ok(())
}

/// True when `p` is or holds a Git checkout (a `.git` entry), never following links.
fn holds_git(p: &Path) -> bool {
    p.join(".git").symlink_metadata().is_ok()
        || std::fs::read_dir(p).into_iter().flatten().flatten().any(|e| e.file_type().is_ok_and(|t| t.is_dir()) && holds_git(&e.path()))
}

/// Removes `.factory/` scratch: every entry but the run's record and the worktrees handled above. An entry
/// holding a Git checkout Git did not remove is never deleted; nothing goes while a launched suite runs.
fn temp(factory: &Path, handled: &[String], dry: bool, out: &mut Vec<Line>) {
    let running = std::fs::read_dir(factory.join("receipts"))
        .into_iter()
        .flatten()
        .flatten()
        .any(|e| e.path().extension().is_some_and(|x| x == "running"));
    if running {
        out.push(Line::Blocked(".factory/".into(), "a launched suite still runs (receipts/*.running)".into()));
        return;
    }
    let Ok(rd) = std::fs::read_dir(factory) else { return };
    for e in rd.flatten() {
        let (p, name) = (e.path(), e.file_name().to_string_lossy().into_owned());
        let at = canon(&p);
        if RECORD.contains(&name.as_str()) || handled.iter().any(|h| *h == at || inside(h, &at)) {
            continue;
        }
        let what = format!(".factory/{name}");
        if p.is_dir() && holds_git(&p) {
            out.push(Line::Blocked(what, "holds a Git checkout that Git did not list as the run's worktree".into()));
            continue;
        }
        let res = if dry {
            Ok(())
        } else if p.is_dir() {
            std::fs::remove_dir_all(&p)
        } else {
            std::fs::remove_file(&p)
        };
        out.push(res.map_or_else(|e| Line::Blocked(what.clone(), e.to_string()), |()| Line::Removed(what.clone())));
    }
}

/// Removes what the merged run created in `run_dir`.
pub fn clean(run_dir: &Path, pr: &Pr, dry: bool, out: &mut Vec<Line>) -> Result<(), String> {
    let repo = Repo::discover(run_dir).ok_or("not a Git checkout")?;
    let factory = run_dir.join(".factory");
    let (mut names, handled) = worktrees(&repo, pr, &canon(&factory), dry, out)?;
    let removed: Vec<String> =
        out.iter().filter_map(|l| if let Line::Removed(x) = l { x.strip_prefix("worktree ").map(String::from) } else { None }).collect();
    names.insert(0, pr.head_ref.clone());
    branches(&repo, pr, names, &removed, dry, out)?;
    temp(&factory, &handled, dry, out);
    Ok(())
}
