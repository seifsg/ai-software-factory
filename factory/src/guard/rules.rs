//! The guard's verdict on a run: which gate is unproven, which steps are skipped, which blocks never
//! reached chat, how many rounds each loop failed. Pure: run-file facts and evidence in, facts out.

use crate::evidence::Evidence;
use crate::receipt::Standing;
use crate::run::{RunFile, after_at, push_list};

/// Loops in round order, with the step whose `CRITICAL:` lines open rounds 4 and 5.
pub const LOOPS: [(char, &str); 4] = [('A', "3"), ('B', "6"), ('C', "8"), ('R', "8")];

/// What the guard reads around the run file.
pub struct Inputs<'a> {
    pub run: &'a RunFile,
    pub ev: &'a Evidence,
    pub head: &'a str,
    pub up: &'a str,
    pub night: bool,
    /// The owner cleared the run: loop caps count from here.
    pub clear: bool,
    /// No state file yet.
    pub new_state: bool,
    /// Ticks the guard saw last time.
    pub prev_ticks: i64,
    /// Failed rounds per loop at the last clear.
    pub base: [i64; 4],
    /// The step label of the heading posted this turn.
    pub posted: &'a str,
    /// Where a Gate C or review commit stands on suite receipts (`receipt::standing`).
    pub receipt: &'a dyn Fn(char, &str) -> Standing,
}

/// The guard's facts about the run.
#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct Facts {
    pub stopped: bool,
    /// No real wait: `Waiting:` is neither owner nor jobs.
    pub driven: bool,
    pub finished: bool,
    pub ticks: i64,
    /// First unproven gate (`A`, `B`, `C`, or `R` for the review), else None.
    pub gate: Option<char>,
    /// Progress signature: tick lines plus proven gates.
    pub sig: i64,
    pub jobs: bool,
    pub jobs_max: u64,
    /// Loops with an open CRITICAL, as letters.
    pub critical: String,
    /// Failed rounds per loop (A, B, C, R), 0 for a converged loop.
    pub rounds: [i64; 4],
    /// Ticked steps whose block never reached chat (Claude Code transcripts only).
    pub unposted: String,
    /// Steps not ticked that should be.
    pub skipped: String,
    pub long_lines: String,
    pub step: u32,
    pub next: String,
    /// Gate C or the review lacks only its suite receipt, or (Gate C) one that counts a single run.
    pub no_receipt: Option<(char, Standing)>,
}

/// First `min(len)` characters agree, at least 7 (a short sha against a full one).
pub fn pre(a: &str, b: &str) -> bool {
    let n = a.len().min(b.len());
    n >= 7 && a.as_bytes()[..n] == b.as_bytes()[..n]
}

fn idx(x: char) -> usize {
    LOOPS.iter().position(|(c, _)| *c == x).unwrap_or(0)
}

struct Judge<'a> {
    i: &'a Inputs<'a>,
    base: [i64; 4],
    f: [i64; 4],
}

impl Judge<'_> {
    fn proven(&self, id: &str, k: char, sha: &str) -> bool {
        let ev = self.i.ev;
        if ev.none {
            return true;
        }
        if ev.fallback {
            return ev.seen.contains(id) && !ev.claude_fallback;
        }
        ev.kind.get(id) == Some(&k) && pre(sha, after_at(ev.last.get(id).map_or("", String::as_str)))
    }

    /// An open CRITICAL in the loop's own step, or in the last review.
    fn open(&self, x: char) -> bool {
        self.i.run.critical.contains(LOOPS[idx(x)].1) || (x == 'R' && self.i.ev.review_critical)
    }

    /// A cap line ends the loop: 3 failed rounds, no open CRITICAL; C and R on the pushed HEAD.
    fn capped(&self, x: char) -> bool {
        let Some(sha) = self.i.run.cap.get(&x) else { return false };
        let ev = self.i.ev;
        !self.open(x)
            && (ev.none || (ev.fallback && !ev.claude_fallback) || self.f[idx(x)] - self.base[idx(x)] >= 3)
            && (matches!(x, 'A' | 'B') || (pre(sha, self.i.head) && self.i.head == self.i.up))
    }

    /// The gate line is proven (checker, cap or waiver), receipts aside.
    fn proven_gate(&self, x: char) -> bool {
        if self.capped(x) {
            return true;
        }
        let Some((id, sha)) = self.i.run.gate.get(&x) else {
            return self.i.run.waived.contains(&x) && !self.i.night;
        };
        let ev = self.i.ev;
        self.proven(id, x, sha)
            && (ev.none
                || ev.fallback
                || ev.last.get(id).is_some_and(|l| l.starts_with("Gate ") && l.get(6..).is_some_and(|s| s.starts_with(": PASS"))))
            && (x != 'C' || (pre(sha, self.i.head) && self.i.head == self.i.up))
    }

    /// The commit a proven Gate C or review line stands on; None for a waiver (it needs no receipt).
    fn gate_commit(&self, x: char) -> Option<&str> {
        if self.capped(x) {
            return self.i.run.cap.get(&x).map(String::as_str);
        }
        match x {
            'R' => self.i.run.review.as_ref().map(|(_, sha)| sha.as_str()),
            _ => self.i.run.gate.get(&x).map(|(_, sha)| sha.as_str()),
        }
    }

    fn ok(&self, x: char) -> bool {
        self.proven_gate(x) && self.standing(x) == Standing::Ok
    }

    /// Gate C and the review judge a head: each stands only on a full-suite receipt for its commit's tree
    /// (Gate C on one that counts a single run). Gate A judges a plan and needs none.
    fn standing(&self, x: char) -> Standing {
        match self.gate_commit(x) {
            Some(c) if crate::receipt::required_at(x) => (self.i.receipt)(x, c),
            _ => Standing::Ok,
        }
    }

    fn review_ok(&self) -> bool {
        self.review_proven() && self.standing('R') == Standing::Ok
    }

    /// The review line is proven (reviewer handback or cap), receipts aside.
    fn review_proven(&self) -> bool {
        if self.capped('R') {
            return true;
        }
        let Some((id, sha)) = &self.i.run.review else { return false };
        let ev = self.i.ev;
        pre(sha, self.i.head)
            && self.i.head == self.i.up
            && self.proven(id, 'R', sha)
            && (ev.none || ev.fallback || ev.last.get(id).is_some_and(|l| l == "verdict: ready" || l.starts_with("verdict: ready @")))
    }
}

/// Judges a run.
pub fn judge(i: &Inputs) -> Facts {
    let run = i.run;
    let c = run.ticked.len() as i64;
    let mut j = Judge { i, base: i.base, f: i.ev.rounds };
    if i.clear || (c <= 1 && (i.new_state || i.prev_ticks > c)) {
        j.base = j.f;
    }
    let mut step = run.next.bytes().next().map_or(0, |b| (b - b'0') as u32);
    step = step.max(run.after_ticked);
    let rok = j.review_ok();
    let r = run.review_ticked;
    let mut no_receipt = None;
    let gate = if (step > 3 || r) && !j.ok('A') {
        Some('A')
    } else if (step > 6 || r) && !j.ok('B') {
        Some('B')
    } else if r && !j.ok('C') {
        Some('C')
    } else if r && !rok {
        Some('R')
    } else {
        None
    };
    let proven = |g: char| if g == 'R' { j.review_proven() } else { j.proven_gate(g) };
    if let Some(g) = gate.filter(|g| crate::receipt::required_at(*g) && proven(*g)) {
        no_receipt = Some((g, j.standing(g)));
    }
    let sig = run.tick_lines as i64 + ['A', 'B', 'C'].iter().filter(|&&x| j.ok(x)).count() as i64 + i64::from(rok);
    let critical: String = LOOPS.iter().filter(|(x, _)| j.open(*x)).map(|(x, _)| *x).collect();
    let mut rounds = j.f;
    for (k, (x, _)) in LOOPS.iter().enumerate() {
        if if *x == 'R' { rok } else { j.ok(*x) } {
            rounds[k] = 0;
        }
    }
    let mut skipped = String::new();
    if step > 3 || r {
        let need: &[&str] = if r { &["0", "1", "2", "2b", "3", "4", "5", "6", "7"] } else { &["0", "1", "2", "2b", "3"] };
        for s in need.iter().filter(|s| !run.done.contains(**s)) {
            push_list(&mut skipped, s);
        }
    }
    let mut unposted = String::new();
    if i.ev.claude {
        for t in run.ticked.iter().filter(|t| t.as_str() != i.posted && !i.ev.sent.contains(*t)) {
            push_list(&mut unposted, t);
        }
    }
    Facts {
        stopped: run.stopped,
        driven: !(run.wait_owner || run.wait_jobs),
        finished: r && gate.is_none() && skipped.is_empty() && run.long_lines.is_empty(),
        ticks: c,
        gate,
        sig,
        jobs: run.wait_jobs,
        jobs_max: run.jobs_max,
        critical,
        rounds,
        unposted,
        skipped,
        long_lines: run.long_lines.clone(),
        step,
        next: run.next.clone(),
        no_receipt,
    }
}
