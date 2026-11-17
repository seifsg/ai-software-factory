//! The background suite can hold a real process while its launch proof is already available.

mod common;

use common::{factory, git, scratch};
use std::fs;
use std::path::Path;
use std::time::{Duration, Instant};

#[test]
#[ignore = "run by the background receipt test as its suite"]
fn blocking_suite() {
    assert!(wait_for(Path::new(".factory/release-suite")));
    println!("suite output reached the log");
}

fn wait_for(path: &Path) -> bool {
    let until = Instant::now() + Duration::from_secs(12);
    while !path.is_file() && Instant::now() < until {
        std::thread::sleep(Duration::from_millis(20));
    }
    path.is_file()
}

#[test]
fn proves_the_live_launch_then_records_one_pass() {
    let dir = scratch("start-suite");
    git(&dir, &["init", "-q"], 8);
    fs::write(dir.join("code.txt"), "tracked\n").unwrap();
    git(&dir, &["add", "code.txt"], 8);
    git(&dir, &["commit", "-qm", "base"], 8);
    let (code, info) = factory(&dir, &dir, &["tree"], "");
    assert_eq!(code, 0, "{info}");
    let tree = info.trim();
    let prefix = dir.join(".factory/receipts").join(format!("{tree}-full"));
    let (code, output) = factory(&dir, &dir, &["receipt", "start", "--", "factory-no-such-suite-program"], "");
    assert_ne!(code, 0, "{output}");
    assert!(!prefix.with_extension("launch.txt").exists());
    let helper = std::env::current_exe().unwrap();
    let cmd = [helper.to_str().unwrap(), "--ignored", "--exact", "blocking_suite", "--nocapture"];
    let mut args = vec!["receipt", "start", "--suite", "full", "--"];
    args.extend(cmd);
    let (code, output) = factory(&dir, &dir, &args, "");
    assert_eq!(code, 0, "{output}");
    assert!(output.starts_with("started "), "{output}");
    let launch = fs::read_to_string(prefix.with_extension("launch.txt")).unwrap();
    assert!(launch.starts_with("factory-suite-launch 1\n"));
    assert!(launch.contains(&format!("tree {tree}\nclean yes\nmode background\n")));
    assert!(launch.contains("\npid "));
    let done = prefix.with_extension("txt");
    assert!(!done.exists());

    let (code, duplicate) = factory(&dir, &dir, &args, "");
    assert_ne!(code, 0, "{duplicate}");
    assert!(duplicate.contains("reserved suite"), "{duplicate}");
    args[1] = "run";
    let (code, foreground) = factory(&dir, &dir, &args, "");
    assert_ne!(code, 0, "{foreground}");
    assert!(foreground.contains("reserved suite"), "{foreground}");
    fs::write(dir.join(".factory/release-suite"), "").unwrap();
    assert!(wait_for(&done), "{} did not receive a receipt", done.display());
    let result = fs::read_to_string(done).unwrap();
    for field in ["clean yes", "result PASS", "runs 1", "passes 1", "log "] {
        assert!(result.contains(field), "missing {field} in {result}");
    }
    assert!(fs::read_to_string(prefix.with_extension("log")).unwrap().contains("suite output reached the log"));
    let _ = fs::remove_dir_all(dir);
}
