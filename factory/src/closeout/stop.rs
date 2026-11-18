//! The process half of a close-out: stops what step 8 left running, by the stop command the run recorded,
//! except the item tagged `(owner preview)`. Then the `Left running:` line keeps only what still runs, so a
//! rerun stops nothing twice.
//! Line form: `Left running: <item> (stop: <command>); <item> (owner preview) (stop: <command>)` or `none`.

use super::clean::Line;
use std::path::Path;
use std::process::Stdio;
use std::time::{Duration, Instant};

const TAG: &str = "(owner preview)";
const LIMIT: Duration = Duration::from_secs(30);

/// One `Left running:` item: its text and its stop command (empty when none was recorded).
fn split(item: &str) -> (&str, &str) {
    match item.rfind("(stop:") {
        Some(i) if item.ends_with(')') => (item[..i].trim(), item[i + 6..item.len() - 1].trim().trim_matches('`').trim()),
        _ => (item.trim(), ""),
    }
}

/// Runs `sh -c <cmd>` in `dir`, killed after 30 s; Err names why it failed.
fn exec(dir: &Path, cmd: &str) -> Result<(), String> {
    let mut child = crate::paths::quiet_command("sh")
        .args(["-c", cmd])
        .current_dir(dir)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("sh: {e}"))?;
    let start = Instant::now();
    loop {
        match child.try_wait().map_err(|e| e.to_string())? {
            Some(s) if s.success() => return Ok(()),
            Some(s) => return Err(format!("stop exit {}", s.code().unwrap_or(-1))),
            None if start.elapsed() > LIMIT => {
                let _ = child.kill();
                let _ = child.wait();
                return Err("stop timed out after 30 s".into());
            }
            None => std::thread::sleep(Duration::from_millis(50)),
        }
    }
}

/// Stops each item of `left` (the `Left running:` value) but the owner's preview; returns its lines and the
/// value the line keeps (`none` when nothing is left).
pub fn stop(run_dir: &Path, left: &str, dry: bool, out: &mut Vec<Line>) -> String {
    let mut keep = Vec::new();
    for item in left.split("; ").map(str::trim).filter(|i| !i.is_empty() && *i != "none") {
        let (what, cmd) = split(item);
        let res = if what.contains(TAG) {
            Err((String::from("the owner's, never stopped"), false))
        } else if cmd.is_empty() {
            Err((String::from("no stop command recorded"), true))
        } else if dry {
            Ok(())
        } else {
            exec(run_dir, cmd).map_err(|e| (e, true))
        };
        match res {
            Ok(()) => out.push(Line::Removed(format!("running {what} (ran: {cmd})"))),
            Err((why, blocks)) => {
                out.push(Line::Kept(format!("running {what}"), why, blocks));
                keep.push(item);
            }
        }
    }
    if keep.is_empty() { "none".into() } else { keep.join("; ") }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn items_split_into_text_and_command() {
        assert_eq!(split("dev server :5173 (stop: `npm stop`)"), ("dev server :5173", "npm stop"));
        assert_eq!(split("watcher (owner preview) (stop: kill 4)"), ("watcher (owner preview)", "kill 4"));
        assert_eq!(split("tail -f log"), ("tail -f log", ""));
    }

    #[test]
    fn preview_stays_and_a_stopped_item_leaves_the_line() {
        let dir = std::env::temp_dir();
        let mut out = Vec::new();
        let left = stop(&dir, "preview :3000 (owner preview) (stop: false); api :8080 (stop: true); loose", false, &mut out);
        assert_eq!(left, "preview :3000 (owner preview) (stop: false); loose");
        assert_eq!(out[1], Line::Removed("running api :8080 (ran: true)".into()));
        assert!(matches!(&out[0], Line::Kept(_, w, false) if w == "the owner's, never stopped"));
        assert!(matches!(&out[2], Line::Kept(_, w, true) if w == "no stop command recorded"));
        assert_eq!(stop(&dir, "none", false, &mut Vec::new()), "none");
    }
}
