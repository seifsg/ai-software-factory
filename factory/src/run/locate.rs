//! Finds this session's run: a step block's `Workspace` (it rebinds), the session's link file, then the
//! nearest `.factory/run.md` inside the checkout. A bound session reaches a run anywhere.

use crate::paths;
use std::path::{Path, PathBuf};

/// Step headings that open a factory block; any other heading is a normal message.
const STEPS: [&str; 10] =
    ["0 Ticket", "1 Analyze", "2 Recommend", "2b Challenge", "3 Plan", "4 Before", "5 Build", "6 Verify", "7 PR", "8 Review"];

/// What the search found.
#[derive(Debug, Default)]
pub struct Found {
    /// The run folder (holds `.factory/run.md`), in `C:/x` form; None when no run applies.
    pub dir: Option<String>,
    /// The turn's last message opens with a step heading.
    pub step_block: bool,
}

/// The text after `## ` when the message opens with a real step heading.
pub fn step_heading(msg: &str) -> Option<&str> {
    let h = msg.strip_prefix("## ")?;
    STEPS.iter().any(|s| h.starts_with(s)).then_some(h)
}

/// The step label of a message opening `## <0-8>[b] ` (the heading posted this turn), else empty.
pub fn posted_label(msg: &str) -> String {
    let Some(h) = msg.strip_prefix("## ") else { return String::new() };
    let Some((label, _)) = h.split_once(' ') else { return String::new() };
    let b = label.as_bytes();
    let ok = matches!(b, [d] | [d, b'b'] if (b'0'..=b'8').contains(d));
    if ok { label.to_string() } else { String::new() }
}

/// The session's link file: `<cache>/sessions/<id>`, only for ids of `[A-Za-z0-9_-]`.
pub fn session_file(session: &str) -> Option<PathBuf> {
    let ok = !session.is_empty() && session.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-');
    ok.then(|| paths::cache_dir().join("sessions").join(session))
}

/// Finds the run for a hook: Workspace, then the session link, then a walk from `start`.
/// `session` is the id used for the link file (unvalidated ids get none).
pub fn find(start: &Path, session: &str, msg: &str) -> Found {
    let heading = step_heading(msg);
    let link = session_file(session);
    let mut found = Found { dir: None, step_block: heading.is_some() };
    let mut bad = false;
    if let Some(h) = heading {
        match bind(h, link.as_deref()) {
            Bind::Bound(d) => found.dir = Some(d),
            Bind::Bad => bad = true,
            Bind::None => {}
        }
    }
    if found.dir.is_none() && !bad {
        if let Some(l) = &link {
            if let Some(d) = std::fs::read_to_string(l).ok().and_then(|t| t.lines().next().map(str::to_string)) {
                if run_at(&d) {
                    found.dir = Some(d);
                }
            }
        }
    }
    if found.dir.is_none() {
        found.dir = walk(start);
    }
    found.dir = found.dir.map(|d| paths::norm(&d));
    found
}

enum Bind {
    None,
    Bad,
    Bound(String),
}

/// Binds to the absolute folder a `**Workspace:** \`<dir>\`` names, if it holds a run file; writes the link.
fn bind(h: &str, link: Option<&Path>) -> Bind {
    const W: &str = "**Workspace:** `";
    let Some(i) = h.find(W) else { return Bind::None };
    let rest = &h[i + W.len()..];
    let w = rest.split('`').next().unwrap_or("").replace('\\', "/");
    if w.contains(['\'', '"', '$', '%']) || !paths::is_abs(&w) || !run_at(&w) {
        return Bind::Bad;
    }
    if let Some(l) = link {
        if let Some(dir) = l.parent() {
            let _ = std::fs::create_dir_all(dir);
            prune(dir);
        }
        let _ = std::fs::write(l, format!("{w}\n"));
    }
    Bind::Bound(w)
}

/// Removes link files older than 30 days.
fn prune(dir: &Path) {
    let Ok(rd) = std::fs::read_dir(dir) else { return };
    for e in rd.flatten() {
        let old = paths::age_secs(&e.path()).is_some_and(|a| a / 86_400 > 30);
        if old && e.file_type().is_ok_and(|t| t.is_file()) {
            let _ = std::fs::remove_file(e.path());
        }
    }
}

/// True when `<dir>/.factory/run.md` is a file.
fn run_at(dir: &str) -> bool {
    Path::new(&paths::norm(dir)).join(".factory/run.md").is_file()
}

/// Nearest folder holding `.factory/run.md`, from `start` up to the checkout top (a `.git` entry) or the root.
pub fn walk(start: &Path) -> Option<String> {
    let start = std::path::absolute(start).unwrap_or_else(|_| start.to_path_buf());
    let mut d = Some(start.as_path());
    while let Some(dir) = d {
        if dir.join(".factory/run.md").is_file() {
            return Some(paths::text(dir));
        }
        if dir.join(".git").exists() {
            return None;
        }
        d = dir.parent();
    }
    None
}
