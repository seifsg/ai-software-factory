//! The work tree's id: tracked and untracked files, `.factory/` left out, hashed by Git's own `git add`
//! (its clean filters: autocrlf, `.gitattributes`) into a private copy of the index, then read natively.
//! One `git` spawn. The real index is never touched or locked.

use super::{Repo, index};
use std::path::Path;
use std::process::Stdio;

/// Tree id of the work tree holding `folder`, as `git add -A -- . ':(exclude).factory'` then
/// `git write-tree` would give it (tracked `.factory/` entries stay as the index has them).
pub fn worktree_tree(folder: &Path) -> Result<String, String> {
    let repo = Repo::discover(folder).ok_or_else(|| format!("not in a Git work tree: {}", crate::paths::text(folder)))?;
    tree_of(&repo)
}

/// The same for a discovered repository.
pub fn tree_of(repo: &Repo) -> Result<String, String> {
    let private = repo.gitdir.join(format!("factory-tree-{}.index", std::process::id()));
    let result = hash_into(repo, &private);
    let _ = std::fs::remove_file(&private);
    result
}

/// Copies the index (its stat cache keeps `git add` fast), adds everything, parses the result.
fn hash_into(repo: &Repo, private: &Path) -> Result<String, String> {
    let real = repo.gitdir.join("index");
    if real.is_file() {
        std::fs::copy(&real, private).map_err(|e| format!("cannot copy the index: {e}"))?;
    }
    // Git refuses an exclude pathspec that names an ignored folder, so it goes only where .factory is not ignored;
    // a rule elsewhere (a global excludes file) costs one more spawn, without it.
    let mut exclude = !factory_ignored(repo);
    let mut out = add(repo, private, exclude)?;
    if exclude && !out.status.success() && String::from_utf8_lossy(&out.stderr).contains("ignored by one of your") {
        exclude = false;
        out = add(repo, private, false)?;
    }
    if !out.status.success() {
        return Err(format!("git add failed: {}", String::from_utf8_lossy(&out.stderr).trim()));
    }
    let data = std::fs::read(private).unwrap_or_default();
    let after = if data.is_empty() { Vec::new() } else { index::parse(&data)? };
    if exclude {
        return Ok(index::tree_id(&after)); // the exclude left tracked `.factory/` entries as they were
    }
    // Without it, the add may have restaged tracked `.factory/` files: take them from the real index instead
    // (one Git may write split or sparse; then `.factory/` stays out, as untracked ones are).
    let factory = |e: &index::Entry| e.path.starts_with(b".factory/");
    let before = index::parse(&std::fs::read(&real).unwrap_or_default()).unwrap_or_default();
    let mut entries: Vec<index::Entry> = after.into_iter().filter(|e| !factory(e)).chain(before.into_iter().filter(factory)).collect();
    entries.sort_by(|a, b| a.path.cmp(&b.path));
    Ok(index::tree_id(&entries))
}

/// One `git add -A` into the private index, with or without the `.factory` exclude.
fn add(repo: &Repo, private: &Path, exclude: bool) -> Result<std::process::Output, String> {
    let mut cmd = super::command(repo);
    cmd.args(["-c", "core.splitIndex=false", "-c", "index.sparse=false", "-c", "core.safecrlf=false", "add", "-A", "--", "."]);
    if exclude {
        cmd.arg(":(exclude).factory");
    }
    // English messages (the shared command sets LC_ALL): the ignored-folder retry reads stderr.
    cmd.env("GIT_INDEX_FILE", private).stdout(Stdio::null()).stderr(Stdio::piped()).output().map_err(|e| format!("cannot run git: {e}"))
}

/// The checkout's own ignore files name `.factory` (the factory adds `.factory/` to `.gitignore`).
fn factory_ignored(repo: &Repo) -> bool {
    let listed = |p: &Path| {
        std::fs::read_to_string(p)
            .is_ok_and(|t| t.lines().map(str::trim).any(|l| matches!(l, ".factory" | ".factory/" | "/.factory" | "/.factory/")))
    };
    listed(&repo.work.join(".gitignore")) || listed(&repo.common.join("info/exclude"))
}

/// `factory tree [<folder>]`: prints the work tree's id.
pub fn cli(args: &[&str]) -> u8 {
    let folder = args.first().map_or_else(crate::guard::cwd, |f| std::path::PathBuf::from(crate::paths::norm(f)));
    match worktree_tree(&folder) {
        Ok(t) => {
            println!("{t}");
            0
        }
        Err(e) => {
            eprintln!("factory tree: {e}");
            1
        }
    }
}
