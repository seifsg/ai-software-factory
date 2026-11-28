//! `factory queue`: one machine-wide FIFO per name for heavy jobs (full suites, builds) that every session on
//! this PC shares. Why: a queued job waits inside this binary, so the agent spends no tokens while it waits,
//! jobs start in arrival order, and a crashed job's ticket is dropped by the next scan.
//!
//! Folder `<machine dir>/queue-<name>/` (the prefix keeps names like `aux` off Windows device names): one
//! ticket per job, named `<20-digit unix nanos>-<owner>` (a `machine::Owner`: pid, then start time where the
//! OS gives one) with body `owner\ncwd\ncommand line\n`, and `lock`, held while a ticket is numbered, so later
//! tickets always sort after earlier ones.

use crate::machine::{self, Lock, Owner};
use crate::paths::{ns, text};
use std::fs::{self, File};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Duration, Instant, SystemTime};

/// A live ticket: file name, arrival nanos, pid.
type Entry = (String, u128, u32);

/// A queued job's ticket; dropping it leaves the queue, however the job ended.
pub struct Ticket(PathBuf, String);

impl Drop for Ticket {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.0);
    }
}

/// `factory queue run|list ...`
pub fn cli(args: &[&str]) -> u8 {
    let done = match args {
        ["run", rest @ ..] => {
            let Some(i) = rest.iter().position(|a| *a == "--") else { return usage() };
            let (opts, cmd) = (&rest[..i], &rest[i + 1..]);
            let Some([name, slots]) = machine::flags(opts, ["--name", "--slots"]) else { return usage() };
            let (Some(name), Some(slots), false) = (queue_name(name), machine::number(slots, 1, 1, 64), cmd.is_empty()) else {
                return usage();
            };
            run(name, slots as usize, cmd)
        }
        ["list", opts @ ..] => {
            let Some(name) = machine::flags(opts, ["--name"]).and_then(|[n]| queue_name(n)) else { return usage() };
            list(name).map(|()| 0)
        }
        _ => return usage(),
    };
    done.unwrap_or_else(|e| {
        eprintln!("factory queue: {e}");
        1
    })
}

fn usage() -> u8 {
    eprintln!("usage: factory queue run [--name <n>] [--slots <k>] -- <command>... | list [--name <n>]");
    2
}

/// The `--name` value (default `heavy`) when it is `[A-Za-z0-9_-]{1,64}`.
fn queue_name(value: Option<&str>) -> Option<&str> {
    let name = value.unwrap_or("heavy");
    machine::valid(name, 64, "_-").then_some(name)
}

/// Joins queue `name` as `cmd` and returns once among its first `slots`; the place lasts until the ticket drops.
/// Why: `roast` holds a place for its whole run, so parallel sessions never start more browsers and agents than slots.
pub fn hold(name: &str, slots: usize, cmd: &[&str]) -> Result<Ticket, String> {
    let dir = machine::dir(&format!("queue-{name}"))?;
    let ticket = join(&dir, cmd)?;
    let (queued, since) = (Instant::now(), crate::paths::now());
    if wait(&dir, &ticket, name, slots)? {
        eprintln!("factory queue: {name} started after {} s", queued.elapsed().as_secs());
        crate::clock::span(&crate::guard::cwd(), crate::clock::Phase::Queue, since, crate::paths::now(), name);
    }
    Ok(ticket)
}

/// Queues `cmd`, waits for one of the first `slots` places, runs it with this terminal's streams and returns
/// its exit code (a code outside 0..=255, or none after a signal, is 1).
fn run(name: &str, slots: usize, cmd: &[&str]) -> Result<u8, String> {
    let _place = hold(name, slots, cmd)?;
    let status = Command::new(cmd[0]).args(&cmd[1..]).status().map_err(|e| format!("cannot run {}: {e}", cmd[0]))?;
    Ok(status.code().and_then(|c| u8::try_from(c).ok()).unwrap_or(1))
}

/// Takes a ticket numbered after every live one, under the queue's lock.
fn join(dir: &Path, cmd: &[&str]) -> Result<Ticket, String> {
    let _lock = Lock::take(dir.join("lock"))?;
    let last = live(dir)?.last().map_or(0, |t| t.1);
    let me = Owner::me();
    let name = format!("{:020}-{me}", ns(SystemTime::now()).max(last + 1));
    let path = dir.join(&name);
    let mut file = File::create_new(&path).map_err(|e| format!("cannot create {}: {e}", text(&path)))?;
    let ticket = Ticket(path, name);
    let body = format!("{me}\n{}\n{}\n", text(&crate::guard::cwd()), cmd.join(" ").replace(['\r', '\n'], " "));
    file.write_all(body.as_bytes()).map_err(|e| format!("cannot write {}: {e}", text(&ticket.0)))?;
    Ok(ticket)
}

/// Waits until the ticket is among the first `slots`, scanning every 500 ms; says once whom it waits behind.
/// Returns whether it waited.
fn wait(dir: &Path, ticket: &Ticket, name: &str, slots: usize) -> Result<bool, String> {
    let mut waited = false;
    loop {
        let queue = live(dir)?;
        let pos =
            queue.iter().position(|t| t.0 == ticket.1).ok_or_else(|| format!("ticket {} was removed while waiting", text(&ticket.0)))?;
        if pos < slots {
            return Ok(waited);
        }
        if !waited {
            let (cwd, cmd) = body(&dir.join(&queue[0].0));
            eprintln!("factory queue: {name} waiting behind {pos}: {cwd} {cmd}");
            waited = true;
        }
        std::thread::sleep(Duration::from_millis(500));
    }
}

/// `factory queue list`: `<pos> <pid> <age s> <cwd> <cmd>` per live ticket, in order.
fn list(name: &str) -> Result<(), String> {
    let dir = machine::dir(&format!("queue-{name}"))?;
    let now = ns(SystemTime::now());
    let lines: String = live(&dir)?
        .iter()
        .enumerate()
        .map(|(i, (file, at, pid))| {
            let (cwd, cmd) = body(&dir.join(file));
            format!("{} {pid} {} {cwd} {cmd}\n", i + 1, now.saturating_sub(*at) / 1_000_000_000)
        })
        .collect();
    print!("{lines}");
    Ok(())
}

/// Live tickets in arrival order (fixed-width names sort by arrival); a dead holder's ticket, or one whose pid
/// now names another process, is deleted.
fn live(dir: &Path) -> Result<Vec<Entry>, String> {
    let mut out = Vec::new();
    for e in fs::read_dir(dir).map_err(|e| format!("cannot read {}: {e}", text(dir)))? {
        let name = e.map_err(|e| format!("cannot read {}: {e}", text(dir)))?.file_name().to_string_lossy().into_owned();
        let Some((at, owner)) = parse(&name) else { continue };
        if owner.alive() {
            out.push((name, at, owner.pid));
            continue;
        }
        match fs::remove_file(dir.join(&name)) {
            Err(e) if e.kind() != std::io::ErrorKind::NotFound => return Err(format!("cannot drop dead ticket {name}: {e}")),
            _ => {}
        }
    }
    out.sort_unstable();
    Ok(out)
}

/// A ticket file name as arrival nanos and owner; None for any other file.
fn parse(name: &str) -> Option<(u128, Owner)> {
    let (at, owner) = name.split_once('-')?;
    (at.len() == 20 && at.bytes().all(|b| b.is_ascii_digit())).then_some(())?;
    Some((at.parse().ok()?, Owner::parse(owner)?))
}

/// A ticket's cwd and command line; empty when its job ended since the scan.
fn body(path: &Path) -> (String, String) {
    let text = fs::read_to_string(path).unwrap_or_default();
    let mut lines = text.lines().skip(1).map(String::from);
    (lines.next().unwrap_or_default(), lines.next().unwrap_or_default())
}
