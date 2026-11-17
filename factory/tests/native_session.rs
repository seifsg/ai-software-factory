mod common;

use std::fs;
use std::path::Path;
use std::process::{Command, Output, Stdio};

fn begin(run: &Path, home: &Path, cache: &Path, thread: &str) -> Output {
    Command::new(env!("CARGO_BIN_EXE_factory"))
        .args(["guard", "begin"])
        .current_dir(run)
        .env("CODEX_HOME", home)
        .env("XDG_CACHE_HOME", cache)
        .env("CODEX_THREAD_ID", thread)
        .env("CODEX_SESSION_ID", "parent")
        .stdin(Stdio::null())
        .output()
        .unwrap()
}

#[test]
fn native_begin_binds_the_child_and_rejects_unsafe_or_ambiguous_identity() {
    let root = common::scratch("native-init");
    let run = root.join("work");
    let home = root.join("codex");
    let cache = root.join("cache");
    fs::create_dir_all(run.join(".factory")).unwrap();
    fs::create_dir_all(home.join("sessions/2026/01/01")).unwrap();
    fs::write(run.join(".factory/run.md"), "# Run: test\nStatus: open\nNext: 0 Ticket · ticketing\nWaiting: none\n").unwrap();
    for id in ["parent", "child"] {
        fs::write(
            home.join(format!("sessions/2026/01/01/rollout-{id}.jsonl")),
            format!("{{\"type\":\"session_meta\",\"payload\":{{\"id\":\"{id}\"}}}}\n"),
        )
        .unwrap();
    }
    let result = begin(&run, &home, &cache, "child");
    assert!(result.status.success(), "{}", String::from_utf8_lossy(&result.stderr));
    let route = cache.join("ai-software-factory/sessions/child");
    assert_eq!(fs::read_to_string(route).unwrap(), format!("{}\n", common::json_path(&run)));
    assert!(!cache.join("ai-software-factory/sessions/parent").exists());
    let state = fs::read_to_string(run.join(".factory/guard/state")).unwrap();
    assert!(state.contains("g_session='child'"));
    assert!(state.contains("rollout-child.jsonl"));
    assert_eq!(fs::read_to_string(run.join(".factory/guard/steps.jsonl")).unwrap().lines().count(), 1);

    for id in ["../escape", "missing"] {
        assert!(!begin(&run, &home, &cache, id).status.success());
        assert_eq!(fs::read_to_string(run.join(".factory/guard/state")).unwrap(), state);
    }
    fs::create_dir_all(home.join("sessions/2026/01/02")).unwrap();
    fs::copy(home.join("sessions/2026/01/01/rollout-child.jsonl"), home.join("sessions/2026/01/02/rollout-child.jsonl")).unwrap();
    assert!(!begin(&run, &home, &cache, "child").status.success());
    assert_eq!(fs::read_to_string(run.join(".factory/guard/state")).unwrap(), state);
}
