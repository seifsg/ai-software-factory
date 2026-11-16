//! The run file `.factory/run.md`: the facts the guard reads from it, line by line, in one pass.
//! Hooks read only the header lines, step headings and gate lines, so spelling here is exact.

pub mod locate;
pub mod state;

use std::collections::{BTreeMap, BTreeSet};

/// Everything the guard takes from a run file.
#[derive(Debug, Default, Clone)]
pub struct RunFile {
    /// `Status: stopped` in the header.
    pub stopped: bool,
    /// The header has a `Waiting:` line (a run without one has a broken header).
    pub has_waiting: bool,
    pub wait_owner: bool,
    pub wait_jobs: bool,
    /// `(max <n> min)` of a jobs wait, 0 when absent.
    pub jobs_max: u64,
    /// Ticked step headings in file order (`0`, `2b`, ...), repeats kept.
    pub ticked: Vec<String>,
    pub done: BTreeSet<String>,
    /// Lines holding a tick mark, anywhere.
    pub tick_lines: u64,
    /// `## 8 Review ✔`.
    pub review_ticked: bool,
    /// One past the highest ticked numeric step.
    pub after_ticked: u32,
    /// The first strict `Next:` value (`5 Build · get-ready-to-code`), or empty.
    pub next: String,
    /// Checker PASS lines per gate: (checker id, sha).
    pub gate: BTreeMap<char, (String, String)>,
    /// Sections holding an open `CRITICAL:` line, by heading label (`3`, `6`, `8`).
    pub critical: BTreeSet<String>,
    /// Cap lines per loop (`A`, `B`, `C`, `R`): their sha.
    pub cap: BTreeMap<char, String>,
    pub waived: BTreeSet<char>,
    /// `Review: ready (reviewer <id>) @<sha>`.
    pub review: Option<(String, String)>,
    /// Line numbers over 300 characters outside tables and closed fences, comma-joined.
    pub long_lines: String,
}

const TICK: &str = "\u{2714}";

impl RunFile {
    /// Parses run-file bytes. Lines split on `\n` only; a CR stays part of its line, as the awk pass sees it.
    pub fn parse(data: &[u8]) -> RunFile {
        let mut r = RunFile::default();
        let mut sec: Option<String> = None;
        let (mut in_fence, mut fence_long, mut long) = (false, String::new(), String::new());
        let text = data.strip_suffix(b"\n").unwrap_or(data);
        for (n, raw) in text.split(|&b| b == b'\n').enumerate() {
            let line = String::from_utf8_lossy(raw);
            let l = line.as_ref();
            let lineno = n + 1;
            if sec.is_none() {
                if l.starts_with("Status: stopped") {
                    r.stopped = true;
                }
                if l.starts_with("Waiting: ") && !r.has_waiting {
                    r.has_waiting = true;
                    r.wait_owner = l.starts_with("Waiting: owner");
                    if l.starts_with("Waiting: jobs:") {
                        r.wait_jobs = true;
                        r.jobs_max = jobs_max(l);
                    }
                }
            }
            if let Some(step) = ticked_heading(l) {
                r.ticked.push(step.clone());
                r.done.insert(step);
            }
            if l.contains(TICK) {
                r.tick_lines += 1;
            }
            if l.starts_with(&format!("## 8 Review {TICK}")) {
                r.review_ticked = true;
            }
            if let Some(d) = numeric_ticked(l) {
                r.after_ticked = r.after_ticked.max(d + 1);
            }
            if r.next.is_empty() {
                r.next = strict_next(l);
            }
            if let Some((g, id, sha)) = gate_pass(l) {
                r.gate.insert(g, (id, sha));
            }
            if l.starts_with("## ") {
                sec = Some(field(l, 1).to_string());
            }
            if fence_line(raw) {
                if in_fence {
                    fence_long.clear();
                }
                in_fence = !in_fence;
            } else if !table_line(raw) && raw.len() > 300 && chars(raw) > 300 {
                if in_fence {
                    fence_long.push_str(&format!(",{lineno}"));
                } else {
                    push_list(&mut long, &lineno.to_string());
                }
            }
            if l.starts_with("CRITICAL: ") {
                r.critical.insert(sec.clone().unwrap_or_default());
            }
            if let Some((x, sha)) = cap_line(l) {
                r.cap.insert(x, sha);
            }
            if let Some(g) = l.strip_prefix("Gate ").filter(|s| s.len() > 1 && s[1..].starts_with(": WAIVED by owner")) {
                if let Some(c) = g.chars().next().filter(|c| "ABC".contains(*c)) {
                    r.waived.insert(c);
                }
            }
            if let Some(rv) = review_line(l) {
                r.review = Some(rv);
            }
        }
        if !r.has_waiting {
            r.next.clear();
        }
        if in_fence && !fence_long.is_empty() {
            if long.is_empty() {
                long = fence_long[1..].to_string();
            } else {
                long.push_str(&fence_long);
            }
        }
        r.long_lines = long;
        r
    }

    /// Checker and reviewer ids the run file names: the evidence scan looks for these.
    pub fn wanted_ids(&self) -> Vec<String> {
        let mut v: Vec<String> = self.gate.values().map(|(id, _)| id.clone()).collect();
        v.extend(self.review.iter().map(|(id, _)| id.clone()));
        v.sort();
        v.dedup();
        v
    }
}

/// Appends to a comma list.
pub fn push_list(list: &mut String, item: &str) {
    if !list.is_empty() {
        list.push(',');
    }
    list.push_str(item);
}

/// Whitespace field `i` (0-based) of a line, as awk splits it.
pub fn field(l: &str, i: usize) -> &str {
    l.split([' ', '\t']).filter(|s| !s.is_empty()).nth(i).unwrap_or("")
}

/// Text after the last `@` (awk's `sub(/.*@/, "")`).
pub fn after_at(t: &str) -> &str {
    t.rfind('@').map_or(t, |i| &t[i + 1..])
}

/// `## <0-8>[b] <...>✔` → the step label.
fn ticked_heading(l: &str) -> Option<String> {
    let b = l.as_bytes();
    if !l.starts_with("## ") || b.len() < 5 || !(b'0'..=b'8').contains(&b[3]) {
        return None;
    }
    let rest = if b[4] == b'b' { &l[5..] } else { &l[4..] };
    (rest.starts_with(' ') && rest[1..].contains(TICK)).then(|| field(l, 1).to_string())
}

/// `## <0-8> <...>✔` (no `b`) → the digit.
fn numeric_ticked(l: &str) -> Option<u32> {
    let b = l.as_bytes();
    (l.starts_with("## ") && b.len() > 5 && (b'0'..=b'8').contains(&b[3]) && b[4] == b' ' && l[5..].contains(TICK))
        .then(|| (b[3] - b'0') as u32)
}

/// `Next: *<0-8>[b] <letters> · <a-z->` → that value (spaces after `Next:` dropped), else empty.
fn strict_next(l: &str) -> String {
    let Some(rest) = l.strip_prefix("Next:") else { return String::new() };
    let v = rest.trim_start_matches(' ');
    let b = v.as_bytes();
    if b.is_empty() || !(b'0'..=b'8').contains(&b[0]) {
        return String::new();
    }
    let mut i = 1;
    if b.get(i) == Some(&b'b') {
        i += 1;
    }
    if b.get(i) != Some(&b' ') {
        return String::new();
    }
    i += 1;
    let name = b[i..].iter().take_while(|c| c.is_ascii_alphabetic()).count();
    if name == 0 {
        return String::new();
    }
    i += name;
    let Some(after) = v[i..].strip_prefix(" \u{b7} ") else { return String::new() };
    let skill = after.bytes().take_while(|&c| c.is_ascii_lowercase() || c == b'-').count();
    if skill == 0 {
        return String::new();
    }
    v[..v.len() - after.len() + skill].to_string()
}

/// `Gate X: PASS (checker <id>) @<hex>...` → (X, id, sha after the last `@` of field 6).
fn gate_pass(l: &str) -> Option<(char, String, String)> {
    let g = l.strip_prefix("Gate ")?.chars().next().filter(|c| "ABC".contains(*c))?;
    let rest = l.get(6..)?.strip_prefix(": PASS (checker ")?;
    let close = rest.find([' ', ')']).filter(|&c| c > 0)?;
    let tail = rest[close..].strip_prefix(") @")?;
    tail.bytes().next().filter(u8::is_ascii_hexdigit).filter(|c| !c.is_ascii_uppercase())?;
    let id = field(l, 4).trim_end_matches_once(')');
    Some((g, id.to_string(), after_at(field(l, 5)).to_string()))
}

/// `Gate X: PASS (cap, 3 rounds, no CRITICAL) @<hex>` or `Review: ready (cap, ...) @<hex>` → (loop, hex).
fn cap_line(l: &str) -> Option<(char, String)> {
    const CAP: &str = " (cap, 3 rounds, no CRITICAL) @";
    let (x, rest) = if let Some(r) = l.strip_prefix("Review: ready") {
        ('R', r)
    } else {
        let g = l.strip_prefix("Gate ")?.chars().next().filter(|c| "ABC".contains(*c))?;
        (g, l.get(6..)?.strip_prefix(": PASS")?)
    };
    let hex: String = rest.strip_prefix(CAP)?.chars().take_while(|c| c.is_ascii_digit() || ('a'..='f').contains(c)).collect();
    (!hex.is_empty()).then_some((x, hex))
}

/// `Review: ready (reviewer <id>) @<hex>` → (id, sha after the last `@` of field 5).
fn review_line(l: &str) -> Option<(String, String)> {
    let rest = l.strip_prefix("Review: ready (reviewer ")?;
    let close = rest.find([' ', ')']).filter(|&c| c > 0)?;
    let tail = rest[close..].strip_prefix(") @")?;
    tail.bytes().next().filter(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(c))?;
    Some((field(l, 3).trim_end_matches_once(')').to_string(), after_at(field(l, 4)).to_string()))
}

/// The number in the first `(max <n> min)` of a line, 0 when none.
fn jobs_max(l: &str) -> u64 {
    let mut s = l;
    while let Some(i) = s.find("(max ") {
        let rest = &s[i + 5..];
        let digits: String = rest.chars().take_while(char::is_ascii_digit).collect();
        if !digits.is_empty() && rest[digits.len()..].starts_with(" min)") {
            return digits.parse().unwrap_or(0);
        }
        s = &s[i + 1..];
    }
    0
}

/// A fence line: spaces, then three backticks.
fn fence_line(raw: &[u8]) -> bool {
    raw.iter().skip_while(|&&b| b == b' ').take(3).eq(b"```".iter())
}

/// A table row: spaces, then `|`.
fn table_line(raw: &[u8]) -> bool {
    raw.iter().find(|&&b| b != b' ') == Some(&b'|')
}

/// Characters of a line: bytes minus UTF-8 continuation bytes.
fn chars(raw: &[u8]) -> usize {
    raw.iter().filter(|&&b| !(0x80..0xc0).contains(&b)).count()
}

trait TrimOnce {
    fn trim_end_matches_once(&self, c: char) -> &str;
}

impl TrimOnce for str {
    /// Removes one trailing `c` (awk's `sub(/\)$/, "")`).
    fn trim_end_matches_once(&self, c: char) -> &str {
        self.strip_suffix(c).unwrap_or(self)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_header_ticks_gates() {
        let r = RunFile::parse(
            "# Run: x\nStatus: open\nNext: 4 Before \u{b7} how-to-make-a-pr\nWaiting: jobs: x (max 9 min)\n\n## 0 Ticket \u{2714}\n## 2b Challenge \u{2714}\n## 3 Plan \u{2714}\nGate A: PASS (checker c1) @abcdef1\nCRITICAL: x\nReview: ready (reviewer r) @1234567\n"
                .as_bytes(),
        );
        assert!(r.wait_jobs && r.jobs_max == 9 && !r.wait_owner);
        assert_eq!(r.ticked, ["0", "2b", "3"]);
        assert_eq!(r.after_ticked, 4);
        assert_eq!(r.next, "4 Before \u{b7} how-to-make-a-pr");
        assert_eq!(r.gate[&'A'], ("c1".into(), "abcdef1".into()));
        assert!(r.critical.contains("3"));
        assert_eq!(r.review, Some(("r".into(), "1234567".into())));
    }
}
