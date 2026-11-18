//! `guard step <n|Tk>`: the coordinator posts a block, then this writes it into the run file (no hand
//! edits of block text), ticks its heading, sets `Next:`, and answers with the Stop rules as one plain line,
//! so the run goes on in the same turn. `T<k>` lines go under `## 5 Build` without ticking it.

use std::io::Read;
use std::path::{Path, PathBuf};

/// Steps in order with their names and skills.
pub const STEPS: [(&str, &str, &str); 10] = [
    ("0", "Ticket", "ticketing"),
    ("1", "Analyze", "analyze-start"),
    ("2", "Recommend", "recommend"),
    ("2b", "Challenge", "recommend"),
    ("3", "Plan", "get-ready-to-code"),
    ("4", "Before", "how-to-make-a-pr"),
    ("5", "Build", "get-ready-to-code"),
    ("6", "Verify", "deep-review"),
    ("7", "PR", "how-to-make-a-pr"),
    ("8", "Review", "how-to-review-a-pr"),
];

const TICK: &str = "\u{2714}";

pub fn cli(args: &[&str]) -> u8 {
    let [label] = args else {
        eprintln!("usage: factory guard step <n|Tk> < block   (run in the run's folder)");
        return 2;
    };
    let Some(dir) = crate::run::locate::walk(&super::cwd()) else {
        eprintln!("factory guard step: no .factory/run.md from this folder");
        return 1;
    };
    // A command Stop hook records its session and transcript in the state: the step judges with that same
    // evidence (gate handbacks, posted blocks) and keeps the record as it is for the hook's next call.
    let state = match crate::run::state::State::load(&Path::new(&dir).join(".factory/guard/state")) {
        crate::run::state::Loaded::Valid(s) => s,
        _ => crate::run::state::State::default(),
    };
    let run = Path::new(&dir).join(".factory/run.md");
    let guard = Path::new(&dir).join(".factory/guard");
    let todo = label.strip_prefix('T').is_some_and(|k| !k.is_empty() && k.bytes().all(|b| b.is_ascii_digit()));
    if !todo && !STEPS.iter().any(|(n, _, _)| n == label) {
        eprintln!("factory guard step: {label} is no step (0 to 8, 2b) or todo (T<k>)");
        return 2;
    }
    let Some(block) = block_for(label, state.get("transcript"), &guard, &run) else {
        eprintln!(
            "factory guard step: no {} block: pipe it in full, its one copy: factory guard step {label} <<'EOF' (the block) EOF. The owner reads it on the run page; chat gets one progress line.",
            heading_of(label)
        );
        return 2;
    };
    // Never write from a failed read: an unreadable or non-UTF-8 run file stays as it is.
    let text = match std::fs::read(&run).map(String::from_utf8) {
        Ok(Ok(t)) if !t.is_empty() => t,
        _ => {
            eprintln!("factory guard step: {} is empty, unreadable or not UTF-8; left as it is", crate::paths::text(&run));
            return 1;
        }
    };
    if *label == "5" || label.starts_with('T') {
        let repo = crate::git::Repo::discover(Path::new(&dir));
        let head = repo.as_ref().map(|r| r.info().head).unwrap_or_default();
        if let Some(why) = super::before::refusal(Path::new(&dir), &text, repo.as_ref(), &head) {
            eprintln!("factory guard step: refused, nothing written. {why}");
            return 1;
        }
    }
    let updated = match write(&text, label, &block) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("factory guard step: {e}");
            return 1;
        }
    };
    if let Err(e) = crate::paths::write_atomic(&run, updated.as_bytes()) {
        eprintln!("factory guard step: cannot write {}: {e}", crate::paths::text(&run));
        return 1;
    }
    let hooked = !state.get("transcript").is_empty();
    let input = crate::hook::Input {
        session_id: state.get("session").into(),
        transcript_path: state.get("transcript").into(),
        cwd: dir.clone(),
        last_assistant_message: format!("## {label} "),
        ..Default::default()
    };
    let r = super::flow::run(&input, super::flow::Mode::Step { changed: updated != text }, Path::new(&dir));
    stamp(&guard, label);
    print!("{}", super::reply::step_line(r.as_ref().map_or("", crate::hook::Reply::inner), hooked));
    0
}

/// The block's heading as the owner sees it: `## 3 Plan`, or a todo line's `T1 pre:`.
fn heading_of(label: &str) -> String {
    STEPS.iter().find(|(n, _, _)| *n == label).map_or_else(|| format!("`{label} pre:`"), |(n, name, _)| format!("`## {n} {name}`"))
}

/// The block: stdin, its one copy (never read from a terminal). A host that posts blocks in chat instead runs
/// with no stdin: the newest post in this session's chat or a subagent coordinator's, made since the last step was
/// written (`.factory/guard/stepped`, else the run file's last write), so an old post is never reused.
fn block_for(label: &str, transcript: &str, guard: &Path, run: &Path) -> Option<String> {
    use std::io::IsTerminal;
    let mut piped = String::new();
    let _ = (!std::io::stdin().is_terminal()).then(|| std::io::stdin().read_to_string(&mut piped));
    if !piped.trim().is_empty() {
        return Some(piped);
    }
    let heading = STEPS.iter().find(|(n, _, _)| *n == label).map(|(n, name, _)| format!("## {n} {name}")).unwrap_or_default();
    let stamp = std::fs::metadata(guard.join("stepped")).or_else(|_| std::fs::metadata(run));
    let since = stamp.and_then(|m| m.modified()).ok().and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok());
    let since = since.map(|d| crate::receipt::utc_iso(d.as_secs())[..19].to_string())?;
    let hooked = Some(PathBuf::from(transcript)).filter(|_| !transcript.is_empty());
    let mut chats: Vec<PathBuf> = [super::posted::own_transcript(), hooked].into_iter().flatten().collect();
    // A coordinator running as a Claude Code subagent posts in its own file beside the session's.
    let subs: Vec<PathBuf> = chats.iter().flat_map(|tp| subagent_chats(tp)).collect();
    chats.extend(subs);
    chats.iter().find_map(|tp| super::posted::block(tp, label, &heading, &since))
}

/// Subagent transcripts of a Claude Code session: `<session>/subagents/*.jsonl` beside `<session>.jsonl`.
fn subagent_chats(tp: &Path) -> Vec<PathBuf> {
    let dir = tp.with_extension("").join("subagents");
    std::fs::read_dir(dir)
        .map(|rd| rd.flatten().map(|e| e.path()).filter(|p| p.extension().is_some_and(|x| x == "jsonl")).collect())
        .unwrap_or_default()
}

/// Marks a written step once the guard folder exists: later posts count from now, and the step is on the list
/// of blocks `guard step` wrote (`written`), which the guard never asks for in chat.
fn stamp(guard: &Path, label: &str) {
    use std::io::Write;
    let _ = std::fs::write(guard.join("stepped"), label);
    let _ = std::fs::OpenOptions::new().append(true).open(guard.join("written")).or_else(|_| std::fs::File::create(guard.join("written"))).and_then(|mut f| writeln!(f, "{label}"));
}

/// The run file with the block written in: a step block replaces its section and ticks it; a `T<k>` line
/// replaces or joins the build section's todo lines. Proof lines the block drops (gate, review) are kept.
pub fn write(text: &str, label: &str, block: &str) -> Result<String, String> {
    let block = block.replace("\r\n", "\n");
    let block = block.trim_end_matches('\n');
    if let Some(k) = label.strip_prefix('T') {
        k.parse::<u32>().map_err(|_| format!("{label}: not a todo id"))?;
        let prefix = format!("{label} pre:");
        if !block.starts_with(&prefix) {
            return Err(format!("a todo line starts with `{prefix}`"));
        }
        return Ok(todo_line(text, &prefix, block));
    }
    let i = STEPS.iter().position(|(n, _, _)| *n == label).ok_or_else(|| format!("{label}: not a step (0-8, 2b, or T<k>)"))?;
    let (n, name, _) = STEPS[i];
    let body = match block.lines().next() {
        Some(first) if first.starts_with("## ") => {
            let want = format!("## {n} {name}");
            if !first.starts_with(&want) {
                return Err(format!("the block opens with `{first}`, not `{want}`"));
            }
            block.split_once('\n').map_or("", |(_, rest)| rest)
        }
        _ => block,
    };
    let mut lines: Vec<String> = text.lines().map(String::from).collect();
    let heading = format!("## {n} {name}");
    let at = lines.iter().position(|l| l.starts_with(&heading));
    let start = match at {
        Some(h) => h,
        None => {
            if lines.last().is_some_and(|l| !l.is_empty()) {
                lines.push(String::new());
            }
            lines.push(heading.clone());
            lines.len() - 1
        }
    };
    let end = lines[start + 1..].iter().position(|l| l.starts_with("## ")).map_or(lines.len(), |e| start + 1 + e);
    let kept: Vec<String> = lines[start + 1..end]
        .iter()
        .filter(|old| proof_kind(old).is_some_and(|kind| !body.lines().any(|new| proof_kind(new) == Some(kind))))
        .cloned()
        .collect();
    if !lines[start].contains(TICK) {
        lines[start] = format!("{} {TICK}", lines[start].trim_end());
    }
    let mut section: Vec<String> = body.lines().map(String::from).collect();
    section.extend(kept);
    if end < lines.len() {
        section.push(String::new());
    }
    lines.splice(start + 1..end, section);
    if let Some((m, mname, skill)) = STEPS.get(i + 1).filter(|_| n != "8") {
        let next = format!("Next: {m} {mname} \u{b7} {skill}");
        let Some(p) = lines.iter().position(|l| l.starts_with("Next:")) else { return Err("the run file has no `Next:` line".into()) };
        // Next only moves forward: reposting an earlier block (an amended plan) keeps the run where it is.
        let current = STEPS.iter().position(|(s, _, _)| lines[p].strip_prefix("Next: ").and_then(|v| v.split(' ').next()) == Some(*s));
        if current.is_none_or(|c| i + 1 > c) {
            lines[p] = next;
        }
    }
    Ok(lines.join("\n") + "\n")
}

/// Omitted proofs survive a rewrite; an explicit replacement supersedes only the same kind.
fn proof_kind(line: &str) -> Option<&'static str> {
    if line.contains(": FAIL") {
        return None;
    }
    ["Gate A:", "Gate B:", "Gate C:", "Review: ready"].into_iter().find(|prefix| line.starts_with(prefix))
}

/// Replaces the `T<k> pre:` line under `## 5 Build`, or adds it after the section's last line.
fn todo_line(text: &str, prefix: &str, line: &str) -> String {
    let mut lines: Vec<String> = text.lines().map(String::from).collect();
    let start = lines.iter().position(|l| l.starts_with("## 5 Build"));
    let start = start.unwrap_or_else(|| {
        if lines.last().is_some_and(|l| !l.is_empty()) {
            lines.push(String::new());
        }
        lines.push("## 5 Build".into());
        lines.len() - 1
    });
    let end = lines[start + 1..].iter().position(|l| l.starts_with("## ")).map_or(lines.len(), |e| start + 1 + e);
    if let Some(p) = lines[start + 1..end].iter().position(|l| l.starts_with(prefix)) {
        lines[start + 1 + p] = line.to_string();
    } else {
        let mut at = end;
        while at > start + 1 && lines[at - 1].is_empty() {
            at -= 1;
        }
        lines.insert(at, line.to_string());
    }
    lines.join("\n") + "\n"
}

#[cfg(test)]
mod tests {
    use super::write;

    const RUN: &str = "# Run: x\nStatus: open\nNext: 3 Plan \u{b7} get-ready-to-code\nWaiting: none\n\n## 3 Plan\nold\nGate A: PASS (checker c) @abc1234\n\n## 4 Before\n";

    #[test]
    fn writes_ticks_and_moves_next() {
        let out = write(RUN, "3", "## 3 Plan\n**Files:** a\n").unwrap();
        assert!(out.contains("## 3 Plan \u{2714}\n**Files:** a\nGate A: PASS (checker c) @abc1234\n\n## 4 Before"));
        assert!(out.contains("Next: 4 Before \u{b7} how-to-make-a-pr"));
        assert!(!out.contains("old"));
    }

    #[test]
    fn reposting_an_earlier_block_keeps_next() {
        let run = "Next: 7 PR \u{b7} how-to-make-a-pr\n\n## 3 Plan \u{2714}\nold\n\n## 4 Before\n";
        let out = write(run, "3", "## 3 Plan\nnew\n").unwrap();
        assert!(out.contains("Next: 7 PR \u{b7} how-to-make-a-pr") && out.contains("## 3 Plan \u{2714}\nnew\n"));
    }

    #[test]
    fn replacement_proof_retires_only_its_previous_stamp() {
        for prefix in ["Review: ready (reviewer r)", "Gate C: PASS (checker c)"] {
            let old = format!("{prefix} @aaaaaaa");
            let new = format!("{prefix} @bbbbbbb");
            let run = format!("Next: 8 Review · how-to-review-a-pr\n## 8 Review ✔\n{old}\nLeft running: none\n");
            let body = format!("## 8 Review\n{new}\nLeft running: none\n");
            let out = write(&run, "8", &body).unwrap();
            assert!(!out.contains(&old), "{out}");
            assert!(out.contains(&new) && out.trim_end().ends_with("Left running: none"));
            assert!(write(&run, "8", "## 8 Review\nno replacement\n").unwrap().contains(&old));
        }
    }

    #[test]
    fn todo_lines_join_the_build_section() {
        let run = "Next: 5 Build \u{b7} get-ready-to-code\n## 5 Build\nT1 pre: a do: b post: c \u{2714}\n\n## 6 Verify\n";
        let out = write(run, "T2", "T2 pre: x do: y post: z \u{2714}").unwrap();
        assert!(out.contains("T1 pre: a do: b post: c \u{2714}\nT2 pre: x do: y post: z \u{2714}\n\n## 6 Verify"));
        assert!(write(run, "4", "## 5 Build\nx").is_err());
    }
}
