//! Saving a revised block can prepare a retry without spending the idle guard's budget.

mod common;

use common::{factory, scratch};
use std::fs;

#[test]
fn revised_step_blocks_do_not_spend_idle_budget() {
    let dir = scratch("guard-repairs");
    let metadata = dir.join(".factory");
    fs::create_dir_all(&metadata).unwrap();
    fs::write(
        metadata.join("run.md"),
        "# Run: local fixture · Fast · change\nStatus: open\nNext: 4 Before · how-to-make-a-pr\nWaiting: none\n\n\
         ## 0 Ticket ✔\n## 1 Analyze ✔\n## 2 Recommend ✔\n## 2b Challenge ✔\n## 3 Plan ✔\nOriginal plan\n",
    )
    .unwrap();
    let save = |block: &str| {
        let (code, output) = factory(&dir, &dir, &["guard", "step", "3"], block);
        assert_eq!(code, 0, "{output}");
        output
    };

    for edit in 1..=8 {
        let output = save(&format!("## 3 Plan\nClarify criterion {edit}.\n"));
        assert!(!output.contains("halted"), "{output}");
    }

    for _ in 0..5 {
        let output = save("## 3 Plan\nClarify criterion 8.\n");
        assert!(!output.contains("halted"), "{output}");
    }
    let repeat = save("## 3 Plan\nClarify criterion 8.\n");
    assert!(repeat.contains("no progress in 6 turns"), "{repeat}");
    let _ = fs::remove_dir_all(dir);
}
