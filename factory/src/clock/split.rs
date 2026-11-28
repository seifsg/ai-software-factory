//! Splits a run's wall time into phases, each second counted once, so the rows sum to the total.
//! Priority at any instant: waiting on you > waiting on queue > tests + CI > idle > the step's phase.

use super::phase::Phase;
use super::stamp::Row;

#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Split {
    pub start: u64,
    pub end: u64,
    pub secs: [u64; 8],
    pub lost: [u64; 8],
    /// The cause that lost the most time, per phase; empty when none was lost.
    pub why: [String; 8],
    pub full_runs: u32,
}

/// One timed claim on the run's clock: `[from, to)` in `phase`, with the cause its time is lost to.
struct Claim {
    from: u64,
    to: u64,
    phase: Phase,
    why: String,
}

/// The split; None before the run has a first stamp. `open_now` ends an open run now; a closed one ends at
/// its `end` row, else at its last stamp.
pub fn split(steps: &[(u64, String)], rows: &[Row], open_now: Option<u64>) -> Option<Split> {
    let start = steps.first().map(|s| s.0).or_else(|| rows.iter().find_map(first_time))?;
    let closed = rows.iter().find_map(|r| if let Row::End { at } = r { Some(*at) } else { None });
    let last = steps.iter().map(|s| s.0).chain(rows.iter().filter_map(last_time)).max().unwrap_or(start);
    let end = closed.or(open_now).unwrap_or(last).max(start);
    let claims = claims(steps, rows, end);
    let mut cuts: Vec<u64> =
        [start, end].into_iter().chain(steps.iter().map(|s| s.0)).chain(claims.iter().flat_map(|c| [c.from, c.to])).collect();
    cuts.retain(|t| (start..=end).contains(t));
    cuts.sort_unstable();
    cuts.dedup();
    let mut out = Split { start, end, ..Split::default() };
    let mut causes: Vec<(Phase, String, u64)> = Vec::new();
    for w in cuts.windows(2) {
        let (a, b) = (w[0], w[1]);
        let won = claims.iter().filter(|c| c.from <= a && a < c.to).min_by_key(|c| rank(c.phase));
        let phase = won.map_or_else(|| step_phase(steps, a), |c| c.phase);
        out.secs[phase as usize] += b - a;
        if let Some(c) = won.filter(|c| c.phase.all_lost()) {
            out.lost[phase as usize] += b - a;
            add(&mut causes, phase, &c.why, b - a);
        }
    }
    for r in rows {
        if let Row::Lost { phase, secs, why } = r {
            let room = out.secs[*phase as usize] - out.lost[*phase as usize];
            out.lost[*phase as usize] += (*secs).min(room);
            add(&mut causes, *phase, why, (*secs).min(room));
        }
    }
    for p in Phase::ALL {
        out.why[p as usize] = causes.iter().filter(|c| c.0 == p).max_by_key(|c| c.2).map(|c| c.1.clone()).unwrap_or_default();
    }
    out.full_runs = rows
        .iter()
        .filter(|r| matches!(r, Row::Span { from, phase: Phase::Tests, note, .. } if note == "full" && (start..=end).contains(from)))
        .count() as u32;
    Some(out)
}

/// Waits (until the next resume, wait, end or step start) and spans, as claims on the clock.
fn claims(steps: &[(u64, String)], rows: &[Row], end: u64) -> Vec<Claim> {
    let mut out = Vec::new();
    for (i, r) in rows.iter().enumerate() {
        match r {
            Row::Wait { at, owner, why } => {
                let later = rows[i + 1..].iter().filter_map(|r| match r {
                    Row::Wait { at: t, .. } | Row::Resume { at: t } | Row::End { at: t } => Some(*t),
                    _ => None,
                });
                let to = later.chain(steps.iter().map(|s| s.0).filter(|t| t > at)).filter(|t| t >= at).min().unwrap_or(end);
                let phase = if *owner { Phase::Owner } else { Phase::Idle };
                out.push(Claim { from: *at, to, phase, why: why.clone() });
            }
            Row::Span { from, to, phase, note } => {
                let why = if *phase == Phase::Queue { format!("queue {note}") } else { note.clone() };
                out.push(Claim { from: *from, to: *to, phase: *phase, why });
            }
            _ => {}
        }
    }
    out
}

fn rank(p: Phase) -> u8 {
    match p {
        Phase::Owner => 0,
        Phase::Queue => 1,
        Phase::Tests => 2,
        _ => 3,
    }
}

fn step_phase(steps: &[(u64, String)], t: u64) -> Phase {
    steps.iter().rev().find(|s| s.0 <= t).map_or(Phase::Plan, |s| Phase::of_step(&s.1))
}

fn add(causes: &mut Vec<(Phase, String, u64)>, p: Phase, why: &str, secs: u64) {
    match causes.iter_mut().find(|c| c.0 == p && c.1 == why) {
        Some(c) => c.2 += secs,
        None => causes.push((p, why.to_string(), secs)),
    }
}

fn first_time(r: &Row) -> Option<u64> {
    match r {
        Row::Wait { at, .. } | Row::Resume { at } | Row::End { at } => Some(*at),
        Row::Span { from, .. } => Some(*from),
        Row::Lost { .. } => None,
    }
}

fn last_time(r: &Row) -> Option<u64> {
    match r {
        Row::Span { to, .. } => Some(*to),
        other => first_time(other),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn s(at: u64, step: &str) -> (u64, String) {
        (at, step.to_string())
    }

    #[test]
    fn rows_sum_to_total_and_priority_holds() {
        let steps = [s(0, "0"), s(100, "5"), s(400, "6"), s(700, "7")];
        let rows = [
            Row::Wait { at: 10, owner: true, why: "plan OK?".into() },
            Row::Resume { at: 40 },
            // A suite runs while the session sits idle: tests win until it ends, idle (lost) after.
            Row::Span { from: 450, to: 500, phase: Phase::Tests, note: "full".into() },
            Row::Wait { at: 460, owner: false, why: "jobs: suite".into() },
            Row::Resume { at: 600 },
            Row::Span { from: 600, to: 620, phase: Phase::Queue, note: "heavy".into() },
            Row::Lost { phase: Phase::Build, secs: 50, why: "bad toolchain".into() },
            Row::End { at: 800 },
        ];
        let x = split(&steps, &rows, Some(9999)).unwrap();
        assert_eq!((x.start, x.end), (0, 800));
        assert_eq!(x.secs.iter().sum::<u64>(), 800);
        let at = |p: Phase| x.secs[p as usize];
        assert_eq!(
            [at(Phase::Owner), at(Phase::Plan), at(Phase::Build), at(Phase::Tests), at(Phase::Idle), at(Phase::Queue)],
            [30, 70, 300, 50, 100, 20]
        );
        assert_eq!([at(Phase::Review), at(Phase::Publish)], [130, 100]);
        assert_eq!((x.lost[Phase::Idle as usize], x.why[Phase::Idle as usize].as_str()), (100, "jobs: suite"));
        assert_eq!((x.lost[Phase::Queue as usize], x.why[Phase::Queue as usize].as_str()), (20, "queue heavy"));
        assert_eq!((x.lost[Phase::Build as usize], x.why[Phase::Build as usize].as_str()), (50, "bad toolchain"));
        assert_eq!(x.full_runs, 1);
    }

    #[test]
    fn open_waits_end_at_a_step_or_now_and_empty_runs_have_no_split() {
        let steps = [s(0, "0"), s(50, "1")];
        let rows = [Row::Wait { at: 20, owner: true, why: "q".into() }];
        let x = split(&steps, &rows, Some(70)).unwrap();
        assert_eq!((x.secs[Phase::Owner as usize], x.secs[Phase::Plan as usize], x.end), (30, 40, 70));
        let open = split(&[s(0, "0")], &[Row::Wait { at: 5, owner: false, why: "w".into() }], Some(65)).unwrap();
        assert_eq!(open.secs[Phase::Idle as usize], 60);
        assert!(split(&[], &[], Some(5)).is_none());
    }
}
