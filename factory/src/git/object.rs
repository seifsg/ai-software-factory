//! Git objects read natively: loose (zlib) and packed (idx v2, deltas), with alternates.
//! Only what receipts need: find a commit by sha prefix and read its body.

use super::Repo;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Kind {
    Commit,
    Tree,
    Blob,
    Tag,
}

/// Object folders: the repo's, then each alternate's.
fn object_dirs(repo: &Repo) -> Vec<PathBuf> {
    let main = repo.common.join("objects");
    let mut dirs = vec![main.clone()];
    if let Ok(text) = std::fs::read_to_string(main.join("info/alternates")) {
        for l in text.lines().map(str::trim).filter(|l| !l.is_empty() && !l.starts_with('#')) {
            let p = PathBuf::from(crate::paths::norm(l));
            dirs.push(if p.is_absolute() || crate::paths::is_abs(l) { p } else { main.join(p) });
        }
    }
    dirs
}

/// The unique full sha starting with `prefix`, across loose objects and pack indexes.
pub fn resolve(repo: &Repo, prefix: &str) -> Option<String> {
    let p = prefix.to_ascii_lowercase();
    if p.len() < 4 || p.len() > 40 || !p.bytes().all(|b| b.is_ascii_hexdigit()) {
        return None;
    }
    let mut found: Vec<String> = Vec::new();
    for dir in object_dirs(repo) {
        if let Ok(rd) = std::fs::read_dir(dir.join(&p[..2])) {
            for e in rd.flatten() {
                let name = e.file_name().to_string_lossy().into_owned();
                let full = format!("{}{}", &p[..2], name);
                if name.len() == 38 && full.starts_with(&p) {
                    found.push(full);
                }
            }
        }
        for idx in pack_indexes(&dir) {
            if let Some(i) = Index::open(&idx) {
                found.extend(i.with_prefix(&p));
            }
        }
    }
    found.sort();
    found.dedup();
    (found.len() == 1).then(|| found.remove(0))
}

/// Reads an object's kind and body by full sha.
pub fn read(repo: &Repo, sha: &str) -> Option<(Kind, Vec<u8>)> {
    let dirs = object_dirs(repo);
    for dir in &dirs {
        if let Some(o) = read_loose(&dir.join(&sha[..2]).join(&sha[2..])) {
            return Some(o);
        }
    }
    let raw = hex(sha)?;
    for dir in &dirs {
        for idx in pack_indexes(dir) {
            if let Some(off) = Index::open(&idx).and_then(|i| i.offset(&raw)) {
                let mut pack = Pack { file: std::fs::File::open(idx.with_extension("pack")).ok()? };
                return unpack(repo, &mut pack, off, 0);
            }
        }
    }
    None
}

/// A loose object: zlib of `<kind> <size>\0<body>`.
fn read_loose(p: &Path) -> Option<(Kind, Vec<u8>)> {
    let z = std::fs::read(p).ok()?;
    let data = miniz_oxide::inflate::decompress_to_vec_zlib(&z).ok()?;
    let nul = data.iter().position(|&b| b == 0)?;
    let kind = match data[..nul].split(|&b| b == b' ').next()? {
        b"commit" => Kind::Commit,
        b"tree" => Kind::Tree,
        b"blob" => Kind::Blob,
        b"tag" => Kind::Tag,
        _ => return None,
    };
    Some((kind, data[nul + 1..].to_vec()))
}

fn pack_indexes(objects: &Path) -> Vec<PathBuf> {
    std::fs::read_dir(objects.join("pack"))
        .map(|rd| rd.flatten().map(|e| e.path()).filter(|p| p.extension().is_some_and(|x| x == "idx")).collect())
        .unwrap_or_default()
}

/// A pack index, version 2.
struct Index {
    data: Vec<u8>,
    count: usize,
}

impl Index {
    fn open(p: &Path) -> Option<Index> {
        let data = std::fs::read(p).ok()?;
        (data.len() > 8 + 1024 && data[..4] == [0xff, b't', b'O', b'c'] && be32(&data, 4) == 2).then_some(())?;
        let count = be32(&data, 8 + 255 * 4) as usize;
        Some(Index { data, count })
    }

    fn sha(&self, i: usize) -> &[u8] {
        let at = 8 + 1024 + i * 20;
        &self.data[at..at + 20]
    }

    /// Index range of shas whose first byte is `b`.
    fn bucket(&self, b: u8) -> (usize, usize) {
        let lo = if b == 0 { 0 } else { be32(&self.data, 8 + (b as usize - 1) * 4) as usize };
        (lo, be32(&self.data, 8 + b as usize * 4) as usize)
    }

    fn offset(&self, raw: &[u8; 20]) -> Option<u64> {
        let (mut lo, mut hi) = self.bucket(raw[0]);
        let i = loop {
            if lo >= hi {
                return None;
            }
            let mid = (lo + hi) / 2;
            match self.sha(mid).cmp(raw) {
                std::cmp::Ordering::Less => lo = mid + 1,
                std::cmp::Ordering::Greater => hi = mid,
                std::cmp::Ordering::Equal => break mid,
            }
        };
        let base = 8 + 1024 + self.count * 24;
        let off = be32(&self.data, base + i * 4);
        if off & 0x8000_0000 == 0 {
            return Some(off as u64);
        }
        let large = base + self.count * 4 + (off & 0x7fff_ffff) as usize * 8;
        Some(((be32(&self.data, large) as u64) << 32) | be32(&self.data, large + 4) as u64)
    }

    fn with_prefix(&self, p: &str) -> Vec<String> {
        let first = u8::from_str_radix(&p[..2], 16).unwrap_or(0);
        let (lo, hi) = self.bucket(first);
        (lo..hi).map(|i| to_hex(self.sha(i))).filter(|s| s.starts_with(p)).collect()
    }
}

/// An open pack file, read in windows: packs can be far larger than the objects the guard needs.
struct Pack {
    file: std::fs::File,
}

impl Pack {
    /// Up to `len` bytes from `off` (fewer at the end of the file).
    fn window(&mut self, off: u64, len: usize) -> Option<Vec<u8>> {
        use std::io::{Read, Seek, SeekFrom};
        self.file.seek(SeekFrom::Start(off)).ok()?;
        let mut buf = Vec::with_capacity(len);
        (&mut self.file).take(len as u64).read_to_end(&mut buf).ok()?;
        Some(buf)
    }

    /// The zlib stream at `off`, inflated to exactly `size` bytes; the window doubles until it holds the stream.
    fn inflate(&mut self, off: u64, size: usize) -> Option<Vec<u8>> {
        let mut len = (size + 64).max(4096);
        loop {
            let z = self.window(off, len)?;
            if let Ok(out) = miniz_oxide::inflate::decompress_to_vec_zlib_with_limit(&z, size.max(1)) {
                return (out.len() == size).then_some(out);
            }
            if z.len() < len {
                return None;
            }
            len *= 2;
        }
    }
}

/// Reads the object at `off` in a pack, applying OFS and REF deltas (depth-limited).
fn unpack(repo: &Repo, pack: &mut Pack, off: u64, depth: u8) -> Option<(Kind, Vec<u8>)> {
    if depth > 50 {
        return None;
    }
    let head = pack.window(off, 32)?;
    let mut i = 0;
    let mut c = *head.get(i)?;
    let t = (c >> 4) & 7;
    let mut size = (c & 15) as usize;
    let mut shift = 4;
    while c & 0x80 != 0 {
        i += 1;
        c = *head.get(i)?;
        size |= ((c & 0x7f) as usize) << shift;
        shift += 7;
    }
    i += 1;
    match t {
        1..=4 => {
            let kind = [Kind::Commit, Kind::Tree, Kind::Blob, Kind::Tag][t as usize - 1];
            Some((kind, pack.inflate(off + i as u64, size)?))
        }
        6 => {
            let mut c = *head.get(i)?;
            let mut rel = (c & 0x7f) as u64;
            while c & 0x80 != 0 {
                i += 1;
                c = *head.get(i)?;
                rel = ((rel + 1) << 7) | (c & 0x7f) as u64;
            }
            let delta = pack.inflate(off + i as u64 + 1, size)?;
            let (kind, base) = unpack(repo, pack, off.checked_sub(rel)?, depth + 1)?;
            Some((kind, apply_delta(&base, &delta)?))
        }
        7 => {
            let base_sha = to_hex(head.get(i..i + 20)?);
            let delta = pack.inflate(off + i as u64 + 20, size)?;
            let (kind, base) = read(repo, &base_sha)?;
            Some((kind, apply_delta(&base, &delta)?))
        }
        _ => None,
    }
}

/// Git's delta format: base size, result size, then copy and insert opcodes.
fn apply_delta(base: &[u8], d: &[u8]) -> Option<Vec<u8>> {
    let mut i = 0;
    let varint = |i: &mut usize| -> Option<usize> {
        let (mut v, mut s) = (0usize, 0);
        loop {
            let c = *d.get(*i)?;
            *i += 1;
            v |= ((c & 0x7f) as usize) << s;
            s += 7;
            if c & 0x80 == 0 {
                return Some(v);
            }
        }
    };
    (varint(&mut i)? == base.len()).then_some(())?;
    let out_len = varint(&mut i)?;
    let mut out = Vec::with_capacity(out_len);
    while i < d.len() {
        let op = d[i];
        i += 1;
        if op & 0x80 != 0 {
            let (mut off, mut len) = (0usize, 0usize);
            for k in 0..4 {
                if op & (1 << k) != 0 {
                    off |= (*d.get(i)? as usize) << (8 * k);
                    i += 1;
                }
            }
            for k in 0..3 {
                if op & (0x10 << k) != 0 {
                    len |= (*d.get(i)? as usize) << (8 * k);
                    i += 1;
                }
            }
            if len == 0 {
                len = 0x10000;
            }
            out.extend_from_slice(base.get(off..off + len)?);
        } else if op != 0 {
            out.extend_from_slice(d.get(i..i + op as usize)?);
            i += op as usize;
        } else {
            return None;
        }
    }
    (out.len() == out_len).then_some(out)
}

fn be32(d: &[u8], at: usize) -> u32 {
    u32::from_be_bytes([d[at], d[at + 1], d[at + 2], d[at + 3]])
}

/// Lowercase hex of bytes.
pub fn to_hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

/// 20 raw bytes of a 40-hex sha.
pub fn hex(s: &str) -> Option<[u8; 20]> {
    let mut out = [0u8; 20];
    (s.len() == 40).then_some(())?;
    for (k, o) in out.iter_mut().enumerate() {
        *o = u8::from_str_radix(&s[2 * k..2 * k + 2], 16).ok()?;
    }
    Some(out)
}
