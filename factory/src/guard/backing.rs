//! `guard check` with no session id: one verdict line per gate and review line in the run file, backed by
//! its delegate's own handback on that commit, or not, plus each Gate B and C line's suite receipt.
//! It reads the transcripts the Stop hook last recorded; it changes no run or state file.

use super::rules::pre;
use crate::evidence::{self, Evidence};
use crate::git::Repo;
use crate::run::state::{Loaded, State};
use crate::run::{RunFile, after_at};
use std::path::Path;

/// The report and whether every line is backed.
pub fn report(dir: &Path) -> (String, bool) {
    let text = std::fs::read(dir.join(".factory/run.md")).unwrap_or_default();
    let run = RunFile::parse(&text);
    let g = dir.join(".factory/guard");
    let state = match State::load(&g.join("state")) {
        Loaded::Valid(s) => s,
        _ => State::default(),
    };
    let sessions: Vec<String> = state.get("sessions").split(' ').filter(|q| !q.is_empty()).map(String::from).collect();
    let ev = evidence::collect(state.get("transcript"), &sessions, &run.wanted_ids(), &g);
    let repo = Repo::discover(dir);
    let mut out = String::new();
    let mut all = true;
    let mut line = |label: &str, ok: bool, why: String| {
        all &= ok;
        out.push_str(&format!("{label}: {} {why}\n", if ok { "backed:" } else { "NOT backed:" }));
    };
    for x in ['A', 'B', 'C'] {
        if let Some((id, sha)) = run.gate.get(&x) {
            let (ok, why) = handback(&ev, id, x, sha);
            let (rok, rwhy) = receipt(repo.as_ref(), x, sha);
            line(&format!("Gate {x}"), ok && rok, format!("{why}{rwhy}"));
        } else if let Some(sha) = run.cap.get(&x) {
            line(&format!("Gate {x}"), false, format!("cap line @{sha}: a reviewer counts its 3 failed handbacks"));
        } else if run.waived.contains(&x) {
            line(&format!("Gate {x}"), false, "owner waiver: a user message must grant it".into());
        }
    }
    if let Some((id, sha)) = &run.review {
        let (ok, why) = handback(&ev, id, 'R', sha);
        line("Review", ok, why);
    }
    if out.is_empty() {
        out.push_str("no gate or review line in the run file\n");
    }
    (out, all)
}

/// Whether delegate `id`'s own last handback backs a line for loop `k` on `sha`.
fn handback(ev: &Evidence, id: &str, k: char, sha: &str) -> (bool, String) {
    if ev.none {
        return (false, format!("{id}: no transcript recorded for this run (no command Stop hook ran): check its handback by hand"));
    }
    if ev.fallback {
        let ok = ev.seen.contains(id) && !ev.claude_fallback;
        return (ok, format!("{id} {} the session transcript", if ok { "appears in" } else { "is not provable from" }));
    }
    let role = ev.kind.get(id).copied();
    let last = ev.last.get(id).map_or("", String::as_str);
    let want = if k == 'R' { "reviewer" } else { "checker" };
    if role != Some(k) {
        return (false, format!("{id} is no {want} for this line (its brief names {})", role.map_or("no role".into(), |r| r.to_string())));
    }
    let passed = if k == 'R' {
        last == "verdict: ready" || last.starts_with("verdict: ready @")
    } else {
        last.get(6..).is_some_and(|s| s.starts_with(": PASS"))
    };
    if !passed {
        return (false, format!("{id}'s last handback is `{last}`"));
    }
    if !pre(sha, after_at(last)) {
        return (false, format!("{id} handed back `{last}`, the line says @{sha}"));
    }
    (true, format!("{id} handed back `{last}`"))
}

/// Gate B and C need a passing full-suite receipt for their commit's tree.
fn receipt(repo: Option<&Repo>, x: char, sha: &str) -> (bool, String) {
    if !matches!(x, 'B' | 'C') {
        return (true, String::new());
    }
    match repo.and_then(|r| crate::receipt::find_pass(r, sha, "full")) {
        Some((p, r)) => (
            true,
            format!("; receipt {} (`{}`, {} s, clean {})", crate::paths::text(&p), r.cmd, r.secs, if r.clean { "yes" } else { "no" }),
        ),
        None => (false, format!("; no full-suite receipt for the tree of {sha}")),
    }
}
