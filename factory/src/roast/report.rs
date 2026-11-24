//! Turns the outside agent's answer into `roast.md` and a verdict. Empty, malformed or cut short is INCOMPLETE, never clean.

use super::pick::Vendor;
use super::run::Done;
use crate::paths::text;
use std::path::Path;

/// The roast's verdict, as the brief defines it.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Verdict {
    Ship,
    ShipWithFixes,
    DoNotShip,
    Incomplete,
}

impl Verdict {
    /// One token for the receipt line.
    pub fn token(self) -> &'static str {
        match self {
            Self::Ship => "SHIP",
            Self::ShipWithFixes => "SHIP-WITH-FIXES",
            Self::DoNotShip => "DO-NOT-SHIP",
            Self::Incomplete => "INCOMPLETE",
        }
    }

    fn from_line(v: &str) -> Option<Self> {
        match v.trim().trim_matches('*').trim().to_ascii_uppercase().as_str() {
            "SHIP" => Some(Self::Ship),
            "SHIP WITH FIXES" => Some(Self::ShipWithFixes),
            "DO NOT SHIP" => Some(Self::DoNotShip),
            _ => None,
        }
    }
}

/// The verdict line and the number of `### F<n> [` findings; `None` without a valid `VERDICT:` line.
pub fn parse(report: &str) -> Option<(Verdict, usize)> {
    let verdict = report.lines().map(|l| l.trim().trim_start_matches('*')).find_map(|l| l.strip_prefix("VERDICT:")).and_then(Verdict::from_line)?;
    let findings = report.lines().filter(|l| is_finding(l.trim_start())).count();
    Some((verdict, findings))
}

fn is_finding(l: &str) -> bool {
    l.strip_prefix("### F").is_some_and(|r| {
        let digits = r.bytes().take_while(u8::is_ascii_digit).count();
        digits > 0 && r[digits..].trim_start().starts_with('[')
    })
}

/// Writes `roast.md` beside the agent's fresh output in `dir` (never a stale copy from an earlier run) and returns
/// the verdict and finding count.
pub fn finish(vendor: Vendor, dir: &Path, done: &Done) -> Result<(Verdict, usize), String> {
    let answer = answer(vendor, dir);
    let parsed = answer.as_deref().ok().and_then(parse);
    let (body, result) = match (parsed, done.timed_out) {
        (Some(p), false) => (answer.unwrap_or_default(), p),
        _ => (incomplete(done, &answer, dir), (Verdict::Incomplete, 0)),
    };
    let file = dir.join("roast.md");
    std::fs::write(&file, body).map_err(|e| format!("cannot write {}: {e}", text(&file)))?;
    Ok(result)
}

/// The agent's final Markdown: Codex writes it with `-o`; Claude returns it as `result` in its JSON.
fn answer(vendor: Vendor, out: &Path) -> Result<String, String> {
    let read = |name: &str| std::fs::read_to_string(out.join(name)).map_err(|e| format!("no {name}: {e}"));
    match vendor {
        Vendor::Codex => read("agent.md"),
        Vendor::Claude => {
            let json: serde_json::Value = serde_json::from_str(&read("agent.out")?).map_err(|e| format!("agent.out is not JSON: {e}"))?;
            if json["is_error"].as_bool() == Some(true) {
                return Err(format!("claude reported an error: {}", json["result"].as_str().unwrap_or("no message")));
            }
            json["result"].as_str().map(str::to_owned).ok_or_else(|| "agent.out has no result".into())
        }
    }
}

/// An INCOMPLETE report that says why and keeps what the agent left, so nothing reads as a clean pass.
fn incomplete(done: &Done, answer: &Result<String, String>, out: &Path) -> String {
    let why = match (done.timed_out, answer) {
        (true, _) => format!("timed out after {} s; the agent was stopped", done.secs),
        (false, Err(e)) => format!("no report ({e}); exit code {:?}", done.code),
        (false, Ok(_)) => format!("report has no valid VERDICT line; exit code {:?}", done.code),
    };
    let err = std::fs::read_to_string(out.join("agent.err")).unwrap_or_default();
    let tail: String = err.lines().rev().take(20).collect::<Vec<_>>().into_iter().rev().collect::<Vec<_>>().join("\n");
    let left = answer.as_deref().unwrap_or_default();
    format!("VERDICT: INCOMPLETE\nReason: {why}\n\nWhat the agent left (data, not a verdict):\n\n~~~~text\n{left}\n~~~~\n\n`agent.err`, last lines:\n\n~~~~text\n{tail}\n~~~~\n")
}

#[cfg(test)]
mod tests {
    use super::{Verdict::*, parse};

    #[test]
    fn verdict_and_findings() {
        let r = "VERDICT: SHIP WITH FIXES\nFirst impression: x\n\n### F1 [MAJOR] Breaks double submit\n### F2 [POLISH] Copy\n### Fx [MAJOR] no\n";
        assert_eq!(parse(r), Some((ShipWithFixes, 2)));
        assert_eq!(parse("**VERDICT: do not ship**\n### F1 [BLOCKER] x"), Some((DoNotShip, 1)));
        assert_eq!(parse("VERDICT: SHIP"), Some((Ship, 0)));
        assert_eq!(parse("VERDICT: SHIP | SHIP WITH FIXES | DO NOT SHIP"), None);
        assert_eq!(parse("all good"), None);
        assert_eq!(parse(""), None);
    }
}
