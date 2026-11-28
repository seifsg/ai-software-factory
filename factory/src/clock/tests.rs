//! The clock's writers on a real run folder: Stop turn ends, resumes from the transcript and from commands, spans.

use super::*;
use crate::hook::{Input, Reply};

fn run_dir(name: &str, waiting: &str, status: &str) -> PathBuf {
    let d = std::env::temp_dir().join(format!("factory-clock-{name}-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&d);
    std::fs::create_dir_all(d.join(".git")).unwrap();
    std::fs::create_dir_all(d.join(".factory/guard")).unwrap();
    let run =
        format!("# Run: https://x/issues/1 · fast · change\nStatus: {status}\nNext: 5 Build · get-ready-to-code\nWaiting: {waiting}\n");
    std::fs::write(d.join(".factory/run.md"), run).unwrap();
    std::fs::write(d.join(".factory/guard/steps.jsonl"), "{\"at\":\"2026-11-27T07:40:54Z\",\"step\":\"0\"}\n").unwrap();
    d
}

fn stop(d: &Path, transcript: &str, subagent: bool) -> Input {
    Input { cwd: crate::paths::text(d), transcript_path: transcript.into(), subagent_running: subagent, ..Input::default() }
}

#[test]
fn stop_stamps_owner_and_idle_waits_once_and_skips_blocked_or_subagent_turns() {
    let d = run_dir("stop", "owner: plan OK?", "open");
    let g = guard(&d);
    on_stop(&stop(&d, "", false), Some(&Reply::Block("go on".into())), &d);
    on_stop(&stop(&d, "", true), None, &d);
    assert!(stamp::read(&g).is_empty());
    on_stop(&stop(&d, "", false), None, &d);
    on_stop(&stop(&d, "", false), Some(&Reply::System("idle".into())), &d);
    let rows = stamp::read(&g);
    assert!(matches!(rows.as_slice(), [Row::Wait { owner: true, why, .. }] if why == "plan OK?"));
    active(&d, "");
    active(&d, "");
    std::fs::write(
        d.join(".factory/run.md"),
        std::fs::read_to_string(d.join(".factory/run.md")).unwrap().replace("owner: plan OK?", "none"),
    )
    .unwrap();
    on_stop(&stop(&d, "", false), None, &d);
    let rows = stamp::read(&g);
    assert!(
        matches!(rows.as_slice(), [Row::Wait { .. }, Row::Resume { .. }, Row::Wait { owner: false, why, .. }] if why == "turn ended with nothing running")
    );
    let _ = std::fs::remove_dir_all(d);
}

#[test]
fn stop_takes_the_resume_from_the_transcript_and_closes_once() {
    let d = run_dir("resume", "owner: ok?", "open");
    let g = guard(&d);
    stamp::append(
        &g,
        &Row::Wait { at: stamp::iso_secs("2026-11-27T07:42:08Z").unwrap(), owner: true, off: 0, src: String::new(), why: "ok?".into() },
    );
    let tp = d.join("t.jsonl");
    std::fs::write(&tp, "{\"type\":\"user\",\"timestamp\":\"2026-11-27T07:51:33.000Z\"}\n").unwrap();
    on_stop(&stop(&d, &crate::paths::text(&tp), false), Some(&Reply::Block("x".into())), &d);
    assert_eq!(stamp::read(&g)[1], Row::Resume { at: stamp::iso_secs("2026-11-27T07:51:33Z").unwrap() });
    let text = std::fs::read_to_string(d.join(".factory/run.md")).unwrap().replace("Status: open", "Status: closed");
    std::fs::write(d.join(".factory/run.md"), text).unwrap();
    on_stop(&stop(&d, "", false), None, &d);
    on_stop(&stop(&d, "", false), None, &d);
    assert_eq!(stamp::read(&g).iter().filter(|r| matches!(r, Row::End { .. })).count(), 1);
    let bench = std::fs::read_to_string(d.join(".factory/bench.md")).unwrap();
    assert!(bench.contains("| 2026-11-27T07:40:54Z | https://x/issues/1 | "), "{bench}");
    let r = report(&d).unwrap();
    assert!(!r.open && r.block().starts_with("```text\ntotal ") && r.json()["phases"][0]["id"] == "owner");
    let _ = std::fs::remove_dir_all(d);
}

#[test]
fn a_late_guard_call_never_hides_the_owner_reply_the_transcript_holds() {
    let d = run_dir("late", "owner: ok?", "open");
    let g = guard(&d);
    let iso = |s: &str| stamp::iso_secs(s).unwrap();
    let tp = d.join("t.jsonl");
    std::fs::write(&tp, "{\"type\":\"assistant\",\"timestamp\":\"2026-11-27T07:42:00.000Z\"}\n").unwrap();
    let off = resume::len(&crate::paths::text(&tp));
    stamp::append(&g, &Row::Wait { at: iso("2026-11-27T07:42:08Z"), owner: true, off, src: "t.jsonl".into(), why: "ok?".into() });
    let mut t = std::fs::read_to_string(&tp).unwrap();
    t.push_str("{\"type\":\"user\",\"timestamp\":\"2026-11-27T07:43:48.000Z\"}\n");
    std::fs::write(&tp, t).unwrap();
    active(&d, "");
    on_stop(&stop(&d, &crate::paths::text(&tp), false), Some(&Reply::Block("x".into())), &d);
    let r = report(&d).unwrap();
    assert_eq!(r.json()["phases"][0], serde_json::json!({"id": "owner", "label": "waiting on you", "secs": 100, "lost": 0, "why": ""}));
    // Once stamped, the same reply is not stamped again.
    on_stop(&stop(&d, &crate::paths::text(&tp), false), Some(&Reply::Block("x".into())), &d);
    assert_eq!(stamp::read(&g).iter().filter(|r| matches!(r, Row::Resume { .. })).count(), 2);
    let _ = std::fs::remove_dir_all(d);
}

#[test]
fn a_run_closed_long_ago_ends_at_its_last_write_and_a_blocked_stop_stamps_nothing() {
    let d = run_dir("old", "none", "closed");
    let run = std::fs::File::options().write(true).open(d.join(".factory/run.md")).unwrap();
    let then = std::time::UNIX_EPOCH + std::time::Duration::from_secs(stamp::iso_secs("2026-11-27T08:00:00Z").unwrap());
    run.set_modified(then).unwrap();
    drop(run);
    on_stop(&stop(&d, "", false), Some(&Reply::Block("x".into())), &d);
    assert!(stamp::read(&guard(&d)).is_empty());
    assert_eq!(report(&d).unwrap().json()["end"], "2026-11-27T08:00:00Z");
    on_stop(&stop(&d, "", false), None, &d);
    assert_eq!(stamp::read(&guard(&d)), [Row::End { at: stamp::iso_secs("2026-11-27T08:00:00Z").unwrap() }]);
    let _ = std::fs::remove_dir_all(d);
}

#[test]
fn a_worktree_run_writes_the_bench_of_its_main_checkout() {
    let root = std::env::temp_dir().join(format!("factory-clock-wt-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&root);
    let (main, wt) = (root.join("main"), root.join("wt"));
    std::fs::create_dir_all(&main).unwrap();
    let git = |dir: &Path, args: &[&str]| {
        let ok = std::process::Command::new("git")
            .arg("-C")
            .arg(dir)
            .args(["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"])
            .args(args)
            .output()
            .is_ok_and(|o| o.status.success());
        assert!(ok, "git {args:?}");
    };
    git(&main, &["init", "-q"]);
    git(&main, &["commit", "-q", "--allow-empty", "-m", "a"]);
    git(&main, &["worktree", "add", "-q", &crate::paths::text(&wt)]);
    assert_eq!(std::fs::canonicalize(bench::file(&wt)).ok(), None, "nothing written yet");
    assert_eq!(bench::file(&wt).parent().and_then(|p| std::fs::canonicalize(p.parent()?).ok()), std::fs::canonicalize(&main).ok());
    let _ = std::fs::remove_dir_all(root);
}

#[test]
fn spans_land_only_in_an_open_run() {
    let d = run_dir("span", "none", "open");
    span(&d.join("sub"), Phase::Tests, 20, 10, "full");
    let rows = stamp::read(&guard(&d));
    assert_eq!(rows, [Row::Span { from: 10, to: 10, phase: Phase::Tests, note: "full".into() }]);
    let closed = run_dir("span-closed", "none", "closed");
    span(&closed, Phase::Queue, 1, 2, "heavy");
    assert!(stamp::read(&guard(&closed)).is_empty());
    let _ = std::fs::remove_dir_all(d);
    let _ = std::fs::remove_dir_all(closed);
}

#[test]
fn a_guard_call_stamps_the_owner_reply_from_the_transcript() {
    let d = run_dir("active", "owner: ok?", "open");
    let g = guard(&d);
    let iso = |s: &str| stamp::iso_secs(s).unwrap();
    let tp = d.join("t.jsonl");
    std::fs::write(&tp, "{\"type\":\"user\",\"timestamp\":\"2026-11-27T07:43:48.000Z\"}\n").unwrap();
    // The wait's offset belongs to another session's transcript: the search starts at this one's beginning.
    stamp::append(&g, &Row::Wait { at: iso("2026-11-27T07:42:08Z"), owner: true, off: 999, src: "other.jsonl".into(), why: "ok?".into() });
    active(&d, &crate::paths::text(&tp));
    assert_eq!(stamp::read(&g)[1], Row::Resume { at: iso("2026-11-27T07:43:48Z") });
    let _ = std::fs::remove_dir_all(d);
}
