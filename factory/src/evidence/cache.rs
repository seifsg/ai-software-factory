//! The offsets cache, `.factory/guard/scan` (JSON, its own file: older guards never read it).
//! Per transcript: size, mtime, the offset after its last full line, a hash of the bytes before that offset,
//! and the scanner state there. A shrunk or rewritten file is rescanned from 0; an unchanged one is not opened.
//! Per projects folder: which project folders hold each session, refreshed by folder mtime, so the
//! guard never stats every project folder on every turn.

use super::scan::{Session, Sub};
use super::FileRef;
use serde_json::{json, Map, Value};
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
    pub fn load(guard: &Path) -> Cache {
        let path = guard.join("scan");
        let data = std::fs::read(&path)
            .ok()
            .and_then(|b| serde_json::from_slice::<Value>(&b).ok())
            .filter(|v| v.get("v") == Some(&json!(1)))
            .unwrap_or_else(|| json!({"v": 1, "files": {}, "homes": {}}));
        Cache { path, data, dirty: false }
    }

    /// Writes the cache when it changed and the guard folder exists (a hook never creates it here).
    pub fn save(&self) {
        if self.dirty && self.path.parent().is_some_and(Path::is_dir) {
            let _ = crate::paths::write_atomic(&self.path, self.data.to_string().as_bytes());
        }
    }

    /// For each session, the project folders under `projects` holding `<session>.jsonl` or `<session>/`.
    /// One directory listing per call; only folders whose mtime moved, and new sessions, are probed.
    /// For each session, the project folders under `projects` holding `<session>.jsonl` or `<session>/`.
    /// A session found in the hook transcript's own project folder is looked up nowhere else; any other is
    /// probed across all project folders once, and again only after the projects folder changed. Why: a full
    /// probe stats every project folder (thousands); a session living in two project folders is rare.
    pub fn session_homes(&mut self, projects: &Path, own: &str, sessions: &[String]) -> HashMap<String, Vec<String>> {
        let key = crate::paths::text(projects);
        let stamp = crate::paths::mtime_ns(projects).unwrap_or(0) as u64;
        let old = self.data["homes"][&key].clone();
        let same_stamp = old["m"].as_u64() == Some(stamp);
        let mut listing: Option<Vec<String>> = None;
        let mut homes: HashMap<String, Vec<String>> = HashMap::new();
        let mut saved = Map::new();
        for q in sessions {
            let cached: Option<Vec<String>> = old["s"][q].as_array().map(|a| a.iter().filter_map(|v| v.as_str().map(String::from)).collect());
            let in_own = !own.is_empty() && holds(&projects.join(own), q);
            let mut found = match cached {
                Some(c) if !c.is_empty() || same_stamp => c,
                _ if in_own => vec![own.to_string()],
                _ => {
                    let names = listing.get_or_insert_with(|| project_dirs(projects));
                    names.iter().filter(|p| holds(&projects.join(p), q)).cloned().collect()
                }
            };
            if in_own && !found.iter().any(|p| p == own) {
                found.push(own.to_string());
                found.sort();
            }
            saved.insert(q.clone(), json!(found));
            homes.insert(q.clone(), found);
        }
        let entry = json!({"m": stamp, "s": saved});
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

    /// True when `id` occurs anywhere in the file (fallback proof); cached per file size and mtime.
    pub fn contains(&mut self, f: &FileRef, id: &str) -> bool {
        let key = format!("{}#{}", crate::paths::text(&f.path), id);
        let stamp = json!([f.size, f.mtime]);
        let e = &self.data["ids"][&key];
        if e["at"] == stamp {
            return e["hit"].as_bool().unwrap_or(false);
        }
        let hit = std::fs::read(&f.path).is_ok_and(|b| memchr::memmem::find(&b, id.as_bytes()).is_some());
        self.data["ids"][&key] = json!({"at": stamp, "hit": hit});
        self.dirty = true;
        hit
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

/// Project folder names under `projects`, sorted as a glob lists them (hidden names left out).
fn project_dirs(projects: &Path) -> Vec<String> {
    let mut v: Vec<String> = std::fs::read_dir(projects)
        .map(|rd| {
            rd.flatten()
                .filter(|e| e.file_type().is_ok_and(|t| t.is_dir() || (t.is_symlink() && e.path().is_dir())))
                .map(|e| e.file_name().to_string_lossy().into_owned())
                .filter(|n| !n.starts_with('.'))
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
