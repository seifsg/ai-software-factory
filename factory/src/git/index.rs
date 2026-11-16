//! The Git index (versions 2, 3, 4) read natively, and the tree id it describes (what `git write-tree` prints).

use sha1_smol::Sha1;

/// One stage-0 index entry.
#[derive(Debug, Clone)]
pub struct Entry {
    pub mode: u32,
    pub sha: [u8; 20],
    pub path: Vec<u8>,
}

/// Parses an index file into its stage-0 entries, in index order.
/// Errors name what this reader refuses (split or sparse indexes) so callers fail loudly.
pub fn parse(data: &[u8]) -> Result<Vec<Entry>, String> {
    if data.len() < 12 || &data[..4] != b"DIRC" {
        return Err("not a Git index".into());
    }
    let version = be32(data, 4);
    if !(2..=4).contains(&version) {
        return Err(format!("index version {version} not supported"));
    }
    let count = be32(data, 8) as usize;
    let mut out = Vec::with_capacity(count);
    let mut at = 12;
    let mut prev: Vec<u8> = Vec::new();
    for _ in 0..count {
        let fixed = data.get(at..at + 62).ok_or("index entry cut short")?;
        let mode = be32(fixed, 24);
        let mut sha = [0u8; 20];
        sha.copy_from_slice(&fixed[40..60]);
        let flags = u16::from_be_bytes([fixed[60], fixed[61]]);
        let mut p = at + 62;
        let mut skip = false;
        if flags & 0x4000 != 0 {
            let ext = u16::from_be_bytes([*data.get(p).ok_or("cut")?, *data.get(p + 1).ok_or("cut")?]);
            skip = ext & 0x2000 != 0; // intent-to-add: never in a written tree
            if ext & 0x4000 != 0 && mode == 0o040000 {
                return Err("sparse index not supported".into());
            }
            p += 2;
        }
        let path = if version == 4 {
            let (strip, n) = varint(data, p)?;
            p += n;
            let end = p + data[p..].iter().position(|&b| b == 0).ok_or("path not ended")?;
            let keep = prev.len().checked_sub(strip).ok_or("bad path prefix")?;
            let mut full = prev[..keep].to_vec();
            full.extend_from_slice(&data[p..end]);
            at = end + 1;
            full
        } else {
            let end = p + data[p..].iter().position(|&b| b == 0).ok_or("path not ended")?;
            let path = data[p..end].to_vec();
            at += (end - at + 8) & !7; // entries pad with 1 to 8 NULs to a multiple of 8
            path
        };
        prev.clone_from(&path);
        if (flags >> 12) & 3 == 0 && !skip {
            out.push(Entry { mode, sha, path });
        }
    }
    if data[at..].windows(4).next() == Some(b"link") {
        return Err("split index not supported".into());
    }
    Ok(out)
}

/// The id of the tree these entries describe, built like `git write-tree` (no object is written).
pub fn tree_id(entries: &[Entry]) -> String {
    let (sha, _) = build(entries, 0, b"");
    super::object::to_hex(&sha)
}

/// Builds the tree for entries under `prefix` starting at `i`; returns its sha and the next index.
fn build(entries: &[Entry], mut i: usize, prefix: &[u8]) -> ([u8; 20], usize) {
    let mut body = Vec::new();
    while i < entries.len() && entries[i].path.starts_with(prefix) {
        let rest = &entries[i].path[prefix.len()..];
        match rest.iter().position(|&b| b == b'/') {
            Some(slash) => {
                let name = &rest[..slash];
                let mut sub = prefix.to_vec();
                sub.extend_from_slice(name);
                sub.push(b'/');
                let (sha, next) = build(entries, i, &sub);
                body.extend_from_slice(b"40000 ");
                body.extend_from_slice(name);
                body.push(0);
                body.extend_from_slice(&sha);
                i = next;
            }
            None => {
                body.extend_from_slice(format!("{:o} ", entries[i].mode).as_bytes());
                body.extend_from_slice(rest);
                body.push(0);
                body.extend_from_slice(&entries[i].sha);
                i += 1;
            }
        }
    }
    (hash_object("tree", &body), i)
}

/// SHA-1 of a Git object: `<kind> <len>\0<body>`.
pub fn hash_object(kind: &str, body: &[u8]) -> [u8; 20] {
    let mut h = Sha1::new();
    h.update(format!("{kind} {}\0", body.len()).as_bytes());
    h.update(body);
    h.digest().bytes()
}

fn be32(d: &[u8], at: usize) -> u32 {
    u32::from_be_bytes([d[at], d[at + 1], d[at + 2], d[at + 3]])
}

/// Index v4 prefix length: Git's offset varint.
fn varint(d: &[u8], mut at: usize) -> Result<(usize, usize), String> {
    let start = at;
    let mut c = *d.get(at).ok_or("cut")?;
    let mut v = (c & 0x7f) as usize;
    while c & 0x80 != 0 {
        at += 1;
        c = *d.get(at).ok_or("cut")?;
        v = ((v + 1) << 7) | (c & 0x7f) as usize;
    }
    Ok((v, at - start + 1))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_tree_id_matches_git() {
        assert_eq!(tree_id(&[]), "4b825dc642cb6eb9a060e54bf8d69288fbee4904");
    }
}
