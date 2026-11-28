//! `guard wait <none | owner: <question> | jobs: <what> (max <n> min)>`: sets the run file's `Waiting:` line in
//! one atomic write, so a coordinator never edits it by hand (no sed, no read-back).

use std::path::Path;

pub fn cli(args: &[&str]) -> u8 {
    let value = args.join(" ");
    let value = value.trim();
    if let Err(e) = valid(value) {
        eprintln!("factory guard wait: {e}. usage: factory guard wait none | owner: <question> | jobs: <what runs, who reports back> (max <n> min)");
        return 2;
    }
    let Some(dir) = crate::run::locate::walk(&super::cwd()) else {
        eprintln!("factory guard wait: no .factory/run.md from this folder");
        return 1;
    };
    let run = Path::new(&dir).join(".factory/run.md");
    let state = crate::run::state::State::load(&Path::new(&dir).join(".factory/guard/state"));
    let transcript = if let crate::run::state::Loaded::Valid(s) = &state { s.get("transcript").to_string() } else { String::new() };
    crate::clock::active(Path::new(&dir), &transcript);
    let text = match std::fs::read(&run).map(String::from_utf8) {
        Ok(Ok(t)) if !t.is_empty() => t,
        _ => {
            eprintln!("factory guard wait: {} is empty, unreadable or not UTF-8; left as it is", crate::paths::text(&run));
            return 1;
        }
    };
    let Some(updated) = set(&text, value) else {
        eprintln!("factory guard wait: the run file has no `Waiting:` line");
        return 1;
    };
    if let Err(e) = crate::paths::write_atomic(&run, updated.as_bytes()) {
        eprintln!("factory guard wait: cannot write {}: {e}", crate::paths::text(&run));
        return 1;
    }
    println!("Waiting: {value}");
    0
}

/// The three forms the run file allows; a jobs wait names its limit.
fn valid(v: &str) -> Result<(), String> {
    if v.contains(['\n', '\r']) {
        return Err("one line only".into());
    }
    if v == "none" {
        return Ok(());
    }
    if let Some(q) = v.strip_prefix("owner:") {
        return if q.trim().is_empty() { Err("an owner wait names its question".into()) } else { Ok(()) };
    }
    if let Some(j) = v.strip_prefix("jobs:") {
        // The guard reads the same limit: one it reads as 0 would fire the job deadline at once.
        let ok = !j.trim().is_empty() && crate::run::jobs_max(j) > 0;
        return if ok { Ok(()) } else { Err("a jobs wait names what runs and ends with `(max <n> min)`".into()) };
    }
    Err(format!("`{v}` is no wait form"))
}

/// The run file with its first `Waiting:` line replaced; None when it has none.
fn set(text: &str, value: &str) -> Option<String> {
    let mut lines: Vec<String> = text.lines().map(String::from).collect();
    let p = lines.iter().position(|l| l.starts_with("Waiting:"))?;
    lines[p] = format!("Waiting: {value}");
    Some(lines.join("\n") + "\n")
}

#[cfg(test)]
mod tests {
    use super::{set, valid};

    #[test]
    fn sets_the_first_waiting_line_only() {
        let run = "# Run: x\nStatus: open\nNext: 3 Plan\nWaiting: none\n\n## 3 Plan\nWaiting: keep\n";
        let out = set(run, "jobs: gate A checker (max 3 min)").unwrap();
        assert!(out.contains("Next: 3 Plan\nWaiting: jobs: gate A checker (max 3 min)\n") && out.contains("Waiting: keep"));
        assert!(set("# Run: x\n", "none").is_none());
    }

    #[test]
    fn only_the_run_file_forms() {
        assert!(valid("none").is_ok() && valid("owner: plan OK?").is_ok() && valid("jobs: suite (max 5 min)").is_ok());
        assert!(valid("owner:").is_err() && valid("jobs: suite").is_err() && valid("later").is_err());
        assert!(valid("jobs: x (max 0 min)").is_err() && valid("jobs: x (max x min)").is_err() && valid("owner: a\nb").is_err());
    }
}
