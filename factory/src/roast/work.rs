//! The outside agent's working folder: a fresh temp folder outside every project, copied into the report folder after.
//! Why: started inside a project, the agent CLI loads that project's rules and hooks (a live run answered the
//! factory's own Stop hook instead of writing its report). Outside, it sees only the brief.

use crate::paths::text;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

/// A temp folder this process created itself, removed when dropped.
pub struct Work(PathBuf);

impl Work {
    /// Creates a new folder under a fresh name; never reuses one that exists (on a shared `/tmp` another
    /// user could have planted it, or a symlink in its place). Owner-only on Unix.
    pub fn new() -> Result<Self, String> {
        let base = std::env::temp_dir();
        for attempt in 0..8u32 {
            let dir = base.join(format!("factory-roast-{}-{:016x}", std::process::id(), nonce(attempt)));
            match create(&dir) {
                Ok(()) => return Ok(Self(PathBuf::from(clean(&dir)?))),
                Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
                Err(e) => return Err(format!("cannot create {}: {e}", text(&dir))),
            }
        }
        Err(format!("cannot create a fresh work folder in {}", text(&base)))
    }

    pub fn path(&self) -> &Path {
        &self.0
    }

    /// Copies the regular files the agent left into `out` (temp and project may sit on different drives).
    /// Symlinks and folders are skipped: the agent must not pull files from elsewhere into the project.
    pub fn collect(&self, out: &Path) -> Result<(), String> {
        for entry in fs::read_dir(&self.0).map_err(|e| format!("cannot read {}: {e}", text(&self.0)))?.flatten() {
            if entry.file_type().is_ok_and(|t| t.is_file()) {
                let (from, to) = (entry.path(), out.join(entry.file_name()));
                // A symlink planted at the target would redirect the write: replace it, never follow it.
                if fs::symlink_metadata(&to).is_ok_and(|m| m.file_type().is_symlink()) {
                    fs::remove_file(&to).map_err(|e| format!("cannot replace the symlink {}: {e}", text(&to)))?;
                }
                fs::copy(&from, &to).map_err(|e| format!("cannot copy {} to {}: {e}", text(&from), text(&to)))?;
            }
        }
        Ok(())
    }
}

impl Drop for Work {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

/// Fails with `AlreadyExists` when anything (folder, file, symlink) has the name.
fn create(dir: &Path) -> std::io::Result<()> {
    let b = fs::DirBuilder::new();
    #[cfg(unix)]
    let b = {
        let mut b = b;
        std::os::unix::fs::DirBuilderExt::mode(&mut b, 0o700);
        b
    };
    b.create(dir)
}

/// Clock nanoseconds mixed with the attempt and a stack address: a fresh name per try; safety comes from never reusing one.
fn nonce(attempt: u32) -> u64 {
    let nanos = SystemTime::now().duration_since(UNIX_EPOCH).map_or(0, |d| d.as_nanos() as u64);
    let addr = &attempt as *const u32 as u64;
    (nanos ^ addr.rotate_left(32) ^ u64::from(attempt)).wrapping_mul(0x9E37_79B9_7F4A_7C15)
}

/// An absolute path as forward-slash text, refused when it holds a quote or newline (it goes into TOML and JSON).
pub fn clean(p: &Path) -> Result<String, String> {
    let abs = std::path::absolute(p).map_err(|e| format!("cannot resolve {}: {e}", text(p)))?;
    let s = text(&abs);
    if s.contains(['\'', '"', '\n', '\r']) {
        return Err(format!("path has a quote or newline: {s}"));
    }
    Ok(s)
}
