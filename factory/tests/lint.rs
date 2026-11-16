//! Lint against two recorded runs (fixtures r3, r4: their final run and ticket files). Each case puts one
//! round-1 checker miss of that run back into its block and asserts the lint flags it before a checker would.

use factory::lint::{check, Input, Report};
use std::path::{Path, PathBuf};

const HEAD_R3: &str = "2ffc440cacbe7a1fa497c259f27ae2099292d1d5";
const HEAD_R4: &str = "adc6ac83540d412f4e2237ded4b1bafbc0082032";

fn root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).to_path_buf()
}

fn fixture(run: &str) -> (PathBuf, String, String) {
    let dir = root().join("tests/fixtures/lint").join(run);
    let text = std::fs::read_to_string(dir.join(".factory/run.md")).unwrap();
    let ticket = std::fs::read_to_string(dir.join(".factory/ticket.md")).unwrap();
    (dir, text, ticket)
}

/// Lints `run` after each (old, new) replacement; every `old` must be present.
fn lint(run: &str, gate: char, head: &str, edits: &[(&str, &str)]) -> Report {
    let (dir, mut text, ticket) = fixture(run);
    for (old, new) in edits {
        assert!(text.contains(old), "fixture {run} lacks {old:?}");
        text = text.replacen(old, new, 1);
    }
    let skills = root().join("../.agents/skills");
    check(&Input { gate, run: &text, ticket: Some(&ticket), head, has_remote: false, skills: Some(&skills), dir: &dir })
}

fn flags(r: &Report, needle: &str) {
    assert!(r.gaps.iter().any(|g| g.contains(needle)), "no gap containing {needle:?} in {:#?}", r.gaps);
}

#[test]
fn r3_a1_recommend_without_no_file_changed() {
    let r = lint("r3", 'A', HEAD_R3, &[("No file changed during this step.\n\n## 2b", "\n## 2b")]);
    flags(&r, "## 2 Recommend");
}

#[test]
fn r3_b1_lens_lines_without_findings() {
    let r = lint(
        "r3",
        'B',
        HEAD_R3,
        &[
            ("**compliance:** A1 to A7 and D1 to D8 met (J2); 3 LOW left (below), deferred pending owner · PASS", "**compliance:** A1 to A7 and D1 to D8 met (J2) · PASS"),
            ("**change-guard:** no findings (3 original tests byte-identical, no-option output unchanged, J2) · PASS", "**change-guard:** 3 original tests byte-identical (J2) · PASS"),
            ("**security:** no findings (pure string functions, no network, files, secrets or logging touched) · PASS", "**security:** N/A, pure string functions"),
        ],
    );
    flags(&r, "**compliance:** has no findings");
    flags(&r, "**change-guard:** has no findings");
    flags(&r, "**security:** has no verdict");
}

#[test]
fn r3_c1_stale_sha_quote_lenses_and_verdict() {
    let quote = "local only (\"This repo has no remote: stop after verify and review (no PR step).\") @2ffc440cacbe7a1fa497c259f27ae2099292d1d5";
    let r = lint(
        "r3",
        'C',
        HEAD_R3,
        &[
            (quote, "local only (\"no remote here, local review only\") @3c57049"),
            ("**Verdict:** APPROVE-WITH-FIXES", "**Summary:** fixes applied"),
        ],
    );
    flags(&r, "is not HEAD");
    flags(&r, "owner quote differs");
    flags(&r, "no verdict APPROVE");
    flags(&r, "PR card lacks");
}

#[test]
fn r3_c1_lens_prose_without_table() {
    let (_, text, _) = fixture("r3");
    let perf = text.find("**performance:**\n").unwrap();
    let sec = text.find("**security:**\n").unwrap();
    let journey = text.find("**journey (library consumer):**").unwrap();
    let prose = "**performance:**\nSet probes O(1); the loop ends at taken.size+1.\n**Verdict:** clean.\n**security:**\nPure string functions.\n**Verdict:** clean.\n";
    let r = lint("r3", 'C', HEAD_R3, &[(&text[perf..journey], prose)]);
    assert!(sec > perf);
    flags(&r, "**performance:** has no findings");
    flags(&r, "**security:** has no findings");
}

#[test]
fn r4_a1_checklist_and_research() {
    let r = lint(
        "r4",
        'A',
        HEAD_R4,
        &[
            ("**Checklist:** `- [ ] T1 slugify maxLength cut, uniqueSlug, tests (A1-A5)` (matches step 3 and .factory/ticket.md)", "**Checklist:** filled at step 3"),
            ("research summary: none (kickoff research skipped, owner's brief fixes the scope), ", ""),
        ],
    );
    flags(&r, "checklist lacks the plan's todos T1");
    flags(&r, "names no research summary");
}

#[test]
fn r4_b1_journey_line_and_old_after_commit() {
    let r = lint("r4", 'B', "562933a000000000000000000000000000000000", &[("- **journey:** no findings, real calls match A1 to A4 · PASS", "- **journey:** real calls match A1 to A4 · PASS")]);
    flags(&r, "**journey:** has no findings");
    flags(&r, "does not name HEAD");
}

#[test]
fn r4_c1_quote_card_claim_table_and_lens_tables() {
    let (_, text, _) = fixture("r4");
    let s8 = text.find("## 8 Review").unwrap();
    let card_start = s8 + text[s8..].find("- Branch `feat/slug-max-length-unique`").unwrap();
    let card_end = text.find("**Claim (verbatim, trimmed):**").unwrap();
    let lens_start = text.find("**Lenses, one findings table per lens:**").unwrap();
    let lens_end = text.find("**Master table:**").unwrap();
    let claim_start = text.find("| Claimed behavior | Where | Delivered? | Note |").unwrap();
    let claim_end = text.find("**Three solutions:**").unwrap();
    let mut edits: Vec<(String, String)> = vec![
        ("local only (\"This repo has no remote: stop after verify and review (no PR step).\")".into(), "local only (\"This repo has no remote; review only.\")".into()),
        (text[card_start..card_end].to_string(), "- Branch `feat/slug-max-length-unique`, head `adc6ac8`.\n".into()),
        (text[lens_start..lens_end].to_string(), "**Lenses:** compliance PASS, change-guard PASS (1 MEDIUM), journey PASS, security PASS, performance PASS.\n\n".into()),
    ];
    edits.push((text[claim_start..claim_end].to_string(), String::new()));
    let refs: Vec<(&str, &str)> = edits.iter().map(|(a, b)| (a.as_str(), b.as_str())).collect();
    let r = lint("r4", 'C', HEAD_R4, &refs);
    flags(&r, "owner quote differs");
    flags(&r, "PR card lacks `author:`");
    flags(&r, "PR card lacks `linked:`");
    flags(&r, "no claim-vs-code table row");
    flags(&r, "no **compliance:** lens line");
}

#[test]
fn placeholders_in_left_running_are_flagged() {
    let r = lint("r4", 'C', HEAD_R4, &[("**Fixes:**", "Left running: worktree, stop: `git worktree remove <this folder>`\n**Fixes:**")]);
    flags(&r, "placeholder <this folder>");
}
