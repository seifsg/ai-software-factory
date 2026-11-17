//! Validate explicit handback files against the portable review contracts before gate submission.

use crate::git::refs::is_sha;

const CLAIM_HEADER: [&str; 4] = ["Claimed behavior", "Where (file:line)", "Delivered? YES / PARTIAL / NO", "Note"];

/// Reads the supplied files and checks their form without granting a verdict or touching the run.
pub(super) fn check(args: &[&str]) -> Result<(), String> {
    let (mut role, mut head, mut gate, mut report, mut handback) = (None, None, None, None, None);
    let mut args = args.iter().copied();
    while let Some(arg) = args.next() {
        let option = match arg {
            "--role" => &mut role,
            "--head" => &mut head,
            "--gate" => &mut gate,
            "--report" => &mut report,
            "--" => {
                let path = args.next().ok_or("missing handback path after --")?;
                if handback.replace(path).is_some() || args.next().is_some() {
                    return Err("provide one handback file".into());
                }
                break;
            }
            _ if arg.starts_with('-') => return Err(format!("unknown option {arg}")),
            _ => {
                if handback.replace(arg).is_some() {
                    return Err("provide one handback file".into());
                }
                continue;
            }
        };
        let value = args.next().filter(|s| !s.is_empty() && !s.starts_with("--")).ok_or_else(|| format!("missing value for {arg}"))?;
        if option.replace(value).is_some() {
            return Err(format!("duplicate {arg}"));
        }
    }

    let head = head.filter(|sha| is_sha(sha)).ok_or("--head must be a full Git commit SHA")?;
    let path = handback.ok_or("provide one handback file")?;
    match (role, gate, report) {
        (Some("deep"), None, None) => verdict(&read(path)?, head, &["ready", "not ready", "PASS", "FAIL", "CONDITIONAL"]),
        (Some("final"), None, Some(report)) => {
            let handback = read(path)?;
            verdict(&handback, head, &["ready", "ready after fixes", "not ready"])?;
            if path == report { claim_table(&handback) } else { claim_table(&read(report)?) }
        }
        (Some("checker"), Some(gate @ ("A" | "B" | "C")), None) => gate_verdict(&read(path)?, gate, head),
        (Some("final"), None, None) => Err("final review requires --report <file>".into()),
        (Some("checker"), _, None) => Err("checker requires --gate A, B or C".into()),
        (Some("deep" | "final" | "checker"), _, _) => Err("use --gate only for checker and --report only for final review".into()),
        _ => Err("--role must be deep, final or checker".into()),
    }
}

fn read(path: &str) -> Result<String, String> {
    std::fs::read_to_string(path).map_err(|err| format!("cannot read {path}: {err}"))
}

/// Compare the final line in full so a quoted example or an older candidate cannot satisfy it.
fn verdict(text: &str, head: &str, allowed: &[&str]) -> Result<(), String> {
    let last = text.trim_start_matches('\u{feff}').trim_end().lines().next_back().unwrap_or_default();
    if last
        .strip_prefix("verdict: ")
        .and_then(|line| line.rsplit_once(" @"))
        .is_some_and(|(word, sha)| sha == head && allowed.contains(&word))
    {
        Ok(())
    } else {
        Err(format!("last line must be verdict: {} @{head}", allowed.join(" | ")))
    }
}

fn gate_verdict(text: &str, gate: &str, head: &str) -> Result<(), String> {
    let last = text.trim_start_matches('\u{feff}').trim_end().lines().next_back().unwrap_or_default();
    let prefix = format!("Gate {gate}: ");
    let line = last.strip_prefix(&prefix).unwrap_or_default();
    let failed = line
        .strip_prefix("FAIL ")
        .and_then(|line| line.strip_suffix(" missing"))
        .is_some_and(|n| !n.is_empty() && n.bytes().all(|b| b.is_ascii_digit()) && n.parse::<u32>().is_ok_and(|n| n > 0));
    if line.strip_prefix("PASS @") == Some(head) {
        return Ok(());
    }
    if failed {
        if text.lines().any(|line| {
            line.split_once(": MISSING ").is_some_and(|(criterion, reason)| !criterion.trim().is_empty() && !reason.trim().is_empty())
        }) {
            return Ok(());
        }
        return Err(format!("Gate {gate} FAIL needs the missing contract lines and their reasons"));
    }
    Err(format!("last line must be Gate {gate}: PASS @{head} or Gate {gate}: FAIL <positive count> missing"))
}

/// A usable report contains a real table, not a fenced example or an empty heading.
fn claim_table(report: &str) -> Result<(), String> {
    let mut fence = None;
    let mut lines = report
        .trim_start_matches('\u{feff}')
        .lines()
        .map(|line| {
            let line = line.trim();
            let marker = line.as_bytes().first().copied();
            let count = line.bytes().take_while(|b| Some(*b) == marker).count();
            match fence {
                Some((open, width)) => {
                    if marker == Some(open) && count >= width && count == line.len() {
                        fence = None;
                    }
                    ""
                }
                None if count >= 3 && matches!(marker, Some(b'`' | b'~')) => {
                    fence = marker.map(|m| (m, count));
                    ""
                }
                None => line,
            }
        })
        .peekable();

    while let Some(line) = lines.next() {
        if columns(line).as_deref() != Some(&CLAIM_HEADER) {
            continue;
        }
        let Some(divider) = lines.next().and_then(columns) else { continue };
        if divider.len() != CLAIM_HEADER.len() || !divider.iter().all(|cell| alignment(cell)) {
            continue;
        }
        let mut found = false;
        while let Some(row) = lines.peek().copied().and_then(columns) {
            lines.next();
            let [claim, location, delivered, _] = row.as_slice() else {
                return Err("claim-versus-code rows must have four columns".into());
            };
            if claim.is_empty() || location.is_empty() || !matches!(delivered.trim_matches(['*', '_', '`']), "YES" | "PARTIAL" | "NO") {
                return Err("claim-versus-code rows need a claim, location and a YES, PARTIAL or NO result".into());
            }
            found = true;
        }
        if found {
            return Ok(());
        }
    }
    Err(format!("report needs a claim-versus-code table with rows under | {} |", CLAIM_HEADER.join(" | ")))
}

fn alignment(cell: &str) -> bool {
    let cell = cell.strip_prefix(':').unwrap_or(cell);
    let cell = cell.strip_suffix(':').unwrap_or(cell);
    !cell.is_empty() && cell.bytes().all(|b| b == b'-')
}

/// Split Markdown cells while keeping escaped pipes inside the field that owns them.
fn columns(line: &str) -> Option<Vec<&str>> {
    let row = line.strip_prefix('|')?.strip_suffix('|')?;
    let mut cells = Vec::new();
    let mut start = 0;
    let mut escaped = false;
    for (i, b) in row.bytes().enumerate() {
        if b == b'|' && !escaped {
            cells.push(row[start..i].trim());
            start = i + 1;
        }
        escaped = b == b'\\' && !escaped;
    }
    cells.push(row[start..].trim());
    Some(cells)
}

#[cfg(test)]
mod tests {
    use super::*;

    const HEAD: &str = "23128516275fabfa34c9a45dd6ab9a089e6f5dea";
    const BASE: &str = "802b5d69305a1d048c7ee11016489caf0baf9f18";
    const HEADER: &str = "| Claimed behavior | Where (file:line) | Delivered? YES / PARTIAL / NO | Note |";
    const ROW: &str = r"| Read `timeoutMs` \| use the default | `src/config.js:5` | YES | Both consumers checked. |";

    #[test]
    fn requires_the_report_shape_that_gate_c_caught() {
        let body = format!("{HEADER}\r\n| --- | :--- | ---: | :---: |\r\n{ROW}\r\n");
        assert!(claim_table(&body).is_ok());
        assert!(claim_table(&format!("```text\n{body}```\n")).is_err());
        assert!(claim_table(&format!("{HEADER}\n| --- | --- | --- | --- |\n")).is_err());
        assert!(claim_table(&body.replace("YES | Both", "Met | Both")).is_err());
        assert!(claim_table("| Criterion | Code and proof | Result |\n| --- | --- | --- |\n| A1 | `src/config.js:5` | Met |\n").is_err());
    }

    #[test]
    fn binds_verdicts_to_the_exact_candidate_and_distinguishes_form_from_approval() {
        let final_words = &["ready", "ready after fixes", "not ready"];
        assert!(verdict(&format!("Report follow-up\nverdict: not ready @{HEAD}\r\n\r\n"), HEAD, final_words).is_ok());
        assert!(verdict(&format!("verdict: ready @{BASE}"), HEAD, final_words).is_err());
        assert!(verdict(&format!("verdict: ready @{HEAD}\nSome more text"), HEAD, final_words).is_err());
        assert!(gate_verdict(&format!("met: proof\nGate C: PASS @{HEAD}"), "C", HEAD).is_ok());
        assert!(gate_verdict("Claim table: MISSING candidate citations\nGate C: FAIL 1 missing", "C", HEAD).is_ok());
        assert!(gate_verdict("Gate C: FAIL 1 missing", "C", HEAD).is_err());
        assert!(gate_verdict("Gate C: FAIL 0 missing", "C", HEAD).is_err());
        assert!(gate_verdict(&format!("Gate B: PASS @{HEAD}"), "C", HEAD).is_err());
        assert!(gate_verdict(&format!("Gate C: PASS @{BASE}"), "C", HEAD).is_err());
    }
}
