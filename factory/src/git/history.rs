//! When the branch's own work began, for the Before rule: the committer time of its first commit after the
//! base, and the modification time of its oldest uncommitted change. Commits are walked natively; changed
//! paths come from one `git status` (ignore rules and stat checks are Git's own).

use super::Repo;
use super::object::{Kind, Store};
use std::collections::{BinaryHeap, HashMap};
use std::process::Stdio;

/// Base candidates in order: the remote's default branch, then the usual names.
const BASES: [&str; 5] =
    ["refs/remotes/origin/HEAD", "refs/remotes/origin/main", "refs/remotes/origin/master", "refs/heads/main", "refs/heads/master"];

/// Walk limit: a base this far from HEAD is no base of this branch; its commits go unjudged.
const MAX_COMMITS: usize = 20_000;

const OWN: u8 = 1;
const BASE: u8 = 2;

/// The base branch's commit, or None when no usual base ref exists.
pub fn base(repo: &Repo) -> Option<String> {
    BASES.iter().find_map(|r| super::refs::read(repo, r, 0))
}

/// Committer time and parents of a commit; None when it cannot be read (a shallow edge, a missing object).
fn commit(store: &Store, sha: &str) -> Option<(i64, Vec<String>)> {
    let (kind, data) = store.read(sha)?;
    (kind == Kind::Commit).then_some(())?;
    let (mut time, mut parents) = (None, Vec::new());
    for l in data.split(|&b| b == b'\n').take_while(|l| !l.is_empty()) {
        if let Some(p) = l.strip_prefix(b"parent ") {
            parents.push(String::from_utf8_lossy(p).into_owned());
        } else if let Some(c) = l.strip_prefix(b"committer ") {
            // `<name> <email> <seconds> <zone>`
            time = c.rsplitn(3, |&b| b == b' ').nth(1).and_then(|t| std::str::from_utf8(t).ok()?.parse().ok());
        }
    }
    Some((time?, parents))
}

struct Node {
    flags: u8,
    time: i64,
    parents: Vec<String>,
    queued: bool,
}

/// Git's merge-base paint, newest commit first: OWN spreads from HEAD, BASE from the base; a commit
/// carrying BASE is stale. The walk ends when no queued commit can still turn out to be HEAD's own.
struct Walk {
    store: Store,
    nodes: HashMap<String, Node>,
    heap: BinaryHeap<(i64, String)>,
    /// Queued commits without BASE.
    live: usize,
}

impl Walk {
    /// Adds `flag` to a commit, queueing it when that changes what it carries.
    fn mark(&mut self, sha: &str, flag: u8) {
        if !self.nodes.contains_key(sha) {
            let Some((time, parents)) = commit(&self.store, sha) else { return };
            self.nodes.insert(sha.to_string(), Node { flags: 0, time, parents, queued: false });
        }
        let Some(n) = self.nodes.get_mut(sha) else { return };
        if n.flags | flag == n.flags {
            return;
        }
        let was_live = n.queued && n.flags & BASE == 0;
        n.flags |= flag;
        if !n.queued {
            n.queued = true;
            self.heap.push((n.time, sha.to_string()));
        }
        let is_live = n.flags & BASE == 0;
        self.live = self.live + usize::from(is_live) - usize::from(was_live);
    }
}

/// Committer time of the earliest commit reachable from `head` and not from `base`; None when there is
/// none, or the walk passes its limit.
pub fn first_own_commit(repo: &Repo, head: &str, base: &str) -> Option<i64> {
    let mut w = Walk { store: Store::open(repo), nodes: HashMap::new(), heap: BinaryHeap::new(), live: 0 };
    w.mark(base, BASE);
    // An unreadable base (shallow, pruned) would make all of HEAD's history its own: judge no commits.
    w.nodes.contains_key(base).then_some(())?;
    w.mark(head, OWN);
    let mut first: Option<i64> = None;
    for _ in 0..MAX_COMMITS {
        if w.live == 0 {
            return first;
        }
        let (time, sha) = w.heap.pop()?;
        let Some(n) = w.nodes.get_mut(&sha) else { continue };
        n.queued = false;
        let (flags, parents) = (n.flags, n.parents.clone());
        if flags & BASE == 0 {
            w.live -= 1;
            first = Some(first.map_or(time, |f| f.min(time)));
        }
        for p in &parents {
            w.mark(p, flags);
        }
    }
    None
}

/// Modification time (ns) of the oldest changed or untracked path outside `.factory/`, as `git status`
/// lists them; a deleted path counts by its folder's time. None when the tree is clean or Git cannot run.
pub fn worktree_first(repo: &Repo) -> Option<u128> {
    let out = super::command(repo)
        .args(["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames", "--ignore-submodules=all"])
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .output()
        .ok()?;
    out.status.success().then_some(())?;
    out.stdout
        .split(|&b| b == 0)
        .filter(|r| r.len() > 3)
        .filter_map(|r| {
            let path = String::from_utf8_lossy(&r[3..]);
            if path.split('/').any(|c| c == ".factory") {
                return None;
            }
            let p = repo.work.join(path.as_ref());
            crate::paths::mtime_ns(&p).or_else(|| crate::paths::mtime_ns(p.parent()?))
        })
        .min()
}
