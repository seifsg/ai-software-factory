//! One guard call, in the sh guard's order: find the run, load and check state, read evidence and Git,
//! judge, then the replies in their fixed priority. Each early return mirrors one `exit 0` of the sh guard.

use super::reply;
use super::rules::{self, Facts, Inputs};
use crate::evidence;
use crate::git::{Info, Repo};
use crate::hook::{Input, Reply};
use crate::paths;
use crate::run::RunFile;
use crate::run::locate;
use crate::run::state::{Loaded, State};
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    Stop,
    Compact,
    Clear,
    /// `guard step`: an inline save which never reads or writes the loop guard's nudge.
    Step { changed: bool },
}

impl Mode {
    /// Stop and step both end a step: they record ticks and the session in the state.
    fn turn_end(self) -> bool {
        matches!(self, Mode::Stop | Mode::Step { .. })
    }
}

/// Runs the guard for one event. `start` is where the walk begins when the input names no usable cwd.
pub fn run(input: &Input, mode: Mode, start: &Path) -> Option<Reply> {
    let start = match mode {
        Mode::Clear => start.to_path_buf(),
        _ => Some(PathBuf::from(paths::norm(&input.cwd)))
            .filter(|p| !input.cwd.is_empty() && p.is_dir())
            .unwrap_or_else(|| start.to_path_buf()),
    };
    let found = locate::find(&start, &input.session_id, &input.last_assistant_message);
    let Some(d) = found.dir else {
        if !mode.turn_end() || !found.step_block {
            return None;
        }
        return Some(if input.stop_hook_active { Reply::System(reply::NO_RUN_ACTIVE.into()) } else { Reply::Block(reply::NO_RUN.into()) });
    };
    let dir = PathBuf::from(&d);
    let run = dir.join(".factory/run.md");
    let g = dir.join(".factory/guard");
    let st = g.join("state");
    let rf = format!("{d}/.factory/run.md");
    if mode.turn_end() && paths::age_secs(&run).is_some_and(|a| a > 720 * 60) {
        return None;
    }
    let sid = input.session_id.as_str();
    let tp = paths::norm(&input.transcript_path).replace('\'', "");
    let now = paths::now() as i64;
    let mut note = String::new();
    let new_state = !st.is_file();
    let mut s = match State::load(&st) {
        Loaded::Valid(s) => s,
        Loaded::Missing => State::default(),
        Loaded::Edited => {
            note = "guard state was edited outside the guard".into();
            State::default()
        }
    };
    let legacy = PathBuf::from(format!("{rf}.ticks"));
    if legacy.is_file() {
        let t = std::fs::read_to_string(&legacy).unwrap_or_default();
        s.set("ticks", t.trim_end_matches('\n'));
        let _ = std::fs::remove_file(&legacy);
        let _ = std::fs::remove_file(format!("{rf}.nudge"));
    }
    if !sid.is_empty() && sid.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-') {
        let list = s.get("sessions").to_string();
        if !list.split(' ').any(|q| q == sid) {
            s.set("sessions", if list.is_empty() { sid.to_string() } else { format!("{list} {sid}") });
        }
    }
    if mode == Mode::Clear {
        return Some(clear(&mut s, &st, &run));
    }
    let text = std::fs::read(&run).unwrap_or_default();
    let rfile = RunFile::parse(&text);
    let sessions: Vec<String> = s.get("sessions").split(' ').filter(|q| !q.is_empty()).map(String::from).collect();
    let ev = evidence::collect(&tp, &sessions, &rfile.wanted_ids(), &g);
    let posted = locate::posted_label(&input.last_assistant_message);
    let repo = Repo::discover(&dir);
    let Info { head, mut up, remote } = repo.as_ref().map(Repo::info).unwrap_or_default();
    let marker = g.join("remote");
    if !up.is_empty() || remote {
        if !marker.is_file() && g.is_dir() {
            let _ = std::fs::write(&marker, b"");
        }
    } else if !marker.is_file() {
        up.clone_from(&head);
    }
    let night = s.num("night_until", 0) > 0;
    let receipt = |x: char, commit: &str| crate::receipt::standing(repo.as_ref(), commit, x);
    let base = ["base_A", "base_B", "base_C", "base_R"].map(|k| s.num(k, 0));
    let f = rules::judge(&Inputs {
        run: &rfile,
        ev: &ev,
        head: &head,
        up: &up,
        night,
        clear: s.get("clear") == "1",
        new_state,
        prev_ticks: s.num("ticks", 0),
        base,
        posted: &posted,
        receipt: &receipt,
    });
    // Only a posted step 5 block or todo line reads the Before files (and Git, when one exists).
    let before = (mode == Mode::Stop && super::before::posted(&input.last_assistant_message))
        .then(|| super::before::refusal(&dir, &String::from_utf8_lossy(&text), repo.as_ref(), &head))
        .flatten();
    // Full-suite receipts that count a repeat run on their tree, as `tree: n runs` (short trees).
    let repeat = repo
        .as_ref()
        .map(|r| crate::receipt::repeats(&r.work))
        .unwrap_or_default()
        .iter()
        .map(|(t, n)| format!("{}: {n} runs", &t[..t.len().min(8)]))
        .collect::<Vec<_>>()
        .join(", ");
    Ctx { mode, input, s, f, d, run, g, st, rf, note, new_state, now, text, sid: sid.to_string(), tp, before, repeat }.after_judge()
}

/// Clear: the owner's command after a halt; also ends night mode. Keeps the run's sessions for gate proof.
fn clear(s: &mut State, st: &Path, run: &Path) -> Reply {
    if s.get("sessions").is_empty() {
        let raw = std::fs::read_to_string(st).unwrap_or_default();
        let recovered = raw.lines().find_map(|l| {
            l.strip_prefix("g_sessions='")?
                .strip_suffix('\'')
                .filter(|v| v.bytes().all(|b| b.is_ascii_alphanumeric() || b" _-".contains(&b)))
        });
        s.set("sessions", recovered.unwrap_or(""));
    }
    for (k, v) in [("halt", ""), ("end", ""), ("idle", "0"), ("clear", "1"), ("night_until", "0")] {
        s.set(k, v);
    }
    s.save(st);
    let text = std::fs::read(run).unwrap_or_default();
    let body = text.strip_suffix(b"\n").unwrap_or(&text);
    let kept: Vec<&[u8]> =
        if text.is_empty() { Vec::new() } else { body.split(|&b| b == b'\n').filter(|l| !l.starts_with(b"Night:")).collect() };
    let out = with_newlines(&kept);
    let tmp = run.with_extension("md.n");
    if std::fs::write(&tmp, &out).is_ok() && !kept.is_empty() {
        let _ = std::fs::rename(&tmp, run);
    }
    Reply::Text(reply::CLEARED.into())
}

struct Ctx<'a> {
    mode: Mode,
    input: &'a Input,
    s: State,
    f: Facts,
    d: String,
    run: PathBuf,
    g: PathBuf,
    st: PathBuf,
    rf: String,
    note: String,
    new_state: bool,
    now: i64,
    text: Vec<u8>,
    sid: String,
    tp: String,
    /// Why this turn's step 5 block or todo line is refused (a Before missing or late).
    before: Option<String>,
    /// Trees the full suite ran on more than once; flagged once per new repeat.
    repeat: String,
}

impl Ctx<'_> {
    fn save(&self) {
        self.s.save(&self.st);
    }

    fn read_marker(&self, name: &str) -> String {
        std::fs::read_to_string(self.g.join(name)).unwrap_or_default()
    }

    fn has_line(&self, prefix: &[u8]) -> bool {
        self.text.split(|&b| b == b'\n').any(|l| l.starts_with(prefix))
    }

    fn after_judge(mut self) -> Option<Reply> {
        let ticks = self.f.ticks;
        let g_ticks = self.s.get("ticks").to_string();
        if ticks <= 1 && (self.new_state || g_ticks.parse::<i64>().unwrap_or(0) > ticks) {
            self.s.set("clear", "1");
        }
        if !(self.st.is_file() || !self.g.is_dir() || ticks <= 1 || !g_ticks.is_empty()) {
            self.note = "guard state was lost".into();
        }
        if !self.note.is_empty() {
            self.s.set("halt", self.note.clone());
        }
        let prev =
            if g_ticks.is_empty() || !g_ticks.bytes().all(|b| b.is_ascii_digit()) { ticks } else { g_ticks.parse().unwrap_or(ticks) };
        if self.s.get("end") == "done" {
            let still = self.has_line(b"Status: closed") && (self.has_line(b"Gate C: PASS") || self.has_line(b"Gate C: WAIVED"));
            // A finish the guard saw holds while the run says closed, wherever HEAD went since.
            if still {
                self.f.finished = true;
            } else {
                self.s.set("end", "");
            }
        }
        if self.f.finished {
            self.s.set("end", "done");
        }
        if self.mode.turn_end() {
            if self.s.get("session") != self.sid {
                self.s.set("sstep", self.f.step.to_string());
            }
            if !self.s.get("relay").is_empty() && self.s.get("relay") != self.sid {
                self.s.set("relay", "");
            }
            self.s.set("ticks", ticks.to_string());
            self.s.set("seen", self.now.to_string());
            self.s.set("session", self.sid.clone());
            self.s.set("transcript", self.tp.clone());
        }
        let unp = self.f.unposted.clone();
        if self.mode.turn_end()
            && !unp.is_empty()
            && !self.f.stopped
            && self.s.get("halt").is_empty()
            && unp != self.read_marker("unposted")
        {
            // The step the run moved to still starts now: the report keeps its work apart.
            if self.f.skipped.is_empty() {
                super::timeline::mark(&self.g, &self.f.next, self.f.gate, self.now as u64);
            }
            self.save();
            let _ = std::fs::write(self.g.join("unposted"), &unp);
            return Some(Reply::Block(reply::unposted(&self.rf, &unp)));
        }
        if self.f.stopped || self.f.finished {
            if let Some(link) = locate::session_file(&self.input.session_id) {
                let _ = std::fs::remove_file(link);
            }
            if self.mode.turn_end() {
                self.save();
            }
            return None;
        }
        let halt = self.s.get("halt").to_string();
        if !halt.is_empty() {
            if self.mode == Mode::Compact {
                return Some(Reply::Text(reply::halted_compact(&halt)));
            }
            self.save();
            return Some(Reply::System(reply::halted_notice(&halt, &self.rf, &format!("{} {}", super::clear_cmd(), self.d))));
        }
        if self.mode == Mode::Compact {
            return Some(self.compact());
        }
        if !self.s.get("relay").is_empty() {
            self.save();
            return Some(Reply::System(reply::relayed(&self.d)));
        }
        self.drive(prev)
    }

    fn compact(&mut self) -> Reply {
        let mut out = String::new();
        if self.input.source == "compact" {
            let n = if self.s.get("csession") == self.sid { self.s.num("compacts", 0) + 1 } else { 1 };
            self.s.set("compacts", n.to_string());
            self.s.set("csession", self.sid.clone());
            self.save();
        }
        if self.input.source == "resume" {
            out.push_str(reply::RESUMED);
        }
        let next = match self.f.gate {
            Some('R') => "8 Review: a proven reviewer verdict on HEAD".to_string(),
            Some(x) => format!("Gate {x} checker"),
            None if self.f.next.is_empty() => "see the run file".into(),
            None => self.f.next.clone(),
        };
        out.push_str(&reply::open(&self.rf, &next));
        let n = self.s.num("compacts", 0);
        if n >= 2 && self.s.get("csession") == self.sid {
            out.push_str(&reply::relay_due(n));
        }
        Reply::Text(out)
    }

    /// The Stop hook's drive: deadlines, real waits, the loop guard, halts, relays, then the next prompt.
    fn drive(&mut self, prev: i64) -> Option<Reply> {
        let f = self.f.clone();
        let batched = f.ticks - prev > 1;
        if self.s.get("clear") == "1" {
            for (k, x) in ["base_A", "base_B", "base_C", "base_R"].iter().zip(f.rounds) {
                self.s.set(k, x.to_string());
            }
            self.s.set("clear", "");
        }
        let (mut lp, mut rounds) = (None, 0i64);
        for (k, (x, _)) in rules::LOOPS.iter().enumerate() {
            let n = f.rounds[k] - self.s.num(["base_A", "base_B", "base_C", "base_R"][k], 0);
            if n > rounds {
                rounds = n;
                lp = Some(*x);
            }
        }
        let mut todo = String::new();
        if f.jobs {
            let jobs: Vec<&[u8]> = self.text.split(|&b| b == b'\n').filter(|l| l.starts_with(b"Waiting: jobs:")).collect();
            let jobs_lines = with_newlines(&jobs);
            let k = super::cksum(&jobs_lines).to_string();
            if self.s.get("jobs_since").is_empty() || self.s.get("jobs_id") != k {
                self.s.set("jobs_since", self.now.to_string());
                self.s.set("jobs_id", k);
            }
            let mut jmax = f.jobs_max as i64;
            if let Some(cap) = env_num("FACTORY_JOB_MAX", 120) {
                jmax = jmax.min(cap);
            }
            if jmax == 0 {
                todo = reply::jobs_deadline();
            } else if self.now - self.s.num("jobs_since", 0) > jmax * 60 {
                todo = reply::jobs_late(jmax, &self.rf);
            }
        } else {
            self.s.set("jobs_since", "");
            self.s.set("jobs_id", "");
        }
        if todo.is_empty() {
            todo = self.before.clone().unwrap_or_default();
        }
        if todo.is_empty() && !self.repeat.is_empty() && self.repeat != self.read_marker("repeat") {
            let _ = std::fs::create_dir_all(&self.g).and_then(|()| std::fs::write(self.g.join("repeat"), &self.repeat));
            todo = reply::repeat(&self.repeat);
        }
        self.save();
        if !todo.is_empty() {
            self.idle();
            if let Some(r) = self.halt(lp, rounds) {
                return Some(r);
            }
            self.save();
            return Some(Reply::Block(reply::for_run(&self.rf, &todo)));
        }
        if !f.driven {
            if f.skipped.is_empty() || f.skipped == self.read_marker("skipwait") {
                return None;
            }
            let _ = std::fs::write(self.g.join("skipwait"), &f.skipped);
            return Some(Reply::Block(reply::wait_skipped(&self.rf, &f.skipped)));
        }
        if self.input.subagent_running {
            return None;
        }
        let nudge = self.g.join("nudge");
        if self.mode == Mode::Stop {
            if self.input.stop_hook_active && nudge.is_file() && paths::mtime_ns(&self.run) <= paths::mtime_ns(&nudge) {
                return Some(Reply::System(reply::idle_stop(&self.rf)));
            }
            paths::touch(&nudge);
        }
        self.idle();
        if let Some(r) = self.halt(lp, rounds) {
            return Some(r);
        }
        let step = f.step as i64;
        let mut why = String::new();
        let compacts = self.s.num("compacts", 0);
        if compacts >= 2 && self.s.get("csession") == self.sid {
            why = format!("compacted {compacts} times");
        }
        if self.night() && matches!(step, 4 | 6 | 8) && self.s.num("sstep", step) < step && self.s.get("rstep") != step.to_string() {
            why = format!("night phase boundary before step {step}");
        }
        if !why.is_empty() {
            self.s.set("relay", self.sid.clone());
            self.s.set("rstep", step.to_string());
            self.save();
            return Some(Reply::Block(reply::relay(&why, &self.rf, &self.d)));
        }
        if f.skipped.is_empty() {
            super::timeline::mark(&self.g, &f.next, f.gate, self.now as u64);
        }
        self.save();
        Some(Reply::Block(reply::drive(&self.rf, &self.prompt(batched, lp, rounds), &self.note)))
    }

    fn night(&self) -> bool {
        self.s.num("night_until", 0) > 0
    }

    /// Saved corrections inside a step preserve the idle budget. A new tick or proven gate resets it.
    fn idle(&mut self) {
        let sig = self.f.sig.to_string();
        let valid_save = matches!(self.mode, Mode::Step { changed: true }) && self.f.skipped.is_empty() && self.f.long_lines.is_empty();
        let n = if sig == self.s.get("sig") { self.s.num("idle", 0) + i64::from(!valid_save) } else { 0 };
        self.s.set("idle", n.to_string());
        self.s.set("sig", sig);
    }

    /// Halts past round 5, after too many idle turns, or past the night budget.
    fn halt(&mut self, lp: Option<char>, rounds: i64) -> Option<Reply> {
        let name = match lp {
            Some('R') => "review".to_string(),
            Some(x) => format!("Gate {x}"),
            None => "Gate ".to_string(),
        };
        let reason = if self.night() && self.now > self.s.num("night_until", 0) {
            "night time budget spent".to_string()
        } else if rounds >= 5 {
            format!("{name}: {rounds} failed rounds")
        } else if env_num("FACTORY_IDLE_TURNS", 6).is_some_and(|max| self.s.num("idle", 0) >= max) {
            format!("no progress in {} turns", self.s.get("idle"))
        } else {
            return None;
        };
        self.s.set("halt", reason.clone());
        self.s.set("end", "halt");
        self.save();
        Some(Reply::Block(reply::halt_block(&reason, &format!("{} {}", super::clear_cmd(), self.d))))
    }

    /// The prompt in priority order: batched, skipped, long lines, a capped loop, an open gate, the next step.
    fn prompt(&self, batched: bool, lp: Option<char>, rounds: i64) -> String {
        let f = &self.f;
        if batched {
            return reply::batched();
        }
        // `guard step` answers in the same turn: every open problem at once, each long line with its start, so one
        // edit fixes them all (the Stop hook keeps its one-at-a-time order, byte for byte with the sh guard).
        let step_mode = matches!(self.mode, Mode::Step { .. });
        let mut all = Vec::new();
        if !f.skipped.is_empty() {
            all.push(reply::skipped(&f.skipped));
        }
        if !f.long_lines.is_empty() {
            all.push(reply::long(&if step_mode { self.long_with_starts(&f.long_lines) } else { f.long_lines.clone() }));
        }
        // Stop keeps one problem per reply, byte for byte with the sh guard; `guard step` answers in the same turn
        // with every open problem at once, the loop item first by the same order (cap, receipt, then the gate).
        if !all.is_empty() && !step_mode {
            return all.swap_remove(0);
        }
        if let Some(x) = lp.filter(|x| rounds >= 3 && !f.critical.contains(*x)) {
            all.push(reply::cap(x, rounds));
        } else if let Some((x, standing)) = f.no_receipt {
            all.push(reply::receipt(x, standing, &super::exe()));
        } else {
            match f.gate {
                Some('R') => all.push(reply::review()),
                Some(x) => all.push(reply::gate(x)),
                None => {}
            }
        }
        if !all.is_empty() {
            return all.join(" ");
        }
        let step = f.next.split(' ').next().unwrap_or("");
        let closed = self.has_line(b"Status: closed");
        let mut todo = reply::next_step(step, &f.next, closed);
        if step != "5" && !(step.is_empty() && closed) {
            todo.push_str(&reply::one_step(&self.run_path()));
        }
        todo
    }

    /// `69,122` as `69 (`**Table:** | Option…`), 122 (…)`: the line numbers with each line's first 60 characters.
    fn long_with_starts(&self, nums: &str) -> String {
        let text = String::from_utf8_lossy(&self.text);
        let lines: Vec<&str> = text.lines().collect();
        nums.split(',')
            .map(|n| {
                // A backtick in the line's start would close the code span early.
                let start = n.trim().parse::<usize>().ok().and_then(|i| lines.get(i.wrapping_sub(1))).map(|l| l.chars().take(60).map(|c| if c == '`' { '\'' } else { c }).collect::<String>());
                start.map_or(n.to_string(), |s| format!("{n} (`{s}…`)"))
            })
            .collect::<Vec<_>>()
            .join(", ")
    }

    fn run_path(&self) -> String {
        paths::text(&self.run)
    }
}

/// A numeric environment setting; unset uses the default, a non-number disables the rule (as `[ -gt ]` fails).
fn env_num(name: &str, default: i64) -> Option<i64> {
    match std::env::var(name) {
        Ok(v) if !v.is_empty() => v.parse().ok(),
        _ => Some(default),
    }
}

/// Lines joined as `grep` prints them: each one ends in a newline.
fn with_newlines(lines: &[&[u8]]) -> Vec<u8> {
    lines.iter().flat_map(|l| l.iter().copied().chain(*b"\n")).collect()
}
