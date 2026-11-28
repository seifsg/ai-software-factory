//! Record real phase starts without requiring the reporting add-on or any host transcript.

use super::step::STEPS;
use serde_json::{Value, json};
use std::fs::{self, OpenOptions};
use std::io::{self, Write};
use std::path::Path;

/// Record Ticket after the host creates the header, before its first post-step guard call.
pub(super) fn begin(start: &Path) -> u8 {
    begin_with(start, super::session::initialize)
}

/// Keep the phase clock test independent of the user's host session.
fn begin_with(start: &Path, initialize: impl FnOnce(&Path) -> Result<(), String>) -> u8 {
    let result = (|| -> Result<(), String> {
        let root = crate::run::locate::walk(start).ok_or("no .factory/run.md from this folder")?;
        let dir = Path::new(&root).join(".factory");
        let run = fs::read_to_string(dir.join("run.md")).map_err(|err| err.to_string())?;
        let header = crate::run::RunFile::parse(run.as_bytes());
        if run.lines().find(|line| line.starts_with("Status:")) != Some("Status: open") || !header.next.starts_with("0 Ticket ") {
            return Err("begin requires a new open run at Step 0".into());
        }
        initialize(Path::new(&root))?;
        // A new run counts chat posts from its own start: an older run's step stamp and written list go.
        if let Ok(rd) = fs::read_dir(dir.join("guard")) {
            for p in rd.flatten().map(|e| e.path()) {
                let name = p.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
                if name == "stepped" || name == "written" {
                    let _ = fs::remove_file(p);
                }
            }
        }
        save(&dir.join("guard"), "0", crate::paths::now()).map_err(|err| err.to_string())
    })();
    if let Err(err) = result {
        eprintln!("factory guard begin: {err}");
        return 1;
    }
    0
}

/// A pending checker keeps the work attributed to its step until the guard backs it.
pub(super) fn mark(guard: &Path, next: &str, gate: Option<char>, now: u64) {
    let step = match gate {
        Some('A') => "3",
        Some('B') => "6",
        Some('C' | 'R') => "8",
        _ => next.split_whitespace().next().unwrap_or_default(),
    };
    if index(step).is_none() {
        return;
    }
    if let Err(err) = save(guard, step, now) {
        eprintln!("factory guard: cannot record the step timeline: {err}");
    }
}

fn index(step: &str) -> Option<usize> {
    STEPS.iter().position(|(id, ..)| *id == step)
}

fn save(guard: &Path, step: &str, now: u64) -> io::Result<()> {
    let file = guard.join("steps.jsonl");
    let last = match fs::read_to_string(&file) {
        Ok(contents) => contents.lines().rev().find_map(|line| {
            let row: Value = serde_json::from_str(line).ok()?;
            index(row["step"].as_str()?)
        }),
        Err(err) if err.kind() == io::ErrorKind::NotFound => None,
        Err(err) => return Err(err),
    };
    let current = index(step).expect("step was validated");
    if last.is_some_and(|previous| previous == current || (current != 0 && previous > current)) {
        return Ok(());
    }
    let entry = format!("{}\n", json!({ "at": crate::receipt::utc_iso(now), "step": step }));
    fs::create_dir_all(guard)?;
    if current == 0 {
        // A new Ticket starts a new clock: the last run's time stamps go with its step starts.
        let _ = fs::remove_file(guard.join(crate::clock::stamp::FILE));
        crate::paths::write_atomic(&file, entry.as_bytes())
    } else {
        OpenOptions::new().create(true).append(true).open(file)?.write_all(entry.as_bytes())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn waits_for_gate_backing_and_resets_on_a_new_ticket() {
        let dir = std::env::temp_dir().join(format!("factory-timeline-test-{}", std::process::id()));
        mark(&dir, "0 Ticket", None, 1);
        mark(&dir, "3 Plan", None, 2);
        mark(&dir, "4 Before", Some('A'), 3);
        mark(&dir, "4 Before", None, 4);
        mark(&dir, "3 Plan", None, 5);
        let file = dir.join("steps.jsonl");
        let history = fs::read_to_string(&file).unwrap();
        let rows: Vec<Value> = history.lines().map(|line| serde_json::from_str(line).unwrap()).collect();
        assert_eq!(rows.iter().map(|row| row["step"].as_str().unwrap()).collect::<Vec<_>>(), ["0", "3", "4"]);
        assert_eq!(rows[2]["at"], crate::receipt::utc_iso(4));
        mark(&dir, "0 Ticket", None, 6);
        assert_eq!(fs::read_to_string(file).unwrap().lines().count(), 1);
        let _ = fs::remove_dir_all(dir);
    }

    #[test]
    fn start_is_recorded_before_ticket_and_later_steps_wait_for_the_owner() {
        let root = std::env::temp_dir().join(format!("factory-timeline-wait-{}", std::process::id()));
        let dir = root.join(".factory");
        std::fs::create_dir_all(&dir).unwrap();
        let run = dir.join("run.md");
        let input = crate::hook::Input::default();
        fs::write(&run, "# Run: test\nStatus: open\nNext: 0 Ticket · ticketing\nWaiting: none\n").unwrap();
        assert_eq!(begin_with(&root, |_| Ok(())), 0);
        let file = dir.join("guard/steps.jsonl");
        let first = fs::read_to_string(&file).unwrap();
        for waiting in ["owner: review", "none"] {
            fs::write(
                &run,
                format!("# Run: test\nStatus: open\nNext: 1 Analyze · analyze-start\nWaiting: {waiting}\n## 0 Ticket ✔\n"),
            )
            .unwrap();
            let _ = super::super::flow::run(&input, super::super::flow::Mode::Stop, &root);
            let current = fs::read_to_string(&file).unwrap();
            assert_eq!(current.lines().count(), if waiting == "none" { 2 } else { 1 });
            assert!(current.starts_with(&first));
        }
        let _ = fs::remove_dir_all(root);
    }
}
