//! The offsets cache, `.factory/guard/scan` (JSON, its own file: older guards never read it).
//! Per transcript: size, mtime, the offset after its last full line, a hash of the bytes before that offset,
//! and the scanner state there. A shrunk or rewritten file is rescanned from 0; an unchanged one is not opened.
//! Per project folder: its mtime and the sessions it holds, probed again only when that mtime moves, so a
//! call lists the projects folder once and stats only folders that changed.

use super::FileRef;
use super::scan::{Session, Sub};
use serde_json::{Map, Value, json};
use std::collections::HashMap;
use std::io::{Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};

const TAIL: u64 = 64;

pub struct Cache {
    path: PathBuf,
    data: Value,
    dirty: bool,
}

impl Cache {
    /// Loads the cache; a cache from another binary version, or of another shape, starts empty.
    pub fn load(guard: &Path) -> Cache {
        let path = guard.join("scan");
        let fresh = || json!({"v": crate::VERSION, "files": {}, "homes": {}, "ids": {}});
        let data = std::fs::read(&path)
            .ok()
            .and_then(|b| serde_json::from_slice::<Value>(&b).ok())
            .filter(|v| v["v"] == crate::VERSION && ["files", "homes", "ids"].iter().all(|k| v[k].is_object()))
            .unwrap_or_else(fresh);
        Cache { path, data, dirty: false }
    }

    /// Writes the cache when it changed and the guard folder exists (a hook never creates it here).
    pub fn save(&self) {
        if self.dirty && self.path.parent().is_some_and(Path::is_dir) {
            let _ = crate::paths::write_atomic(&self.path, self.data.to_string().as_bytes());
        }
    }

    /// For each session, the project folders under `projects` holding `<session>.jsonl` or `<session>/`, as
    /// the sh guard's glob over every project folder finds them. One listing of the projects folder per call
    /// (on Windows its entries carry their mtimes); a folder is probed again only when its mtime moved, and
    /// for a session not seen before.
    pub fn session_homes(&mut self, projects: &Path, sessions: &[String]) -> HashMap<String, Vec<String>> {
        let key = crate::paths::text(projects);
        let old = self.data["homes"][&key].clone();
        let checked: Vec<&str> = old["checked"].as_array().map(|a| a.iter().filter_map(Value::as_str).collect()).unwrap_or_default();
        let mut dirs = Map::new();
        let mut homes: HashMap<String, Vec<String>> = HashMap::new();
        for (name, mtime) in project_dirs(projects) {
            let prev = &old["dirs"][&name];
            let fresh = prev["m"].as_u64() == Some(mtime);
            let had = |q: &str| prev["s"].as_array().is_some_and(|a| a.iter().any(|v| v.as_str() == Some(q)));
            let held: Vec<&String> = sessions
                .iter()
                .filter(|q| if fresh && checked.contains(&q.as_str()) { had(q) } else { holds(&projects.join(&name), q) })
                .collect();
            for q in &held {
                homes.entry((*q).clone()).or_default().push(name.clone());
            }
            dirs.insert(name, if held.is_empty() { json!({"m": mtime}) } else { json!({"m": mtime, "s": held}) });
        }
        let entry = json!({"checked": sessions, "dirs": dirs});
        if self.data["homes"][&key] != entry {
            self.data["homes"][&key] = entry;
            self.dirty = true;
        }
        homes
    }

    /// Scanner state of a subagent file after all its lines.
    pub fn sub(&mut self, f: &FileRef) -> Sub {
        self.scan(f)
    }

    /// Scanner state of a session transcript after all its lines.
    pub fn session(&mut self, f: &FileRef) -> Session {
        self.scan(f)
    }

    /// True when `id` occurs anywhere in the file (fallback proof). Read from the saved offset, overlapping
    /// by the id's length; a found id stays found while the file only grows, a shrunk file is read again.
    pub fn contains(&mut self, f: &FileRef, id: &str) -> bool {
        let key = format!("{}#{}", crate::paths::text(&f.path), id);
        let e = &self.data["ids"][&key];
        let (mut off, hit) = (e["off"].as_u64().unwrap_or(0), e["hit"].as_bool().unwrap_or(false));
        if off > f.size {
            off = 0;
        } else if hit {
            return true;
        }
        let start = off.saturating_sub(id.len() as u64);
        let mut rest = Vec::new();
        let read = std::fs::File::open(&f.path).and_then(|mut file| {
            file.seek(SeekFrom::Start(start))?;
            file.read_to_end(&mut rest)
        });
        let found = read.is_ok() && memchr::memmem::find(&rest, id.as_bytes()).is_some();
        self.data["ids"][&key] = json!({"off": start + rest.len() as u64, "hit": found});
        self.dirty = true;
        found
    }

    /// Feeds the file's new full lines to a scanner restored at the saved offset, saves it there, then
    /// feeds the unfinished last line, if any, to a copy (fed fresh each call, never saved).
    fn scan<S: Scanner>(&mut self, f: &FileRef) -> S {
        let key = crate::paths::text(&f.path);
        let saved = &self.data["files"][&key];
        let same = saved["k"] == S::KIND;
        let restore = |v: &Value| S::from_json(v);
        if same && saved["size"].as_u64() == Some(f.size) && saved["mtime"].as_u64() == Some(f.mtime) && saved["part"] == json!(false) {
            return restore(&saved["st"]);
        }
        let Ok(mut file) = std::fs::File::open(&f.path) else { return S::default() };
        let mut off = saved["off"].as_u64().unwrap_or(0);
        let mut s = restore(&saved["st"]);
        if !(same && off <= f.size && tail_hash(&mut file, off).as_deref() == saved["tail"].as_str()) {
            off = 0;
            s = S::default();
        }
        let mut rest = Vec::new();
        if file.seek(SeekFrom::Start(off)).is_ok() {
            let _ = file.read_to_end(&mut rest);
        }
        let full = rest.iter().rposition(|&b| b == b'\n').map_or(0, |i| i + 1);
        if full > 0 {
            for line in rest[..full - 1].split(|&b| b == b'\n') {
                s.line(line);
            }
        }
        let new_off = off + full as u64;
        let partial = full < rest.len();
        self.data["files"][&key] = json!({
            "k": S::KIND, "size": f.size, "mtime": f.mtime, "off": new_off,
            "tail": tail_hash(&mut file, new_off), "part": partial, "st": s.to_json(),
        });
        self.dirty = true;
        if partial {
            s.line(&rest[full..]);
        }
        s
    }
}

/// A line scanner whose state survives between calls as JSON.
trait Scanner: Default {
    const KIND: &'static str;
    fn line(&mut self, l: &[u8]);
    fn to_json(&self) -> Value;
    fn from_json(v: &Value) -> Self;
}

impl Scanner for Sub {
    const KIND: &'static str = "sub";
    fn line(&mut self, l: &[u8]) {
        Sub::line(self, l);
    }
    fn to_json(&self) -> Value {
        json!({"n": self.nonempty, "role": self.role.map(String::from), "last": self.last, "rr": self.r_reset, "rc": self.r_count, "crit": self.r_critical})
    }
    fn from_json(v: &Value) -> Sub {
        Sub {
            nonempty: v["n"].as_bool().unwrap_or(false),
            role: v["role"].as_str().and_then(|r| r.chars().next()),
            last: v["last"].as_str().map(String::from),
            r_reset: v["rr"].as_bool().unwrap_or(false),
            r_count: v["rc"].as_i64().unwrap_or(0),
            r_critical: v["crit"].as_bool(),
        }
    }
}

impl Scanner for Session {
    const KIND: &'static str = "ses";
    fn line(&mut self, l: &[u8]) {
        Session::line(self, l);
    }
    fn to_json(&self) -> Value {
        json!({"sc": self.sidechain, "sent": self.sent})
    }
    fn from_json(v: &Value) -> Session {
        Session {
            sidechain: v["sc"].as_bool().unwrap_or(false),
            sent: v["sent"].as_array().map(|a| a.iter().filter_map(|x| x.as_str().map(String::from)).collect()).unwrap_or_default(),
        }
    }
}

/// FNV-1a of the up to 64 bytes before `off`: detects a rewritten file without rereading it.
fn tail_hash(file: &mut std::fs::File, off: u64) -> Option<String> {
    let start = off.saturating_sub(TAIL);
    file.seek(SeekFrom::Start(start)).ok()?;
    let mut buf = vec![0u8; (off - start) as usize];
    file.read_exact(&mut buf).ok()?;
    let h = buf.iter().fold(0xcbf2_9ce4_8422_2325u64, |h, &b| (h ^ b as u64).wrapping_mul(0x0100_0000_01b3));
    Some(format!("{h:016x}"))
}

/// Project folder names under `projects` with their mtimes, sorted as a glob lists them (hidden names left out).
fn project_dirs(projects: &Path) -> Vec<(String, u64)> {
    let mut v: Vec<(String, u64)> = std::fs::read_dir(projects)
        .map(|rd| {
            rd.flatten()
                .filter(|e| e.file_type().is_ok_and(|t| t.is_dir() || (t.is_symlink() && e.path().is_dir())))
                .map(|e| {
                    // A symlinked folder: its target's mtime, which moves when a session lands there.
                    let md = if e.file_type().is_ok_and(|t| t.is_symlink()) { std::fs::metadata(e.path()) } else { e.metadata() };
                    let m = md.ok().and_then(|m| m.modified().ok()).map_or(0, crate::paths::ns) as u64;
                    (e.file_name().to_string_lossy().into_owned(), m)
                })
                .filter(|(n, _)| !n.starts_with('.'))
                .collect()
        })
        .unwrap_or_default();
    v.sort();
    v
}

/// The project folder holds session `q`: its transcript or its folder.
fn holds(p: &Path, q: &str) -> bool {
    p.join(q).exists() || p.join(format!("{q}.jsonl")).exists()
}
