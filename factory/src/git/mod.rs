//! Git read natively: repository discovery, HEAD, upstream, remotes and commit trees with no `git` process.
//! Why: a `git.exe` spawn costs 20 to 80 ms on Windows; the Stop guard runs at every turn end.
//! One spawn remains, only where Git must compute: the work tree's hash (`tree`), its changed paths
//! (`history::worktree_first`) and the rare repos whose refs or config this module cannot read alone
//! (reftable, `includeIf` in the repo's own config).

pub mod config;
pub mod history;
pub mod index;
pub mod object;
pub mod refs;
pub mod tree;

use std::path::{Path, PathBuf};

/// A repository found from a folder inside it.
#[derive(Debug, Clone)]
pub struct Repo {
    /// Per-worktree Git folder (`.git`, or `.git/worktrees/<name>`).
    pub gitdir: PathBuf,
    /// Shared Git folder (objects, refs, config).
    pub common: PathBuf,
    /// Top folder of the work tree.
    pub work: PathBuf,
    pub config: config::Config,
}

/// HEAD, its upstream and whether any remote exists: what the guard compares gate commits against.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Info {
    /// Full HEAD sha; `HEAD` on an unborn branch (as `git rev-parse HEAD` prints); empty outside Git.
    pub head: String,
    /// Full sha of `@{u}`, or empty when the branch has none.
    pub up: String,
    pub remote: bool,
}

impl Repo {
    /// Finds the repository holding `start`, walking up like Git (no ceiling or GIT_DIR handling).
    pub fn discover(start: &Path) -> Option<Repo> {
        let start = std::path::absolute(start).unwrap_or_else(|_| start.to_path_buf());
        let mut dir = Some(start.as_path());
        while let Some(d) = dir {
            if let Some(gitdir) = gitdir_at(&d.join(".git")) {
                let common =
                    std::fs::read_to_string(gitdir.join("commondir")).map(|c| gitdir.join(c.trim())).unwrap_or_else(|_| gitdir.clone());
                let mut config = config::Config::load(&common.join("config"));
                if config.bool("extensions.worktreeconfig") {
                    let wt = config::Config::load(&gitdir.join("config.worktree"));
                    config.has_include_if |= wt.has_include_if;
                    config.entries.extend(wt.entries);
                }
                return Some(Repo { gitdir, common, work: d.to_path_buf(), config });
            }
            dir = d.parent();
        }
        None
    }

    /// HEAD, upstream and remotes. Reftable refs or a conditional include: one `git rev-parse` reads them.
    pub fn info(&self) -> Info {
        let remote = self.config.has_remote();
        if self.config.has_include_if || self.config.get("extensions.refstorage").is_some_and(|v| v != "files") {
            return self.info_by_git(remote);
        }
        Info { head: refs::head(self), up: refs::upstream(self).unwrap_or_default(), remote }
    }

    /// The single spawn fallback: `git rev-parse HEAD @{u}` prints HEAD, then the upstream when it exists.
    fn info_by_git(&self, remote: bool) -> Info {
        let out = std::process::Command::new("git")
            .arg("-C")
            .arg(&self.work)
            .args(["rev-parse", "HEAD", "@{u}"])
            .stderr(std::process::Stdio::null())
            .output();
        let text = out.map(|o| String::from_utf8_lossy(&o.stdout).into_owned()).unwrap_or_default();
        let mut l = text.lines();
        Info { head: l.next().unwrap_or("").into(), up: l.next().unwrap_or("").into(), remote }
    }

    /// Full sha of the one commit whose id starts with `prefix` (4+ hex), or None (missing or ambiguous).
    pub fn resolve(&self, prefix: &str) -> Option<String> {
        object::Store::open(self).resolve(prefix)
    }

    /// Tree sha of a commit (full or unique prefix), read from loose or packed objects.
    pub fn commit_tree(&self, commit: &str) -> Option<String> {
        let store = object::Store::open(self);
        let full = store.resolve(commit)?;
        let (kind, data) = store.read(&full)?;
        (kind == object::Kind::Commit).then_some(())?;
        let line = data.split(|&b| b == b'\n').next()?;
        line.strip_prefix(b"tree ").map(|t| String::from_utf8_lossy(t).into_owned())
    }
}

/// A `git` command on this work tree that ignores the caller's Git environment, takes no optional locks
/// and prints English: the spawns that read Git's own computation share it.
pub(crate) fn command(repo: &Repo) -> std::process::Command {
    let mut cmd = std::process::Command::new("git");
    cmd.arg("-C").arg(&repo.work);
    for v in ["GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"] {
        cmd.env_remove(v);
    }
    cmd.env("GIT_OPTIONAL_LOCKS", "0").env("LC_ALL", "C").env("LANGUAGE", "").stdin(std::process::Stdio::null());
    cmd
}

/// The Git folder a `.git` entry names: the folder itself, or the target of a `gitdir:` file.
fn gitdir_at(dotgit: &Path) -> Option<PathBuf> {
    let md = std::fs::metadata(dotgit).ok()?;
    let dir = if md.is_file() {
        let text = std::fs::read_to_string(dotgit).ok()?;
        let target = text.lines().next()?.strip_prefix("gitdir:")?.trim().to_string();
        let p = PathBuf::from(crate::paths::norm(&target));
        if p.is_absolute() || crate::paths::is_abs(&target) { p } else { dotgit.parent()?.join(p) }
    } else {
        dotgit.to_path_buf()
    };
    let valid = dir.join("HEAD").is_file() && (dir.join("commondir").is_file() || dir.join("objects").is_dir());
    valid.then_some(dir)
}
