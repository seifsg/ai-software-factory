//! The full suite runs once per tree: a run with one passing full run on its final head finishes; a second
//! run on that unchanged tree is flagged once, and Gate C stops standing on a receipt that counts two runs.
//! `receipt run` reuses a PASS already on the tree and never runs the suite again unless told `--again`.

mod common;

use common::{factory, git, json_path};
use std::path::{Path, PathBuf};

const STEPS: [&str; 10] =
    ["0 Ticket", "1 Analyze", "2 Recommend", "2b Challenge", "3 Plan", "4 Before", "5 Build", "6 Verify", "7 PR", "8 Review"];

/// A closed run in `<d>/r` (no remote: HEAD counts as pushed), every gate and the review on HEAD, each backed
/// by its delegate's handback in `<d>/hp/s1/subagents`. Returns the checkout.
fn closed_run(d: &Path) -> PathBuf {
    let r = d.join("r");
    std::fs::create_dir_all(r.join(".factory")).unwrap();
    git(&r, &["init", "-q", "-b", "main"], 8);
    std::fs::write(r.join("a.txt"), "a\n").unwrap();
    git(&r, &["add", "a.txt"], 8);
    git(&r, &["commit", "-q", "-m", "a"], 8);
    let sha = std::process::Command::new("git").arg("-C").arg(&r).args(["rev-parse", "HEAD"]).output().unwrap();
    let sha = String::from_utf8_lossy(&sha.stdout).trim().to_string();
    let a = d.join("hp/s1/subagents");
    std::fs::create_dir_all(&a).unwrap();
    let say = |text: &str| format!("{{\"message\":{{\"role\":\"assistant\",\"content\":[{{\"type\":\"text\",\"text\":\"{text}\"}}]}}}}\n");
    for g in ['A', 'B', 'C'] {
        let body = format!("{{\"message\":\"Role: checker. Gate {g}\"}}\n{}", say(&format!("Gate {g}: PASS @{sha}")));
        std::fs::write(a.join(format!("agent-c{g}.jsonl")), body).unwrap();
    }
    std::fs::write(a.join("agent-r.jsonl"), format!("{{\"message\":\"Role: reviewer.\"}}\n{}", say(&format!("verdict: ready @{sha}"))))
        .unwrap();
    let mut run = String::from("# Run: x\nStatus: closed\nNext: none (closed)\nWaiting: none\n\n");
    STEPS.iter().for_each(|s| run.push_str(&format!("## {s} \u{2714}\n")));
    run.push_str(&format!(
        "Gate A: PASS (checker cA) @{sha}\nGate B: PASS (checker cB) @{sha}\nReview: ready (reviewer r) @{sha}\nGate C: PASS (checker cC) @{sha}\n"
    ));
    std::fs::write(r.join(".factory/run.md"), run).unwrap();
    r
}

/// The Stop hook's reply for session s1 in checkout `r`.
fn stop(d: &Path, r: &Path) -> String {
    let json = format!(
        r#"{{"session_id":"s1","transcript_path":"{}","cwd":"{}","stop_hook_active":false,"last_assistant_message":"x"}}"#,
        json_path(&d.join("hp/s1.jsonl")),
        json_path(r)
    );
    factory(r, d, &["guard", "stop"], &json).1
}

/// `factory receipt run` with the binary itself as a suite that passes.
fn suite(d: &Path, r: &Path, again: bool) -> (i32, String) {
    let exe = env!("CARGO_BIN_EXE_factory");
    let mut args = vec!["receipt", "run", "--suite", "full"];
    if again {
        args.push("--again");
    }
    args.extend(["--", exe, "--version"]);
    factory(r, d, &args, "")
}

fn runs_line(r: &Path) -> String {
    let rd = std::fs::read_dir(r.join(".factory/receipts")).unwrap();
    let f = rd.flatten().find(|e| e.file_name().to_string_lossy().ends_with("-full.txt")).unwrap();
    std::fs::read_to_string(f.path()).unwrap().lines().find(|l| l.starts_with("runs ")).unwrap_or("").to_string()
}

#[test]
fn gate_b_can_advance_while_the_final_suite_runs() {
    let d = common::scratch("pending-pr");
    let r = closed_run(&d);
    let run_path = r.join(".factory/run.md");
    let closed = std::fs::read_to_string(&run_path).unwrap();
    let prior_to_pr = closed
        .lines()
        .filter(|line| !["## 7 PR", "## 8 Review", "Review:", "Gate C:"].iter().any(|prefix| line.starts_with(prefix)))
        .collect::<Vec<_>>()
        .join("\n")
        .replace("Status: closed", "Status: open")
        .replace("Next: none (closed)", "Next: 7 PR · how-to-make-a-pr");
    std::fs::write(&run_path, prior_to_pr).unwrap();
    let next = stop(&d, &r);
    assert!(next.contains("Step 7 PR"), "Gate B lets the draft advance while the suite runs: {next}");
    let (code, report) = factory(&r, &d, &["guard", "check"], "");
    assert_eq!(code, 0, "{report}");
    assert!(report.contains("Gate B: backed:"), "{report}");

    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn a_run_with_one_full_suite_finishes() {
    let d = common::scratch("once");
    let r = closed_run(&d);
    let missing = stop(&d, &r);
    assert!(missing.contains("Gate C has no full-suite receipt"), "no receipt yet: {missing}");
    let (code, out) = suite(&d, &r, false);
    assert_eq!(code, 0, "{out}");
    assert_eq!(runs_line(&r), "runs 1");
    assert_eq!(stop(&d, &r), "", "one passing full run on the final head: the run is finished");
    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn a_second_run_on_the_same_tree_is_reused_or_flagged() {
    let d = common::scratch("twice");
    let r = closed_run(&d);
    suite(&d, &r, false);
    let (code, out) = suite(&d, &r, false);
    assert!(code == 0 && out.contains("reused, not run again"), "an unchanged tree reuses its PASS: {out}");
    assert_eq!(runs_line(&r), "runs 1");
    let (code, _) = suite(&d, &r, true);
    assert_eq!(code, 0);
    assert_eq!(runs_line(&r), "runs 2");
    let flag = stop(&d, &r);
    assert!(
        flag.contains("\"decision\":\"block\"") && flag.contains("ran more than once on an unchanged tree") && flag.contains(": 2 runs"),
        "{flag}"
    );
    let gate = stop(&d, &r);
    assert!(
        gate.contains("Gate C needs exactly one passing full-suite run") && gate.contains("counts 2"),
        "flagged once, then Gate C: {gate}"
    );
    let _ = std::fs::remove_dir_all(&d);
}

fn head(r: &Path) -> String {
    let out = std::process::Command::new("git").arg("-C").arg(r).args(["rev-parse", "HEAD"]).output().unwrap();
    String::from_utf8_lossy(&out.stdout).trim().to_string()
}

#[test]
fn protected_git_index_still_proves_a_clean_receipt() {
    let d = common::scratch("protected-git");
    let r = closed_run(&d);
    std::fs::write(r.join(".git/info/exclude"), ".factory/\n").unwrap();
    std::fs::create_dir(r.join(format!(".git/factory-tree-{}.index", std::process::id()))).unwrap();

    let expected_head = head(&r);
    let receipt = || factory::receipt::stamp(&r, "full", true, "suite", 1, "test", "");
    let (_, saved) = receipt().expect("clean checkout can use its commit tree");
    assert!(saved.clean);
    assert_eq!(saved.head, expected_head);
    let repo = factory::git::Repo::discover(&r).unwrap();
    assert_eq!(saved.tree, repo.commit_tree(&expected_head).unwrap());

    std::fs::write(r.join("untracked.txt"), "work\n").unwrap();
    assert!(receipt().is_err(), "untracked work cannot borrow HEAD's tree");
    std::fs::remove_file(r.join("untracked.txt")).unwrap();
    std::fs::write(r.join("a.txt"), "different\n").unwrap();
    assert!(receipt().is_err(), "tracked edits cannot borrow HEAD's tree");
    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn successful_suite_without_a_writable_receipt_is_an_error() {
    let d = common::scratch("receipt-write-fails");
    let r = closed_run(&d);
    std::fs::write(r.join(".factory/receipts"), "blocks the receipt directory").unwrap();
    let (code, out) = suite(&d, &r, false);
    assert_ne!(code, 0, "a PASS with no written receipt is not a successful command");
    assert!(out.contains("cannot write the receipt"), "{out}");
    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn a_failed_run_then_a_pass_counts_one_pass() {
    let d = common::scratch("fail-pass");
    let r = closed_run(&d);
    let (code, _) = factory(&r, &d, &["receipt", "run", "--suite", "full", "--", env!("CARGO_BIN_EXE_factory"), "no-such-command"], "");
    assert_ne!(code, 0, "the failing suite's own code");
    let (code, out) = suite(&d, &r, false);
    assert_eq!(code, 0, "a FAIL is never reused: {out}");
    assert!(
        std::fs::read_dir(r.join(".factory/receipts")).unwrap().flatten().any(|e| {
            std::fs::read_to_string(e.path()).is_ok_and(|t| t.contains("\nruns 2\npasses 1\n") && t.contains("\nresult PASS\n"))
        })
    );
    assert_eq!(stop(&d, &r), "", "one passing run: Gate C stands and the run is finished (a finished run is never flagged)");
    let (code, report) = factory(&r, &d, &["guard", "check"], "");
    assert_eq!(code, 0, "{report}");
    assert!(report.contains("Gate C: backed:"), "{report}");
    let _ = std::fs::remove_dir_all(&d);
}

#[test]
fn a_review_with_no_receipt_for_its_commit_is_not_backed() {
    let d = common::scratch("review-receipt");
    let r = closed_run(&d);
    suite(&d, &r, false);
    std::fs::write(r.join("a.txt"), "b\n").unwrap();
    git(&r, &["commit", "-q", "-am", "b"], 9);
    let new = head(&r);
    let run = std::fs::read_to_string(r.join(".factory/run.md")).unwrap();
    let run: String = run
        .lines()
        .map(|l| if l.starts_with("Review: ") { format!("Review: ready (reviewer r) @{new}\n") } else { format!("{l}\n") })
        .collect();
    std::fs::write(r.join(".factory/run.md"), run).unwrap();
    let a = d.join("hp/s1/subagents/agent-r.jsonl");
    let body = std::fs::read_to_string(&a).unwrap();
    let old = body.rsplit_once("verdict: ready @").map(|(_, s)| s[..40].to_string()).unwrap();
    std::fs::write(&a, body.replace(&old, &new)).unwrap();
    stop(&d, &r);
    let (code, report) = factory(&r, &d, &["guard", "check"], "");
    assert_eq!(code, 1, "{report}");
    let line = report.lines().find(|l| l.starts_with("Review:")).unwrap_or("");
    assert!(line.contains("NOT backed") && line.contains(&format!("no full-suite receipt for the tree of {new}")), "{report}");
    let _ = std::fs::remove_dir_all(&d);
}
