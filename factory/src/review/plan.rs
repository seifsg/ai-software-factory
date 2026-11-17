//! Gate A's form check and a reproducible brief for the independent semantic check.

use super::packet;
use crate::git::Repo;
use crate::{contracts, lint, paths};
use std::collections::BTreeMap;
use std::fmt::Write;
use std::path::Path;

type ProofInputs = BTreeMap<String, Vec<String>>;

pub(super) fn assemble(args: &[&str]) -> Result<String, String> {
    let (mut skills, mut manifest) = (None, None);
    let mut pairs = args.chunks_exact(2);
    for pair in &mut pairs {
        match pair {
            ["--skills", value] if skills.is_none() => skills = Some(*value),
            ["--proof-inputs", value] if manifest.is_none() => manifest = Some(*value),
            _ => return Err(format!("unknown or repeated Gate A option {}", pair[0])),
        }
    }
    if !pairs.remainder().is_empty() {
        return Err(format!("missing value for {}", pairs.remainder()[0]));
    }
    let dir = crate::run::locate::walk(&crate::guard::cwd()).ok_or("no .factory/run.md from this folder")?;
    let root = Path::new(&dir);
    let repo = Repo::discover(root).ok_or("Gate A requires a Git checkout")?;
    let info = repo.info();
    if !crate::git::refs::is_sha(&info.head) {
        return Err("Gate A requires a committed HEAD".into());
    }
    let steps = packet::proof(root, ".factory/run.md")?;
    let steps = packet::through(&steps, &["## 4 Before", "## 5 Build", "## 6 Verify", "## 7 PR", "## 8 Review"]);
    let ticket_path = ".factory/ticket.md";
    let ticket = root.join(ticket_path).try_exists().map_err(|err| format!("{ticket_path}: {err}"))?
        .then(|| packet::proof(root, ticket_path)).transpose()?;
    let skills = contracts::skills_dir(skills).ok_or("no skills folder found; pass --skills <dir>")?;
    let rules_file = skills.join("safe-factory/references/checker.md");
    let rules = std::fs::read_to_string(&rules_file).map_err(|err| format!("{}: {err}", paths::text(&rules_file)))?;
    let expected = manifest.map(read_manifest).transpose()?;
    let mut gaps = lint::check(&lint::Input {
        gate: 'A',
        run: steps,
        ticket: ticket.as_deref(),
        head: &info.head,
        has_remote: info.remote,
        skills: Some(&skills),
        proof: &root.join(".factory/proof"),
    }).gaps;
    if let Some(ticket) = &ticket {
        check_criteria(ticket, block(steps, "0"), &mut gaps);
    }
    check_callers(root, block(steps, "1"), &mut gaps);
    if let Some(input) = &expected {
        check_proof_inputs(steps, input, &mut gaps);
    }
    if !gaps.is_empty() {
        return Err(format!("Gate A preflight failed:\n- {}", gaps.join("\n- ")));
    }

    let (_, contract_names) = lint::scope('A').expect("Gate A has contracts");
    let mut out = format!("Role: checker. Gate A. Project: {}. Commit: {}.\n", paths::text(root), info.head);
    out.push_str("Check steps 0 through 3 against every relevant contract before deciding. Stay read-only.\n");
    out.push_str("Check the ticket and source where needed. Future proof inputs in the Plan may be produced later.\n");
    out.push_str("Preflight checked form. Judge meaning, completeness and evidence independently.\n\n");
    out.push_str(&rules);
    for name in contract_names {
        let contract = contracts::of(&skills, name)?;
        writeln!(out, "\n# {name}\n\n{contract}").unwrap();
    }
    if let Some(ticket) = ticket {
        packet::section(&mut out, ".factory/ticket.md", &ticket);
    }
    packet::section(&mut out, ".factory/run.md through Plan", steps);
    Ok(out)
}

fn block(run: &str, id: &str) -> String {
    let prefix = format!("## {id} ");
    let mut lines = run.lines();
    if !lines.any(|line| line.starts_with(&prefix)) {
        return String::new();
    }
    lines.take_while(|line| !line.starts_with("## ")).collect::<Vec<_>>().join("\n")
}

/// Labelled criteria already written in the local ticket are the source for the Ticket block.
fn criterion(line: &str) -> Option<(&str, &str)> {
    let line = line.trim();
    let line = line.strip_prefix("- ").or_else(|| line.strip_prefix("* ")).unwrap_or(line).strip_prefix("**")?;
    let (label, body) = line.split_once(":**")?;
    let id = label.split_whitespace().next()?.strip_prefix('A')?;
    (!id.is_empty() && id.bytes().all(|b| b.is_ascii_digit())).then_some((label, body.trim()))
}

fn check_criteria(ticket: &str, intake: String, gaps: &mut Vec<String>) {
    let actual: Vec<_> = intake.lines().filter_map(criterion).collect();
    for accepted in ticket.lines().filter_map(criterion) {
        if !actual.contains(&accepted) {
            gaps.push(format!("## 0 Ticket: copy the ticket's **{}:** criterion with its full text", accepted.0));
        }
    }
}

/// Read exact file citations in the caller list. A literal tab can come from an interpreted path.
fn check_callers(root: &Path, analysis: String, gaps: &mut Vec<String>) {
    let Some((_, callers)) = analysis.split_once("**Used by:**") else { return };
    for line in callers.lines() {
        if line.trim_start().starts_with("**") {
            break;
        }
        if line.trim().contains('\t') {
            gaps.push("## 1 Analyze: a tab in Used by may be a corrupted file citation".into());
        }
        for span in spans(line) {
            let path = span.split(':').next().unwrap_or_default();
            if !path.contains(['/', '\\']) || !path.rsplit(['/', '\\']).next().is_some_and(|name| name.contains('.'))
                || path.contains(['*', '?', '<', '>', '(', ')', '=']) {
                continue;
            }
            if let Ok(path) = packet::relative(path) {
                if !root.join(path).is_file() {
                    gaps.push(format!("## 1 Analyze: cited caller path does not name a file: {span}"));
                }
            }
        }
    }
}

fn read_manifest(file: &str) -> Result<ProofInputs, String> {
    let content = std::fs::read_to_string(file).map_err(|err| format!("{file}: {err}"))?;
    let map: ProofInputs = serde_json::from_str(content.trim_start_matches('\u{feff}')).map_err(|err| format!("{file}: {err}"))?;
    for (id, files) in &map {
        if id.is_empty() || files.is_empty() {
            return Err(format!("{file}: every proof needs an ID and at least one input"));
        }
        for path in files {
            packet::relative(path)?;
        }
    }
    Ok(map)
}

/// Compare exact literal paths per proof. The manifest may name future generated files.
fn check_proof_inputs(run: &str, expected: &ProofInputs, gaps: &mut Vec<String>) {
    let rows = crate::guard::before::rows(run);
    for (id, files) in expected {
        let mut found = rows.iter().filter(|(row, _)| *row == id);
        let Some((_, row)) = found.next() else {
            gaps.push(format!("## 3 Plan: Proof list is missing {id}"));
            continue;
        };
        if found.next().is_some() {
            gaps.push(format!("## 3 Plan: Proof list has duplicate rows for {id}"));
            continue;
        }
        let spans: Vec<_> = spans(row).map(paths::norm).collect();
        for file in files {
            if !spans.contains(&paths::norm(file)) {
                gaps.push(format!("## 3 Plan: {id} needs proof input `{file}`"));
            }
        }
    }
}

fn spans(line: &str) -> impl Iterator<Item = &str> {
    let mut fields = line.split('`').skip(1);
    std::iter::from_fn(move || {
        let inside = fields.next()?;
        fields.next()?;
        Some(inside.trim())
    })
}
