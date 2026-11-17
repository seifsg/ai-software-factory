//! The run guard: keeps an open run going, one step per turn, until step 8 is ticked and gates A, B, C
//! and the review are proven on their commits. Same rules and bytes as the sh guard it replaces.
//!   stop     the Stop hook (JSON in, decision out)
//!   compact  after compaction or a resume: re-injects the run's place
//!   check    a host with no command hook: stop's rules from the run file and Git, as one plain line
//!   clear    the owner's command after a halt
//!   step     writes a posted block under its heading, ticks it, then answers like check

pub mod backing;
pub mod before;
pub mod flow;
pub mod reply;
pub mod rules;
mod session;
pub mod step;
mod timeline;

use crate::hook::{Input, Reply};
use std::path::{Path, PathBuf};

/// `factory guard <mode> ...`
pub fn cli(args: &[&str]) -> u8 {
    match args {
        ["stop"] => emit(flow::run(&Input::from_stdin(), flow::Mode::Stop, &cwd())),
        ["compact"] => emit(flow::run(&Input::from_stdin(), flow::Mode::Compact, &cwd())),
        ["check"] => {
            let Some(dir) = crate::run::locate::walk(&cwd()) else {
                println!("no .factory/run.md from this folder");
                return 1;
            };
            let (text, all) = backing::report(Path::new(&dir));
            print!("{text}");
            u8::from(!all)
        }
        ["check", sid] => {
            print!("{}", check(sid, &cwd()));
            0
        }
        ["clear"] => clear(None),
        ["clear", dir] => clear(Some(dir)),
        ["begin"] => timeline::begin(&cwd()),
        ["step", rest @ ..] => step::cli(rest),
        _ => {
            eprintln!("usage: factory guard stop|compact | begin | check [<session id>] | clear [<run folder>] | step <n|Tk> < block");
            2
        }
    }
}

fn emit(r: Option<Reply>) -> u8 {
    if let Some(r) = r {
        r.print();
    }
    0
}

/// The current folder as the shell names it (`$PWD`, so `/var` stays `/var` on macOS, not `/private/var`),
/// else as the system resolves it, or `.` when unreadable. Why: replies name the run in the agent's spelling.
pub fn cwd() -> PathBuf {
    let real = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    let shell = std::env::var_os("PWD").map(|p| PathBuf::from(crate::paths::norm(&p.to_string_lossy())));
    let same = |p: &PathBuf| p.is_absolute() && std::fs::canonicalize(p).ok() == std::fs::canonicalize(&real).ok();
    shell.filter(same).unwrap_or(real)
}

/// Plays the Stop event from the run file and Git alone (never a transcript) and says may stop or continue.
pub fn check(session: &str, dir: &Path) -> String {
    let input = Input { session_id: session.to_string(), cwd: crate::paths::text(dir), ..Input::default() };
    let r = flow::run(&input, flow::Mode::Stop, dir);
    reply::check_line(r.as_ref().map_or("", Reply::inner), dir.join(".factory/run.md").is_file())
}

fn clear(dir: Option<&str>) -> u8 {
    let start = match dir {
        Some(d) => {
            let p = PathBuf::from(crate::paths::norm(d));
            if !p.is_dir() {
                eprintln!("factory guard clear: {d}: no such folder");
                return 1;
            }
            p
        }
        None => cwd(),
    };
    match flow::run(&Input::default(), flow::Mode::Clear, &start) {
        Some(Reply::Text(t)) if t == reply::CLEARED => {
            print!("{t}");
            0
        }
        _ => {
            eprintln!("factory guard: no run file here; give its folder: clear <run folder>");
            1
        }
    }
}

/// How the owner resumes a halted run with this binary: `<exe> guard clear`.
pub fn clear_cmd() -> String {
    format!("{} guard clear", exe())
}

/// This binary's path in `C:/x` form.
pub fn exe() -> String {
    std::env::current_exe().map(|p| crate::paths::text(&p)).unwrap_or_else(|_| "factory".into())
}

/// POSIX `cksum`'s CRC: the jobs wait's identity (a new job text starts a new deadline).
pub fn cksum(data: &[u8]) -> u32 {
    fn step(mut c: u32, b: u8) -> u32 {
        c ^= (b as u32) << 24;
        for _ in 0..8 {
            c = if c & 0x8000_0000 != 0 { (c << 1) ^ 0x04c1_1db7 } else { c << 1 };
        }
        c
    }
    let mut crc = data.iter().fold(0u32, |c, &b| step(c, b));
    let mut len = data.len();
    while len > 0 {
        crc = step(crc, (len & 0xff) as u8);
        len >>= 8;
    }
    !crc
}

#[cfg(test)]
mod tests {
    #[test]
    fn cksum_matches_posix() {
        assert_eq!(super::cksum(b""), 4294967295);
        assert_eq!(super::cksum(b"a\n"), 2418082923);
    }
}
