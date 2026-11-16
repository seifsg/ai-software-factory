//! The work tree's id: tracked and untracked files, `.factory/` left out, hashed by Git's own `git add`
//! (its clean filters: autocrlf, `.gitattributes`) into a private copy of the index, then read natively.
//! One `git` spawn. The real index is never touched or locked.

use super::{index, Repo};
use std::path::Path;
use std::process::{Command, Stdio};

/// Tree id of the work tree holding `folder`, as `git add -A` then `git write-tree` would give it.
pub fn worktree_tree(folder: &Path) -> Result<String, String> {
    let repo = Repo::discover(folder).ok_or_else(|| format!("not in a Git work tree: {}", crate::paths::text(folder)))?;
    let private = repo.gitdir.join(format!("factory-tree-{}.index", std::process::id()));
    let result = hash_into(&repo, &private);
    let _ = std::fs::remove_file(&private);
    result
}

/// Copies the index (its stat cache keeps `git add` fast), adds everything, parses the result.
fn hash_into(repo: &Repo, private: &Path) -> Result<String, String> {
    let real = repo.gitdir.join("index");
    if real.is_file() {
        std::fs::copy(&real, private).map_err(|e| format!("cannot copy the index: {e}"))?;
    }
    let out = Command::new("git")
        .arg("-C")
        .arg(&repo.work)
        .args(["-c", "core.splitIndex=false", "-c", "core.safecrlf=false", "add", "-A", "--", "."])
        .env("GIT_INDEX_FILE", private)
        .env("GIT_OPTIONAL_LOCKS", "0")
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("cannot run git: {e}"))?;
    if !out.status.success() {
        return Err(format!("git add failed: {}", String::from_utf8_lossy(&out.stderr).trim()));
    }
    let data = std::fs::read(private).unwrap_or_default();
    if data.is_empty() {
        return Ok(index::tree_id(&[]));
    }
    // `.factory/` is left out here, not by an exclude pathspec: Git refuses one that names an ignored folder.
    let entries: Vec<index::Entry> = index::parse(&data)?.into_iter().filter(|e| !e.path.starts_with(b".factory/")).collect();
    Ok(index::tree_id(&entries))
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
