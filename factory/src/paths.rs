//! Paths and clock: native paths in the `C:/x` form the agent's tools read, the cache folder, file ages.

use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

/// A path as text with forward slashes; on Windows an MSYS form `/c/x` becomes `C:/x`.
/// Why: replies name paths the agent opens with native tools, and Git Bash spellings mean nothing there.
pub fn norm(p: &str) -> String {
    let s = p.replace('\\', "/");
    if cfg!(windows) {
        let b = s.as_bytes();
        if b.len() >= 2 && b[0] == b'/' && b[1].is_ascii_alphabetic() && (b.len() == 2 || b[2] == b'/') {
            let rest = if b.len() == 2 { "/" } else { &s[2..] };
            return format!("{}:{}", (b[1] as char).to_ascii_uppercase(), rest);
        }
    }
    s
}

/// Path text of a native path, normalized by [`norm`].
pub fn text(p: &Path) -> String {
    norm(&p.to_string_lossy())
}

/// True for an absolute path in either spelling (`/x` or `C:/x`).
pub fn is_abs(p: &str) -> bool {
    let b = p.as_bytes();
    b.first() == Some(&b'/') || (b.len() >= 3 && b[0].is_ascii_alphabetic() && b[1] == b':' && b[2] == b'/')
}

/// The user's home: `HOME`, else `USERPROFILE` (native Windows hosts set no HOME).
pub fn home() -> PathBuf {
    std::env::var_os("HOME")
        .filter(|v| !v.is_empty())
        .or_else(|| std::env::var_os("USERPROFILE"))
        .map(|v| PathBuf::from(norm(&v.to_string_lossy())))
        .unwrap_or_default()
}

/// `${XDG_CACHE_HOME:-$HOME/.cache}/ai-software-factory`: session links, the release cache, doctor backups.
pub fn cache_dir() -> PathBuf {
    let base = std::env::var_os("XDG_CACHE_HOME")
        .filter(|v| !v.is_empty())
        .map(|v| PathBuf::from(norm(&v.to_string_lossy())))
        .unwrap_or_else(|| home().join(".cache"));
    base.join("ai-software-factory")
}

/// Seconds since the Unix epoch.
pub fn now() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0)
}

/// Modification time in nanoseconds since the epoch, or None when the file is missing.
pub fn mtime_ns(p: &Path) -> Option<u128> {
    std::fs::metadata(p).ok()?.modified().ok().map(ns)
}

/// A system time as nanoseconds since the epoch (0 before it).
pub fn ns(t: SystemTime) -> u128 {
    t.duration_since(UNIX_EPOCH).map(|d| d.as_nanos()).unwrap_or(0)
}

/// Age of a file in whole seconds, or None when it is missing.
pub fn age_secs(p: &Path) -> Option<u64> {
    let m = mtime_ns(p)? / 1_000_000_000;
    Some(now().saturating_sub(m as u64))
}

/// Writes a file through a temporary sibling and a rename, so a reader never sees half of it.
pub fn write_atomic(p: &Path, data: &[u8]) -> std::io::Result<()> {
    let tmp = p.with_extension(format!("tmp{}", std::process::id()));
    std::fs::write(&tmp, data)?;
    std::fs::rename(&tmp, p).inspect_err(|_| {
        let _ = std::fs::remove_file(&tmp);
    })
}

/// Empties a file and sets its mtime to now, as sh `: > file` does. Why: on Windows a write of no bytes to
/// an empty file keeps its old mtime, and the loop guard compares that mtime with the run file's.
pub fn touch(p: &Path) {
    if let Ok(f) = std::fs::File::create(p) {
        let _ = f.set_modified(SystemTime::now());
    }
}
