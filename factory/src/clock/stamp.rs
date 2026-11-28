//! The run's time stamps, `.factory/guard/time.jsonl`: one JSON object per line, appended, never rewritten.
//! Step starts stay in `steps.jsonl` (the guard's timeline); this file holds what steps cannot show.

use super::phase::Phase;
use serde_json::{Value, json};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;

pub const FILE: &str = "time.jsonl";

/// One stamp. Waits run until the next resume, wait, end or step start; spans are written once, at their end.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Row {
    Wait { at: u64, owner: bool, why: String },
    Resume { at: u64 },
    End { at: u64 },
    Span { from: u64, to: u64, phase: Phase, note: String },
    Lost { phase: Phase, secs: u64, why: String },
}

impl Row {
    fn value(&self) -> Value {
        let iso = crate::receipt::utc_iso;
        match self {
            Row::Wait { at, owner, why } => json!({ "at": iso(*at), "wait": if *owner { "owner" } else { "idle" }, "why": why }),
            Row::Resume { at } => json!({ "at": iso(*at), "resume": true }),
            Row::End { at } => json!({ "at": iso(*at), "end": true }),
            Row::Span { from, to, phase, note } => json!({ "from": iso(*from), "to": iso(*to), "span": phase.id(), "note": note }),
            Row::Lost { phase, secs, why } => json!({ "lost": phase.id(), "secs": secs, "why": why }),
        }
    }

    /// The row a line holds; None for a torn, edited or unknown line (skipped, never guessed).
    fn parse(line: &str) -> Option<Row> {
        let v: Value = serde_json::from_str(line).ok()?;
        let at = || v.get("at").and_then(Value::as_str).and_then(iso_secs);
        let why = || v.get("why").and_then(Value::as_str).unwrap_or_default().to_string();
        if let Some(kind) = v.get("wait").and_then(Value::as_str) {
            return Some(Row::Wait { at: at()?, owner: kind == "owner", why: why() });
        }
        if v.get("resume").is_some() {
            return Some(Row::Resume { at: at()? });
        }
        if v.get("end").is_some() {
            return Some(Row::End { at: at()? });
        }
        if let Some(phase) = v.get("span").and_then(Value::as_str).and_then(Phase::from_id) {
            let t = |k: &str| v.get(k).and_then(Value::as_str).and_then(iso_secs);
            let (from, to) = (t("from")?, t("to")?);
            let note = v.get("note").and_then(Value::as_str).unwrap_or_default().to_string();
            return (from <= to).then_some(Row::Span { from, to, phase, note });
        }
        let phase = v.get("lost").and_then(Value::as_str).and_then(Phase::from_id)?;
        Some(Row::Lost { phase, secs: v.get("secs")?.as_u64()?, why: why() })
    }
}

/// Every readable row of the guard folder's stamp file, in file order.
pub fn read(guard: &Path) -> Vec<Row> {
    fs::read_to_string(guard.join(FILE)).unwrap_or_default().lines().filter_map(Row::parse).collect()
}

/// Appends one row. Why lenient: a stamp must never fail the hook or command that writes it.
pub fn append(guard: &Path, row: &Row) {
    let line = format!("{}\n", row.value());
    let done = fs::create_dir_all(guard)
        .and_then(|()| OpenOptions::new().create(true).append(true).open(guard.join(FILE))?.write_all(line.as_bytes()));
    if let Err(e) = done {
        eprintln!("factory time: cannot stamp {}: {e}", crate::paths::text(&guard.join(FILE)));
    }
}

/// Step starts from the guard's `steps.jsonl`: `(at, step)` in file order.
pub fn steps(guard: &Path) -> Vec<(u64, String)> {
    let text = fs::read_to_string(guard.join("steps.jsonl")).unwrap_or_default();
    text.lines()
        .filter_map(|l| {
            let v: Value = serde_json::from_str(l).ok()?;
            Some((iso_secs(v.get("at")?.as_str()?)?, v.get("step")?.as_str()?.to_string()))
        })
        .collect()
}

/// Unix seconds of `YYYY-MM-DDTHH:MM:SS` (fraction and `Z` ignored): the inverse of `receipt::utc_iso`.
pub fn iso_secs(s: &str) -> Option<u64> {
    let b = s.as_bytes();
    if b.len() < 19 || b[4] != b'-' || b[7] != b'-' || b[10] != b'T' || b[13] != b':' || b[16] != b':' {
        return None;
    }
    let n = |r: std::ops::Range<usize>| s.get(r)?.parse::<i64>().ok();
    let (y, m, d, hh, mm, ss) = (n(0..4)?, n(5..7)?, n(8..10)?, n(11..13)?, n(14..16)?, n(17..19)?);
    if !(1..=12).contains(&m) || !(1..=31).contains(&d) || hh > 23 || mm > 59 || ss > 60 {
        return None;
    }
    // Days from civil (proleptic Gregorian), the same calendar `utc_iso` writes.
    let y = if m <= 2 { y - 1 } else { y };
    let era = y.div_euclid(400);
    let yoe = y - era * 400;
    let doy = (153 * (if m > 2 { m - 3 } else { m + 9 }) + 2) / 5 + d - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    let days = era * 146_097 + doe - 719_468;
    u64::try_from(days * 86_400 + hh * 3600 + mm * 60 + ss).ok()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn iso_round_trips_and_rejects_junk() {
        for t in [0u64, 951_782_400, 1_795_000_000, 4_102_444_799] {
            assert_eq!(iso_secs(&crate::receipt::utc_iso(t)), Some(t));
        }
        assert_eq!(iso_secs("2026-11-27T07:40:54.123Z"), iso_secs("2026-11-27T07:40:54Z"));
        assert!(iso_secs("2026-13-01T00:00:00Z").is_none() && iso_secs("nope").is_none() && iso_secs("").is_none());
    }

    #[test]
    fn rows_round_trip_and_bad_lines_are_skipped() {
        let dir = std::env::temp_dir().join(format!("factory-stamp-{}", std::process::id()));
        let rows = [
            Row::Wait { at: 10, owner: true, why: "plan OK?".into() },
            Row::Resume { at: 20 },
            Row::Span { from: 30, to: 40, phase: Phase::Tests, note: "full".into() },
            Row::Lost { phase: Phase::Build, secs: 5, why: "x".into() },
            Row::End { at: 50 },
        ];
        for r in &rows {
            append(&dir, r);
        }
        let mut f = OpenOptions::new().append(true).open(dir.join(FILE)).unwrap();
        f.write_all(b"{\"at\":\"x\",\"wait\":\"owner\"}\n{torn\n{\"from\":\"1970-01-01T00:00:09Z\",\"to\":\"1970-01-01T00:00:01Z\",\"span\":\"tests\"}\n").unwrap();
        assert_eq!(read(&dir), rows);
        let _ = fs::remove_dir_all(dir);
    }
}
