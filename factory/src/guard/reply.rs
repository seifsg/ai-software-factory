//! Every text the guard sends, in one place: the agent reads these as its next prompt, so their bytes
//! match the sh guard's (parity) and change only on purpose.

/// The prompt for the step `Next:` names; `closed` when the run file says `Status: closed`.
pub fn next_step(step: &str, next: &str, closed: bool) -> String {
    match step {
        "0" => "Step 0 Ticket: load `ticketing` fresh. Check access, ask the owner once for anything the host may block, open or reuse the ticket.".into(),
        "1" => "Step 1 Analyze: load `analyze-start` fresh. Analyze the request and everything it touches, then teach the owner what exists and what we want: visual (tables, ASCII diagrams, emojis), no code.".into(),
        "2" => "Step 2 Recommend: load `recommend` fresh. The three best real solutions, no fillers or placeholders, compared in one table; pick one and say why not the others.".into(),
        "2b" => "Step 2b Challenge: I don't think this is the best we could do. Do better. Make no mistake. Use the Challenge section of `recommend` and stay neutral: keep the pick and make it stronger if it truly is the best, else replace it and say why.".into(),
        "3" => "Step 3 Plan: load `get-ready-to-code` fresh and write Part A: the plan, the todo checklist, the proof list and the test map.".into(),
        "4" => "Step 4 Before: load `how-to-make-a-pr` fresh and capture every Before proof the plan lists, before any source edit.".into(),
        "5" => "Step 5 Build: load Part B of `get-ready-to-code` fresh. Take only the next unticked todo through its loop (before, change, light check, mapped tests), post its log line as your last message, then end your turn. Tick `## 5 Build` and set Next to 6 only after the last todo, then post the full `## 5 Build` block.".into(),
        "6" => "Step 6 Verify: load `deep-review` fresh. Review the whole build, make the final manual round with After captures, run the full suite once.".into(),
        "7" => "Step 7 PR: load `how-to-make-a-pr` fresh and open the draft PR.".into(),
        "8" => "Step 8 Review: load `how-to-review-a-pr` fresh and brief a fresh reviewer that did not build it.".into(),
        "" if closed => "This run says closed but its gates and review are not proven here. Set `Status: open` with a real `Next:`, or `Status: stopped (<reason>)`.".into(),
        "" => "Run file header is wrong. Fix these lines, spelled exactly: `Status: open`, `Next: <step> <name> · <skill>`, `Waiting: none`. Then do that step.".into(),
        _ => format!("Next: {next}. Load that skill fresh."),
    }
}

/// The tail every step prompt but step 5's and the closed-run one gets.
pub fn one_step(run: &str) -> String {
    format!(" Do only this step: update {run} (tick, Next), post its full block as your last message, then end your turn.")
}

pub fn batched() -> String {
    "Batched: 2+ step headings ticked in one turn. Redo the last ticked step fresh, run any open gate, repost no heading, then run this check in the same turn and do what it prints.".into()
}

pub fn skipped(skip: &str) -> String {
    format!(
        "Steps not ticked: {skip}. Do each now, in order: load its skill, post its block, tick it. Only the owner skips a step: `Waiting: owner:` to ask."
    )
}

pub fn long(lines: &str) -> String {
    format!(
        "Run file lines over 300 characters: {lines}. Split each into short bullets or a table, every fact kept; shorten exact lines (Status, Gate, T1 pre), never split them."
    )
}

pub fn cap(x: char, rounds: i64) -> String {
    let (cl, ln) =
        if x == 'R' { ("Review: ready".to_string(), "review".to_string()) } else { (format!("Gate {x}: PASS"), format!("Gate {x}")) };
    format!(
        "{ln}: {rounds} failed rounds, no open CRITICAL: the loop passes by cap. Write `{cl} (cap, 3 rounds, no CRITICAL) @<sha>` under its step (Gate C and review: on the pushed HEAD, or HEAD with no remote), move what is left to the ticket's follow-ups, then go on with the run."
    )
}

/// The step 5 block or a todo line came while a Before is missing or was saved after the work began.
pub fn before_first(missing: &str, late: &str) -> String {
    let mut s = String::from(
        "Before proof comes first: step 5 and its todo lines wait until every proof-list id has its `before-<id>` file under .factory/proof/, saved before the first source change.",
    );
    if !missing.is_empty() {
        s.push_str(&format!(" No Before file: {missing}."));
    }
    if !late.is_empty() {
        s.push_str(&format!(" Saved after the work began: {late}."));
    }
    s + " Never capture a Before after the work: set the work aside (commit it to a side branch or stash it), put the checkout back at its base, capture each of these Befores there, then build again; or set `Waiting: owner: <question>` and end your turn."
}

pub fn review() -> String {
    "Step 8 has no verified reviewer verdict on the pushed HEAD (no remote: HEAD): brief a fresh reviewer on that head, paste its line as `Review: ready (reviewer <id>) @<sha>`, then end your turn.".into()
}

pub fn gate(x: char) -> String {
    let push = if x == 'C' { ", HEAD pushed, unless no remote" } else { "" };
    format!(
        "Gate {x} has not passed: its line needs a checker result on its commit (`Gate {x}: PASS (checker <id>) @<sha>`{push}). Run the checker for Gate {x}, paste its line, then end your turn."
    )
}

/// Gate B or C is proven but its commit's tree has no full-suite receipt (new with the binary guard).
pub fn receipt(x: char, exe: &str) -> String {
    format!(
        "Gate {x} has no full-suite receipt for the tree of its commit: run the full suite on that commit with `{exe} receipt run --suite full -- <full-suite command>` (commit or ignore any untracked file first), then end your turn."
    )
}

pub fn jobs_deadline() -> String {
    "Waiting: jobs: needs a deadline: write it as `Waiting: jobs: <what runs> (max <minutes> min)`, then end your turn.".into()
}

pub fn jobs_late(max: i64, run: &str) -> String {
    format!(
        "The job in Waiting: jobs: is past its deadline ({max} min): check it, stop it if it hangs, record its result or failure in {run}, update Waiting, then end your turn."
    )
}

/// Wraps a todo: the run it belongs to, an optional note, the way to end a turn on purpose.
pub fn drive(run: &str, todo: &str, note: &str) -> String {
    let note = if note.is_empty() { String::new() } else { format!(" Note: {note}") };
    format!(
        "If this session runs the factory run in {run}: {todo}{note} Ending on purpose? Set Waiting: owner: <question> or Waiting: jobs: <what runs> (max <minutes> min)."
    )
}

pub fn for_run(run: &str, text: &str) -> String {
    format!("If this session runs the factory run in {run}: {text}")
}

pub fn unposted(run: &str, unp: &str) -> String {
    for_run(
        run,
        &format!(
            "Step blocks not posted in chat: {unp}. Post each full block from {run} now, each as its own message opening with its heading (## <step> <name>), then go on with the run."
        ),
    )
}

pub fn wait_skipped(run: &str, skip: &str) -> String {
    for_run(run, &format!("Steps not ticked: {skip}. Do each now, in order, or name them in Waiting: owner: only the owner skips a step."))
}

pub fn halted_notice(halt: &str, run: &str, clear: &str) -> String {
    format!("Factory run halted ({halt}). The owner reads the packet in {run} and resumes with: {clear}")
}

pub fn halt_block(halt: &str, clear: &str) -> String {
    format!(
        "HALT ({halt}): the guard stops driving this run. Start no new round. Write the owner packet under the current step: findings per round (new vs repeated), the shared cause, options (extend, amend scope, cancel). Set Waiting: owner: <question>, then end your turn. Only the owner resumes it: {clear}"
    )
}

pub fn relay(why: &str, run: &str, dir: &str) -> String {
    format!(
        "Relay ({why}): this session stops driving the run. Make sure {run} and the ticket hold everything the next step needs: the next session reads only those. Start a fresh session with your session tool if you have one, prompt: safe-factory Resume {dir}; otherwise the watchdog starts it. Set Waiting: jobs: relay to a fresh session (max 30 min), then end your turn."
    )
}

pub fn relayed(dir: &str) -> String {
    format!("Factory run relayed to a fresh session; this session no longer drives it. Start one with: safe-factory Resume {dir}")
}

pub fn idle_stop(run: &str) -> String {
    format!("Factory run idle since the last nudge; stopping. See {run}.")
}

pub const NO_RUN_ACTIVE: &str = "Factory step block posted, but no usable run file found: this run may have no guard.";
pub const NO_RUN: &str = "Factory step block, but no run file found from this folder. If this session runs a factory run, post that block again with a line **Workspace:** `<absolute folder holding .factory/run.md>` so the guard binds it.";
pub const CLEARED: &str = "Factory run cleared: the guard drives it again, loop caps count from here, night mode is off.\n";
pub const RESUMED: &str = "Load `safe-factory` first: a resumed session may have lost its Stop guard.\n";

pub fn open(run: &str, next: &str) -> String {
    format!("Factory run open ({run}). Next: {next}. Read the run file, load that skill fresh, do only that step, then end your turn.\n")
}

pub fn relay_due(n: i64) -> String {
    format!("Relay due: this session was compacted {n} times; at the next turn end the guard hands the run to a fresh session.\n")
}

pub fn halted_compact(halt: &str) -> String {
    format!("Factory run halted ({halt}): wait for the owner; do not continue the run.\n")
}

/// The plain check line built from a stop reply (empty when the stop let the turn end).
pub fn check_line(reply: &str, has_run_here: bool) -> String {
    if reply.is_empty() {
        return if has_run_here {
            "Factory check: may stop. This stop ends the Stop check: load stop-check right before the next block.\n".into()
        } else {
            "Factory check: may stop. No run file in this folder: if this session has a run, go to its folder and check again.\n".into()
        };
    }
    if ["Factory run idle", "Factory run halted", "Factory run relayed"].iter().any(|p| reply.starts_with(p)) {
        return format!("Factory check: may stop. {reply}\n");
    }
    format!("Factory check: continue. {reply} Load stop-check right before your block or todo line.\n")
}

/// The line `guard step` prints: the check line, minus the stop-check advice when a command Stop hook
/// already guards the run (the method loads `stop-check` only where none does).
pub fn step_line(reply: &str, hooked: bool) -> String {
    let line = check_line(reply, true);
    if !hooked {
        return line;
    }
    line.replace(" Load stop-check right before your block or todo line.", "")
        .replace(" This stop ends the Stop check: load stop-check right before the next block.", "")
}
