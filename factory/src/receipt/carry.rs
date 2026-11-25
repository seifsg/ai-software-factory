//! Inert carry: a PASS stays proof for a later tree when Git shows every path changed since is one the
//! suite never reads (its receipt's `inert <glob>` lines). Why: a docs-only head must not rerun a long suite,
//! and the proof comes from `git diff`, never from an agent's word.

use super::Receipt;
use crate::git::{Repo, refs::is_sha};
use std::path::PathBuf;

/// A PASS carried to another tree: the tree it ran on and how many inert paths changed since.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Carried {
    pub from: String,
    pub paths: usize,
}

impl Carried {
    /// The words `receipt check` and `receipt run` print after the receipt's path.
    pub fn note(&self) -> String {
        format!("carried from tree {}: {} inert paths changed", &self.from[..12], self.paths)
    }
}

/// Refuses a glob that matches every path (nothing left once `*` and `/` go) or breaks the one-line format.
pub fn check_glob(glob: &str) -> Result<(), String> {
    if glob.contains(['\n', '\r']) {
        return Err(format!("--inert {glob:?} spans lines; a receipt line holds one glob"));
    }
    if glob.chars().all(|c| c == '*' || c == '/') {
        return Err(format!("--inert '{glob}' matches every path, so any change would keep the PASS; name paths the suite never reads (docs/**)"));
    }
    Ok(())
}

/// Whole-path match: `**` any bytes, `*` any bytes but `/`, `?` one byte but `/`, the rest literal.
/// One row per glob token over the path (O(glob x path)), no backtracking blow-up.
pub fn matches(glob: &str, path: &[u8]) -> bool {
    let g = glob.as_bytes();
    let mut cur = vec![false; path.len() + 1];
    let mut next = cur.clone();
    cur[0] = true;
    let mut i = 0;
    while i < g.len() {
        next.fill(false);
        if g[i] == b'*' {
            let cross = g.get(i + 1) == Some(&b'*');
            i += usize::from(cross);
            for j in 0..=path.len() {
                next[j] = cur[j] || (j > 0 && next[j - 1] && (cross || path[j - 1] != b'/'));
            }
        } else {
            for j in 1..=path.len() {
                let c = path[j - 1];
                next[j] = cur[j - 1] && if g[i] == b'?' { c != b'/' } else { c == g[i] };
            }
        }
        std::mem::swap(&mut cur, &mut next);
        i += 1;
    }
    cur[path.len()]
}

/// Paths that differ between two trees, renames as delete + add; None when Git cannot diff them (an object
/// is missing: a dirty receipt's tree is never written).
fn changed(repo: &Repo, from: &str, to: &str) -> Option<Vec<Vec<u8>>> {
    let out = crate::git::command(repo).args(["diff", "--name-only", "-z", "--no-renames", from, to]).output().ok()?;
    out.status.success().then(|| out.stdout.split(|b| *b == 0).filter(|p| !p.is_empty()).map(<[u8]>::to_vec).collect())
}

/// The newest PASS among `passes` whose inert globs cover every path changed from its tree to `tree`.
pub fn find(repo: &Repo, mut passes: Vec<(PathBuf, Receipt)>, tree: &str) -> Option<(PathBuf, Receipt, Carried)> {
    // Shas only: a receipt's tree goes to `git diff` as an argument.
    passes.retain(|(_, r)| !r.inert.is_empty() && r.tree != tree && is_sha(&r.tree) && is_sha(tree));
    passes.sort_by(|a, b| b.1.at.cmp(&a.1.at));
    passes.into_iter().find_map(|(p, r)| {
        let paths = changed(repo, &r.tree, tree)?;
        let inert = !paths.is_empty() && paths.iter().all(|x| r.inert.iter().any(|g| matches(g, x)));
        let carried = Carried { from: r.tree.clone(), paths: paths.len() };
        inert.then_some((p, r, carried))
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn globs_match_whole_paths() {
        let m = |g, p: &str| matches(g, p.as_bytes());
        assert!(m("docs/**", "docs/a/b.md") && m("**.md", "a/b.md") && m("*.md", "a.md") && m("a?c", "abc"));
        assert!(!m("*.md", "d/a.md") && !m("docs/*", "docs/a/b") && !m("a?c", "a/c") && !m("docs", "docs/x") && !m("x", "xy"));
        for bad in ["", "*", "**", "**/*", "/**", "a\nb"] {
            assert!(check_glob(bad).is_err(), "{bad:?}");
        }
        assert!(check_glob("docs/**").is_ok());
    }
}
