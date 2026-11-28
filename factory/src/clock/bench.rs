//! The project's bench table across runs: one row per run under `## Factory runs` in the main checkout's
//! `.factory/bench.md` (worktrees of one project share it), upserted by the run's start time. Every other line
//! of the file is kept as it is.

use super::block::dur;
use super::phase::Phase;
use super::split::Split;
use std::path::{Path, PathBuf};

const HEADING: &str = "## Factory runs";
const HEAD: &str = "| Start (UTC) | Run | End (UTC) | Total | Waiting on you | Plan | Build | Tests + CI | Review + gates | Publish | Queue | Idle | Lost | Full-suite runs |";

/// The bench file of the project the run folder belongs to.
pub fn file(run_dir: &Path) -> PathBuf {
    // A linked worktree names the shared Git folder as `<gitdir>/../..`: resolve it, then take the checkout holding it.
    let main = crate::git::Repo::discover(run_dir)
        .and_then(|r| std::fs::canonicalize(&r.common).ok())
        .map(|c| PathBuf::from(c.to_string_lossy().trim_start_matches(r"\\?\").to_string()))
        .and_then(|c| c.file_name().is_some_and(|n| n == ".git").then(|| c.parent().map(Path::to_path_buf)).flatten())
        .unwrap_or_else(|| run_dir.to_path_buf());
    main.join(".factory/bench.md")
}

/// Writes this run's row (atomic, under a lock beside the file, so two worktrees never lose a row).
pub fn upsert(run_dir: &Path, title: &str, x: &Split, open: bool) -> Result<PathBuf, String> {
    let path = file(run_dir);
    let dir = path.parent().ok_or("bench file has no folder")?;
    std::fs::create_dir_all(dir).map_err(|e| format!("cannot create {}: {e}", crate::paths::text(dir)))?;
    let _lock = crate::machine::Lock::take(path.with_extension("md.lock"))?;
    let old = std::fs::read_to_string(&path).unwrap_or_default();
    // A hand-kept file keeps its line endings.
    let new = with_row(&old.replace("\r\n", "\n"), &row(title, x, open));
    let new = if old.contains("\r\n") { new.replace('\n', "\r\n") } else { new };
    if new != old {
        crate::paths::write_atomic(&path, new.as_bytes()).map_err(|e| format!("cannot write {}: {e}", crate::paths::text(&path)))?;
    }
    Ok(path)
}

fn row(title: &str, x: &Split, open: bool) -> String {
    let iso = crate::receipt::utc_iso;
    let cell = |p: Phase| match x.secs[p as usize] {
        0 => "0".to_string(),
        s => dur(s),
    };
    let lost: u64 = x.lost.iter().sum();
    let title = title.replace(['|', '\n', '\r'], "/");
    let end = if open { "open".to_string() } else { iso(x.end) };
    let mut cells = vec![iso(x.start), title, end, dur(x.end - x.start)];
    cells.extend(Phase::ALL.into_iter().map(cell));
    cells.extend([if lost == 0 { "0".into() } else { dur(lost) }, x.full_runs.to_string()]);
    format!("| {} |", cells.join(" | "))
}

/// The file text with `row` replacing the row of the same start, else added at the end of the section's table.
fn with_row(old: &str, row: &str) -> String {
    let key = &row[..row[2..].find(" |").map_or(row.len(), |i| i + 2)];
    let mut lines: Vec<String> = old.lines().map(String::from).collect();
    let Some(h) = lines.iter().position(|l| l == HEADING) else {
        let mut out = if old.is_empty() { "# Bench\n".to_string() } else { format!("{}\n", old.trim_end_matches('\n')) };
        out.push_str(&format!("\n{HEADING}\n\n{HEAD}\n{}\n{row}\n", sep()));
        return out;
    };
    let end = lines[h + 1..].iter().position(|l| l.starts_with("## ")).map_or(lines.len(), |i| h + 1 + i);
    if let Some(i) = (h + 1..end).find(|&i| lines[i].starts_with(key) && lines[i][key.len()..].starts_with(" |")) {
        lines[i] = row.to_string();
    } else if let Some(last) = (h + 1..end).rev().find(|&i| lines[i].starts_with('|')) {
        lines.insert(last + 1, row.to_string());
    } else {
        lines.splice(h + 1..h + 1, ["".to_string(), HEAD.to_string(), sep(), row.to_string()]);
    }
    lines.join("\n") + "\n"
}

fn sep() -> String {
    format!("|{}", "---|".repeat(HEAD.matches(" | ").count() + 1))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn keeps_other_lines_and_replaces_its_own_row() {
        let mut x = Split { start: 0, end: 90, ..Split::default() };
        x.secs[Phase::Build as usize] = 90;
        let hand = "# Bench: one task at a time\n\n| # | Task |\n|---|---|\n| 1 | typed |\n\nFound: a note.\n";
        let one = with_row(hand, &row("t|1", &x, true));
        assert!(one.starts_with(hand) && one.contains("\n## Factory runs\n\n| Start (UTC) |"));
        assert!(one.ends_with("| 1970-01-01T00:00:00Z | t/1 | open | 1m30s | 0 | 0 | 1m30s | 0 | 0 | 0 | 0 | 0 | 0 | 0 |\n"));
        x.end = 120;
        x.secs[Phase::Build as usize] = 120;
        let two = with_row(&one, &row("t|1", &x, false));
        assert_eq!(two.matches("| 1970-01-01T00:00:00Z |").count(), 1);
        assert!(two.contains("| 1970-01-01T00:02:00Z | 2m00s |") && two.starts_with(hand));
        let other = Split { start: 5, end: 6, ..Split::default() };
        let three = with_row(&two, &row("u", &other, false));
        assert!(three.find("00:00:00Z | t/1").unwrap() < three.find("00:00:05Z | u").unwrap());
        assert_eq!(sep().matches("---|").count(), HEAD.matches('|').count() - 1);
    }
}
