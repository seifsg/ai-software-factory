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
    active(&d);
    active(&d);
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
    stamp::append(&g, &Row::Wait { at: stamp::iso_secs("2026-11-27T07:42:08Z").unwrap(), owner: true, why: "ok?".into() });
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
