//! Runs the outside agent under a hard clock: brief on stdin, output to files, the whole process tree killed at the cap.

use super::cmd::Job;
use crate::paths::{quiet_command, text};
use std::fs::File;
use std::io::Write;
use std::path::Path;
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};

/// Poll step while waiting on a child: short against a run of tens of seconds, cheap on CPU.
const TICK: Duration = Duration::from_millis(200);

/// How the run ended.
pub struct Done {
    pub secs: u64,
    pub timed_out: bool,
    pub code: Option<i32>,
}

/// Spawns the job inside `out` (stdout to `agent.out`, stderr to `agent.err`) and waits at most `cap`.
pub fn run(job: Job, cap: Duration, out: &Path) -> Result<Done, String> {
    let Job { mut command, brief } = job;
    let file = |name: &str| File::create(out.join(name)).map_err(|e| format!("cannot write {}: {e}", text(&out.join(name))));
    command.stdin(Stdio::piped()).stdout(file("agent.out")?).stderr(file("agent.err")?);
    group(&mut command);
    let start = Instant::now();
    let mut child = command.spawn().map_err(|e| format!("cannot start the agent CLI: {e}"))?;
    let mut stdin = child.stdin.take().ok_or("agent CLI has no stdin")?;
    // A thread, so a child that reads late never blocks the clock below.
    let feeder = std::thread::spawn(move || stdin.write_all(brief.as_bytes()));
    let exited = wait(&mut child, cap)?;
    if exited.is_none() {
        kill_tree(&mut child);
    }
    let _ = feeder.join();
    Ok(Done { secs: start.elapsed().as_secs(), timed_out: exited.is_none(), code: exited.flatten() })
}

/// True or false for the command's success within `cap`; `None` when it hung (it is killed) or did not start.
pub fn status_within(mut command: Command, cap: Duration) -> Option<bool> {
    group(&mut command);
    let mut child = command.spawn().ok()?;
    match wait(&mut child, cap).ok()? {
        Some(code) => Some(code == Some(0)),
        None => {
            kill_tree(&mut child);
            None
        }
    }
}

/// `Some(exit code)` once the child exits, `None` at the cap.
fn wait(child: &mut Child, cap: Duration) -> Result<Option<Option<i32>>, String> {
    let deadline = Instant::now() + cap;
    loop {
        if let Some(status) = child.try_wait().map_err(|e| format!("cannot read the agent's status: {e}"))? {
            return Ok(Some(status.code()));
        }
        if Instant::now() >= deadline {
            return Ok(None);
        }
        std::thread::sleep(TICK);
    }
}

/// Own process group on Unix, so one signal reaches the CLI, its browser server and the browser.
fn group(command: &mut Command) {
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        command.process_group(0);
    }
    #[cfg(not(unix))]
    let _ = command;
}

/// Kills the child and everything it started: `taskkill /T` on Windows, the process group elsewhere.
fn kill_tree(child: &mut Child) {
    let pid = child.id().to_string();
    let mut k = if cfg!(windows) {
        let mut k = quiet_command("taskkill");
        k.args(["/PID", &pid, "/T", "/F"]);
        k
    } else {
        let mut k = quiet_command("kill");
        k.args(["-KILL", &format!("-{pid}")]);
        k
    };
    let _ = k.stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null()).status();
    let _ = child.kill();
    let _ = child.wait();
}
