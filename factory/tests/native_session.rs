mod common;

use std::fs;
use std::path::{Path, PathBuf};
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

fn setup(name: &str) -> (PathBuf, PathBuf, PathBuf) {
    let root = common::scratch(name);
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
    (run, home, cache)
}

#[test]
fn native_begin_binds_the_child_and_rejects_unsafe_or_ambiguous_identity() {
    let (run, home, cache) = setup("native-init");
    let result = begin(&run, &home, &cache, "child");
    assert!(result.status.success(), "{}", String::from_utf8_lossy(&result.stderr));
    let route = cache.join("ai-software-factory/sessions/child");
    let saved = fs::read_to_string(route).unwrap();
    let target = saved.strip_suffix('\n').expect("newline-terminated route");
    // macOS spells the same temporary directory as /var or /private/var.
    assert_eq!(fs::canonicalize(target).unwrap(), fs::canonicalize(&run).unwrap());
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

#[test]
fn prebound_native_sessions_still_relay_at_the_night_phase_boundary() {
    for reused in [true, false] {
        let (run, home, cache) = setup(if reused { "native-night-reused" } else { "native-night" });
        if reused {
            fs::create_dir_all(run.join(".factory/guard")).unwrap();
            fs::write(run.join(".factory/guard/state"), "g_ticks='6'\ng_session='prior'\ng_sessions='prior'\ng_sstep='4'\n").unwrap();
        }
        assert!(begin(&run, &home, &cache, "child").status.success());
        let transcript = home.join("sessions/2026/01/01/rollout-child.jsonl");
        use std::io::Write;
        writeln!(
            fs::OpenOptions::new().append(true).open(&transcript).unwrap(),
            "{{\"type\":\"event_msg\",\"payload\":{{\"message\":\"fixture_gate_a\"}}}}"
        )
        .unwrap();
        let state = run.join(".factory/guard/state");
        let until = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() + 3600;
        let text = fs::read_to_string(&state).unwrap().replace("g_night_until=''", &format!("g_night_until='{until}'"));
        fs::write(&state, text).unwrap();
        let input = serde_json::json!({
            "session_id": "child", "cwd": common::json_path(&run),
            "transcript_path": common::json_path(&transcript),
        });
        assert_eq!(common::factory(&run, &cache, &["guard", "stop"], &input.to_string()).0, 0);
        let mut last = String::new();
        for (id, name) in [("0", "Ticket"), ("1", "Analyze"), ("2", "Recommend"), ("2b", "Challenge"), ("3", "Plan")] {
            let mut block = format!("## {id} {name}\nfixture\n");
            if id == "3" {
                block.push_str("Gate A: PASS (checker fixture_gate_a) @aaaaaaa\n");
            }
            // The bound chat holds no post of it: the first stdin try is refused, the second taken.
            let (code, output) = common::factory(&run, &cache, &["guard", "step", id], &block);
            assert!(code == 2 && output.contains("refused, nothing written"), "{output}");
            let (code, output) = common::factory(&run, &cache, &["guard", "step", id], &block);
            assert_eq!(code, 0, "{output}");
            last = output;
        }
        assert!(last.contains("Relay (night phase boundary before step 4)"), "reused={reused}: {last}");
    }
}
