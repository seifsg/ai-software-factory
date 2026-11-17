//! Suite receipts: proof that a suite passed on an exact tree, read by the guard and the pro gate runner.
//!
//! File `<checkout>/.factory/receipts/<tree>-<suite>.txt`, LF, written through a temp file and a rename:
//! ```text
//! factory-receipt 1
//! suite <name>        `full` = the project's full suite
//! tree <sha>          work tree id: tracked + untracked, .factory/ out (`factory tree`)
//! head <sha>          HEAD when the suite started
//! clean yes|no        yes when tree equals HEAD's tree
//! result PASS|FAIL    exit 0 = PASS
//! cmd <command line>
//! runtime <stamp>     optional, writer-defined
//! secs <n>
//! at <UTC ISO 8601>
//! runs <n>            runs of this suite recorded on this tree; absent = 1
//! passes <n>          passing runs among them; absent = 1 for a PASS, 0 for a FAIL
//! ```
//! Readers ignore unknown lines. Gate C and review lines stand only on a `full` PASS receipt for their
//! commit's tree; Gate C only on one that counts a single passing run: the suite runs once per tree, and
//! the guard flags any rerun on a tree.

use crate::git::{Repo, tree};
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Receipt {
    pub suite: String,
    pub tree: String,
    pub head: String,
    pub clean: bool,
    pub pass: bool,
    pub cmd: String,
    pub runtime: String,
    pub secs: u64,
    pub at: String,
    /// Where the suite's output was saved, when the writer kept it (optional line).
    pub log: String,
    /// Runs of this suite recorded on this tree; 0 when the line is absent (read as 1).
    pub runs: u32,
    /// Passing runs among them; None when the line is absent (read from `result`).
    pub passes: Option<u32>,
}

/// Where a gate's commit stands on receipts.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Standing {
    Ok,
    /// No full-suite PASS receipt for the commit's tree.
    Missing,
    /// Gate C: the PASS receipt counts this many passing full runs on the tree, not one.
    Repeated(u32),
}

impl Receipt {
    /// Parses receipt text; None unless it starts with `factory-receipt 1`.
    pub fn parse(text: &str) -> Option<Receipt> {
        let mut lines = text.lines();
        (lines.next()? == "factory-receipt 1").then_some(())?;
        let mut r = Receipt::default();
        for l in lines {
            let (k, v) = l.split_once(' ').unwrap_or((l, ""));
            match k {
                "suite" => r.suite = v.into(),
                "tree" => r.tree = v.into(),
                "head" => r.head = v.into(),
                "clean" => r.clean = v == "yes",
                "result" => r.pass = v == "PASS",
                "cmd" => r.cmd = v.into(),
                "runtime" => r.runtime = v.into(),
                "secs" => r.secs = v.parse().unwrap_or(0),
                "at" => r.at = v.into(),
                "log" => r.log = v.into(),
                "runs" => r.runs = v.parse().unwrap_or(0),
                "passes" => r.passes = v.parse().ok(),
                _ => {}
            }
        }
        Some(r)
    }

    /// The receipt's text.
    pub fn render(&self) -> String {
        let one = |s: &str| s.replace(['\n', '\r'], " ");
        let log = if self.log.is_empty() { String::new() } else { format!("log {}\n", one(&self.log)) };
        format!(
            "factory-receipt 1\nsuite {}\ntree {}\nhead {}\nclean {}\nresult {}\ncmd {}\nruntime {}\nsecs {}\nat {}\nruns {}\npasses {}\n{log}",
            one(&self.suite),
            self.tree,
            self.head,
            if self.clean { "yes" } else { "no" },
            if self.pass { "PASS" } else { "FAIL" },
            one(&self.cmd),
            one(&self.runtime),
            self.secs,
            self.at,
            self.runs.max(1),
            self.pass_count()
        )
    }

    /// Full runs this receipt counts on its tree (an old receipt with no `runs` line counts one).
    pub fn run_count(&self) -> u32 {
        self.runs.max(1)
    }

    /// Passing full runs it counts (an old receipt with no `passes` line: 1 for a PASS, 0 for a FAIL).
    pub fn pass_count(&self) -> u32 {
        self.passes.unwrap_or(u32::from(self.pass))
    }
}

/// The receipts folder of a checkout.
pub fn dir(work: &Path) -> PathBuf {
    work.join(".factory/receipts")
}

/// The receipt file of a tree and suite.
fn path_of(work: &Path, tree: &str, suite: &str) -> PathBuf {
    let suite: String = suite.chars().map(|c| if c.is_ascii_alphanumeric() || c == '-' || c == '_' { c } else { '_' }).collect();
    dir(work).join(format!("{tree}-{suite}.txt"))
}

/// The receipt already written for a tree and suite, if any.
fn existing(work: &Path, tree: &str, suite: &str) -> Option<(PathBuf, Receipt)> {
    let p = path_of(work, tree, suite);
    let r = Receipt::parse(&std::fs::read_to_string(&p).ok()?)?;
    Some((p, r))
}

/// Writes a receipt for its tree and suite, counting this run after any earlier one on that tree; returns
/// its path.
pub fn write(work: &Path, r: &mut Receipt) -> std::io::Result<PathBuf> {
    let old = existing(work, &r.tree, &r.suite).map(|(_, o)| o);
    r.runs = old.as_ref().map_or(0, Receipt::run_count) + 1;
    r.passes = Some(old.as_ref().map_or(0, Receipt::pass_count) + u32::from(r.pass));
    std::fs::create_dir_all(dir(work))?;
    let p = path_of(work, &r.tree, &r.suite);
    crate::paths::write_atomic(&p, r.render().as_bytes())?;
    Ok(p)
}

/// Full-suite receipts that count more than one run on their tree: `(tree, runs)`, sorted.
pub fn repeats(work: &Path) -> Vec<(String, u32)> {
    let Ok(rd) = std::fs::read_dir(dir(work)) else { return Vec::new() };
    let mut out: Vec<(String, u32)> = rd
        .flatten()
        .filter(|e| e.file_name().to_string_lossy().ends_with("-full.txt"))
        .filter_map(|e| Receipt::parse(&std::fs::read_to_string(e.path()).ok()?))
        .filter(|r| r.suite == "full" && r.run_count() > 1)
        .map(|r| {
            let n = r.run_count();
            (r.tree, n)
        })
        .collect();
    out.sort();
    out
}

/// The passing receipt of `suite` for the tree of `commit` (sha or unique prefix), if any.
/// Fast path: a clean receipt whose `head` is that commit needs no object read.
pub fn find_pass(repo: &Repo, commit: &str, suite: &str) -> Option<(PathBuf, Receipt)> {
    let rd = std::fs::read_dir(dir(&repo.work)).ok()?;
    let mut all: Vec<(PathBuf, Receipt)> = rd
        .flatten()
        .filter(|e| e.file_name().to_string_lossy().ends_with(&format!("-{suite}.txt")))
        .filter_map(|e| Some((e.path(), Receipt::parse(&std::fs::read_to_string(e.path()).ok()?)?)))
        .filter(|(_, r)| r.pass && r.suite == suite)
        .collect();
    all.sort_by(|a, b| a.0.cmp(&b.0));
    if let Some(hit) = all.iter().find(|(_, r)| r.clean && crate::guard::rules::pre(commit, &r.head)) {
        return Some(hit.clone());
    }
    let t = repo.commit_tree(commit)?;
    all.into_iter().find(|(_, r)| r.tree == t)
}

/// Only final review and Gate C wait for a passing full suite.
pub(crate) fn required_at(gate: char) -> bool {
    matches!(gate, 'C' | 'R')
}

/// Judge the final receipt consistently in the Stop guard and the read-only backing report.
pub(crate) fn gate_standing(receipt: Option<&Receipt>, gate: char) -> Standing {
    match receipt.map(Receipt::pass_count) {
        None | Some(0) => Standing::Missing,
        Some(n) if gate == 'C' && n > 1 => Standing::Repeated(n),
        Some(_) => Standing::Ok,
    }
}

/// Check the full-suite receipt for the tree a final gate or review line names.
pub fn standing(repo: Option<&Repo>, commit: &str, gate: char) -> Standing {
    if !required_at(gate) {
        return Standing::Ok;
    }
    let found = repo.and_then(|r| find_pass(r, commit, "full"));
    gate_standing(found.as_ref().map(|(_, receipt)| receipt), gate)
}

/// What a receipt stands on: the work tree and HEAD at one moment (one `git add` spawn for the tree id).
pub struct Snapshot {
    pub work: PathBuf,
    pub tree: String,
    pub head: String,
    pub clean: bool,
}

/// Takes the snapshot. A suite's receipt takes it before the suite starts: what the suite tested.
pub fn snapshot(folder: &Path) -> Result<Snapshot, String> {
    let repo = Repo::discover(folder).ok_or("not in a Git work tree")?;
    let head = crate::git::refs::head(&repo);
    let committed = repo.commit_tree(&head);
    let tree = match tree::tree_of(&repo) {
        Ok(tree) => tree,
        Err(error) => committed.as_ref().filter(|_| clean_at(&repo, &head)).cloned().ok_or(error)?,
    };
    let clean = committed.is_some_and(|tree_id| tree_id == tree);
    Ok(Snapshot { work: repo.work, tree, head, clean })
}

/// A protected Git directory can still prove a clean checkout without writing an index or objects.
fn clean_at(repo: &Repo, head: &str) -> bool {
    crate::git::command(repo)
        .args(["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"])
        .output()
        .is_ok_and(|out| out.status.success() && out.stdout.is_empty() && crate::git::refs::head(repo) == head)
}

/// Writes the receipt of a suite run on snapshot `s`.
pub fn record(s: Snapshot, suite: &str, pass: bool, cmd: &str, secs: u64, runtime: &str, log: &str) -> Result<(PathBuf, Receipt), String> {
    let r = Receipt {
        suite: suite.into(),
        tree: s.tree,
        head: s.head,
        clean: s.clean,
        pass,
        cmd: cmd.into(),
        runtime: runtime.into(),
        secs,
        at: utc_iso(crate::paths::now()),
        log: log.into(),
        runs: 0,
        passes: None,
    };
    let mut r = r;
    let p = write(&s.work, &mut r).map_err(|e| format!("cannot write the receipt: {e}"))?;
    Ok((p, r))
}

/// A receipt for the work tree as it is now (`receipt write`, after a suite another runner ran).
pub fn stamp(folder: &Path, suite: &str, pass: bool, cmd: &str, secs: u64, runtime: &str, log: &str) -> Result<(PathBuf, Receipt), String> {
    record(snapshot(folder)?, suite, pass, cmd, secs, runtime, log)
}

/// `factory receipt run|write|check ...`
pub fn cli(args: &[&str]) -> u8 {
    let here = crate::guard::cwd();
    let runtime = format!("factory {} {}-{}", crate::VERSION, std::env::consts::OS, std::env::consts::ARCH);
    match args {
        ["run", rest @ ..] => {
            let (opts, cmd) = match rest.iter().position(|a| *a == "--") {
                Some(i) => (&rest[..i], &rest[i + 1..]),
                None => return usage(),
            };
            let Some((prog, argv)) = cmd.split_first() else { return usage() };
            let suite = opt(opts, "--suite").unwrap_or("full");
            let before = match snapshot(&here) {
                Ok(s) => s,
                Err(e) => {
                    eprintln!("factory receipt: {e}");
                    return 1;
                }
            };
            // The suite runs once per tree: a passing receipt for this very tree is reused, never rerun.
            if let Some((p, r)) = existing(&before.work, &before.tree, suite).filter(|(_, r)| r.pass && !opts.contains(&"--again")) {
                eprintln!(
                    "factory receipt: {suite} already passed on this tree ({}, {} s): reused, not run again. Reviews and gates read it; `--again` runs it anyway and counts a repeat.",
                    crate::paths::text(&p),
                    r.secs
                );
                return 0;
            }
            let started = std::time::Instant::now();
            let status = std::process::Command::new(prog).args(argv).status();
            let code = match status {
                Ok(s) => s.code().unwrap_or(1),
                Err(e) => {
                    eprintln!("factory receipt: cannot run {prog}: {e}");
                    return 1;
                }
            };
            let receipt = report(record(before, suite, code == 0, &cmd.join(" "), started.elapsed().as_secs(), &runtime, ""));
            // A successful suite still needs a receipt. Preserve a failing suite's own exit code.
            if code == 0 { receipt } else { u8::try_from(code).ok().filter(|c| *c != 0).unwrap_or(1) }
        }
        ["write", opts @ ..] => {
            // The result as `--result PASS|FAIL` or the suite's `--exit <code>`; the suite defaults to `full`.
            let pass = match (opt(opts, "--result"), opt(opts, "--exit")) {
                (Some("PASS"), None) => true,
                (Some("FAIL"), None) => false,
                (None, Some(code)) => match code.parse::<i64>() {
                    Ok(c) => c == 0,
                    Err(_) => return usage(),
                },
                _ => return usage(),
            };
            let Some(cmd) = opt(opts, "--cmd") else { return usage() };
            let suite = opt(opts, "--suite").unwrap_or("full");
            let secs = opt(opts, "--secs").and_then(|s| s.parse().ok()).unwrap_or(0);
            let rt = opt(opts, "--runtime").map_or(runtime, String::from);
            report(stamp(&here, suite, pass, cmd, secs, &rt, opt(opts, "--log").unwrap_or("")))
        }
        ["check", opts @ ..] => {
            let suite = opt(opts, "--suite").unwrap_or("full");
            let Some(repo) = Repo::discover(&here) else {
                eprintln!("factory receipt: not in a Git work tree");
                return 1;
            };
            let commit = opt(opts, "--commit").map_or_else(|| repo.info().head, String::from);
            match find_pass(&repo, &commit, suite) {
                Some((p, _)) => {
                    println!("{}", crate::paths::text(&p));
                    0
                }
                None => {
                    println!("no {suite} PASS receipt for the tree of {commit}");
                    1
                }
            }
        }
        _ => usage(),
    }
}

fn report(r: Result<(PathBuf, Receipt), String>) -> u8 {
    match r {
        Ok((p, _)) => {
            eprintln!("factory receipt: {}", crate::paths::text(&p));
            0
        }
        Err(e) => {
            eprintln!("factory receipt: {e}");
            1
        }
    }
}

fn usage() -> u8 {
    eprintln!(
        "usage: factory receipt run [--suite <name>] [--again] -- <command>... | write --cmd <command> (--exit <code> | --result PASS|FAIL) [--suite <name>] [--secs <n>] [--log <path>] [--runtime <s>] | check [--commit <sha>] [--suite <name>]"
    );
    2
}

/// The value after `--name` in an option list.
pub fn opt<'a>(args: &[&'a str], name: &str) -> Option<&'a str> {
    args.iter().position(|a| *a == name).and_then(|i| args.get(i + 1).copied())
}

/// `YYYY-MM-DDTHH:MM:SSZ` for Unix seconds (civil-from-days, no time zone database).
pub fn utc_iso(secs: u64) -> String {
    let days = (secs / 86_400) as i64;
    let rem = secs % 86_400;
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = yoe + era * 400 + i64::from(m <= 2);
    format!("{y:04}-{m:02}-{d:02}T{:02}:{:02}:{:02}Z", rem / 3600, rem % 3600 / 60, rem % 60)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trips_and_dates() {
        let r = Receipt {
            suite: "full".into(),
            tree: "t".into(),
            head: "h".into(),
            clean: true,
            pass: true,
            cmd: "sh x".into(),
            runtime: "r".into(),
            secs: 3,
            at: "a".into(),
            log: "l".into(),
            runs: 2,
            passes: Some(1),
        };
        assert_eq!(Receipt::parse(&r.render()), Some(r));
        let old = Receipt::parse("factory-receipt 1\nsuite full\nresult PASS\n").unwrap();
        assert_eq!((old.run_count(), old.pass_count()), (1, 1));
        assert_eq!(utc_iso(0), "1970-01-01T00:00:00Z");
        assert_eq!(utc_iso(1_794_808_234), "2026-11-16T05:50:34Z");
    }
}
