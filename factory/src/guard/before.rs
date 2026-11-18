//! Before proof comes first: the step 5 block and every `T<n> pre:` line are refused while a proof-list id
//! has no `before-<id>` file under `.factory/proof/`, or has one saved after the branch's first source
//! change (its first commit after the base, or its oldest uncommitted change). A Before taken after the
//! work began cannot show where it started.

use crate::git::{Repo, history};
use std::path::{Path, PathBuf};

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

/// A proof id: letters, digits, `_` or `-`, opening with a letter or digit and holding a digit (`P1`),
/// so a note's first word (`- Capture manifest: ...`, the `Id` header) is never read as one.
fn is_id(s: &str) -> bool {
    s.as_bytes().first().is_some_and(u8::is_ascii_alphanumeric)
        && s.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
        && s.bytes().any(|b| b.is_ascii_digit())
}

/// Proof-list ids under `**Proof list:**` in `## 3 Plan`: a table row's first cell or a bullet's first word.
pub fn ids(run: &str) -> Vec<String> {
    let mut out = Vec::new();
    for (id, _) in rows(run) {
        if !out.iter().any(|found| found == id) {
            out.push(id.to_string());
        }
    }
    out
}

/// Step 3's proof rows, with their IDs and full text for evidence validation.
pub(crate) fn rows(run: &str) -> Vec<(&str, &str)> {
    entries(run).into_iter().filter(|(id, _)| is_id(id)).collect()
}

/// First words of Proof-list bullets and rows that hold no proof id: notes the Before check skips, which
/// Gate A's preflight names so an id without a digit never drops out of the check unseen.
pub(crate) fn notes(run: &str) -> Vec<&str> {
    entries(run).into_iter().map(|(id, _)| id).filter(|id| !is_id(id)).collect()
}

/// Each bullet or table body row under step 3's `**Proof list:**`: its first word or cell, and the line.
/// A table's header and separator rows are no entries.
fn entries(run: &str) -> Vec<(&str, &str)> {
    let (mut plan, mut list, mut table, mut out) = (false, false, false, Vec::new());
    for l in run.lines() {
        if l.starts_with("## ") {
            (plan, list) = (l.starts_with("## 3 Plan"), false);
        } else if plan && l.starts_with("**") {
            list = l.starts_with("**Proof list:**");
        } else if list {
            let t = l.trim_start();
            let (first, header) = match t.strip_prefix('|') {
                Some(row) => (row.split('|').next(), !std::mem::replace(&mut table, true)),
                None => {
                    table = false;
                    (t.strip_prefix("- ").or_else(|| t.strip_prefix("* ")).and_then(|b| b.split_whitespace().next()), false)
                }
            };
            let id = first.map_or("", |c| c.trim().trim_matches(['`', '*', ':']));
            if !header && !id.is_empty() && !id.bytes().all(|b| b == b'-') {
                out.push((id, t));
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
    if repo.is_some_and(|r| from_scratch(dir, r, head)) {
        return None;
    }
    let folder = proof_dir(dir, run);
    let files = crate::proof::files(&folder);
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
    let late: Vec<String> =
        start.as_ref().map_or_else(Vec::new, |(c, _)| saved.into_iter().filter(|(_, t)| t > c).map(|(id, _)| id).collect());
    if missing.is_empty() && late.is_empty() {
        let _ = std::fs::write(&cache, key); // no guard folder yet: no cache, the next todo checks again
        return None;
    }
    let began = start.filter(|_| !late.is_empty()).map_or_else(String::new, |(t, what)| {
        format!("{what} at {}", crate::receipt::utc_iso(u64::try_from(t / 1_000_000_000).unwrap_or(0)))
    });
    let shown = folder.strip_prefix(dir).unwrap_or(&folder).to_string_lossy().replace('\\', "/");
    Some(super::reply::before_first(&shown, &missing.join(", "), &late.join(", "), &began))
}

/// A new project: the base branch's commit has no files (Git's empty tree, SHA-1 or SHA-256) and nothing
/// on the branch, committed or not, predates this run's ticket (`.factory/guard/steps.jsonl`). Every
/// surface is then new, so no Before can show anything. Older work (a branch stacked on another run, code
/// left untracked) or no ticket record keeps the check.
fn from_scratch(dir: &Path, repo: &Repo, head: &str) -> bool {
    const EMPTY: [&str; 2] =
        ["4b825dc642cb6eb9a060e54bf8d69288fbee4904", "6ef19b41225c5369f1c104d45d8d85efa9b057b53b14b4b9b939dd74decc5321"];
    let Some(base) = history::base(repo).filter(|b| repo.commit_tree(b).is_some_and(|t| EMPTY.contains(&t.as_str()))) else {
        return false;
    };
    let Some(start) = ticket_start(dir) else { return false };
    let iso = |secs: u128| crate::receipt::utc_iso(u64::try_from(secs).unwrap_or(u64::MAX));
    let Some(own) = history::own_commits(repo, head, &base) else { return false };
    let old_commit = own.first.is_some_and(|(t, _)| iso(u128::try_from(t).unwrap_or(0)) < start);
    let old_file = history::worktree_first(repo, 0).is_some_and(|(t, _)| iso(t / 1_000_000_000) < start);
    !old_commit && !old_file
}

/// When this run's ticket step began (`YYYY-MM-DDTHH:MM:SSZ`), from the guard's step record.
fn ticket_start(dir: &Path) -> Option<String> {
    let text = std::fs::read_to_string(dir.join(".factory/guard/steps.jsonl")).ok()?;
    let row: serde_json::Value = serde_json::from_str(text.lines().next()?).ok()?;
    (row["step"] == "0").then(|| row["at"].as_str().map(str::to_string))?
}

/// The run's own proof folder: `.factory/proof/<ticket>/` when the `# Run:` line's first word is a ticket
/// link (`.../issues/314`) or reference (`#314`), whether or not the folder exists yet (then every Before
/// is missing); else the whole proof folder. Another run's Before with the same id never stands in.
fn proof_dir(dir: &Path, run: &str) -> PathBuf {
    let all = dir.join(".factory/proof");
    let first = run.lines().next().and_then(|l| l.strip_prefix("# Run: ")).and_then(|r| r.split_whitespace().next()).unwrap_or("");
    let link = first.contains('/') || first.starts_with('#');
    let id = first.trim_end_matches('/').rsplit(['/', '#']).next().unwrap_or("");
    let safe = !id.is_empty() && id.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_');
    if link && safe { all.join(id) } else { all }
}

/// When the branch's own work began (ns) and what began it: its first commit after the base (the last
/// instant of that commit's second: commit times are whole seconds), or its oldest uncommitted change
/// made after the branch left its base, whichever is first.
fn first_change(repo: Option<&Repo>, head: &str) -> Option<(u128, String)> {
    let repo = repo?;
    let walk = history::base(repo).and_then(|b| history::own_commits(repo, head, &b));
    let secs = |s: i64| u128::try_from(s).unwrap_or(0) * 1_000_000_000;
    let commit =
        walk.as_ref().and_then(|w| w.first.as_ref()).map(|(t, sha)| (secs(*t + 1) - 1, format!("commit {}", &sha[..sha.len().min(8)])));
    let floor = walk.as_ref().and_then(|w| w.fork).map_or(0, secs);
    let change = history::worktree_first(repo, floor).map(|(t, path)| (t, format!("uncommitted `{path}`")));
    [commit, change].into_iter().flatten().min_by_key(|(t, _)| *t)
}

#[cfg(test)]
mod tests {
    use super::{ids, notes, posted};

    #[test]
    fn notes_are_list_lines_with_no_id_never_headers_or_separators() {
        let run = "## 3 Plan\n**Proof list:**\n| Id | What |\n|:---|---|\n| P1 | a |\n| home | b |\n- P3 cmd\n- Capture manifest: x\n**Test map:**\n- note\n";
        assert_eq!(notes(run), ["home", "Capture"]);
    }

    #[test]
    fn reads_ids_from_tables_and_bullets_of_the_plan_only() {
        let run = "## 3 Plan\n**Proof list:**\n| Id | What |\n|---|---|\n| P1 | a |\n| `P2` | b |\n- P3 cmd\n- Capture manifest: x\n**Test map:**\n| P9 | x |\n## 6 Verify\n**Proof list:**\n- P8 x\n";
        assert_eq!(ids(run), ["P1", "P2", "P3"]);
    }

    #[test]
    fn todo_lines_and_the_build_block_count_as_posts() {
        assert!(posted("T3 pre: a do: b post: c"));
        assert!(posted("## 5 Build\nx"));
        assert!(!posted("## 6 Verify\nT1 is done") && !posted("Tx pre: no") && !posted("T pre: no"));
    }
}
