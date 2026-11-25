//! A PASS carries to a later tree only when Git shows every changed path matches its inert globs, and
//! `receipt check --wait` blocks in one call until a PASS, a FAIL on the exact tree, or the deadline.

mod common;

use common::{factory, git, scratch};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

/// A repo with `src/lib.rs` and `docs/a.md` committed, and the tree id of that commit.
fn repo(name: &str) -> (PathBuf, String) {
    let dir = scratch(name);
    git(&dir, &["init", "-q"], 8);
    fs::create_dir_all(dir.join("src")).unwrap();
    fs::create_dir_all(dir.join("docs")).unwrap();
    fs::write(dir.join("src/lib.rs"), "code\n").unwrap();
    fs::write(dir.join("docs/a.md"), "words\n").unwrap();
    git(&dir, &["add", "-A"], 8);
    git(&dir, &["commit", "-qm", "base"], 8);
    let (code, tree) = factory(&dir, &dir, &["tree"], "");
    assert_eq!(code, 0, "{tree}");
    (dir, tree.trim().to_string())
}

/// `receipt write` for the work tree as it is, with extra options.
fn write(dir: &Path, result: &str, extra: &[&str]) -> (i32, String) {
    let mut args = vec!["receipt", "write", "--cmd", "suite", "--result", result];
    args.extend(extra);
    factory(dir, dir, &args, "")
}

/// Edits the named files and commits them.
fn change(dir: &Path, files: &[&str]) {
    for f in files {
        fs::write(dir.join(f), "changed\n").unwrap();
    }
    git(dir, &["commit", "-qam", "change"], 9);
}

#[test]
fn docs_only_change_carries_the_pass() {
    let (dir, tree) = repo("carry-docs");
    let (code, out) = write(&dir, "PASS", &["--inert", "docs/**", "--inert", "*.md"]);
    assert_eq!(code, 0, "{out}");
    let receipt = fs::read_to_string(dir.join(format!(".factory/receipts/{tree}-full.txt"))).unwrap();
    assert!(receipt.contains("inert docs/**\ninert *.md\n"), "{receipt}");
    let (code, exact) = factory(&dir, &dir, &["receipt", "check"], "");
    assert_eq!(code, 0, "{exact}");
    assert!(exact.trim_end().ends_with(&format!("{tree}-full.txt")), "exact hit output stays the bare path: {exact}");
    change(&dir, &["docs/a.md"]);
    let (code, out) = factory(&dir, &dir, &["receipt", "check"], "");
    assert_eq!(code, 0, "{out}");
    assert!(
        out.contains(&format!("{tree}-full.txt (carried from tree {}: 1 inert paths changed (inert: docs/**, *.md))", &tree[..12])),
        "{out}"
    );
    // `run` reuses the carried PASS: the missing program would fail if it ran.
    let (code, out) = factory(&dir, &dir, &["receipt", "run", "--", "factory-no-such-suite-program"], "");
    assert_eq!(code, 0, "{out}");
    assert!(out.contains("carried from tree") && out.contains("reused"), "{out}");
    let (code, out) = factory(&dir, &dir, &["receipt", "run", "--again", "--", "factory-no-such-suite-program"], "");
    assert_ne!(code, 0, "`--again` runs the suite: {out}");
    let _ = fs::remove_dir_all(dir);
}

#[test]
fn start_hands_the_globs_to_its_worker() {
    let (dir, tree) = repo("carry-start");
    let (code, out) = factory(&dir, &dir, &["receipt", "start", "--inert", "docs/**", "--", "git", "--version"], "");
    assert_eq!(code, 0, "{out}");
    let done = dir.join(format!(".factory/receipts/{tree}-full.txt"));
    let until = Instant::now() + Duration::from_secs(20);
    while !done.is_file() && Instant::now() < until {
        std::thread::sleep(Duration::from_millis(50));
    }
    let receipt = fs::read_to_string(&done).unwrap();
    assert!(receipt.contains("result PASS") && receipt.contains("inert docs/**\n"), "{receipt}");
    let _ = fs::remove_dir_all(dir);
}

#[test]
fn a_change_outside_the_globs_does_not_carry() {
    for (name, files) in [("carry-src", &["src/lib.rs"][..]), ("carry-mixed", &["docs/a.md", "src/lib.rs"][..])] {
        let (dir, _) = repo(name);
        let (code, out) = write(&dir, "PASS", &["--inert", "docs/**"]);
        assert_eq!(code, 0, "{out}");
        change(&dir, files);
        let (code, out) = factory(&dir, &dir, &["receipt", "check"], "");
        assert_eq!(code, 1, "{name}: {out}");
        assert!(out.starts_with("no full PASS receipt for the tree of "), "{out}");
        let _ = fs::remove_dir_all(dir);
    }
}

#[test]
fn no_inert_line_means_no_carry() {
    let (dir, _) = repo("carry-none");
    let (code, out) = write(&dir, "PASS", &[]);
    assert_eq!(code, 0, "{out}");
    change(&dir, &["docs/a.md"]);
    let (code, out) = factory(&dir, &dir, &["receipt", "check"], "");
    assert_eq!(code, 1, "{out}");
    let _ = fs::remove_dir_all(dir);
}

#[test]
fn a_glob_matching_every_path_is_refused() {
    let (dir, tree) = repo("carry-refuse");
    for glob in ["**", "*", "**/*", "/**", "", "?**", "**?", "*?/**", "**.*", "**a"] {
        let (code, out) = write(&dir, "PASS", &["--inert", glob]);
        assert_eq!(code, 2, "{glob:?}: {out}");
        assert!(out.contains("so a code change would keep the PASS"), "{out}");
        let (code, out) = factory(&dir, &dir, &["receipt", "run", "--inert", glob, "--", "factory-no-such-suite-program"], "");
        assert_eq!(code, 2, "{glob:?}: {out}");
        let (code, out) = factory(&dir, &dir, &["receipt", "start", "--inert", glob, "--", "factory-no-such-suite-program"], "");
        assert_eq!(code, 2, "{glob:?}: {out}");
    }
    assert!(!dir.join(format!(".factory/receipts/{tree}-full.txt")).exists());
    let (code, out) = write(&dir, "PASS", &["--inert", "docs/**", "--inert", "*.md", "--inert", "**/*.md", "--inert", "notes/**"]);
    assert_eq!(code, 0, "{out}");
    let _ = fs::remove_dir_all(dir);
}

/// A PASS with `--inert docs/**` on the base tree, then a docs-only commit; the new tree's id.
fn carried_head(name: &str) -> (PathBuf, String) {
    let (dir, _) = repo(name);
    let (code, out) = write(&dir, "PASS", &["--inert", "docs/**"]);
    assert_eq!(code, 0, "{out}");
    change(&dir, &["docs/a.md"]);
    let (code, tree) = factory(&dir, &dir, &["tree"], "");
    assert_eq!(code, 0, "{tree}");
    (dir, tree.trim().to_string())
}

#[test]
fn a_fail_on_the_exact_tree_beats_a_carried_pass() {
    let (dir, _) = carried_head("carry-fail");
    let (code, out) = write(&dir, "FAIL", &[]);
    assert_eq!(code, 0, "{out}");
    let (code, out) = factory(&dir, &dir, &["receipt", "check"], "");
    assert_eq!(code, 1, "{out}");
    assert!(!out.contains("carried"), "{out}");
    let started = Instant::now();
    let (code, out) = factory(&dir, &dir, &["receipt", "check", "--wait", "30"], "");
    assert_eq!(code, 1, "{out}");
    assert!(started.elapsed() < Duration::from_secs(10), "the FAIL ends the wait");
    assert!(out.trim_end().ends_with("-full.txt FAIL"), "{out}");
    let _ = fs::remove_dir_all(dir);
}

#[test]
fn a_run_claiming_the_exact_tree_blocks_the_carry() {
    let (dir, tree) = carried_head("carry-claim");
    let claim = dir.join(format!(".factory/receipts/{tree}-full.running"));
    fs::write(&claim, "").unwrap();
    let (code, out) = factory(&dir, &dir, &["receipt", "check"], "");
    assert_eq!(code, 1, "{out}");
    assert!(!out.contains("carried"), "{out}");
    fs::remove_file(&claim).unwrap();
    let (code, out) = factory(&dir, &dir, &["receipt", "check"], "");
    assert_eq!(code, 0, "the claim gone, the PASS carries: {out}");
    let _ = fs::remove_dir_all(dir);
}

#[test]
fn wait_returns_when_another_process_writes_the_pass() {
    let (dir, _) = repo("wait-pass");
    let writer = {
        let dir = dir.clone();
        std::thread::spawn(move || {
            std::thread::sleep(Duration::from_millis(1500));
            write(&dir, "PASS", &[])
        })
    };
    let (code, out) = factory(&dir, &dir, &["receipt", "check", "--wait", "30"], "");
    let (wrote, written) = writer.join().unwrap();
    assert_eq!(wrote, 0, "{written}");
    assert_eq!(code, 0, "{out}");
    assert!(out.trim_end().ends_with("-full.txt"), "{out}");
    let _ = fs::remove_dir_all(dir);
}

#[test]
fn wait_ends_at_the_deadline_or_on_a_fail() {
    let (dir, _) = repo("wait-end");
    for bad in ["0", "3601", "x"] {
        let (code, out) = factory(&dir, &dir, &["receipt", "check", "--wait", bad], "");
        assert_eq!(code, 2, "{bad}: {out}");
    }
    let (code, out) = factory(&dir, &dir, &["receipt", "check", "--wait"], "");
    assert_eq!(code, 2, "{out}");
    let started = Instant::now();
    let (code, out) = factory(&dir, &dir, &["receipt", "check", "--wait", "2"], "");
    assert_eq!(code, 1, "{out}");
    assert!(started.elapsed() >= Duration::from_secs(2), "returned before the deadline");
    assert!(out.contains("no full PASS receipt for the tree of ") && out.trim_end().ends_with(" after 2 s"), "{out}");
    let (code, out) = write(&dir, "FAIL", &[]);
    assert_eq!(code, 0, "{out}");
    let started = Instant::now();
    let (code, out) = factory(&dir, &dir, &["receipt", "check", "--wait", "30"], "");
    assert_eq!(code, 1, "{out}");
    assert!(started.elapsed() < Duration::from_secs(10), "a FAIL ends the wait");
    assert!(out.trim_end().ends_with("-full.txt FAIL"), "{out}");
    let _ = fs::remove_dir_all(dir);
}

#[test]
fn only_the_newest_three_inert_passes_are_tried() {
    let (dir, _) = repo("carry-bound");
    let (code, out) = write(&dir, "PASS", &["--inert", "docs/**"]);
    assert_eq!(code, 0, "{out}");
    // Three newer inert PASSes on trees whose src differs from the head's: none of them carries.
    for i in 1..=3 {
        fs::write(dir.join("src/lib.rs"), format!("v{i}\n")).unwrap();
        git(&dir, &["commit", "-qam", "src"], 9);
        let (_, tree) = factory(&dir, &dir, &["tree"], "");
        let tree = tree.trim();
        let text = format!(
            "factory-receipt 1\nsuite full\ntree {tree}\nhead {tree}\nclean no\nresult PASS\ncmd suite\nat 2999-01-0{i}T00:00:00Z\ninert docs/**\n"
        );
        fs::write(dir.join(format!(".factory/receipts/{tree}-full.txt")), text).unwrap();
    }
    fs::write(dir.join("src/lib.rs"), "code\n").unwrap();
    change(&dir, &["docs/a.md"]);
    let (code, out) = factory(&dir, &dir, &["receipt", "check"], "");
    assert_eq!(code, 1, "the oldest PASS would carry, but only the newest three are tried: {out}");
    let _ = fs::remove_dir_all(dir);
}
