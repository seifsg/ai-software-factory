//! Git config files read natively: `[section "sub"]`, `key = value`, quotes, escapes, comments, continuation
//! lines and unconditional `include.path`. Keys come back as `section.sub.key` with section and key lowercased.

use std::path::{Path, PathBuf};

/// Parsed entries in file order; a later entry of the same key wins on lookup.
#[derive(Debug, Default, Clone)]
pub struct Config {
    pub entries: Vec<(String, String)>,
    /// A conditional include was seen: its conditions are not evaluated here.
    pub has_include_if: bool,
}

impl Config {
    /// Reads a config file and every file its `include.path` names (depth-limited like Git, 10).
    pub fn load(path: &Path) -> Config {
        let mut c = Config::default();
        c.read(path, 0);
        c
    }

    fn read(&mut self, path: &Path, depth: u8) {
        let Ok(text) = std::fs::read(path) else { return };
        let mut section = String::new();
        for (key, value) in parse(&String::from_utf8_lossy(&text), &mut section) {
            if key.starts_with("includeif.") {
                self.has_include_if = true;
            }
            if key == "include.path" && depth < 10 {
                let inc = resolve_include(path, &value);
                self.read(&inc, depth + 1);
            }
            self.entries.push((key, value));
        }
    }

    /// Last value of a key, e.g. `branch.main.remote`.
    pub fn get(&self, key: &str) -> Option<&str> {
        self.entries.iter().rev().find(|(k, _)| k == key).map(|(_, v)| v.as_str())
    }

    /// Every value of a key in file order (multi-valued keys such as `remote.origin.fetch`).
    pub fn all<'a>(&'a self, key: &'a str) -> impl Iterator<Item = &'a str> + 'a {
        self.entries.iter().filter(move |(k, _)| k == key).map(|(_, v)| v.as_str())
    }

    /// True when any `remote.<name>.*` key exists: what `git remote` lists.
    pub fn has_remote(&self) -> bool {
        self.entries.iter().any(|(k, _)| k.starts_with("remote.") && k.matches('.').count() >= 2)
    }

    /// A boolean key as Git reads it (`true`, `yes`, `on`, `1`; a bare key is true).
    pub fn bool(&self, key: &str) -> bool {
        matches!(self.get(key).map(str::to_ascii_lowercase).as_deref(), Some("true" | "yes" | "on" | "1" | ""))
    }
}

/// An include path, relative to the including file's folder, `~/` from home.
fn resolve_include(from: &Path, v: &str) -> PathBuf {
    if let Some(rest) = v.strip_prefix("~/") {
        return crate::paths::home().join(rest);
    }
    let p = PathBuf::from(v);
    if p.is_absolute() || crate::paths::is_abs(v) { p } else { from.parent().unwrap_or(Path::new(".")).join(p) }
}

/// Parses config text into `(section.sub.key, value)` pairs.
fn parse(text: &str, section: &mut String) -> Vec<(String, String)> {
    let mut out = Vec::new();
    let mut lines = text.lines();
    while let Some(raw) = lines.next() {
        let line = raw.trim_start();
        if line.is_empty() || line.starts_with('#') || line.starts_with(';') {
            continue;
        }
        if line.starts_with('[') {
            *section = header(line);
            continue;
        }
        let (name, rest) = match line.find('=') {
            Some(i) => (line[..i].trim(), Some(&line[i + 1..])),
            None => (line.split(['#', ';']).next().unwrap_or("").trim(), None),
        };
        if name.is_empty() || section.is_empty() {
            continue;
        }
        let mut value = String::new();
        if let Some(mut r) = rest.map(str::to_string) {
            // A value ending in an unescaped backslash continues on the next line.
            while ends_continued(&r) {
                r.pop();
                match lines.next() {
                    Some(n) => r.push_str(n),
                    None => break,
                }
            }
            value = unquote(&r);
        }
        out.push((format!("{}.{}", section, name.to_ascii_lowercase()), value));
    }
    out
}

/// True when the value ends in a backslash that is not itself escaped.
fn ends_continued(r: &str) -> bool {
    let trailing = r.bytes().rev().take_while(|&b| b == b'\\').count();
    trailing % 2 == 1
}

/// `[core]` → `core`; `[remote "origin"]` → `remote.origin`; `[branch.main]` (old form) → `branch.main`.
fn header(line: &str) -> String {
    let inner = line[1..].split(']').next().unwrap_or("");
    match inner.find('"') {
        Some(q) => {
            let name = inner[..q].trim().to_ascii_lowercase();
            let sub = inner[q + 1..].trim_end().trim_end_matches('"').replace("\\\"", "\"").replace("\\\\", "\\");
            format!("{name}.{sub}")
        }
        None => {
            let t = inner.trim();
            match t.find('.') {
                Some(d) => format!("{}.{}", t[..d].to_ascii_lowercase(), &t[d + 1..]),
                None => t.to_ascii_lowercase(),
            }
        }
    }
}

/// A raw value: quotes removed, escapes `\" \\ \n \t \b` applied, comments outside quotes dropped, trimmed.
fn unquote(r: &str) -> String {
    let mut out = String::new();
    let mut quoted = false;
    let mut chars = r.trim().chars().peekable();
    let mut pending_space = String::new();
    while let Some(c) = chars.next() {
        match c {
            '"' => quoted = !quoted,
            '\\' => {
                out.push_str(&pending_space);
                pending_space.clear();
                match chars.next() {
                    Some('n') => out.push('\n'),
                    Some('t') => out.push('\t'),
                    Some('b') => {
                        out.pop();
                    }
                    Some(o) => out.push(o),
                    None => {}
                }
            }
            '#' | ';' if !quoted => break,
            ' ' | '\t' if !quoted => pending_space.push(c),
            _ => {
                out.push_str(&pending_space);
                pending_space.clear();
                out.push(c);
            }
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_sections_and_values() {
        let mut s = String::new();
        let v = parse(
            "[remote \"origin\"]\n\turl = https://x/y.git ; c\n[branch \"main\"]\n\tremote = origin\n\tmerge = \"refs/heads/main\"\n",
            &mut s,
        );
        assert_eq!(v[0], ("remote.origin.url".into(), "https://x/y.git".into()));
        assert_eq!(v[2], ("branch.main.merge".into(), "refs/heads/main".into()));
    }
}
