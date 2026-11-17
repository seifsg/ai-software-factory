//! Common review evidence stays pinned to committed text even when the worktree has changed.

mod common;

use common::{factory, git};
use std::path::Path;

fn head(dir: &Path) -> String {
    let out = std::process::Command::new("git").current_dir(dir).args(["rev-parse", "HEAD"]).output().unwrap();
    assert!(out.status.success());
    String::from_utf8(out.stdout).unwrap().trim().into()
}

#[test]
fn packet_shares_committed_context_and_only_named_run_proof() {
    let dir = common::scratch("review-packet");
    git(&dir, &["init", "-q"], 8);
    std::fs::write(dir.join("context.md"), "committed context\n").unwrap();
    std::fs::write(dir.join("code.txt"), "first line\nold value\nlast line\n").unwrap();
    git(&dir, &["add", "code.txt", "context.md"], 8);
    git(&dir, &["commit", "-qm", "base"], 8);
    let base = head(&dir);
    std::fs::write(dir.join("code.txt"), "first line\nnew value\nlast line\n").unwrap();
    git(&dir, &["commit", "-qam", "candidate"], 8);
    let candidate = head(&dir);
    std::fs::write(dir.join("code.txt"), "dirty worktree\n").unwrap();
    std::fs::write(dir.join("context.md"), "dirty context\n").unwrap();
    let run = dir.join(".factory");
    std::fs::create_dir(&run).unwrap();
    for (name, content) in [
        ("ticket.md", "requested behavior\n"),
        ("run.md", "## 5 Build ✔\nbuild evidence\n## 6 Verify ✔\nother verdict\n"),
        ("proof.txt", "named proof\n"),
        ("private.txt", "unselected proof\n"),
    ] {
        std::fs::write(run.join(name), content).unwrap();
    }
    let args = ["review", "packet", "--base", &base, "--head", &candidate, "--context", "context.md", "--proof", ".factory/proof.txt"];
    let (code, packet) = factory(&dir, &dir, &args, "");
    assert_eq!(code, 0, "{packet}");
    for text in ["requested behavior", "build evidence", "named proof", "committed context", " first line", "+new value", " last line"] {
        assert!(packet.contains(text), "missing {text}: {packet}");
    }
    for text in ["dirty worktree", "dirty context", "unselected proof", "other verdict"] {
        assert!(!packet.contains(text), "unexpected {text}: {packet}");
    }
    let missing = ["review", "packet", "--base", &base, "--head", &candidate, "--proof", ".factory/missing.txt"];
    let (code, err) = factory(&dir, &dir, &missing, "");
    assert_ne!(code, 0, "{err}");
    assert!(err.contains("missing.txt"), "{err}");
    std::fs::remove_file(run.join("ticket.md")).unwrap();
    std::fs::write(run.join("run.md"), "## 0 Ticket ✔\nTracker ticket and acceptance criteria\n## 5 Build ✔\nbuild evidence\n").unwrap();
    let (code, packet) = factory(&dir, &dir, &args, "");
    assert_eq!(code, 0, "{packet}");
    assert!(packet.contains("Tracker ticket and acceptance criteria"), "{packet}");
    let _ = std::fs::remove_dir_all(dir);
}
