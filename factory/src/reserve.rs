//! `factory reserve <key>`: hands out the next numbers of a machine-wide counter (decision numbers, table
//! rows). Why: parallel sessions on one PC never take the same next id and never have to renumber.
//!
//! State `<machine dir>/reserve/last-<key>`: the last number handed, one decimal line, changed only under the
//! key's lock `lock-<key>`, through a temp file and a rename. The prefixes keep keys like `con` off Windows
//! device names.

use crate::machine::{self, Lock};
use crate::paths::text;
use std::fs;
use std::io::ErrorKind;
use std::path::Path;

/// `factory reserve <key> [--floor <n>] [--count <k>]`
pub fn cli(args: &[&str]) -> u8 {
    let Some((key, opts)) = args.split_first() else { return usage() };
    let Some([floor, count]) = machine::flags(opts, ["--floor", "--count"]) else { return usage() };
    let (true, Some(floor), Some(count)) = (key_ok(key), machine::number(floor, 0, 0, u64::MAX), machine::number(count, 1, 1, 1000)) else {
        return usage();
    };
    match reserve(key, floor, count) {
        Ok(first) => {
            print!("{}", (first..=first + (count - 1)).map(|n| format!("{n}\n")).collect::<String>());
            0
        }
        Err(e) => {
            eprintln!("factory reserve: {e}");
            1
        }
    }
}

fn usage() -> u8 {
    eprintln!("usage: factory reserve <key> [--floor <n>] [--count <k>]   key [A-Za-z0-9_.-]{{1,128}}, count 1..=1000");
    2
}

/// `[A-Za-z0-9_.-]{1,128}`, not starting with `-` (an option) nor ending with `.` (Windows drops it).
fn key_ok(key: &str) -> bool {
    machine::valid(key, 128, "_.-") && !key.starts_with('-') && !key.ends_with('.')
}

/// Hands `count` numbers after both the last handed and `floor`; returns the first.
fn reserve(key: &str, floor: u64, count: u64) -> Result<u64, String> {
    let dir = machine::dir("reserve")?;
    let _lock = Lock::take(dir.join(format!("lock-{key}")))?;
    let state = dir.join(format!("last-{key}"));
    let first = last(&state)?.max(floor).checked_add(1);
    let Some((first, end)) = first.and_then(|f| Some((f, f.checked_add(count - 1)?))) else {
        return Err(format!("{key}: the next numbers would pass {}", u64::MAX));
    };
    let tmp = dir.join(format!("last-{key}~tmp"));
    fs::write(&tmp, format!("{end}\n"))
        .and_then(|()| fs::rename(&tmp, &state))
        .map_err(|e| format!("cannot write {}: {e}", text(&state)))?;
    Ok(first)
}

/// The last number handed (0 before the first). Anything but one number is an error, never a silent reset.
fn last(state: &Path) -> Result<u64, String> {
    match fs::read_to_string(state) {
        Ok(t) => t.trim_end().parse().map_err(|_| format!("{} is not one number: fix or remove it by hand", text(state))),
        Err(e) if e.kind() == ErrorKind::NotFound => Ok(0),
        Err(e) => Err(format!("cannot read {}: {e}", text(state))),
    }
}
