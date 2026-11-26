//! Roast reuse: a finished roast stands while the app it tested has not changed. Why: each roast costs minutes and
//! up to $3, and a run revisits step 6 (fix rounds, a base merge) with heads that touch no UI.
//! `<out>/roast.txt` records what the last finished roast stood on; `git diff` decides, never an agent.

use crate::git::{Repo, refs::is_sha};
use crate::paths::text;
use crate::receipt::carry;
use std::fs;
use std::path::Path;

const FILE: &str = "roast.txt";

/// The repository and working-copy tree (uncommitted edits included) of `here`; None outside Git.
pub fn stand(here: &Path) -> Option<(Repo, String)> {
    let s = crate::receipt::snapshot(here).ok()?;
    Some((Repo::discover(&s.work)?, s.tree))
}

/// The last roast's line with why it still stands, when `out` holds a finished roast of `url` on `tree`, or on a
/// tree that differs from `tree` only in paths matching the inert globs recorded with it.
pub fn find(out: &Path, url: &str, repo: &Repo, tree: &str) -> Option<String> {
    let record = fs::read_to_string(out.join(FILE)).ok()?;
    let (mut from, mut was, mut line, mut inert) = (None, None, None, Vec::new());
    for l in record.lines() {
        match l.split_once(' ')? {
            ("tree", v) => from = Some(v),
            ("url", v) => was = Some(v),
            ("line", v) => line = Some(v),
            ("inert", v) => inert.push(v),
            _ => return None,
        }
    }
    let (from, line) = (from?, line?);
    (was? == url && !line.contains(" INCOMPLETE ") && out.join("roast.md").is_file()).then_some(())?;
    if from == tree {
        return Some(format!("{line} (reused: same tree)"));
    }
    // A record edited by hand must not widen the carry: every glob passes the receipt rules again.
    (is_sha(from) && is_sha(tree) && !inert.is_empty() && inert.iter().all(|g| carry::check_glob(g).is_ok())).then_some(())?;
    let paths = carry::changed(repo, from, tree)?;
    let covered = !paths.is_empty() && paths.iter().all(|p| inert.iter().any(|g| carry::matches(g, p)));
    covered.then(|| format!("{line} (reused: {} inert paths changed since tree {})", paths.len(), &from[..12]))
}

/// Drops the record before a new roast, so a run that ends INCOMPLETE never leaves an older verdict standing.
pub fn forget(out: &Path) -> Result<(), String> {
    match fs::remove_file(out.join(FILE)) {
        Err(e) if e.kind() != std::io::ErrorKind::NotFound => Err(format!("cannot remove {}: {e}", text(&out.join(FILE)))),
        _ => Ok(()),
    }
}

/// Records a finished roast of `url` on `tree` with the globs it may carry across.
pub fn save(out: &Path, url: &str, tree: &str, inert: &[&str], line: &str) -> Result<(), String> {
    let globs: String = inert.iter().map(|g| format!("inert {g}\n")).collect();
    let body = format!("tree {tree}\nurl {url}\n{globs}line {line}\n");
    let path = out.join(FILE);
    crate::paths::write_atomic(&path, body.as_bytes()).map_err(|e| format!("cannot write {}: {e}", text(&path)))
}
