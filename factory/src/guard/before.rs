//! Before proof comes first: the step 5 block and every `T<n> pre:` line are refused while a proof-list id
//! has no `before-<id>` file under `.factory/proof/`, or has one saved after the branch's first source
//! change (its first commit after the base, or its oldest uncommitted change). A Before taken after the
//! work began cannot show where it started.

use crate::git::{Repo, history};
use std::path::Path;

/// The message posts the step 5 block or a todo line.
pub fn posted(msg: &str) -> bool {
    crate::run::locate::posted_label(msg) == "5" || msg.lines().any(todo_line)
}

/// `T<n> pre:` at the start of a line.
pub fn todo_line(l: &str) -> bool {
    l.strip_prefix('T')
        .and_then(|r| r.split_once(' '))
        .is_some_and(|(n, rest)| !n.is_empty() && n.bytes().all(|b| b.is_ascii_digit()) && rest.starts_with("pre:"))
}

/// A proof id: letters, digits, `_` or `-`, opening with a letter or digit; never the `Id` header.
fn is_id(s: &str) -> bool {
    s.as_bytes().first().is_some_and(u8::is_ascii_alphanumeric)
        && s.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
        && !s.eq_ignore_ascii_case("id")
}

/// Proof-list ids under `**Proof list:**` in `## 3 Plan`: a table row's first cell or a bullet's first word.
pub fn ids(run: &str) -> Vec<String> {
    let (mut plan, mut list, mut out) = (false, false, Vec::<String>::new());
    for l in run.lines() {
        if l.starts_with("## ") {
            (plan, list) = (l.starts_with("## 3 Plan"), false);
        } else if plan && l.starts_with("**") {
            list = l.starts_with("**Proof list:**");
        } else if list {
            let t = l.trim_start();
            let first = match t.strip_prefix('|') {
                Some(row) => row.split('|').next(),
                None => t.strip_prefix("- ").or_else(|| t.strip_prefix("* ")).and_then(|b| b.split_whitespace().next()),
            };
            let id = first.map_or("", |c| c.trim().trim_matches(['`', '*', ':']));
            if is_id(id) && !out.iter().any(|x| x == id) {
                out.push(id.to_string());
            }
        }
    }
    out
}

/// Why the step 5 block or a todo line is refused, or None when every Before came first.
/// `head` is HEAD's sha; Git is read only when every Before file exists. A pass is kept in
/// `.factory/guard/before`, keyed by the Befores and their times: work after a pass is always later than
/// each Before, so the pass holds until a Before changes, and later todos skip Git.
pub fn refusal(dir: &Path, run: &str, repo: Option<&Repo>, head: &str) -> Option<String> {
    let files = crate::proof::files(&dir.join(".factory/proof"));
    let (mut missing, mut saved) = (Vec::new(), Vec::new());
    for id in ids(run) {
        let want = format!("before-{id}");
        let at = files
            .iter()
            .filter(|f| f.file_stem().is_some_and(|s| s.to_string_lossy() == want))
            .filter_map(|f| crate::paths::mtime_ns(f))
            .max();
        match at {
            None => missing.push(id),
            Some(t) => saved.push((id, t)),
        }
    }
    let key: String = saved.iter().map(|(id, t)| format!("{id} {t}\n")).collect();
    let cache = dir.join(".factory/guard/before");
    if missing.is_empty() && (saved.is_empty() || std::fs::read_to_string(&cache).is_ok_and(|k| k == key)) {
        return None;
    }
    let start = if saved.is_empty() { None } else { first_change(repo, head) };
    let late: Vec<String> = start.map_or_else(Vec::new, |c| saved.into_iter().filter(|(_, t)| *t > c).map(|(id, _)| id).collect());
    if missing.is_empty() && late.is_empty() {
        let _ = std::fs::write(&cache, key); // no guard folder yet: no cache, the next todo checks again
        return None;
    }
    Some(super::reply::before_first(&missing.join(", "), &late.join(", ")))
}

/// When the branch's own work began (ns): its first commit after the base (the last instant of that
/// commit's second: commit times are whole seconds), or its oldest uncommitted change, whichever is first.
fn first_change(repo: Option<&Repo>, head: &str) -> Option<u128> {
    let repo = repo?;
    let commit = history::base(repo)
        .and_then(|b| history::first_own_commit(repo, head, &b))
        .map(|s| (u128::try_from(s).unwrap_or(0) + 1) * 1_000_000_000 - 1);
    [commit, history::worktree_first(repo)].into_iter().flatten().min()
}

#[cfg(test)]
mod tests {
    use super::{ids, posted};

    #[test]
    fn reads_ids_from_tables_and_bullets_of_the_plan_only() {
        let run = "## 3 Plan\n**Proof list:**\n| Id | What |\n|---|---|\n| P1 | a |\n| `P2` | b |\n- P3 cmd\n**Test map:**\n| P9 | x |\n## 6 Verify\n**Proof list:**\n- P8 x\n";
        assert_eq!(ids(run), ["P1", "P2", "P3"]);
    }

    #[test]
    fn todo_lines_and_the_build_block_count_as_posts() {
        assert!(posted("T3 pre: a do: b post: c"));
        assert!(posted("## 5 Build\nx"));
        assert!(!posted("## 6 Verify\nT1 is done") && !posted("Tx pre: no") && !posted("T pre: no"));
    }
}
