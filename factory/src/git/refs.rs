//! Refs in the files backend: loose ref files, `packed-refs`, symbolic refs, per-worktree HEAD.

use super::Repo;

/// HEAD's commit sha; `HEAD` when the branch is unborn (what `git rev-parse HEAD` prints there).
pub fn head(repo: &Repo) -> String {
    match symbolic_head(repo) {
        Some(name) => read(repo, &name, 0).unwrap_or_else(|| "HEAD".into()),
        None => read_file_ref(&repo.gitdir.join("HEAD")).unwrap_or_default(),
    }
}

/// The branch HEAD points at (`refs/heads/x`), or None when detached.
pub fn symbolic_head(repo: &Repo) -> Option<String> {
    let text = std::fs::read_to_string(repo.gitdir.join("HEAD")).ok()?;
    text.trim().strip_prefix("ref:").map(|r| r.trim().to_string())
}

/// `@{u}`: the remote-tracking ref of HEAD's branch, mapped through the remote's fetch refspecs.
pub fn upstream(repo: &Repo) -> Option<String> {
    let branch = symbolic_head(repo)?.strip_prefix("refs/heads/")?.to_string();
    let remote = repo.config.get(&format!("branch.{branch}.remote"))?.to_string();
    let merge = repo.config.get(&format!("branch.{branch}.merge"))?.to_string();
    let tracking = if remote == "." {
        merge
    } else {
        let key = format!("remote.{remote}.fetch");
        repo.config.all(&key).filter_map(|spec| map_refspec(spec, &merge)).last()?
    };
    read(repo, &tracking, 0)
}

/// Maps `src` through one fetch refspec (`+refs/heads/*:refs/remotes/o/*` or an exact pair).
fn map_refspec(spec: &str, src: &str) -> Option<String> {
    let spec = spec.strip_prefix('+').unwrap_or(spec);
    let (from, to) = spec.split_once(':')?;
    match (from.split_once('*'), to.split_once('*')) {
        (Some((fp, fs)), Some((tp, ts))) => {
            let mid = src.strip_prefix(fp)?.strip_suffix(fs)?;
            Some(format!("{tp}{mid}{ts}"))
        }
        (None, None) if from == src => Some(to.to_string()),
        _ => None,
    }
}

/// Resolves a full ref name to a sha, following symbolic refs (depth 5, like Git's limit order).
pub fn read(repo: &Repo, name: &str, depth: u8) -> Option<String> {
    if depth > 5 {
        return None;
    }
    let per_worktree = ["refs/bisect/", "refs/worktree/", "refs/rewritten/"].iter().any(|p| name.starts_with(p));
    let base = if per_worktree || name == "HEAD" { &repo.gitdir } else { &repo.common };
    if let Ok(text) = std::fs::read_to_string(base.join(name)) {
        let t = text.trim();
        return match t.strip_prefix("ref:") {
            Some(target) => read(repo, target.trim(), depth + 1),
            None => is_sha(t).then(|| t.to_string()),
        };
    }
    packed(repo, name)
}

/// A ref's sha from `packed-refs`.
fn packed(repo: &Repo, name: &str) -> Option<String> {
    let text = std::fs::read_to_string(repo.common.join("packed-refs")).ok()?;
    text.lines()
        .filter(|l| !l.starts_with('#') && !l.starts_with('^'))
        .find_map(|l| l.split_once(' ').filter(|(_, n)| *n == name).map(|(s, _)| s.to_string()))
}

/// A ref file holding a bare sha (a detached HEAD).
fn read_file_ref(p: &std::path::Path) -> Option<String> {
    let t = std::fs::read_to_string(p).ok()?;
    let t = t.trim();
    is_sha(t).then(|| t.to_string())
}

/// 40 or 64 lowercase hex characters.
pub fn is_sha(s: &str) -> bool {
    (s.len() == 40 || s.len() == 64) && s.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

#[cfg(test)]
mod tests {
    use super::map_refspec;

    #[test]
    fn maps_default_refspec() {
        assert_eq!(map_refspec("+refs/heads/*:refs/remotes/origin/*", "refs/heads/main").as_deref(), Some("refs/remotes/origin/main"));
        assert_eq!(map_refspec("refs/heads/a:refs/remotes/o/b", "refs/heads/a").as_deref(), Some("refs/remotes/o/b"));
        assert_eq!(map_refspec("refs/heads/a:refs/remotes/o/b", "refs/heads/c"), None);
    }
}
