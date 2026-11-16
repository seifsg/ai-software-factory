//! Line scanners for host transcripts, as small state machines so a scan can stop at a byte offset and
//! resume there next call. Subagent files: the brief's role on line 1, then each own handback's verdict.
//! Session transcripts: whether lines carry `isSidechain` (Claude Code) and which step blocks reached chat.

use memchr::memmem;

/// Folded facts of one subagent transcript (`<session>/subagents/agent-<id>.jsonl`).
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Sub {
    /// At least one line was read (an empty file takes no part in the round count).
    pub nonempty: bool,
    /// `A`, `B`, `C` from `Role: checker. Gate X`, `R` from `Role: reviewer`; None: not a gate delegate.
    pub role: Option<char>,
    /// The last verdict of its own handbacks.
    pub last: Option<String>,
    /// Reviewer: a `verdict: ready` was seen; rounds count from the last one.
    pub r_reset: bool,
    /// Reviewer: failed verdicts after the last ready one (or all, with no ready one).
    pub r_count: i64,
    /// Reviewer: whether its last verdict line named a `CRITICAL:` finding.
    pub r_critical: Option<bool>,
}

impl Sub {
    /// Feeds one line (no newline).
    pub fn line(&mut self, l: &[u8]) {
        if !self.nonempty {
            self.nonempty = true;
            self.role = role(l);
            return;
        }
        let Some(role) = self.role else { return };
        if memmem::find(l, br#""role":"assistant""#).is_none() || memmem::find(l, b"api-request-blob").is_some() {
            return;
        }
        if role == 'R' {
            if let Some(v) = last_verdict(l) {
                let ready = v == "verdict: ready" || v.starts_with("verdict: ready @");
                if ready {
                    self.r_reset = true;
                    self.r_count = 0;
                } else {
                    self.r_count += 1;
                }
                self.r_critical = Some(memmem::find(l, b"CRITICAL:").is_some());
                self.last = Some(v);
            }
        } else if let Some(v) = last_gate(l, role) {
            self.last = Some(v);
        }
    }
}

/// The role a delegate's brief (first line) names.
fn role(l: &[u8]) -> Option<char> {
    let mut at = 0;
    while let Some(i) = memmem::find(&l[at..], b"Role: checker. Gate ") {
        let p = at + i + 20;
        if let Some(&g) = l.get(p).filter(|g| matches!(g, b'A' | b'B' | b'C')) {
            return Some(g as char);
        }
        at = at + i + 1;
    }
    memmem::find(l, b"Role: reviewer").map(|_| 'R')
}

/// Last non-overlapping `verdict: (not ready|ready after fixes|ready)( @<hex>)?` of a line.
fn last_verdict(l: &[u8]) -> Option<String> {
    let mut last = None;
    let mut at = 0;
    while let Some(i) = memmem::find(&l[at..], b"verdict: ") {
        let start = at + i;
        let after = &l[start + 9..];
        let word: &[u8] = if after.starts_with(b"not ready") {
            b"not ready"
        } else if after.starts_with(b"ready after fixes") {
            b"ready after fixes"
        } else if after.starts_with(b"ready") {
            b"ready"
        } else {
            at = start + 1;
            continue;
        };
        let mut end = start + 9 + word.len();
        if l[end..].starts_with(b" @") {
            let hex = l[end + 2..].iter().take_while(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(b)).count();
            if hex > 0 {
                end += 2 + hex;
            }
        }
        last = Some(String::from_utf8_lossy(&l[start..end]).into_owned());
        at = end;
    }
    last
}

/// Last non-overlapping `Gate X: (PASS|FAIL)<up to a quote or backslash>` of a line.
fn last_gate(l: &[u8], g: char) -> Option<String> {
    let pat = format!("Gate {g}: ");
    let mut last = None;
    let mut at = 0;
    while let Some(i) = memmem::find(&l[at..], pat.as_bytes()) {
        let start = at + i;
        let word = start + pat.len();
        if l[word..].starts_with(b"PASS") || l[word..].starts_with(b"FAIL") {
            let end = word + 4 + l[word + 4..].iter().take_while(|&&b| b != b'"' && b != b'\\').count();
            last = Some(String::from_utf8_lossy(&l[start..end]).into_owned());
            at = end;
        } else {
            at = start + 1;
        }
    }
    last
}

/// Folded facts of one session transcript.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Session {
    /// A line carried `"isSidechain"`: a Claude Code transcript.
    pub sidechain: bool,
    /// Step labels whose block opened an assistant text message (`0`..`8`, `2b`).
    pub sent: Vec<String>,
}

impl Session {
    pub fn line(&mut self, l: &[u8]) {
        if memmem::find(l, br#""isSidechain""#).is_some() {
            self.sidechain = true;
        }
        if memmem::find(l, br#""role":"assistant""#).is_none() {
            return;
        }
        const P: &[u8] = b"\"type\":\"text\",\"text\":\"## ";
        let mut at = 0;
        while let Some(i) = memmem::find(&l[at..], P) {
            let s = at + i + P.len();
            at = s;
            if !l.get(s).is_some_and(|d| (b'0'..=b'8').contains(d)) {
                continue;
            }
            // `[0-8]b? `: the longer `<d>b ` wins, as the awk regex matches.
            let len = match (l.get(s + 1), l.get(s + 2)) {
                (Some(b'b'), Some(b' ')) => 2,
                (Some(b' '), _) => 1,
                _ => continue,
            };
            let label = String::from_utf8_lossy(&l[s..s + len]).into_owned();
            if !self.sent.contains(&label) {
                self.sent.push(label);
            }
            at = s + len + 1;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn verdicts_take_the_last_longest_match() {
        assert_eq!(last_verdict(b"verdict: ready after fixes x verdict: not ready @ab12").as_deref(), Some("verdict: not ready @ab12"));
        assert_eq!(last_verdict(b"verdict: ready @zz").as_deref(), Some("verdict: ready"));
        assert_eq!(last_gate(br#"Gate A: FAIL 2 x\nGate A: PASS @abc""#, 'A').as_deref(), Some("Gate A: PASS @abc"));
    }

    #[test]
    fn sessions_collect_posted_headings() {
        let mut s = Session::default();
        s.line(br###"{"isSidechain":false,"message":{"role":"assistant","content":[{"type":"text","text":"## 2b Challenge x"},{"type":"text","text":"## 3 Plan"}]}}"###);
        assert!(s.sidechain);
        assert_eq!(s.sent, ["2b", "3"]);
    }

    #[test]
    fn roles_from_the_brief() {
        let mut s = Sub::default();
        s.line(br#"{"message":"Role: checker. Gate B. Project"}"#);
        assert_eq!(s.role, Some('B'));
    }
}
