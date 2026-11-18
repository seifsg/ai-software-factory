//! `factory closeout [<pr>] [--dry-run]`: after the owner merges a run's PR, proves the merge, checks the
//! run's ticket records it, and removes what the run created. Safe to rerun; refuses an unmerged PR.
//!   facts   the PR and ticket, read from `gh` JSON
//!   ticket  closed, PR link, merge commit
//!   stop    what step 8 left running, by its recorded stop command, except the owner's preview
//!   clean   `.factory/` worktrees, their branches and the PR branch, `.factory/` temp
//! It runs only when the owner says so after merging: the owner watches the run's result first.

pub mod clean;
pub mod facts;
pub mod stop;
pub mod ticket;

use clean::Line;
use facts::{Issue, Pr};
use std::path::Path;

const USAGE: &str = "usage: factory closeout [<pr number|url>] [--dry-run]";

/// The ticket line's verdict.
#[derive(Debug, PartialEq, Eq)]
pub enum Ticket {
    Ok(String),
    Needs(String, Vec<&'static str>),
    /// Another tracker or a local ticket: the agent checks it by `ticketing`.
    ByHand(String),
}

/// What a run file's header says: ticket link, `Status: open`, the `Left running:` line's items.
#[derive(Debug, Default)]
pub struct Header {
    pub ticket: String,
    pub open: bool,
    pub left: String,
    /// The `## 7 PR` block: it names the run's PR.
    pub pr_block: String,
}

impl Header {
    /// Reads `# Run: <link> · ...`, the header's `Status:`, the `## 7 PR` block and the last `Left running:` line.
    pub fn parse(text: &str) -> Header {
        let (mut h, mut seen, mut in_pr) = (Header::default(), false, false);
        for l in text.lines() {
            if l.starts_with("## ") {
                in_pr = l.starts_with("## 7 PR");
            } else if in_pr {
                h.pr_block.push_str(l);
                h.pr_block.push('\n');
            }
            if let Some(r) = l.strip_prefix("# Run: ") {
                h.ticket = r.split(" · ").next().unwrap_or("").trim().to_string();
            } else if let Some(s) = l.strip_prefix("Status: ").filter(|_| !seen) {
                (h.open, seen) = (s.trim().eq_ignore_ascii_case("open"), true);
            } else if let Some(x) = l.strip_prefix("Left running:") {
                h.left = x.trim().to_string();
            }
        }
        h
    }
}

/// The close-out of a merged PR in `run_dir`; `issue` is the fetched ticket when it is a GitHub issue.
/// Returns the report and whether everything is done. Refuses (Err) before any effect: see [`check`].
pub fn run(run_dir: &Path, head: &Header, pr: &Pr, issue: Option<&Issue>, dry: bool) -> Result<(String, bool), String> {
    check(head, pr)?;
    let t = match issue {
        Some(i) => match ticket::missing(pr, i) {
            m if m.is_empty() => Ticket::Ok(i.url.clone()),
            m => Ticket::Needs(i.url.clone(), m),
        },
        None => Ticket::ByHand(head.ticket.clone()),
    };
    let mut lines = Vec::new();
    // Processes first: a server may hold files under `.factory/`.
    let left = stop::stop(run_dir, &head.left, dry, &mut lines);
    if !dry && !head.left.is_empty() && left != head.left {
        set_left(run_dir, &left)?;
    }
    clean::clean(run_dir, pr, dry, &mut lines)?;
    Ok(report(&t, &lines, dry))
}

/// Err unless the close-out may act: the PR is merged, the run is closed or stopped (an open run owns its
/// state, and its header may be a newer run's), and the run file names the PR (step 7 records it).
pub fn check(head: &Header, pr: &Pr) -> Result<(), String> {
    pr.require_merged()?;
    if head.open {
        return Err("the run is still open: finish or stop it first".into());
    }
    if !ticket::cites(&head.pr_block, &pr.url) {
        return Err(format!("{} is not in run.md's `## 7 PR` block: not this run's PR", pr.url));
    }
    Ok(())
}

/// Rewrites the run file's last `Left running:` line to `value`: what still runs after the stops.
fn set_left(run_dir: &Path, value: &str) -> Result<(), String> {
    let p = run_dir.join(".factory/run.md");
    let text = std::fs::read_to_string(&p).map_err(|e| format!("run.md: {e}"))?;
    let i = text.rfind("\nLeft running:").ok_or("run.md lost its Left running: line")? + 1;
    let end = text[i..].find('\n').map_or(text.len(), |n| i + n);
    let cr = if text[..end].ends_with('\r') { "\r" } else { "" };
    let new = format!("{}Left running: {value}{cr}{}", &text[..i], &text[end..]);
    crate::paths::write_atomic(&p, new.as_bytes()).map_err(|e| format!("run.md: {e}"))
}

/// The report: ticket line, one line per item, then the verdict line.
fn report(t: &Ticket, lines: &[Line], dry: bool) -> (String, bool) {
    let mut s = match t {
        Ticket::Ok(u) => format!("ticket: ok ({u})\n"),
        Ticket::Needs(u, m) => format!("ticket: needs {} ({u}): record it per `ticketing`, then rerun\n", m.join(", ")),
        Ticket::ByHand(l) => format!("ticket: by hand ({l}): check closed + PR link + merge commit per `ticketing`\n"),
    };
    let verb = if dry { "would remove" } else { "removed" };
    for l in lines {
        match l {
            Line::Removed(x) => s.push_str(&format!("{verb}: {x}\n")),
            Line::Kept(x, why) => s.push_str(&format!("kept: {x} ({why})\n")),
            Line::Blocked(x, why) => s.push_str(&format!("blocked: {x} ({why})\n")),
        }
    }
    let done = !matches!(t, Ticket::Needs(..)) && !lines.iter().any(|l| matches!(l, Line::Blocked(..)));
    let verdict = if done { "done" } else { "incomplete (act on each blocked: and ticket: needs line, then rerun)" };
    s.push_str(&if dry { format!("closeout: dry run, would be {verdict}\n") } else { format!("closeout: {verdict}\n") });
    (s, done)
}

/// `factory closeout [<pr>] [--dry-run]`: exit 0 done, 1 incomplete or refused, 2 usage.
pub fn cli(args: &[&str]) -> u8 {
    let dry = args.contains(&"--dry-run");
    let rest: Vec<&str> = args.iter().copied().filter(|a| *a != "--dry-run").collect();
    if rest.len() > 1 || rest.iter().any(|a| a.starts_with('-')) {
        eprintln!("{USAGE}");
        return 2;
    }
    let cwd = std::env::current_dir().unwrap_or_default();
    match fetch_and_run(&cwd, rest.first().copied(), dry) {
        Ok((text, done)) => {
            print!("{text}");
            u8::from(!done)
        }
        Err(e) => {
            println!("closeout: refused ({e})");
            1
        }
    }
}

/// Finds the run, reads the PR and ticket through `gh`, then closes out.
fn fetch_and_run(cwd: &Path, pr_arg: Option<&str>, dry: bool) -> Result<(String, bool), String> {
    let dir = crate::run::locate::walk(cwd).ok_or("no .factory/run.md from this folder")?;
    let run_dir = Path::new(&dir);
    let head = Header::parse(&std::fs::read_to_string(run_dir.join(".factory/run.md")).map_err(|e| format!("run.md: {e}"))?);
    let mut args = vec!["pr", "view"];
    args.extend(pr_arg);
    let pr = Pr::parse(&facts::gh(run_dir, &args, facts::PR_FIELDS)?)?;
    check(&head, &pr)?;
    let issue = match ticket::github_issue(&head.ticket) {
        Some(u) => Some(Issue::parse(&facts::gh(run_dir, &["issue", "view", u], facts::ISSUE_FIELDS)?)?),
        None => None,
    };
    run(run_dir, &head, &pr, issue.as_ref(), dry)
}
