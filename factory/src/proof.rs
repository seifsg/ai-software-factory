//! `proof-hash`: one id for a proof's input files, so an After capture stays valid while its inputs are
//! unchanged. Each file's Git blob id (raw bytes, as `git hash-object --no-filters` gives), then SHA-1 over
//! the sorted `<blob id> <path>` lines.

use crate::git::{index::hash_object, object::to_hex};
use sha1_smol::Sha1;

/// The combined hash of files; an unreadable file is an error, never a skipped input.
pub fn hash(files: &[&str]) -> Result<String, String> {
    hash_in(std::path::Path::new("."), files)
}

/// The same with each path read from `base` (a run folder) and hashed as written.
pub fn hash_in(base: &std::path::Path, files: &[&str]) -> Result<String, String> {
    let mut lines: Vec<String> = Vec::with_capacity(files.len());
    for f in files {
        let data = std::fs::read(base.join(crate::paths::norm(f))).map_err(|e| format!("{f}: {e}"))?;
        let path = crate::paths::norm(f);
        let path = path.strip_prefix("./").unwrap_or(&path).to_string();
        lines.push(format!("{} {path}\n", to_hex(&hash_object("blob", &data))));
    }
    lines.sort_by(|a, b| a[41..].cmp(&b[41..]));
    lines.dedup();
    let mut h = Sha1::new();
    lines.iter().for_each(|l| h.update(l.as_bytes()));
    Ok(h.digest().to_string())
}

/// `factory proof-hash <file>...`
pub fn cli(args: &[&str]) -> u8 {
    if args.is_empty() {
        eprintln!("usage: factory proof-hash <file>...");
        return 2;
    }
    match hash(args) {
        Ok(h) => {
            println!("{h}");
            0
        }
        Err(e) => {
            eprintln!("factory proof-hash: {e}");
            1
        }
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn blob_ids_match_git() {
        let id = super::to_hex(&super::hash_object("blob", b"hello\n"));
        assert_eq!(id, "ce013625030ba8dba906f756967f9e9ca394464a");
    }
}
