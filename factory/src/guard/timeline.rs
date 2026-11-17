//! Record real phase starts without requiring the reporting add-on or any host transcript.

use super::step::STEPS;
use serde_json::{Value, json};
use std::fs::{self, OpenOptions};
use std::io::{self, Write};
use std::path::Path;

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
}
