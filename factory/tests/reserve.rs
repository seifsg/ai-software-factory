//! `factory reserve`: parallel callers get distinct consecutive numbers, a floor raises the start, a count
//! hands a range, bad arguments exit 2 and a corrupt state file exits 1 untouched. Each test has its own
//! machine folder.

mod common;

use common::scratch;
use std::path::Path;
use std::process::{Command, Output};
use std::time::{Duration, Instant};

/// `factory reserve <args>` with machine folder `m`, started.
fn reserve(m: &Path, args: &[&str]) -> std::process::Child {
    Command::new(env!("CARGO_BIN_EXE_factory"))
        .arg("reserve")
        .args(args)
        .env("FACTORY_QUEUE_DIR", m)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .unwrap()
}

/// Exit code and stdout of `factory reserve <args>`; the caller is killed and the test fails past 4 s.
fn run(m: &Path, args: &[&str]) -> (i32, String) {
    let mut child = reserve(m, args);
    let end = Instant::now() + Duration::from_secs(4);
    while child.try_wait().unwrap().is_none() {
        if Instant::now() > end {
            let _ = child.kill();
            panic!("reserve {args:?} still running after 4 s");
        }
        std::thread::sleep(Duration::from_millis(20));
    }
    let Output { status, stdout, .. } = child.wait_with_output().unwrap();
    (status.code().unwrap(), String::from_utf8_lossy(&stdout).into_owned())
}

#[test]
fn parallel_callers_get_distinct_consecutive_numbers() {
    let d = scratch("r-par");
    let kids: Vec<_> = (0..8).map(|_| reserve(&d, &["decisions"])).collect();
    let mut got: Vec<u64> = kids
        .into_iter()
        .map(|k| {
            let out = k.wait_with_output().unwrap();
            assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
            String::from_utf8_lossy(&out.stdout).trim().parse().unwrap()
        })
        .collect();
    got.sort_unstable();
    assert_eq!(got, (1..=8).collect::<Vec<u64>>());
}

#[test]
fn a_live_lock_holds_callers_and_a_dead_one_is_taken_over() {
    let d = scratch("r-lock");
    let lock = d.join("reserve/lock-k");
    std::fs::create_dir_all(d.join("reserve")).unwrap();
    std::fs::write(&lock, std::process::id().to_string()).unwrap();
    let mut held = reserve(&d, &["k"]);
    std::thread::sleep(Duration::from_millis(300));
    assert!(held.try_wait().unwrap().is_none(), "reserve ran past a live lock");
    std::fs::remove_file(&lock).unwrap();
    assert_eq!(String::from_utf8_lossy(&held.wait_with_output().unwrap().stdout), "1\n");
    // The owner of this lock has exited: the next caller clears it and goes on.
    let mut gone = Command::new(env!("CARGO_BIN_EXE_factory")).arg("--version").stdout(std::process::Stdio::null()).spawn().unwrap();
    gone.wait().unwrap();
    std::fs::write(&lock, gone.id().to_string()).unwrap();
    assert_eq!(run(&d, &["k"]), (0, "2\n".into()));
    assert!(!lock.exists());
}

#[test]
fn floor_raises_the_start_and_count_hands_a_range() {
    let d = scratch("r-floor");
    assert_eq!(run(&d, &["rows", "--floor", "100"]), (0, "101\n".into()));
    assert_eq!(run(&d, &["rows", "--floor", "50"]), (0, "102\n".into()));
    assert_eq!(run(&d, &["rows", "--count", "3"]), (0, "103\n104\n105\n".into()));
    assert_eq!(run(&d, &["other.key", "--count", "2", "--floor", "7"]), (0, "8\n9\n".into()));
    assert_eq!(std::fs::read_to_string(d.join("reserve/last-rows")).unwrap(), "105\n");
}

#[test]
fn bad_args_exit_2() {
    let d = scratch("r-bad");
    let long = "k".repeat(129);
    for args in [
        &[][..],
        &["a/b"],
        &[""],
        &[&long],
        &["."],
        &["a."],
        &["--floor"],
        &["k", "--count", "0"],
        &["k", "--count", "1001"],
        &["k", "--floor", "-1"],
        &["k", "--floor"],
        &["k", "--step", "2"],
    ] {
        assert_eq!(run(&d, args).0, 2, "{args:?}");
    }
    assert_eq!(run(&d, &[&"k".repeat(128)]), (0, "1\n".into()));
}

#[test]
fn corrupt_state_exits_1_untouched() {
    let d = scratch("r-bad-state");
    std::fs::create_dir_all(d.join("reserve")).unwrap();
    std::fs::write(d.join("reserve/last-k"), "twelve\n").unwrap();
    assert_eq!(run(&d, &["k"]), (1, String::new()));
    assert_eq!(std::fs::read_to_string(d.join("reserve/last-k")).unwrap(), "twelve\n");
    // A number past u64 is no number either; one at the very top cannot hand a next one.
    std::fs::write(d.join("reserve/last-k"), "18446744073709551616\n").unwrap();
    assert_eq!(run(&d, &["k"]).0, 1);
    std::fs::write(d.join("reserve/last-k"), "18446744073709551615\n").unwrap();
    assert_eq!(run(&d, &["k"]).0, 1);
}
