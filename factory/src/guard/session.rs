//! Bind native Codex runs before their first hook, including children with an inherited parent SESSION id.

use crate::paths;
use crate::run::{
    locate,
    state::{Loaded, State},
};
use serde_json::Value;
use std::fs;
use std::io::{BufRead, BufReader, Read};
use std::path::{Path, PathBuf};

/// Other hosts keep their initialization. A native thread must resolve to its exact transcript.
pub(super) fn initialize(root: &Path) -> Result<(), String> {
    let Some(id) = std::env::var("CODEX_THREAD_ID")
        .ok()
        .filter(|id| !id.is_empty())
        .or_else(|| std::env::var("CODEX_SESSION_ID").ok().filter(|id| !id.is_empty()))
    else {
        return Ok(());
    };
    let link = locate::session_file(&id).ok_or("unsafe Codex session id")?;
    let home =
        std::env::var_os("CODEX_HOME").filter(|home| !home.is_empty()).map(PathBuf::from).unwrap_or_else(|| paths::home().join(".codex"));
    bind(root, &home, &id, &link)
}

/// Verify metadata before saving the existing state and route formats through atomic writes.
fn bind(root: &Path, home: &Path, id: &str, link: &Path) -> Result<(), String> {
    let mut matches = Vec::new();
    discover(&home.join("sessions"), id, 3, &mut matches);
    let [transcript] = matches.as_slice() else {
        return Err(format!("expected one Codex transcript for {id}, found {} under {}", matches.len(), paths::text(home)));
    };
    let transcript = paths::text(transcript);
    let folder = paths::text(root);
    if [&transcript, &folder].iter().any(|value| value.contains(['\'', '$', '`', '\r', '\n'])) {
        return Err("session paths cannot be represented safely in guard state".into());
    }
    let guard = root.join(".factory/guard");
    let path = guard.join("state");
    let mut state = match State::load(&path) {
        Loaded::Valid(state) => state,
        Loaded::Missing => State::default(),
        Loaded::Edited => return Err("guard state was edited outside the guard".into()),
    };
    let sessions = state.get("sessions");
    if !sessions.split_whitespace().any(|session| session == id) {
        state.set("sessions", if sessions.is_empty() { id.to_string() } else { format!("{sessions} {id}") });
    }
    // Begin owns the new Step-0 run, so no prior session's phase may carry forward.
    state.set("sstep", "0");
    state.set("session", id);
    state.set("transcript", transcript);
    fs::create_dir_all(&guard).map_err(|err| err.to_string())?;
    paths::write_atomic(&path, &state.bytes()).map_err(|err| err.to_string())?;
    fs::create_dir_all(link.parent().ok_or("no session cache folder")?).map_err(|err| err.to_string())?;
    paths::write_atomic(link, format!("{folder}\n").as_bytes()).map_err(|err| err.to_string())
}

/// Native rollouts live under sessions/YYYY/MM/DD. Read metadata only for exact filename candidates.
fn discover(dir: &Path, id: &str, depth: u8, found: &mut Vec<PathBuf>) {
    let Ok(entries) = fs::read_dir(dir) else { return };
    let suffix = format!("-{id}.jsonl");
    for entry in entries.flatten() {
        let Ok(kind) = entry.file_type() else { continue };
        if kind.is_dir() && depth > 0 {
            discover(&entry.path(), id, depth - 1, found);
        } else if kind.is_file() && entry.file_name().to_string_lossy().ends_with(&suffix) {
            let Ok(file) = fs::File::open(entry.path()) else { continue };
            let mut line = String::new();
            if BufReader::new(file.take(1024 * 1024)).read_line(&mut line).is_err() {
                continue;
            }
            let Ok(meta) = serde_json::from_str::<Value>(&line) else { continue };
            if meta["type"] == "session_meta" && meta["payload"]["id"].as_str() == Some(id) {
                found.push(entry.path());
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture(name: &str) -> PathBuf {
        let root = std::env::temp_dir().join(format!("factory-native-session-{}-{name}", std::process::id()));
        fs::create_dir_all(&root).unwrap();
        root
    }

    fn transcript(home: &Path, day: &str, id: &str, actual: &str) -> PathBuf {
        let dir = home.join("sessions/2026/01").join(day);
        fs::create_dir_all(&dir).unwrap();
        let path = dir.join(format!("rollout-{id}.jsonl"));
        fs::write(&path, format!("{{\"type\":\"session_meta\",\"payload\":{{\"id\":\"{actual}\"}}}}\n")).unwrap();
        path
    }

    #[test]
    fn binds_the_verified_thread_and_preserves_other_state() {
        let root = fixture("bind");
        let home = root.join("home");
        let file = transcript(&home, "01", "child", "child");
        transcript(&home, "01", "parent", "parent");
        let guard = root.join(".factory/guard");
        fs::create_dir_all(&guard).unwrap();
        let mut initial = State::default();
        initial.set("ticks", "4");
        initial.set("sessions", "parent");
        initial.save(&guard.join("state"));
        let link = root.join("cache/sessions/child");
        bind(&root, &home, "child", &link).unwrap();
        bind(&root, &home, "child", &link).unwrap();
        let Loaded::Valid(state) = State::load(&guard.join("state")) else { panic!("invalid state") };
        assert_eq!(state.get("session"), "child");
        assert_eq!(state.get("sessions"), "parent child");
        assert_eq!(state.get("ticks"), "4");
        assert_eq!(state.get("transcript"), paths::text(&file));
        assert_eq!(fs::read_to_string(link).unwrap(), format!("{}\n", paths::text(&root)));
    }

    #[test]
    fn refuses_missing_mismatched_and_ambiguous_transcripts_before_writing() {
        let root = fixture("reject");
        let home = root.join("home");
        let link = root.join("cache/sessions/child");
        assert!(bind(&root, &home, "child", &link).is_err());
        let file = transcript(&home, "01", "child", "foreign");
        assert!(bind(&root, &home, "child", &link).is_err());
        fs::remove_file(file).unwrap();
        transcript(&home, "01", "child", "child");
        transcript(&home, "02", "child", "child");
        assert!(bind(&root, &home, "child", &link).is_err());
        assert!(!link.exists());
        assert!(!root.join(".factory/guard/state").exists());
    }
}
