//! Time blocks: where a run's wall time went, stamped by the guard, receipts and the queue at no model cost,
//! printed in the owner's bar format by `factory time` and carried by the guard's step 6 and 8 replies.
//! Format and rules: `docs/time-blocks.md`.

mod bench;
mod block;
pub mod phase;
mod resume;
mod split;
pub mod stamp;

pub use phase::Phase;
use stamp::Row;
use std::path::{Path, PathBuf};

/// A run's split and what the block needs to print it.
pub struct Report {
    pub dir: PathBuf,
    pub title: String,
    pub open: bool,
    split: split::Split,
}

impl Report {
    pub fn block(&self) -> String {
        block::text(&self.split)
    }

    pub fn json(&self) -> serde_json::Value {
        block::json(&self.split, self.open)
    }

    /// Upserts the run's row in the project's bench table; the error says why it could not.
    pub fn bench(&self) -> Result<PathBuf, String> {
        bench::upsert(&self.dir, &self.title, &self.split, self.open)
    }
}

/// The header lines the clock reads: run title (`# Run:` up to its first ` · `), Status, Waiting.
struct Header {
    title: String,
    status: String,
    waiting: String,
}

fn header(dir: &Path) -> Option<Header> {
    let text = std::fs::read_to_string(dir.join(".factory/run.md")).ok()?;
    let get = |p: &str| text.lines().find_map(|l| l.strip_prefix(p)).unwrap_or_default().trim().to_string();
    let title = get("# Run:");
    let title = title.split(" · ").next().unwrap_or_default().to_string();
    Some(Header { title, status: get("Status:"), waiting: get("Waiting:") })
}

fn guard(dir: &Path) -> PathBuf {
    dir.join(".factory/guard")
}

/// The run folder from `start` up, when its run is open.
fn open_run(start: &Path) -> Option<PathBuf> {
    let dir = PathBuf::from(crate::run::locate::walk(start)?);
    (header(&dir)?.status == "open").then_some(dir)
}

/// The last wait, resume or end row: whether the run's clock is in a wait now, and since when.
fn waiting_since(rows: &[Row]) -> Option<(u64, bool)> {
    rows.iter().rev().find_map(|r| match r {
        Row::Wait { at, owner, .. } => Some(Some((*at, *owner))),
        Row::Resume { .. } | Row::End { .. } => Some(None),
        _ => None,
    })?
}

/// The run's report; None when the folder holds no run or the run has no stamp yet.
pub fn report(dir: &Path) -> Option<Report> {
    let h = header(dir)?;
    let g = guard(dir);
    let open = h.status == "open";
    let now = crate::paths::now();
    let until = if open { now } else { last_write(dir, now) };
    let split = split::split(&stamp::steps(&g), &stamp::read(&g), Some(until))?;
    Some(Report { dir: dir.to_path_buf(), title: h.title, open, split })
}

/// The report with the bench row written: what `factory time` and the guard's replies show.
pub fn publish(dir: &Path) -> Option<Report> {
    let r = report(dir)?;
    if let Err(e) = r.bench() {
        eprintln!("factory time: bench table not updated: {e}");
    }
    Some(r)
}

/// A command the session ran itself (`guard step`, `guard wait`): it is back, so an open wait ends now.
pub fn active(start: &Path) {
    let Some(dir) = open_run(start) else { return };
    let g = guard(&dir);
    if waiting_since(&stamp::read(&g)).is_some() {
        stamp::append(&g, &Row::Resume { at: crate::paths::now() });
    }
}

/// A suite or queue span that just ended, for the open run `from` belongs to.
pub fn span(from: &Path, phase: Phase, start: u64, end: u64, note: &str) {
    if let Some(dir) = open_run(from) {
        stamp::append(&guard(&dir), &Row::Span { from: start.min(end), to: end, phase, note: note.to_string() });
    }
}

/// After the Stop hook decided: a resume the transcript shows, then the turn's end as a wait (owner or idle),
/// or the run's end once it is closed. A blocked stop ends no turn; a running subagent will wake the session.
pub fn on_stop(input: &crate::hook::Input, reply: Option<&crate::hook::Reply>, start: &Path) {
    let from = Some(PathBuf::from(crate::paths::norm(&input.cwd)))
        .filter(|p| !input.cwd.is_empty() && p.is_dir())
        .unwrap_or_else(|| start.to_path_buf());
    let Some(dir) = crate::run::locate::walk(&from).map(PathBuf::from) else { return };
    let (Some(h), g) = (header(&dir), guard(&dir)) else { return };
    let mut rows = stamp::read(&g);
    let now = crate::paths::now();
    let blocked = matches!(reply, Some(crate::hook::Reply::Block(_)));
    if h.status != "open" {
        // A run closed before this Stop ended when its run file last changed, never at this later hook call.
        let ended = rows.iter().any(|r| matches!(r, Row::End { .. }));
        if h.status == "closed" && !ended && !blocked && g.join("steps.jsonl").is_file() {
            stamp::append(&g, &Row::End { at: last_write(&dir, now) });
            let _ = publish(&dir);
        }
        return;
    }
    let tp = &input.transcript_path;
    if let Some(back) = resume_due(&rows, &stamp::steps(&g), tp, now) {
        let row = Row::Resume { at: back };
        stamp::append(&g, &row);
        rows.push(row);
    }
    if blocked || input.subagent_running {
        return;
    }
    let open_wait = waiting_since(&rows);
    let owner = h.waiting.strip_prefix("owner:").map(str::trim);
    let why = owner.map(str::to_string).unwrap_or_else(|| match h.waiting.as_str() {
        "none" | "" => "turn ended with nothing running".to_string(),
        w => w.to_string(),
    });
    // A second stop inside the same wait adds nothing: the open row already covers it.
    if open_wait.is_none_or(|(_, was_owner)| was_owner != owner.is_some()) {
        stamp::append(&g, &Row::Wait { at: now, owner: owner.is_some(), off: resume::len(tp), why });
    }
}

/// The transcript's first entry after the last wait, when it comes before whatever closes that wait now (a
/// `guard step` call stamps its resume late, after the session already worked).
fn resume_due(rows: &[Row], steps: &[(u64, String)], transcript: &str, now: u64) -> Option<u64> {
    let i = rows.iter().rposition(|r| matches!(r, Row::Wait { .. }))?;
    let Row::Wait { at, off, .. } = &rows[i] else { return None };
    let later = rows[i + 1..].iter().filter_map(|r| match r {
        Row::Wait { at: t, .. } | Row::Resume { at: t } | Row::End { at: t } => Some(*t),
        _ => None,
    });
    let close = later.chain(steps.iter().map(|s| s.0).filter(|t| t > at)).min();
    let back = resume::first_after(transcript, *at, *off).filter(|t| *t < now)?;
    close.is_none_or(|c| back < c).then_some(back)
}

/// The run file's last write in Unix seconds, never later than `now`.
fn last_write(dir: &Path, now: u64) -> u64 {
    crate::paths::mtime_ns(&dir.join(".factory/run.md")).map_or(now, |ns| u64::try_from(ns / 1_000_000_000).unwrap_or(now)).min(now)
}

/// `factory time [<run folder>] [--json]` and `factory time lost <phase> <XmYYs> <cause>`.
pub fn cli(args: &[&str]) -> u8 {
    const USAGE: &str = "usage: factory time [<run folder>] [--json] | factory time lost <owner|plan|build|tests|review|publish|queue|idle> <XmYYs> <cause>";
    match args {
        ["lost", phase, d, why @ ..] if !why.is_empty() => lost(phase, d, &why.join(" ")),
        ["lost", ..] => {
            eprintln!("{USAGE}");
            2
        }
        _ => {
            let json = args.contains(&"--json");
            let rest: Vec<&str> = args.iter().copied().filter(|a| *a != "--json").collect();
            let start = match rest.as_slice() {
                [] => crate::guard::cwd(),
                [d] if !d.starts_with('-') => PathBuf::from(crate::paths::norm(d)),
                _ => {
                    eprintln!("{USAGE}");
                    return 2;
                }
            };
            let Some(dir) = crate::run::locate::walk(&start) else {
                eprintln!("factory time: no .factory/run.md from {}", crate::paths::text(&start));
                return 1;
            };
            let Some(r) = publish(Path::new(&dir)) else {
                eprintln!("factory time: {dir} has no stamps yet (`factory guard begin` records the start)");
                return 1;
            };
            if json {
                println!("{}", r.json())
            } else {
                print!("{}", r.block())
            }
            0
        }
    }
}

/// Adds lost time with a cause only the agent knows (a failed toolchain path): shown on that phase's row.
fn lost(phase: &str, d: &str, why: &str) -> u8 {
    let (Some(p), Some(secs)) = (Phase::from_id(phase), block::parse_dur(d)) else {
        eprintln!("factory time lost: phase is one of owner, plan, build, tests, review, publish, queue, idle; time like 11m03s");
        return 2;
    };
    let Some(dir) = open_run(&crate::guard::cwd()) else {
        eprintln!("factory time lost: no open run from this folder");
        return 1;
    };
    stamp::append(&guard(&dir), &Row::Lost { phase: p, secs, why: why.replace(['\n', '\r'], " ") });
    println!("lost {} in {}: {why}", block::dur(secs), p.label());
    0
}

#[cfg(test)]
mod tests;
