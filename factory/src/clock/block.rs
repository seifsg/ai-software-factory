//! The owner's time block: a `text` fence, `total` first, one bar per phase that took time, bars scaled to
//! the longest phase, and a cause note on lost time. `--json` carries the same numbers.

use super::phase::Phase;
use super::split::Split;
use serde_json::{Value, json};

const LABEL: usize = 29;
const BAR: u64 = 12;

/// `9m25s`, `0m41s`, from one hour `2h13m20s`.
pub fn dur(secs: u64) -> String {
    let (h, m, s) = (secs / 3600, secs % 3600 / 60, secs % 60);
    if h > 0 { format!("{h}h{m:02}m{s:02}s") } else { format!("{m}m{s:02}s") }
}

/// Parses `dur`'s forms back, plus bare `<n>s` and `<n>m`; None for anything else.
pub fn parse_dur(s: &str) -> Option<u64> {
    let (mut total, mut num, mut seen) = (0u64, String::new(), false);
    for c in s.chars() {
        match c {
            '0'..='9' => num.push(c),
            'h' | 'm' | 's' if !num.is_empty() => {
                let unit = match c {
                    'h' => 3600,
                    'm' => 60,
                    _ => 1,
                };
                total = total.checked_add(num.parse::<u64>().ok()?.checked_mul(unit)?)?;
                num.clear();
                seen = true;
            }
            _ => return None,
        }
    }
    (seen && num.is_empty()).then_some(total)
}

/// The phases that took time, in row order.
fn rows(x: &Split) -> impl Iterator<Item = Phase> + '_ {
    Phase::ALL.into_iter().filter(|p| x.secs[*p as usize] > 0)
}

/// The note after a bar: the full-suite count on tests, then lost time and its cause.
fn note(x: &Split, p: Phase) -> String {
    let mut parts = Vec::new();
    if p == Phase::Tests && x.full_runs > 0 {
        parts.push(format!("{} full-suite run{}", x.full_runs, if x.full_runs == 1 { "" } else { "s" }));
    }
    let lost = x.lost[p as usize];
    if lost > 0 {
        let why = cause(&x.why[p as usize]);
        parts.push(if why.is_empty() { format!("{} lost", dur(lost)) } else { format!("{} lost: {why}", dur(lost)) });
    }
    if parts.is_empty() { String::new() } else { format!("  ({})", parts.join("; ")) }
}

/// A cause as one short line that can never close the fence (a `Waiting:` text or an agent's note), capped.
fn cause(why: &str) -> String {
    const MAX: usize = 120;
    let one: String = why
        .chars()
        .map(|c| {
            if c == '`' {
                '\''
            } else if c.is_control() {
                ' '
            } else {
                c
            }
        })
        .collect();
    if one.chars().count() > MAX { one.chars().take(MAX - 1).chain(['…']).collect() } else { one }
}

/// The block, fence included, ready to paste.
pub fn text(x: &Split) -> String {
    let longest = rows(x).map(|p| x.secs[p as usize]).max().unwrap_or(0);
    let mut out = format!("```text\n{:<LABEL$}{}\n", "total", dur(x.end - x.start));
    for p in rows(x) {
        let s = x.secs[p as usize];
        let n = ((s * BAR + longest / 2) / longest).max(1) as usize;
        let note = note(x, p);
        out.push_str(&format!("{:<LABEL$}{} {}{note}\n", p.label(), "█".repeat(n), dur(s)));
    }
    out.push_str("```\n");
    out
}

/// The same numbers as data (seconds), plus the block.
pub fn json(x: &Split, open: bool) -> Value {
    let phases: Vec<Value> = rows(x)
        .map(|p| json!({ "id": p.id(), "label": p.label(), "secs": x.secs[p as usize], "lost": x.lost[p as usize], "why": x.why[p as usize] }))
        .collect();
    let iso = crate::receipt::utc_iso;
    json!({
        "start": iso(x.start), "end": iso(x.end), "open": open, "total": x.end - x.start,
        "phases": phases, "full_runs": x.full_runs, "block": text(x),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn owner_format_exactly() {
        // The owner's example of 27 Nov: 57m42s, waiting 9m25s, build 16m22s (11m03s lost), tests 10m17s, review 2m10s.
        let mut x = Split { start: 0, end: 3462, ..Split::default() };
        for (p, s) in [(Phase::Owner, 565), (Phase::Build, 982), (Phase::Tests, 617), (Phase::Review, 130)] {
            x.secs[p as usize] = s;
        }
        x.lost[Phase::Build as usize] = 663;
        x.why[Phase::Build as usize] = "xwin symlink".into();
        let want = "```text\ntotal                        57m42s\nwaiting on you               ███████ 9m25s\nbuild                        ████████████ 16m22s  (11m03s lost: xwin symlink)\ntests + CI                   ████████ 10m17s\nreview + gates               ██ 2m10s\n```\n";
        assert_eq!(text(&x), want);
        x.full_runs = 7;
        assert!(text(&x).contains("10m17s  (7 full-suite runs)\n"));
        // A cause can never close the fence or run on: backticks and control characters go, long text is cut.
        x.why[Phase::Build as usize] = format!("```\nrm {}", "x".repeat(200));
        let line = text(&x).lines().find(|l| l.starts_with("build")).unwrap().to_string();
        assert!(line.ends_with("…)") && line.contains("lost: ''' rm xx") && !line.contains('`'), "{line}");
        assert_eq!(text(&x).matches("```").count(), 2);
        assert_eq!(json(&x, false)["phases"][1]["lost"], 663);
    }

    #[test]
    fn durations_round_trip() {
        assert_eq!([dur(41), dur(565), dur(8000)], ["0m41s", "9m25s", "2h13m20s"]);
        assert_eq!(
            [parse_dur("11m03s"), parse_dur("2h13m20s"), parse_dur("90s"), parse_dur("5m")],
            [Some(663), Some(8000), Some(90), Some(300)]
        );
        assert!(parse_dur("").is_none() && parse_dur("5").is_none() && parse_dur("1x").is_none() && parse_dur("m").is_none());
    }
}
