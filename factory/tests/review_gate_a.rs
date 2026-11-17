//! Gate A can report the whole mechanical repair list before launching a checker.

mod common;

use common::{factory, git, scratch};
use std::fs;
use std::path::Path;

const RUN: &str = r#"# Run: local: .factory/ticket.md · Fast · change
Status: open
Next: 4 Before · how-to-make-a-pr
Waiting: none
## 0 Ticket ✔
**A1 (ask):** Keep the acceptance receipt.
**Checklist:** T1 (A1)
## 1 Analyze ✔
**Inputs:** Local ticket A1. Research found a default handler. Size none.
**Purpose:** Preserve the default handler.
**Flow:** Input -> handler [change here] -> result.
**Used by:** `src/main.js:handler`, `test/handler.test.js`.
**Edges:** Callers may pass a missing value.
**Claims:** No claims to check.
**Scope:** Handler and its existing caller.
**Unknowns:** None.
**For Recommend:** Pick the validation site.
No file changed during this step.
## 2 Recommend ✔
**Goal:** Keep behavior.
**Table:** Compare three implementations.
**Pick:** Reuse the handler.
**Look:** No UI.
**Decider:** Delegated.
No file changed during this step.
## 2b Challenge ✔
**Challenge:** I don't think this is the best we could do. Do better. Make no mistake.
**Found:** Nothing new.
**Result:** Keep the pick.
## 3 Plan ✔
**Files:** Handler and tests. Critique changed nothing.
**Todos:** T1 validates A1.
**Plan:** Same public interface.
**Proof list:**
| ID | Command | Inputs |
| --- | --- | --- |
| P1 | Inspect the acceptance receipt | `src/main.js`, `.factory/out/T1/gates.txt` |
**Test map:** node --test.
No source file changed during this step.
## 4 Before
LATER STEP CONTENT
"#;

#[test]
fn generates_only_a_checked_gate_a_brief() {
    let dir = scratch("gate-a-brief");
    git(&dir, &["init", "-q"], 8);
    for path in ["src/main.js", "test/handler.test.js"] {
        let file = dir.join(path);
        fs::create_dir_all(file.parent().unwrap()).unwrap();
        fs::write(file, "// test input\n").unwrap();
    }
    git(&dir, &["add", "src", "test"], 8);
    git(&dir, &["commit", "-qm", "base"], 8);
    let metadata = dir.join(".factory");
    fs::create_dir_all(&metadata).unwrap();
    fs::write(metadata.join("ticket.md"), "# Ticket\n- **A1 (ask):** Keep the acceptance receipt.\n").unwrap();
    fs::write(metadata.join("inputs.json"), r#"{"P1":["src/main.js",".factory/out/T1/gates.txt"]}"#).unwrap();
    let broken = RUN.replace("Keep the acceptance receipt.", "Keep a receipt.")
        .replace("`test/handler.test.js`", "broken\tpath and `test/missing.test.js`")
        .replace("`.factory/out/T1/gates.txt`", "`.factory/out/T1/receipt.json`");
    let run_path = metadata.join("run.md");
    fs::write(&run_path, broken).unwrap();

    let skills = Path::new(env!("CARGO_MANIFEST_DIR")).join("../.agents/skills");
    let args = ["review", "gate-a", "--skills", skills.to_str().unwrap(), "--proof-inputs", ".factory/inputs.json"];
    let (code, output) = factory(&dir, &dir, &args, "");
    assert_eq!(code, 1, "{output}");
    for expected in ["**A1 (ask):**", "a tab in Used by", "test/missing.test.js", "P1 needs proof input `.factory/out/T1/gates.txt`"] {
        assert!(output.contains(expected), "{expected}: {output}");
    }
    assert!(!output.contains("Role: checker"));

    fs::write(&run_path, RUN).unwrap();
    let (code, output) = factory(&dir, &dir, &args, "");
    assert_eq!(code, 0, "{output}");
    for expected in ["Role: checker. Gate A.", "## Output contract", ".factory/ticket.md", "through Plan", "`.factory/out/T1/gates.txt`"] {
        assert!(output.contains(expected), "{expected}: {output}");
    }
    assert!(!output.contains("LATER STEP CONTENT"));

    let nested = dir.join("component");
    for folder in [".factory", "src", "test"] {
        fs::create_dir_all(nested.join(folder)).unwrap();
    }
    for input in [".factory/inputs.json", "src/main.js", "test/handler.test.js"] {
        fs::copy(dir.join(input), nested.join(input)).unwrap();
    }
    let nested_run = RUN.replace("Keep the acceptance receipt.", "Keep the component receipt.");
    fs::write(nested.join(".factory/run.md"), nested_run).unwrap();
    fs::write(nested.join(".factory/ticket.md"), "**A1 (ask):** Keep the component receipt.\n").unwrap();
    let (code, output) = factory(&nested, &dir, &args, "");
    assert_eq!(code, 0, "{output}");
    assert!(output.contains("Keep the component receipt."));
    assert!(!output.contains("Keep the acceptance receipt."));
    let _ = fs::remove_dir_all(dir);
}
