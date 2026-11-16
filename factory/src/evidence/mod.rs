//! Evidence the host wrote: each session's subagent transcripts (gate rounds and verdicts) and session
//! transcripts (step blocks that reached chat). Read from saved byte offsets: each call reads only new bytes.
//!
//! Claude Code keeps `<projects>/<project>/<session>/subagents/agent-<id>.jsonl`, brief first; other hosts
//! have only the session transcript, where a gate's agent id must appear (never a Claude Code one).

pub mod cache;
pub mod scan;

use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};

/// What the evidence proves, folded in the guard's file order.
#[derive(Debug, Default, Clone)]
pub struct Evidence {
    /// No subagent files, but a session transcript: ids are looked up in its text.
    pub fallback: bool,
    /// No transcript at all: gate lines count as text.
    pub none: bool,
    /// Role per agent id (`A`, `B`, `C`, `R`).
    pub kind: HashMap<String, char>,
    /// Last verdict per agent id.
    pub last: HashMap<String, String>,
    /// Failed rounds per loop since its last pass: A, B, C, R.
    pub rounds: [i64; 4],
    /// The last reviewer verdict named a CRITICAL finding.
    pub review_critical: bool,
    /// Fallback mode: a transcript is Claude Code's (its text holds the model's own run-file edits).
    pub claude_fallback: bool,
    /// Fallback mode: wanted ids found in the transcripts.
    pub seen: HashSet<String>,
    /// A session transcript is Claude Code's (only those prove posted blocks).
    pub claude: bool,
    /// Step labels posted as chat blocks.
    pub sent: HashSet<String>,
}

/// One evidence file with what ordering needs.
#[derive(Debug, Clone)]
pub struct FileRef {
    pub path: PathBuf,
    /// The name `ls -tr` sorts on (`./<project>/<session>/subagents/agent-<id>.jsonl`).
    pub sort_name: String,
    pub mtime: u64,
    pub size: u64,
}

/// `${s%/*}`: drops the last `/` component when there is one.
fn sh_dirname(s: &str) -> &str {
    s.rfind('/').map_or(s, |i| &s[..i])
}

/// Gathers and folds the evidence for a run's sessions. `tp` is the hook's transcript path (`/` form),
/// `want` the checker and reviewer ids the run file names, `guard` the run's guard folder (offsets cache).
pub fn collect(tp: &str, sessions: &[String], want: &[String], guard: &Path) -> Evidence {
    let projects = sh_dirname(sh_dirname(tp)).to_string();
    let mut c = cache::Cache::load(guard);
    let own = sh_dirname(tp).rsplit('/').next().unwrap_or("");
    let homes = if projects.is_empty() { HashMap::new() } else { c.session_homes(Path::new(&projects), own, sessions) };
    let mut subs: Vec<FileRef> = Vec::new();
    for q in sessions {
        for p in homes.get(q).into_iter().flatten() {
            subs.extend(subagent_files(&projects, p, q));
        }
    }
    subs.sort_by(|a, b| a.mtime.cmp(&b.mtime).then_with(|| b.sort_name.cmp(&a.sort_name)));
    let mut ev = Evidence::default();
    let tp_file = !tp.is_empty() && Path::new(tp).is_file();
    let mut sessions_files: Vec<FileRef> = Vec::new();
    if subs.is_empty() {
        if tp_file {
            ev.fallback = true;
            sessions_files.push(file_ref(Path::new(tp), tp.to_string()));
        } else {
            ev.none = true;
        }
    }
    for q in sessions {
        for p in homes.get(q).into_iter().flatten() {
            let f = format!("{projects}/{p}/{q}.jsonl");
            if Path::new(&f).is_file() && !(ev.fallback && f == tp) {
                sessions_files.push(file_ref(Path::new(&f), f.clone()));
            }
        }
    }
    fold_subagents(&mut ev, &subs, &mut c);
    for f in &sessions_files {
        let s = c.session(f);
        ev.claude |= s.sidechain;
        ev.sent.extend(s.sent.iter().cloned());
        if ev.fallback {
            ev.claude_fallback |= s.sidechain;
            for id in want {
                if c.contains(f, id) {
                    ev.seen.insert(id.clone());
                }
            }
        }
    }
    c.save();
    ev
}

/// Subagent files of session `q` in project folder `p`, as the guard's glob lists them.
fn subagent_files(projects: &str, p: &str, q: &str) -> Vec<FileRef> {
    let dir = format!("{projects}/{p}/{q}/subagents");
    let Ok(rd) = std::fs::read_dir(&dir) else { return Vec::new() };
    let mut out = Vec::new();
    for e in rd.flatten() {
        let name = e.file_name().to_string_lossy().into_owned();
        if !name.starts_with("agent-") || !name.ends_with(".jsonl") {
            continue;
        }
        // Not the directory listing's copy: on Windows it can lag a file still being appended.
        let md = match std::fs::metadata(e.path()) {
            Ok(m) if m.is_file() => m,
            _ => continue,
        };
        out.push(FileRef {
            path: PathBuf::from(format!("{dir}/{name}")),
            sort_name: format!("./{p}/{q}/subagents/{name}"),
            mtime: md.modified().map(crate::paths::ns).unwrap_or(0) as u64,
            size: md.len(),
        });
    }
    out
}

fn file_ref(p: &Path, sort_name: String) -> FileRef {
    let md = std::fs::metadata(p).ok();
    FileRef {
        path: p.to_path_buf(),
        sort_name,
        mtime: md.as_ref().and_then(|m| m.modified().ok()).map(crate::paths::ns).unwrap_or(0) as u64,
        size: md.map_or(0, |m| m.len()),
    }
}

/// Folds subagent files oldest first: role per id, last verdict per id, rounds per loop.
/// A checker file closes its round when the next file starts (a PASS resets its gate's count).
fn fold_subagents(ev: &mut Evidence, subs: &[FileRef], c: &mut cache::Cache) {
    let mut prev: Option<String> = None;
    for f in subs {
        let s = c.sub(f);
        if !s.nonempty {
            continue;
        }
        if let Some(p) = prev.take() {
            close_round(ev, &p);
        }
        let id = agent_id(&f.path);
        if let Some(r) = s.role {
            ev.kind.insert(id.clone(), r);
            if let Some(v) = &s.last {
                ev.last.insert(id.clone(), v.clone());
            }
            if r == 'R' {
                ev.rounds[3] = if s.r_reset { s.r_count } else { ev.rounds[3] + s.r_count };
                if let Some(cr) = s.r_critical {
                    ev.review_critical = cr;
                }
            }
        }
        prev = Some(id);
    }
    if let Some(p) = prev {
        close_round(ev, &p);
    }
}

/// A gate checker's round ends: PASS resets the gate's count, a FAIL handback adds one.
fn close_round(ev: &mut Evidence, id: &str) {
    let Some(&k) = ev.kind.get(id) else { return };
    let i = match k {
        'A' => 0,
        'B' => 1,
        'C' => 2,
        _ => return,
    };
    let last = ev.last.get(id).map_or("", String::as_str);
    ev.rounds[i] = if last.starts_with("Gate ") && last.get(6..).is_some_and(|s| s.starts_with(": PASS")) {
        0
    } else {
        ev.rounds[i] + i64::from(last.contains("FAIL"))
    };
}

/// `agent-<id>.jsonl` → `<id>`.
fn agent_id(p: &Path) -> String {
    let name = p.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
    let base = name.strip_suffix(".jsonl").unwrap_or(&name);
    base.rsplit_once("agent-").map_or(base, |(_, id)| id).to_string()
}
