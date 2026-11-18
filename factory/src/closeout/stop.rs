//! The process half of a close-out: stops what step 8 left running, by the stop command the run recorded,
//! except the item tagged `(owner preview)`. Then the `Left running:` line keeps only what was not stopped,
//! so a rerun stops nothing twice. Nothing here blocks `closeout: done`: a process the binary cannot prove
//! stopped is reported for the agent to check, never guessed at.
//! Line form: `Left running: <item> (stop: <sh command>); <item> (owner preview) (stop: <sh command>)` or `none`.

use super::clean::Line;
use std::path::Path;
use std::process::Stdio;
use std::time::{Duration, Instant};

const TAG: &str = "(owner preview)";
/// Marks an item whose stop failed: `<item> (stop failed: <cmd>)`, kept on the line, never run again.
const FAILED: &str = "(stop failed:";
const LIMIT: Duration = Duration::from_secs(30);

/// The items of a `Left running:` value. Items end with `)`, so they split at `); `: a stop command may
/// hold `; ` itself.
fn items(left: &str) -> Vec<&str> {
    let mut v = Vec::new();
    let mut rest = left.trim();
    while let Some(i) = rest.find("); ") {
        v.push(&rest[..=i]);
        rest = rest[i + 3..].trim_start();
    }
    v.push(rest);
    v.into_iter().map(str::trim).filter(|i| !i.is_empty() && *i != "none").collect()
}

/// One item's text and its stop command (empty when none was recorded).
fn split(item: &str) -> (&str, &str) {
    match item.rfind("(stop:") {
        Some(i) if item.ends_with(')') => (item[..i].trim(), item[i + 6..item.len() - 1].trim().trim_matches('`').trim()),
        _ => (item.trim(), ""),
    }
}

/// Runs `sh -c <cmd>` in `dir`, killed after 30 s; Err names why it failed. Git for Windows' `sh` would
/// rewrite `/PID`-style arguments into paths: path conversion is off.
fn exec(dir: &Path, cmd: &str) -> Result<(), String> {
    let mut child = crate::paths::quiet_command("sh")
        .args(["-c", cmd])
        .current_dir(dir)
        .env("MSYS_NO_PATHCONV", "1")
        .env("MSYS2_ARG_CONV_EXCL", "*")
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("sh: {e}"))?;
    let start = Instant::now();
    loop {
        match child.try_wait().map_err(|e| e.to_string())? {
            Some(s) if s.success() => return Ok(()),
            Some(s) => return Err(format!("stop exited {}", s.code().unwrap_or(-1))),
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
    let mut keep: Vec<String> = Vec::new();
    for item in items(left) {
        let (what, cmd) = split(item);
        let mut kept = item.to_string();
        let why = if what.contains(TAG) {
            "the owner's preview, never stopped".to_string()
        } else if what.contains(FAILED) {
            "its stop failed before: check it by hand, never rerun".to_string()
        } else if cmd.is_empty() {
            "no stop command recorded: stop it by hand if it still runs".to_string()
        } else if dry {
            String::new()
        } else {
            // A failed stop is never run again: a rerun could hit a reused pid.
            exec(run_dir, cmd)
                .err()
                .map(|e| {
                    kept = format!("{what} {FAILED} {cmd})");
                    format!("{e}: stop it by hand if it still runs")
                })
                .unwrap_or_default()
        };
        if why.is_empty() {
            out.push(Line::Removed(format!("running {what} (ran: {cmd})")));
        } else {
            out.push(Line::Kept(format!("running {what}"), why));
            keep.push(kept);
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
        assert_eq!(items("a (stop: kill 1; kill 2); b (stop: x)"), ["a (stop: kill 1; kill 2)", "b (stop: x)"]);
        assert!(items("none").is_empty() && items("").is_empty());
    }

    #[test]
    fn preview_stays_and_a_stopped_item_leaves_the_line() {
        let dir = std::env::temp_dir();
        let mut out = Vec::new();
        let left = stop(&dir, "preview :3000 (owner preview) (stop: false); api :8080 (stop: true); loose", false, &mut out);
        assert_eq!(left, "preview :3000 (owner preview) (stop: false); loose");
        assert_eq!(out[1], Line::Removed("running api :8080 (ran: true)".into()));
        assert!(matches!(&out[0], Line::Kept(_, w) if w.starts_with("the owner's preview")));
        assert!(matches!(&out[2], Line::Kept(_, w) if w.starts_with("no stop command")));
        let mut failed = Vec::new();
        assert_eq!(stop(&dir, "gone (stop: exit 3)", false, &mut failed), "gone (stop failed: exit 3)");
        let mut again = Vec::new();
        assert_eq!(stop(&dir, "gone (stop failed: exit 3)", false, &mut again), "gone (stop failed: exit 3)");
        assert!(matches!(&again[0], Line::Kept(_, w) if w.starts_with("its stop failed before")), "never run twice");
        assert!(matches!(&failed[0], Line::Kept(_, w) if w.starts_with("stop exited 3")));
    }
}
