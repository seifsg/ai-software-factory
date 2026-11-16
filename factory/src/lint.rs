//! `lint <gate>`: every gap a regex can prove, before a checker is briefed (a form FAIL costs a round).
//! Generic rules (ticks, `@sha` against HEAD, missing proof files, placeholders, owner quotes, lens lines,
//! the review's card and verdict) plus the `**Label:**` lines each step's Output contract asks for, read
//! from the installed skills so the lint follows the contracts as they change.

use crate::contracts;
use crate::guard::rules::pre;
use std::path::Path;

/// The steps each gate checks, and the skills whose contracts cover them.
fn scope(gate: char) -> Option<(&'static [&'static str], &'static [&'static str])> {
    match gate {
        'A' => Some((&["0", "1", "2", "2b", "3"], &["ticketing", "analyze-start", "recommend", "get-ready-to-code"])),
        'B' => Some((&["4", "5", "6"], &["how-to-make-a-pr", "get-ready-to-code", "deep-review"])),
        'C' => Some((&["7", "8"], &["how-to-make-a-pr", "how-to-review-a-pr"])),
        _ => None,
    }
}

const PLACEHOLDERS: [&str; 12] = [
    "<this folder>", "<absolute run folder>", "<run folder>", "<sha>", "<id>", "<agent id>", "<PR URL>", "<ticket link>",
    "<owner's words>", "<their words>", "<question>", "<what runs>",
];

/// What the lint reads.
pub struct Input<'a> {
    pub gate: char,
    pub run: &'a str,
    /// `.factory/ticket.md`, when the run keeps one.
    pub ticket: Option<&'a str>,
    pub head: &'a str,
    pub has_remote: bool,
    /// Skills folder for contracts; None runs only the generic rules.
    pub skills: Option<&'a Path>,
    /// The run folder, for proof files.
    pub dir: &'a Path,
}

/// Findings: gaps fail the lint, notes never do.
#[derive(Debug, Default)]
pub struct Report {
    pub gaps: Vec<String>,
    pub notes: Vec<String>,
}

/// One `## <label> <Name>` section of the run file.
struct Section<'a> {
    label: &'a str,
    heading: &'a str,
    lines: Vec<&'a str>,
}

fn sections(run: &str) -> Vec<Section<'_>> {
    let mut out: Vec<Section> = Vec::new();
    for l in run.lines() {
        if let Some(h) = l.strip_prefix("## ") {
            let label = h.split(' ').next().unwrap_or("");
            out.push(Section { label, heading: l, lines: Vec::new() });
        } else if let Some(s) = out.last_mut() {
            s.lines.push(l);
        }
    }
    out
}

/// Runs every rule for one gate.
pub fn check(i: &Input) -> Report {
    let mut r = Report::default();
    let Some((steps, skills)) = scope(i.gate) else {
        r.gaps.push(format!("unknown gate {}", i.gate));
        return r;
    };
    let secs = sections(i.run);
    let find = |l: &str| secs.iter().find(|s| s.label == l);
    let all: &[&str] = &["0", "1", "2", "2b", "3", "4", "5", "6", "7", "8"];
    for st in if i.gate == 'C' { all } else { steps } {
        match find(st) {
            None => r.gaps.push(format!("## {st}: heading missing")),
            Some(s) if !s.heading.contains('\u{2714}') => r.gaps.push(format!("{}: heading not ticked", s.heading)),
            _ => {}
        }
    }
    for st in steps.iter().filter_map(|s| find(s)) {
        placeholders(st, &mut r);
        owner_quotes(st, i.ticket, &mut r);
    }
    match i.skills {
        Some(dir) => labels(&secs, steps, skills, dir, run_kind(i.run), &mut r),
        None => r.notes.push("no skills folder found: contract labels not checked (pass --skills <dir>)".into()),
    }
    let lenses = i.skills.map(lens_names).unwrap_or_else(|| ["change-guard", "compliance", "security", "performance", "journey"].map(String::from).to_vec());
    match i.gate {
        'A' => gate_a(&secs, i.run, &mut r),
        'B' => {
            if let Some(s) = find("6") {
                lens_lines(s, &lenses, &mut r);
            }
            proof_files(&secs, i, &mut r);
        }
        _ => gate_c(&secs, i, &lenses, &mut r),
    }
    let mut seen = std::collections::HashSet::new();
    r.gaps.retain(|g| seen.insert(g.clone()));
    r
}

/// Contract checklist lines `- [ ] **Label:**` and `No (source) file changed` lines, per block they name.
fn labels(secs: &[Section], steps: &[&str], skills: &[&str], dir: &Path, kind: &str, r: &mut Report) {
    for sk in skills {
        let Ok(text) = contracts::of(dir, sk) else {
            r.notes.push(format!("no contract for {sk} in {}", crate::paths::text(dir)));
            continue;
        };
        let mut block: Option<String> = None;
        for l in text.lines() {
            let t = l.trim_start();
            if !t.starts_with("- [ ]") {
                if let Some(i) = t.find("`## ") {
                    block = t[i + 4..].split(' ').next().map(String::from);
                }
                continue;
            }
            let Some(b) = block.as_deref().filter(|b| steps.contains(b)) else { continue };
            let Some(sec) = secs.iter().find(|s| s.label == b) else { continue };
            let item = t[5..].trim_start();
            if kind == "change" && item.contains("a `change` omits it") {
                continue;
            }
            if let Some(rest) = item.strip_prefix("**") {
                if let Some(end) = rest.find(":**") {
                    let want = format!("**{}:**", &rest[..end]);
                    if !has_label(sec, &rest[..end]) {
                        r.gaps.push(format!("{}: no {want} line (contract of {sk})", sec.heading));
                    }
                }
            } else if let Some(phrase) = item.strip_suffix(" during this step").filter(|p| p.starts_with("No ")) {
                if !no_change_line(sec, phrase) {
                    r.gaps.push(format!("{}: no \"{phrase} during this step\" line (contract of {sk})", sec.heading));
                }
            }
        }
    }
}

/// Gate A: step 0 lists every todo id the plan names; the analysis Inputs name the research (product, feature).
fn gate_a(secs: &[Section], run: &str, r: &mut Report) {
    let find = |l: &str| secs.iter().find(|s| s.label == l);
    if let (Some(s0), Some(s3)) = (find("0"), find("3")) {
        let ids = |s: &Section| -> Vec<String> { s.lines.iter().flat_map(|l| todo_ids(l)).collect() };
        let have = ids(s0);
        let mut missing: Vec<String> = ids(s3).into_iter().filter(|t| !have.contains(t)).collect();
        missing.sort();
        missing.dedup();
        if !missing.is_empty() {
            r.gaps.push(format!("{}: checklist lacks the plan's todos {}", s0.heading, missing.join(", ")));
        }
    }
    let kind = run_kind(run);
    if matches!(kind, "product" | "feature") {
        if let Some(s1) = find("1") {
            let inputs = s1.lines.iter().find(|l| l.contains("**Inputs:**"));
            if inputs.is_some_and(|l| !l.to_ascii_lowercase().contains("research")) {
                r.gaps.push(format!("{}: **Inputs:** names no research summary ({kind} run)", s1.heading));
            }
        }
    }
}

/// `T1`, `T12` tokens of a line.
fn todo_ids(l: &str) -> Vec<String> {
    let b = l.as_bytes();
    let mut out = Vec::new();
    for (i, w) in b.windows(2).enumerate() {
        if w[0] == b'T' && w[1].is_ascii_digit() && (i == 0 || !b[i - 1].is_ascii_alphanumeric()) {
            let n: String = l[i + 1..].chars().take_while(char::is_ascii_digit).collect();
            let after = l.as_bytes().get(i + 1 + n.len());
            if !after.is_some_and(|c| c.is_ascii_alphabetic()) {
                out.push(format!("T{n}"));
            }
        }
    }
    out
}

/// Gate B: every `before-<id>` / `after-<id>` the blocks name exists; each After names HEAD's commit.
fn proof_files(secs: &[Section], i: &Input, r: &mut Report) {
    let proof = i.dir.join(".factory/proof");
    let files = walk_files(&proof);
    for s in secs.iter().filter(|s| s.label == "4" || s.label == "6") {
        for name in s.lines.iter().flat_map(|l| proof_names(l)) {
            let hit = files.iter().find(|f| f.file_stem().is_some_and(|st| st.to_string_lossy() == name));
            match hit {
                None => r.gaps.push(format!("{}: {name} names no file under .factory/proof/", s.heading)),
                Some(f) if name.starts_with("after-") && !i.head.is_empty() => {
                    let first = std::fs::read_to_string(f).unwrap_or_default();
                    let sha = first.lines().next().and_then(first_sha);
                    if !sha.is_some_and(|c| pre(&c, i.head)) {
                        r.gaps.push(format!("{}: {name} does not name HEAD {}", s.heading, &i.head[..i.head.len().min(8)]));
                    }
                }
                _ => {}
            }
        }
    }
}

fn walk_files(d: &Path) -> Vec<std::path::PathBuf> {
    let mut out = Vec::new();
    let Ok(rd) = std::fs::read_dir(d) else { return out };
    for e in rd.flatten() {
        let p = e.path();
        if p.is_dir() {
            out.extend(walk_files(&p));
        } else {
            out.push(p);
        }
    }
    out
}

/// `before-P1`, `after-x2` tokens (a proof id is letters, digits, `_` or `-`).
fn proof_names(l: &str) -> Vec<String> {
    let mut out = Vec::new();
    for pfx in ["before-", "after-"] {
        for (i, _) in l.match_indices(pfx) {
            if i > 0 && l.as_bytes()[i - 1].is_ascii_alphanumeric() {
                continue;
            }
            let id: String = l[i + pfx.len()..].chars().take_while(|c| c.is_ascii_alphanumeric() || *c == '_' || *c == '-').collect();
            let id = id.trim_end_matches('-');
            if !id.is_empty() && id != "id" {
                out.push(format!("{pfx}{id}"));
            }
        }
    }
    out
}

/// The first hex token of 7 to 40 characters in a line.
fn first_sha(l: &str) -> Option<String> {
    l.split(|c: char| !c.is_ascii_alphanumeric()).find(|w| (7..=40).contains(&w.len()) && w.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))).map(String::from)
}

/// Gate C: stamps on HEAD, the review's card, claim, tables and verdict, `Left running:` last, gates A and B.
fn gate_c(secs: &[Section], i: &Input, lenses: &[String], r: &mut Report) {
    let find = |l: &str| secs.iter().find(|s| s.label == l);
    for s in secs.iter().filter(|s| s.label == "7" || s.label == "8") {
        for l in &s.lines {
            let stamp = l.contains("local only (") || l.starts_with("Review: ready") || l.contains("verdict: ");
            if let Some(sha) = l.rfind(" @").map(|p| &l[p + 2..]).filter(|_| stamp).and_then(first_sha) {
                if !i.head.is_empty() && !pre(&sha, i.head) {
                    r.gaps.push(format!("{}: `@{sha}` is not HEAD {}: {}", s.heading, &i.head[..i.head.len().min(8)], short(l)));
                }
            }
            if l.contains("local only (") && i.has_remote {
                r.gaps.push(format!("{}: says local only but the checkout has a remote", s.heading));
            }
        }
    }
    let lines_of = |l: &str| find(l).map(|s| s.lines.clone()).unwrap_or_default();
    let all: Vec<&str> = secs.iter().flat_map(|s| s.lines.iter().copied()).collect();
    for g in ['A', 'B'] {
        let ok = all.iter().any(|l| l.starts_with(&format!("Gate {g}: PASS")) || l.starts_with(&format!("Gate {g}: WAIVED")));
        if !ok {
            r.gaps.push(format!("no Gate {g}: PASS or WAIVED line"));
        }
    }
    let Some(s8) = find("8") else { return };
    let text = lines_of("8").join("\n");
    let lower = text.to_ascii_lowercase();
    for field in ["author:", "state:", "mergeable:", "linked:"] {
        if !lower.contains(field) {
            r.gaps.push(format!("{}: PR card lacks `{field}`", s8.heading));
        }
    }
    if !(text.contains("CLAIM") || quoted(&text)) {
        r.gaps.push(format!("{}: no quoted claim", s8.heading));
    }
    if !claim_table(&s8.lines) {
        r.gaps.push(format!("{}: no claim-vs-code table row naming file:line", s8.heading));
    }
    if !["APPROVE", "REQUEST-CHANGES", "BLOCK"].iter().any(|v| text.contains(v)) {
        r.gaps.push(format!("{}: no verdict APPROVE, APPROVE-WITH-FIXES, REQUEST-CHANGES or BLOCK", s8.heading));
    }
    lens_lines(s8, lenses, r);
    let last = s8.lines.iter().rev().find(|l| !l.trim().is_empty() && !l.starts_with("Gate C:"));
    if !last.is_some_and(|l| l.starts_with("Left running:")) {
        r.gaps.push(format!("{}: `Left running:` is not its last line before Gate C", s8.heading));
    }
}

/// A double-quoted run of 20+ characters (a verbatim claim or quote).
fn quoted(t: &str) -> bool {
    t.split('"').enumerate().any(|(k, part)| k % 2 == 1 && part.chars().count() >= 20)
}

/// A `path:line` reference such as `src/a.rs:12`.
fn file_line(l: &str) -> bool {
    l.split(|c: char| c.is_whitespace() || c == '`' || c == '|').any(|w| {
        w.rsplit_once(':').is_some_and(|(p, n)| p.contains('.') && !n.is_empty() && n.bytes().all(|b| b.is_ascii_digit() || b == b'-'))
    })
}

/// Lens names from deep-review's lens table (`| [name](references/...)`).
fn lens_names(skills: &Path) -> Vec<String> {
    let text = std::fs::read_to_string(skills.join("deep-review/SKILL.md")).unwrap_or_default();
    let v: Vec<String> = text
        .lines()
        .filter_map(|l| l.strip_prefix("| [")?.split_once("](references/").map(|(n, _)| n.to_string()))
        .collect();
    if v.is_empty() { ["change-guard", "compliance", "security", "performance", "journey"].map(String::from).to_vec() } else { v }
}

/// Each lens line carries its findings (a table or "no findings") and a verdict; compliance always runs.
/// Each lens carries its findings (a table, or "no findings") and a verdict; compliance always runs.
/// A lens's text runs from its `**<lens>:**` line to the next lens or `**Label:**` line, so a review's
/// lens subsections (heading line, prose, table, verdict) count as one.
fn lens_lines(s: &Section, lenses: &[String], r: &mut Report) {
    let starts: Vec<(usize, &String)> = s
        .lines
        .iter()
        .enumerate()
        .filter_map(|(k, l)| lenses.iter().find(|n| l.trim_start_matches(['-', ' ']).starts_with(&format!("**{n}"))).map(|n| (k, n)))
        .collect();
    for (j, (k, name)) in starts.iter().enumerate() {
        let next_label = s.lines[k + 1..]
            .iter()
            .position(|l| {
                let t = l.trim_start_matches(['-', ' ']);
                t.starts_with("**") && t.contains(":**") && !t.starts_with("**Verdict") && !t.starts_with("**Findings")
            })
            .map(|p| k + 1 + p);
        let end = starts.get(j + 1).map(|(n, _)| *n).into_iter().chain(next_label).min().unwrap_or(s.lines.len());
        let body = &s.lines[*k..end];
        let low = body.join("\n").to_ascii_lowercase();
        let table = body.iter().skip(1).any(|x| x.trim_start().starts_with('|'));
        let named = s.lines.iter().any(|x| x.trim_start().starts_with('|') && x.contains(&format!("| {name} |")));
        let severity = ["low", "medium", "high", "critical", "finding"].iter().any(|w| low.contains(w)) && s.lines.iter().any(|x| x.trim_start().starts_with('|') && ["LOW", "MEDIUM", "HIGH", "CRITICAL"].iter().any(|w| x.contains(w)));
        if !(low.contains("no findings") || table || named || severity) {
            r.gaps.push(format!("{}: **{name}:** has no findings table or \"no findings\"", s.heading));
        }
        if !body.iter().any(|l| ["PASS", "FAIL", "CONDITIONAL", "BLOCK"].iter().any(|v| l.contains(v))) {
            r.gaps.push(format!("{}: **{name}:** has no verdict (PASS, FAIL, CONDITIONAL)", s.heading));
        }
    }
    if !starts.iter().any(|(_, n)| n.as_str() == "compliance") {
        r.gaps.push(format!("{}: no **compliance:** lens line", s.heading));
    }
}

/// Placeholder text left in a block: outside code spans anywhere, and inside them on `Left running:` lines.
fn placeholders(s: &Section, r: &mut Report) {
    let mut fence = false;
    for l in &s.lines {
        if l.trim_start().starts_with("```") {
            fence = !fence;
            continue;
        }
        if fence {
            continue;
        }
        let text: String = if l.starts_with("Left running:") { l.to_string() } else { outside_code(l) };
        if let Some(p) = PLACEHOLDERS.iter().find(|p| text.contains(**p)) {
            r.gaps.push(format!("{}: placeholder {p} left in: {}", s.heading, short(l)));
        }
    }
}

/// The text of a line outside backtick spans.
fn outside_code(l: &str) -> String {
    l.split('`').step_by(2).collect::<Vec<_>>().join(" ")
}

/// Owner words quoted in `("…")` must be the ticket's words.
fn owner_quotes(s: &Section, ticket: Option<&str>, r: &mut Report) {
    for l in &s.lines {
        for key in ["local only (\"", "Skipped by owner (\"", "WAIVED by owner (\""] {
            let text = outside_code(l);
            let Some(p) = text.find(key) else { continue };
            let q = text[p + key.len()..].split("\")").next().unwrap_or("");
            match ticket {
                Some(t) if !t.contains(q) => r.gaps.push(format!("{}: owner quote differs from the ticket: \"{}\"", s.heading, short(q))),
                None => r.notes.push(format!("{}: owner quote not checked: no .factory/ticket.md", s.heading)),
                _ => {}
            }
        }
    }
}

fn short(l: &str) -> String {
    let t: String = l.chars().take(80).collect();
    if t.len() < l.len() { format!("{t}...") } else { t }
}

/// `factory lint <A|B|C> [--skills <dir>] [<run folder>]`
pub fn cli(args: &[&str]) -> u8 {
    let gate = args.first().and_then(|g| g.chars().next()).filter(|c| "ABC".contains(*c) && args[0].len() == 1);
    let Some(gate) = gate else {
        eprintln!("usage: factory lint <A|B|C> [--skills <dir>] [<run folder>]");
        return 2;
    };
    let flag = crate::receipt::opt(args, "--skills");
    let folder = args[1..].iter().enumerate().find(|(k, a)| **a != "--skills" && (*k == 0 || args[*k] != "--skills")).map(|(_, a)| *a);
    let start = folder.map_or_else(crate::guard::cwd, |f| std::path::PathBuf::from(crate::paths::norm(f)));
    let Some(dir) = crate::run::locate::walk(&start) else {
        eprintln!("factory lint: no .factory/run.md from {}", crate::paths::text(&start));
        return 1;
    };
    let dir = Path::new(&dir).to_path_buf();
    let run = std::fs::read_to_string(dir.join(".factory/run.md")).unwrap_or_default();
    let ticket = std::fs::read_to_string(dir.join(".factory/ticket.md")).ok();
    let info = crate::git::Repo::discover(&dir).map(|r| r.info()).unwrap_or_default();
    let skills = contracts::skills_dir(flag);
    let rep = check(&Input { gate, run: &run, ticket: ticket.as_deref(), head: &info.head, has_remote: info.remote, skills: skills.as_deref(), dir: &dir });
    for g in &rep.gaps {
        println!("lint {gate}: {g}");
    }
    for n in &rep.notes {
        println!("note: {n}");
    }
    u8::from(!rep.gaps.is_empty())
}

/// The run's kind from its title line `# Run: <link> · <mode> · <kind>`.
fn run_kind(run: &str) -> &str {
    run.lines().next().and_then(|l| l.rsplit(" \u{b7} ").next()).unwrap_or("").trim()
}

/// A contract label is met by `**Label:**`, a bold label starting with it (`**Plan (decisions):**`), or the
/// form the label names: a table for `Table`, a fenced diagram for `Flow`.
fn has_label(sec: &Section, label: &str) -> bool {
    let bold = format!("**{label}");
    let labeled = sec.lines.iter().any(|l| {
        l.match_indices(&bold).any(|(i, _)| matches!(l[i + bold.len()..].chars().next(), Some(':' | ' ' | '(' | '*')))
    });
    labeled
        || (label == "Table" && sec.lines.iter().any(|l| l.trim_start().starts_with('|')))
        || (label == "Flow" && sec.lines.iter().any(|l| l.trim_start().starts_with("```")))
}

/// `No (source) file changed during this step`, or the same fact as `Files changed this step: none`.
fn no_change_line(sec: &Section, phrase: &str) -> bool {
    let p = phrase.to_ascii_lowercase();
    sec.lines.iter().map(|l| l.to_ascii_lowercase()).any(|l| l.contains(&p) || (l.contains("changed this step") && l.contains("none")))
}

/// A claim-vs-code table: a header naming the claim or its delivery, then a row naming `file:line`.
fn claim_table(lines: &[&str]) -> bool {
    let mut in_claim = false;
    for (k, l) in lines.iter().enumerate() {
        let row = l.trim_start().starts_with('|');
        if !row {
            in_claim = false;
            continue;
        }
        let header = lines.get(k + 1).is_some_and(|n| n.trim_start().starts_with("|---") || n.trim_start().starts_with("| ---"));
        if header {
            let low = l.to_ascii_lowercase();
            in_claim = low.contains("claim") || low.contains("delivered");
        } else if in_claim && file_line(l) {
            return true;
        }
    }
    false
}
