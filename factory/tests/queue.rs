//! `factory queue`: one slot never runs two jobs at once, two slots do, a dead job's ticket is skipped and
//! dropped, the job's exit code passes through and bad arguments exit 2. Each test has its own machine folder.

mod common;

use common::scratch;
use std::path::Path;
use std::process::{Child, Command, ExitStatus};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

fn now_ns() -> u128 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()
}

/// Not a check on its own: the job the queue runs when `JOB_OUT` is set. Sleeps `JOB_MS`, writes its start
/// and end nanos to `JOB_OUT` and exits with `JOB_EXIT`. Why: one job that runs on every OS, with no shell.
#[test]
fn job() {
    let Some(out) = std::env::var_os("JOB_OUT") else { return };
    let var = |k| std::env::var(k).unwrap().parse::<u64>().unwrap();
    let start = now_ns();
    std::thread::sleep(Duration::from_millis(var("JOB_MS")));
    std::fs::write(out, format!("{start} {}", now_ns())).unwrap();
    std::process::exit(var("JOB_EXIT") as i32);
}

/// `factory <args>` with machine folder `m`.
fn factory(m: &Path, args: &[&str]) -> Command {
    let mut c = Command::new(env!("CARGO_BIN_EXE_factory"));
    c.args(args).env("FACTORY_QUEUE_DIR", m);
    c
}

/// `factory queue run <opts> -- <job>` writing to `out`; started, not awaited.
fn queued(m: &Path, opts: &[&str], out: &Path, ms: u64, exit: i32) -> Child {
    let exe = std::env::current_exe().unwrap();
    let mut args = vec!["queue", "run"];
    args.extend(opts);
    args.extend(["--", exe.to_str().unwrap(), "--exact", "job", "--nocapture"]);
    factory(m, &args).env("JOB_OUT", out).env("JOB_MS", ms.to_string()).env("JOB_EXIT", exit.to_string()).spawn().unwrap()
}

/// The child's status within 4 s; it is killed and the test fails past that.
fn finish(mut child: Child) -> ExitStatus {
    let end = Instant::now() + Duration::from_secs(4);
    loop {
        if let Some(s) = child.try_wait().unwrap() {
            return s;
        }
        if Instant::now() > end {
            let _ = child.kill();
            panic!("queued job still waiting after 4 s");
        }
        std::thread::sleep(Duration::from_millis(20));
    }
}

/// A job's `(start, end)` nanos.
fn span(out: &Path) -> (u128, u128) {
    let t = std::fs::read_to_string(out).unwrap();
    let (a, b) = t.split_once(' ').unwrap();
    (a.parse().unwrap(), b.parse().unwrap())
}

/// Two jobs started together; true when their runs overlapped.
fn overlap(name: &str, opts: &[&str]) -> bool {
    let d = scratch(name);
    let (a, b) = (d.join("a"), d.join("b"));
    let (ja, jb) = (queued(&d, opts, &a, 800, 0), queued(&d, opts, &b, 800, 0));
    assert!(finish(ja).success() && finish(jb).success());
    let ((s1, e1), (s2, e2)) = (span(&a), span(&b));
    s1 < e2 && s2 < e1
}

#[test]
fn one_slot_never_overlaps() {
    assert!(!overlap("q-one", &["--slots", "1"]));
}

#[test]
fn two_slots_overlap() {
    assert!(overlap("q-two", &["--slots", "2"]));
}

/// A ticket of a pid that has exited.
fn dead_ticket(dir: &Path, at: u64) -> std::path::PathBuf {
    let mut c = Command::new(env!("CARGO_BIN_EXE_factory")).arg("--version").stdout(std::process::Stdio::null()).spawn().unwrap();
    let pid = c.id();
    c.wait().unwrap();
    std::fs::create_dir_all(dir).unwrap();
    let t = dir.join(format!("{at:020}-{pid}"));
    std::fs::write(&t, format!("{pid}\nC:/gone\ncargo test\n")).unwrap();
    t
}

#[test]
fn dead_ticket_is_skipped_and_dropped() {
    let d = scratch("q-dead");
    let q = d.join("queue-heavy");
    let stale = dead_ticket(&q, 1);
    assert!(finish(queued(&d, &[], &d.join("a"), 0, 0)).success());
    assert!(!stale.exists(), "the dead ticket stays");
    // list: a live ticket (this test's own pid) in order, the dead one dropped.
    let stale = dead_ticket(&q, 1);
    std::fs::write(q.join(format!("{:020}-{}", 2, std::process::id())), format!("{}\nC:/here\ncargo build\n", std::process::id())).unwrap();
    let out = factory(&d, &["queue", "list"]).output().unwrap();
    let text = String::from_utf8_lossy(&out.stdout);
    assert!(out.status.success());
    let fields: Vec<&str> = text.split(' ').collect();
    assert_eq!(
        (text.lines().count(), fields[0], fields[1], fields[3], fields[4]),
        (1, "1", &*std::process::id().to_string(), "C:/here", "cargo")
    );
    assert!(!stale.exists(), "list keeps the dead ticket");
}

#[test]
fn exit_code_passes_through() {
    let d = scratch("q-exit");
    assert_eq!(finish(queued(&d, &[], &d.join("a"), 0, 7)).code(), Some(7));
    // A command that cannot start: a loud error, exit 1, and no ticket left behind.
    let out = factory(&d, &["queue", "run", "--", "factory-no-such-program"]).output().unwrap();
    assert_eq!(out.status.code(), Some(1));
    assert!(String::from_utf8_lossy(&out.stderr).contains("cannot run factory-no-such-program"));
    assert_eq!(std::fs::read_dir(d.join("queue-heavy")).unwrap().filter(|e| e.as_ref().unwrap().file_name() != "lock").count(), 0);
}

#[test]
fn bad_args_exit_2() {
    let d = scratch("q-bad");
    for args in [
        &["queue"][..],
        &["queue", "run", "x"],
        &["queue", "run", "--"],
        &["queue", "run", "--slots", "0", "--", "x"],
        &["queue", "run", "--slots", "65", "--", "x"],
        &["queue", "run", "--slots", "two", "--", "x"],
        &["queue", "run", "--name", "a/b", "--", "x"],
        &["queue", "run", "--name", "", "--", "x"],
        &["queue", "run", "--name", "a", "--name", "b", "--", "x"],
        &["queue", "run", "--wait", "1", "--", "x"],
        &["queue", "list", "--name"],
    ] {
        assert_eq!(factory(&d, args).output().unwrap().status.code(), Some(2), "{args:?}");
    }
}
