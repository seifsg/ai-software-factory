//! Which agent CLI roasts: the other vendor than the host, then the host's own, each only when found and logged in.

use crate::paths::quiet_command;
use std::path::PathBuf;
use std::process::Stdio;
use std::time::Duration;

/// An agent CLI the roast can drive.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Vendor {
    Codex,
    Claude,
}

impl Vendor {
    pub fn name(self) -> &'static str {
        match self {
            Self::Codex => "codex",
            Self::Claude => "claude",
        }
    }

    pub fn named(s: &str) -> Option<Self> {
        [Self::Codex, Self::Claude].into_iter().find(|v| v.name() == s)
    }

    fn other(self) -> Self {
        match self {
            Self::Codex => Self::Claude,
            Self::Claude => Self::Codex,
        }
    }

    /// Env var naming a CLI off PATH (desktop installs); the night tools use the same names.
    fn path_var(self) -> &'static str {
        match self {
            Self::Codex => "FACTORY_CODEX",
            Self::Claude => "FACTORY_CLAUDE",
        }
    }

    /// Exits 0 only when logged in.
    fn status_args(self) -> [&'static str; 2] {
        match self {
            Self::Codex => ["login", "status"],
            Self::Claude => ["auth", "status"],
        }
    }
}

/// A found, logged-in CLI.
pub struct Agent {
    pub vendor: Vendor,
    pub path: PathBuf,
}

/// The host agent from its own env: Codex sets a thread id, Claude Code sets `CLAUDECODE=1`.
fn host() -> Option<Vendor> {
    let set = |k| std::env::var(k).is_ok_and(|v| !v.is_empty());
    if set("CODEX_THREAD_ID") || set("CODEX_SESSION_ID") {
        Some(Vendor::Codex)
    } else if std::env::var("CLAUDECODE").is_ok_and(|v| v == "1") {
        Some(Vendor::Claude)
    } else {
        None
    }
}

/// Try order: a forced CLI alone; else the host's other vendor first, then the host's own; no host: Codex, Claude.
pub fn order(host: Option<Vendor>, forced: Option<Vendor>) -> Vec<Vendor> {
    match (forced, host) {
        (Some(v), _) => vec![v],
        (None, Some(h)) => vec![h.other(), h],
        (None, None) => vec![Vendor::Codex, Vendor::Claude],
    }
}

/// The first CLI in [`order`] that is found and logged in; else every reason, for the SKIP line.
pub fn choose(forced: Option<Vendor>) -> Result<Agent, String> {
    let mut why = Vec::new();
    for vendor in order(host(), forced) {
        match locate(vendor).and_then(|path| logged_in(vendor, path)) {
            Ok(path) => return Ok(Agent { vendor, path }),
            Err(e) => why.push(format!("{}: {e}", vendor.name())),
        }
    }
    Err(format!("no agent CLI ready ({})", why.join("; ")))
}

fn locate(v: Vendor) -> Result<PathBuf, String> {
    match std::env::var_os(v.path_var()).filter(|p| !p.is_empty()) {
        Some(p) => Some(PathBuf::from(p)).filter(|p| p.is_file()).ok_or_else(|| format!("{} is not a file", v.path_var())),
        None => find(v.name()).ok_or_else(|| "not found on PATH".into()),
    }
}

/// Runs the CLI's own login check, at most 10 s; a hung check counts as not logged in.
fn logged_in(v: Vendor, path: PathBuf) -> Result<PathBuf, String> {
    let mut c = quiet_command(&path);
    c.args(v.status_args()).stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null());
    super::cmd::scrub(&mut c);
    match super::run::status_within(c, Duration::from_secs(10)) {
        Some(true) => Ok(path),
        Some(false) => Err(format!("not logged in (`{} {}`)", v.name(), v.status_args().join(" "))),
        None => Err("login check did not answer in 10 s".into()),
    }
}

/// A program on PATH, with Windows' PATHEXT forms (`codex.cmd`, `claude.exe`); `None` when absent.
pub fn find(name: &str) -> Option<PathBuf> {
    let exts: Vec<String> = if cfg!(windows) {
        std::env::var("PATHEXT").unwrap_or_else(|_| ".COM;.EXE;.BAT;.CMD".into()).split(';').filter(|e| !e.is_empty()).map(str::to_ascii_lowercase).collect()
    } else {
        vec![String::new()]
    };
    std::env::split_paths(&std::env::var_os("PATH")?).find_map(|dir| exts.iter().map(|e| dir.join(format!("{name}{e}"))).find(|p| p.is_file()))
}

#[cfg(test)]
mod tests {
    use super::{Vendor::*, order};

    #[test]
    fn other_vendor_first() {
        assert_eq!(order(Some(Claude), None), [Codex, Claude]);
        assert_eq!(order(Some(Codex), None), [Claude, Codex]);
        assert_eq!(order(None, None), [Codex, Claude]);
        assert_eq!(order(Some(Claude), Some(Claude)), [Claude]);
    }
}
