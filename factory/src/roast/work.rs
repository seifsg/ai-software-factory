//! The outside agent's working folder: a fresh temp folder outside every project, moved into the report folder after.
//! Why: started inside a project, the agent CLI loads that project's rules and hooks (a live run answered the
//! factory's own Stop hook instead of writing its report). Outside, it sees only the brief.

use crate::paths::text;
use std::fs;
use std::path::{Path, PathBuf};

/// A temp folder removed when dropped.
pub struct Work(PathBuf);

impl Work {
    pub fn new() -> Result<Self, String> {
        let dir = std::env::temp_dir().join(format!("factory-roast-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).map_err(|e| format!("cannot create {}: {e}", text(&dir)))?;
        Ok(Self(PathBuf::from(clean(&dir)?)))
    }

    pub fn path(&self) -> &Path {
        &self.0
    }

    /// Moves every file the agent left into `out` (copy then delete: temp and project may be on different drives).
    pub fn collect(&self, out: &Path) -> Result<(), String> {
        for entry in fs::read_dir(&self.0).map_err(|e| format!("cannot read {}: {e}", text(&self.0)))?.flatten() {
            let from = entry.path();
            if from.is_file() {
                let to = out.join(entry.file_name());
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

/// An absolute path as forward-slash text, refused when it holds a quote or newline (it goes into TOML and JSON).
pub fn clean(p: &Path) -> Result<String, String> {
    let abs = std::path::absolute(p).map_err(|e| format!("cannot resolve {}: {e}", text(p)))?;
    let s = text(&abs);
    if s.contains(['\'', '"', '\n', '\r']) {
        return Err(format!("path has a quote or newline: {s}"));
    }
    Ok(s)
}
