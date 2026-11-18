//! `guard step` with no stdin takes the block posted in chat from this session's transcript, only when posted after
//! the run file's last write; `guard wait` sets `Waiting:`.

mod common;

use common::scratch;
use std::fs;
use std::io::Write;
use std::path::Path;
use std::process::{Command, Stdio};

const RUN: &str = "# Run: local fixture · Fast · change\nStatus: open\nNext: 3 Plan · get-ready-to-code\nWaiting: none\n\n\
                   ## 0 Ticket ✔\n## 1 Analyze ✔\n## 2 Recommend ✔\n## 2b Challenge ✔\n## 3 Plan\n";

/// The binary in `dir`, empty stdin, `session` as Claude Code's session id and `dir/cfg` as its config folder.
fn factory(dir: &Path, session: &str, args: &[&str]) -> (i32, String) {
    let mut child = Command::new(env!("CARGO_BIN_EXE_factory"))
        .args(args)
        .current_dir(dir)
        .env("HOME", dir)
        .env("USERPROFILE", dir)
        .env("XDG_CACHE_HOME", dir)
        .env("CLAUDE_CONFIG_DIR", dir.join("cfg"))
        .env("CLAUDE_CODE_SESSION_ID", session)
        .env_remove("PWD")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("run factory");
    child.stdin.take().unwrap().write_all(b"").unwrap();
    let out = child.wait_with_output().unwrap();
    (out.status.code().unwrap_or(-1), format!("{}{}", String::from_utf8_lossy(&out.stdout), String::from_utf8_lossy(&out.stderr)))
}

/// One assistant message: the chat post, and the tool call that carries no block.
fn post(ts: &str, text: &str) -> String {
    format!(
        "{{\"timestamp\":\"{ts}\",\"type\":\"assistant\",\"message\":{{\"role\":\"assistant\",\"content\":[{{\"type\":\"text\",\"text\":\"{text}\"}},{{\"type\":\"tool_use\",\"input\":{{\"command\":\"factory guard step 3\"}}}}]}}}}\n"
    )
}

#[test]
fn step_takes_a_fresh_post_only_and_wait_sets_the_line() {
    let dir = scratch("guard-posted");
    let f = dir.join(".factory");
    fs::create_dir_all(&f).unwrap();
    fs::write(f.join("run.md"), RUN).unwrap();
    let proj = dir.join("cfg/projects/p");
    fs::create_dir_all(&proj).unwrap();
    let tp = proj.join("s1.jsonl");

    // A post older than the run file's last write (another turn, another session) is never taken.
    fs::write(&tp, post("2000-01-01T00:00:00.000Z", "## 3 Plan\\nstale")).unwrap();
    let (code, out) = factory(&dir, "s1", &["guard", "step", "3"]);
    assert_eq!(code, 2, "{out}");
    assert!(out.contains("posted since the run file's last write"), "{out}");
    assert_eq!(fs::read_to_string(f.join("run.md")).unwrap(), RUN);

    // A fresh post is written, ticked and moves Next; another session's id finds nothing.
    fs::write(&tp, post("2999-01-01T00:00:00.000Z", "## 3 Plan\\n**Files:** `a.html` (new)")).unwrap();
    assert_eq!(factory(&dir, "other", &["guard", "step", "3"]).0, 2);
    let (code, out) = factory(&dir, "s1", &["guard", "step", "3"]);
    assert_eq!(code, 0, "{out}");
    let run = fs::read_to_string(f.join("run.md")).unwrap();
    assert!(run.contains("## 3 Plan ✔\n**Files:** `a.html` (new)\n"), "{run}");
    assert!(run.contains("Next: 4 Before"), "{run}");

    let (code, out) = factory(&dir, "s1", &["guard", "wait", "jobs:", "gate", "A", "checker", "(max", "3", "min)"]);
    assert_eq!(code, 0, "{out}");
    assert!(fs::read_to_string(f.join("run.md")).unwrap().contains("\nWaiting: jobs: gate A checker (max 3 min)\n"));
    for bad in [&["guard", "wait", "later"][..], &["guard", "wait", "jobs:", "x", "(max", "0", "min)"], &["guard", "wait", "owner:", "a\nb"]] {
        assert_eq!(factory(&dir, "s1", bad).0, 2, "{bad:?}");
    }
    let _ = fs::remove_dir_all(dir);
}

#[test]
fn a_step_reply_names_the_long_line_and_the_gate_at_once() {
    let dir = scratch("guard-all-problems");
    let f = dir.join(".factory");
    fs::create_dir_all(&f).unwrap();
    let long = "x".repeat(320);
    fs::write(
        f.join("run.md"),
        format!(
            "# Run: local fixture · Fast · change\nStatus: open\nNext: 6 Verify · deep-review\nWaiting: none\n\n\
             ## 0 Ticket ✔\n## 1 Analyze ✔\n## 2 Recommend ✔\n## 2b Challenge ✔\n## 3 Plan ✔\nold\n\n## 4 Before\n\n## 5 Build ✔\n"
        ),
    )
    .unwrap();
    let (code, out) = common::factory(&dir, &dir, &["guard", "step", "3"], &format!("## 3 Plan\n**Files:** a `b`\n{long}\n"));
    assert_eq!(code, 0, "{out}");
    // One reply: the long line by number and start, then the open gate (the Stop hook would name only the first).
    let (lines, gate) = (out.find("over 300 characters: 12 (`xxx"), out.find("Gate A has not passed"));
    assert!(lines.is_some() && gate.is_some() && lines < gate, "{out}");
    let _ = fs::remove_dir_all(dir);
}
