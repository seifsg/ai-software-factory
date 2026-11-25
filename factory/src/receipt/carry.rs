//! Inert carry: a PASS stays proof for a later tree when Git shows every path changed since is one the
//! suite never reads (its receipt's `inert <glob>` lines). Why: a docs-only head must not rerun a long suite,
//! and the proof comes from `git diff`, never from an agent's word.

use super::Receipt;
use crate::git::{Repo, refs::is_sha};
use std::path::PathBuf;

/// Paths any real suite reads: a glob matching one would carry a PASS across code changes.
const PROBES: [&str; 5] = ["a", "a.rs", "src/a.rs", "a/b/c", "x/y.ts"];

/// Inert PASS receipts tried per call, newest first: each costs one `git diff` spawn, and the guard calls
/// this several times per Stop, so a miss costs at most this many spawns however many receipts pile up.
const TRIED: usize = 3;

/// A PASS carried to another tree: the tree it ran on, how many inert paths changed since, and its globs.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Carried {
    pub from: String,
    pub paths: usize,
    pub inert: Vec<String>,
}

impl Carried {
    /// The words `receipt check` and `receipt run` print after the receipt's path: globs named so a checker
    /// can judge them.
    pub fn note(&self) -> String {
        format!("carried from tree {}: {} inert paths changed (inert: {})", &self.from[..12], self.paths, self.inert.join(", "))
    }
}

/// Refuses a glob with no literal character, one matching a probe source path, or one that breaks the
/// one-line format: any of them would let a code change keep the PASS.
pub fn check_glob(glob: &str) -> Result<(), String> {
    if glob.contains(['\n', '\r']) {
        return Err(format!("--inert {glob:?} spans lines; a receipt line holds one glob"));
    }
    let why = if glob.chars().all(|c| matches!(c, '*' | '?' | '/')) {
        "matches every path".to_string()
    } else if let Some(p) = PROBES.iter().find(|p| matches(glob, p.as_bytes())) {
        format!("matches source paths such as '{p}'")
    } else {
        return Ok(());
    };
    Err(format!("--inert '{glob}' {why}, so a code change would keep the PASS; name paths the suite never reads (docs/**)"))
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

/// Among the `TRIED` newest inert PASSes in `passes`, the newest whose globs cover every path changed from
/// its tree to `tree`.
pub fn find(repo: &Repo, mut passes: Vec<(PathBuf, Receipt)>, tree: &str) -> Option<(PathBuf, Receipt, Carried)> {
    // Shas only: a receipt's tree goes to `git diff` as an argument.
    passes.retain(|(_, r)| !r.inert.is_empty() && r.tree != tree && is_sha(&r.tree) && is_sha(tree));
    passes.sort_by(|a, b| b.1.at.cmp(&a.1.at));
    passes.truncate(TRIED);
    passes.into_iter().find_map(|(p, r)| {
        let paths = changed(repo, &r.tree, tree)?;
        let inert = !paths.is_empty() && paths.iter().all(|x| r.inert.iter().any(|g| matches(g, x)));
        let carried = Carried { from: r.tree.clone(), paths: paths.len(), inert: r.inert.clone() };
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
        for bad in ["", "*", "**", "**/*", "/**", "?", "?**", "**?", "*?/**", "**.*", "**a", "*.rs", "src/**", "a\nb"] {
            assert!(check_glob(bad).is_err(), "{bad:?}");
        }
        for good in ["docs/**", "*.md", "**/*.md", "notes/**"] {
            assert!(check_glob(good).is_ok(), "{good:?}");
        }
    }
}
