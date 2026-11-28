//! Background suite launch proof. Only the process that starts the suite can publish its launch record.

use super::{Snapshot, existing, path_of, record, snapshot, utc_iso};
use crate::paths::{self, text};
use std::fs::{self, File};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

/// A per-tree claim shared by the foreground and background native runners.
pub(super) struct Claim(PathBuf);

impl Claim {
    pub(super) fn take(s: &Snapshot, suite: &str) -> Result<Self, String> {
        let path = path_of(&s.work, &s.tree, suite).with_extension("running");
        fs::create_dir_all(super::dir(&s.work)).map_err(|e| format!("cannot write the receipt: {e}"))?;
        if let Err(error) = File::create_new(&path) {
            return Err(format!("cannot reserve {}: {error}; a reserved suite may still be running", text(&path)));
        }
        Ok(Self(path))
    }
}

impl Drop for Claim {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.0);
    }
}

pub(super) fn start(args: &[&str], here: &Path) -> u8 {
    let Some((suite, inert, cmd)) = options(args) else { return super::usage() };
    let suite = suite.unwrap_or("full");
    if suite.is_empty() || !suite.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_') {
        return super::usage();
    }
    if cmd.is_empty() || cmd.iter().any(|arg| arg.contains(['\r', '\n'])) {
        return super::usage();
    }
    let inert = match super::globs(inert) {
        Ok(globs) => globs,
        Err(code) => return code,
    };
    launch(here, suite, &inert, cmd).map_or_else(failed, |line| {
        println!("{line}");
        0
    })
}

/// `--suite <name>` and `--inert <glob>` pairs, then `--` and the command; None on anything else.
fn options<'a>(mut args: &'a [&'a str]) -> Option<(Option<&'a str>, Vec<&'a str>, &'a [&'a str])> {
    let (mut suite, mut inert) = (None, Vec::new());
    loop {
        match args {
            ["--", cmd @ ..] => return Some((suite, inert, cmd)),
            ["--suite", s, rest @ ..] => (suite, args) = (Some(*s), rest),
            ["--inert", g, rest @ ..] => {
                inert.push(*g);
                args = rest;
            }
            _ => return None,
        }
    }
}

fn launch(here: &Path, suite: &str, inert: &[String], cmd: &[&str]) -> Result<String, String> {
    let before = snapshot(here)?;
    if !before.clean {
        return Err("background suite requires a clean committed checkout".into());
    }
    let reuse = || existing(&before.work, &before.tree, suite).filter(|(_, receipt)| receipt.pass).map(|(path, _)| format!("reused {}", text(&path)));
    if let Some(line) = reuse() {
        return Ok(line);
    }
    let claim = Claim::take(&before, suite)?;
    if let Some(line) = reuse() {
        return Ok(line);
    }
    let launch_path = claim.0.with_extension("launch.txt");
    if launch_path.is_file() {
        fs::remove_file(&launch_path).map_err(|e| format!("cannot clear old launch receipt: {e}"))?;
    }
    let log_path = claim.0.with_extension("log");
    let log = File::create(&log_path).map_err(|e| format!("cannot open {}: {e}", text(&log_path)))?;
    let err = log.try_clone().map_err(|e| format!("cannot clone suite log: {e}"))?;
    let exe = std::env::current_exe().map_err(|e| format!("cannot locate factory: {e}"))?;
    let mut command = background(exe.as_os_str());
    command
        .args(["receipt", "_worker", suite, &before.head, &before.tree])
        .args(inert.iter().flat_map(|g| ["--inert", g.as_str()]))
        .arg("--")
        .args(cmd)
        .current_dir(here)
        .stdout(log)
        .stderr(err);
    #[cfg(windows)]
    let _handles = crate::streams::PrivateStreams::new().map_err(|e| format!("cannot isolate the host streams: {e}"))?;
    let mut worker = command.spawn().map_err(|e| format!("cannot launch suite supervisor: {e}"))?;
    // The supervisor owns release from here, including if the calling host disconnects.
    std::mem::forget(claim);
    let deadline = Instant::now() + Duration::from_secs(10);
    loop {
        if launch_path.is_file() {
            return Ok(format!("started {}", text(&launch_path)));
        }
        if worker.try_wait().map_err(|e| format!("cannot read supervisor status: {e}"))?.is_some() {
            if launch_path.is_file() {
                return Ok(format!("started {}", text(&launch_path)));
            }
            let launch_error = fs::read_to_string(&log_path).unwrap_or_default();
            return Err(format!("suite did not start; see {}. {}", text(&log_path), launch_error.trim()));
        }
        if Instant::now() >= deadline {
            return Err(format!("suite start has not been confirmed; see {} and {}", text(&launch_path), text(&log_path)));
        }
        std::thread::sleep(Duration::from_millis(20));
    }
}

pub(super) fn worker(args: &[&str], here: &Path, runtime: &str) -> u8 {
    let [suite, head, tree, rest @ ..] = args else { return super::usage() };
    let Some((None, inert, [prog, argv @ ..])) = options(rest) else { return super::usage() };
    if !crate::git::refs::is_sha(head) || !crate::git::refs::is_sha(tree) {
        return super::usage();
    }
    // `start` checked the globs before it reserved the tree.
    let inert = inert.into_iter().map(String::from).collect();
    let Some(repo) = crate::git::Repo::discover(here) else { return failed("not in a Git work tree".into()) };
    let path = path_of(&repo.work, tree, suite).with_extension("running");
    if !path.is_file() {
        return failed("no active suite reservation".into());
    }
    let claim = Claim(path);
    match run(&claim, here, suite, head, tree, prog, argv, runtime, inert) {
        Ok(code) => code,
        Err(e) => failed(e),
    }
}

#[allow(clippy::too_many_arguments)] // the worker's own arguments, passed through
fn run(
    claim: &Claim,
    here: &Path,
    suite: &str,
    head: &str,
    tree: &str,
    prog: &str,
    argv: &[&str],
    runtime: &str,
    inert: Vec<String>,
) -> Result<u8, String> {
    let before = snapshot(here)?;
    if !same(&before, head, tree) {
        return Err("checkout changed before the background suite started".into());
    }
    let start = Instant::now();
    let mut suite_child = background(prog).args(argv).current_dir(here).spawn().map_err(|e| format!("cannot run {prog}: {e}"))?;
    let log = text(&claim.0.with_extension("log"));
    let cmd = std::iter::once(prog).chain(argv.iter().copied()).collect::<Vec<_>>().join(" ");
    let at = utc_iso(paths::now());
    let proof = format!(
        "factory-suite-launch 1\nsuite {suite}\nhead {head}\ntree {tree}\nclean yes\nmode background\ncmd {cmd}\nlog {log}\nat {at}\npid {}\nowner {}\n",
        suite_child.id(),
        crate::machine::Owner::of(suite_child.id()).map_or_else(|| suite_child.id().to_string(), |o| o.to_string())
    );
    let launched = paths::write_atomic(&claim.0.with_extension("launch.txt"), proof.as_bytes());
    let status = suite_child.wait().map_err(|e| format!("cannot wait for {prog}: {e}"))?;
    let unchanged = snapshot(here).is_ok_and(|after| same(&after, head, tree));
    let (path, _) = record(before, suite, status.success() && unchanged, &cmd, start.elapsed().as_secs(), runtime, &log, inert)?;
    eprintln!("factory receipt: {}", text(&path));
    launched.map_err(|e| format!("cannot save the suite launch receipt: {e}"))?;
    if !unchanged {
        return Err("checkout changed while the background suite ran; the receipt is FAIL".into());
    }
    Ok(if status.success() { 0 } else { status.code().and_then(|code| u8::try_from(code).ok()).unwrap_or(1) })
}

fn same(snapshot: &Snapshot, head: &str, tree: &str) -> bool {
    snapshot.clean && snapshot.head == head && snapshot.tree == tree
}

fn failed(error: String) -> u8 {
    eprintln!("factory receipt: {error}");
    1
}

fn background(program: impl AsRef<std::ffi::OsStr>) -> Command {
    let mut command = paths::quiet_command(program);
    command.stdin(Stdio::null());
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        command.process_group(0);
    }
    command
}

/// A live background suite run: its suite, its pid and when it started (Unix seconds, 0 when unrecorded).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Detached {
    pub suite: String,
    pub pid: u32,
    pub since: u64,
}

/// The background run that is live now: its reservation stands, its launch record names a running pid. A dead
/// supervisor's leftover reservation never counts. Why: the guard keeps a session from ending its turn on a run
/// whose end wakes no one.
pub fn live_detached(work: &Path) -> Option<Detached> {
    let rd = fs::read_dir(super::dir(work)).ok()?;
    rd.flatten().map(|e| e.path()).filter(|p| p.to_string_lossy().ends_with(".launch.txt")).find_map(|p| {
        let running = PathBuf::from(p.to_string_lossy().trim_end_matches(".launch.txt").to_string() + ".running");
        if !running.is_file() {
            return None;
        }
        let text = fs::read_to_string(&p).ok()?;
        let field = |k: &str| text.lines().find_map(|l| l.strip_prefix(k)).map(str::trim);
        // `owner` (pid and start time) beats a bare `pid`: a reused pid never reads as the suite still running.
        let pid = crate::machine::Owner::parse(field("owner ").or_else(|| field("pid "))?)?;
        let suite = field("suite ").filter(|s| !s.is_empty() && s.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_'));
        let since = field("at ").and_then(crate::clock::stamp::iso_secs).unwrap_or(0);
        pid.alive().then(|| Detached { suite: suite.unwrap_or("full").to_string(), pid: pid.pid, since })
    })
}

#[cfg(test)]
mod tests {
    use super::live_detached;

    #[test]
    fn a_live_owner_counts_and_a_reused_pid_or_lost_reservation_never_does() {
        let work = std::env::temp_dir().join(format!("factory-detached-{}", std::process::id()));
        let dir = super::super::dir(&work);
        std::fs::create_dir_all(&dir).unwrap();
        let me = crate::machine::Owner::me();
        let launch = |owner: &str| std::fs::write(dir.join("t-full.launch.txt"), format!("suite full\npid {}\n{owner}", me.pid)).unwrap();
        std::fs::write(dir.join("t-full.running"), "").unwrap();
        launch(&format!("owner {me}\n"));
        assert_eq!(live_detached(&work), Some(super::Detached { suite: "full".into(), pid: me.pid, since: 0 }));
        if let Some(start) = me.start {
            launch(&format!("owner {}-{}\n", me.pid, start + 1));
            assert_eq!(live_detached(&work), None, "same pid, another start time");
        }
        launch("");
        std::fs::remove_file(dir.join("t-full.running")).unwrap();
        assert_eq!(live_detached(&work), None, "no reservation");
        let _ = std::fs::remove_dir_all(work);
    }
}
