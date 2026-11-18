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
    factory_in(dir, session, args, b"")
}

/// The same, with `input` on stdin.
fn factory_in(dir: &Path, session: &str, args: &[&str], input: &[u8]) -> (i32, String) {
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
    child.stdin.take().unwrap().write_all(input).unwrap();
    let out = child.wait_with_output().unwrap();
    (out.status.code().unwrap_or(-1), format!("{}{}", String::from_utf8_lossy(&out.stdout), String::from_utf8_lossy(&out.stderr)))
}

/// `t` as a transcript timestamp, `YYYY-MM-DDTHH:MM:SS.000Z`.
fn time_iso(t: std::time::SystemTime) -> String {
    let s = t.duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() as i64;
    let (days, rem) = (s.div_euclid(86_400), s.rem_euclid(86_400));
    // Civil date from days since 1970-01-01 (Howard Hinnant's algorithm).
    let z = days + 719_468;
    let (era, doe) = (z.div_euclid(146_097), z.rem_euclid(146_097));
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let (d, m) = (doy - (153 * mp + 2) / 5 + 1, if mp < 10 { mp + 3 } else { mp - 9 });
    let y = yoe + era * 400 + i64::from(m <= 2);
    format!("{y:04}-{m:02}-{d:02}T{:02}:{:02}:{:02}.000Z", rem / 3600, rem % 3600 / 60, rem % 60)
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
    assert!(out.contains("no `## 3 Plan` block: pipe it in full, its one copy") && out.contains("<<'EOF'"), "{out}");
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
fn a_piped_block_is_its_one_copy_and_never_asked_for_in_chat() {
    let dir = scratch("guard-piped");
    let f = dir.join(".factory");
    fs::create_dir_all(&f).unwrap();
    fs::create_dir_all(dir.join("cfg/projects/p")).unwrap();
    fs::write(dir.join("cfg/projects/p/s1.jsonl"), "").unwrap();
    fs::write(f.join("run.md"), RUN).unwrap();
    // A readable chat with no post: stdin is taken at once, and the step joins the written list.
    let (code, out) = factory_in(&dir, "s1", &["guard", "step", "3"], b"## 3 Plan\n**Files:** `a.html` (new)\n");
    assert!(code == 0 && !out.contains("not posted in chat"), "{out}");
    let (code, out) = factory_in(&dir, "s1", &["guard", "step", "4"], b"## 4 Before\nsaved\n");
    assert!(code == 0 && !out.contains("not posted in chat"), "{out}");
    assert_eq!(fs::read_to_string(f.join("guard/written")).unwrap_or_default(), "3\n4\n");

    // A post made after the last step counts even when the run file was written since (a `guard wait`).
    let now = std::time::SystemTime::now();
    let ts = time_iso(now);
    fs::write(dir.join("cfg/projects/p/s1.jsonl"), post(&ts, "## 5 Build\\nT1 pre: a do: b post: c ✔")).unwrap();
    let later = now + std::time::Duration::from_secs(120);
    fs::File::options().write(true).open(f.join("run.md")).unwrap().set_modified(later).unwrap();
    let (code, out) = factory(&dir, "s1", &["guard", "step", "5"]);
    assert!(code == 0 && fs::read_to_string(f.join("run.md")).unwrap().contains("## 5 Build ✔"), "{out}");

    // A coordinator running as a subagent posts in its own file beside the session's: that post counts.
    let subs = dir.join("cfg/projects/p/s1/subagents");
    fs::create_dir_all(&subs).unwrap();
    fs::write(subs.join("agent-x.jsonl"), post("2999-01-01T00:00:00.000Z", "## 6 Verify\\nchecked")).unwrap();
    let (code, out) = factory(&dir, "s1", &["guard", "step", "6"]);
    assert!(code == 0 && fs::read_to_string(f.join("run.md")).unwrap().contains("## 6 Verify ✔\nchecked"), "{out}");
    assert_eq!(factory(&dir, "s1", &["guard", "step", "9"]).0, 2, "no such step");
    let _ = fs::remove_dir_all(dir);
}

#[test]
fn only_a_hand_ticked_step_is_asked_for_in_chat() {
    let dir = scratch("guard-written-nag");
    let f = dir.join(".factory");
    fs::create_dir_all(&f).unwrap();
    let tp = dir.join("cfg/projects/p/s1.jsonl");
    fs::create_dir_all(tp.parent().unwrap()).unwrap();
    // A Claude Code transcript (it carries isSidechain) with no block posted in it.
    fs::write(&tp, "{\"isSidechain\":false,\"type\":\"user\",\"message\":{\"role\":\"user\",\"content\":\"go\"}}\n").unwrap();
    fs::write(f.join("run.md"), "# Run: local fixture · Fast · change\nStatus: open\nNext: 1 Analyze · analyze-start\nWaiting: none\n\n## 0 Ticket ✔\nby hand\n## 1 Analyze\n").unwrap();
    // The Stop hook's record of this session and its transcript, as it keeps it.
    fs::create_dir_all(f.join("guard")).unwrap();
    let state = format!("g_ticks='1'\ng_session='s1'\ng_sessions='s1'\ng_transcript='{}'\n", common::json_path(&tp));
    fs::write(f.join("guard/state"), state).unwrap();
    let (code, out) = factory_in(&dir, "s1", &["guard", "step", "1"], b"## 1 Analyze\na\n");
    assert_eq!(code, 0, "{out}");
    assert!(out.contains("not posted in chat: 0.") && !out.contains("as your last message"), "the hand-ticked step 0 only: {out}");
    // A later step still asks only for step 0, never for step 1, which `guard step` wrote.
    fs::remove_file(f.join("guard/unposted")).ok();
    let (code, out) = factory_in(&dir, "s1", &["guard", "step", "2"], b"## 2 Recommend\nb\n");
    assert!(code == 0 && out.contains("not posted in chat: 0.") && !out.contains("0,1"), "{out}");
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
