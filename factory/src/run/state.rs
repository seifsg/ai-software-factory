//! The guard's own state, `.factory/guard/state`: single-quoted `g_<field>='<value>'` lines, byte-compatible
//! with every sh guard version. Never a new field here (an older guard halts on it); new data gets its own file.

use std::collections::HashMap;
use std::path::Path;

/// Fields in the order the guard writes them.
pub const FIELDS: [&str; 22] = [
    "ticks",
    "session",
    "sessions",
    "transcript",
    "seen",
    "night_until",
    "sig",
    "idle",
    "halt",
    "end",
    "clear",
    "base_A",
    "base_B",
    "base_C",
    "base_R",
    "sstep",
    "relay",
    "rstep",
    "compacts",
    "csession",
    "jobs_since",
    "jobs_id",
];

/// Loaded state; an unknown or malformed line means someone else edited it.
#[derive(Debug, Default, Clone)]
pub struct State {
    values: HashMap<String, String>,
}

/// What loading found.
pub enum Loaded {
    Missing,
    Valid(State),
    /// A line no guard writes: the run halts until the owner clears it.
    Edited,
}

impl State {
    /// Reads and validates a state file, line by line, exactly as the sh guard's `grep -v` test does.
    pub fn load(path: &Path) -> Loaded {
        let Ok(data) = std::fs::read(path) else { return Loaded::Missing };
        let text = String::from_utf8_lossy(&data);
        let body = text.strip_suffix('\n').unwrap_or(&text);
        let mut values = HashMap::new();
        if !data.is_empty() {
            for line in body.split('\n') {
                match valid_line(line) {
                    Some((k, v)) => {
                        values.insert(k.to_string(), v.to_string());
                    }
                    None => return Loaded::Edited,
                }
            }
        }
        Loaded::Valid(State { values })
    }

    /// A field's value, empty when unset.
    pub fn get(&self, k: &str) -> &str {
        self.values.get(k).map_or("", String::as_str)
    }

    /// A numeric field, or `default` when empty or not a number (shell `${x:-d}` then arithmetic).
    pub fn num(&self, k: &str, default: i64) -> i64 {
        self.get(k).parse().unwrap_or(default)
    }

    pub fn set(&mut self, k: &str, v: impl Into<String>) {
        self.values.insert(k.to_string(), v.into());
    }

    /// The state bytes: every field in order, unset ones empty.
    pub fn bytes(&self) -> Vec<u8> {
        FIELDS.iter().map(|k| format!("g_{k}='{}'\n", self.get(k))).collect::<String>().into_bytes()
    }

    /// Writes the state, creating the guard folder; through a rename, so a reader never sees half a state.
    pub fn save(&self, path: &Path) {
        if let Some(dir) = path.parent() {
            let _ = std::fs::create_dir_all(dir);
        }
        let _ = crate::paths::write_atomic(path, &self.bytes());
    }
}

const NUMERIC: [&str; 9] = ["ticks", "seen", "night_until", "sig", "idle", "sstep", "rstep", "compacts", "clear"];
const TEXT: [&str; 7] = ["session", "sessions", "transcript", "halt", "end", "relay", "csession"];

/// `g_<name>='<value>'` with a known name and an allowed value, else None.
fn valid_line(line: &str) -> Option<(&str, &str)> {
    let rest = line.strip_prefix("g_")?;
    let (name, v) = rest.split_once("='")?;
    let value = v.strip_suffix('\'')?;
    let numeric = NUMERIC.contains(&name)
        || matches!(name, "base_A" | "base_B" | "base_C" | "base_R")
        || name.strip_prefix("jobs_").is_some_and(|s| s.bytes().all(|b| b.is_ascii_lowercase()));
    let ok = if numeric { value.bytes().all(|b| b.is_ascii_digit()) } else { TEXT.contains(&name) && !value.contains(['\'', '$', '`']) };
    ok.then_some((name, value))
}

#[cfg(test)]
mod tests {
    use super::valid_line;

    #[test]
    fn validates_like_the_sh_guard() {
        assert!(valid_line("g_ticks='10'").is_some());
        assert!(valid_line("g_jobs_key='12'").is_some());
        assert!(valid_line("g_halt='no progress in 6 turns'").is_some());
        assert!(valid_line("g_ticks='1a'").is_none());
        assert!(valid_line("g_halt='$x'").is_none());
        assert!(valid_line("g_new='1'").is_none());
        assert!(valid_line("g_ticks='1'\r").is_none());
    }
}
