//! When a waiting session came back: the first transcript entry after the wait that the session or its owner
//! wrote (Claude Code `user`/`assistant` lines, Codex `user_message`/`response_item`). Hook and system lines do not count.

use std::io::{BufRead, BufReader, Seek, SeekFrom};

/// The transcript's length now: where a wait stamped now starts its later resume search (0 when unreadable).
pub fn len(transcript: &str) -> u64 {
    if transcript.is_empty() { 0 } else { std::fs::metadata(crate::paths::norm(transcript)).map_or(0, |m| m.len()) }
}

/// Unix seconds of the first counted entry strictly after `after`, read from byte `from` on (the file's start
/// when `from` is past its end: a rewritten transcript). Stops at the first match, so a long turn after the
/// resume costs nothing.
pub fn first_after(transcript: &str, after: u64, from: u64) -> Option<u64> {
    if transcript.is_empty() {
        return None;
    }
    let mut f = std::fs::File::open(crate::paths::norm(transcript)).ok()?;
    let start = if from <= f.metadata().ok()?.len() { from } else { 0 };
    f.seek(SeekFrom::Start(start)).ok()?;
    let mut lines = BufReader::with_capacity(1 << 16, f);
    let mut line = Vec::new();
    loop {
        line.clear();
        if lines.read_until(b'\n', &mut line).ok()? == 0 {
            return None;
        }
        if counted(&line)
            && let Some(t) = timestamp(&line).filter(|t| *t > after)
        {
            return Some(t);
        }
    }
}

fn counted(line: &[u8]) -> bool {
    const KINDS: [&[u8]; 4] = [b"\"type\":\"user\"", b"\"type\":\"assistant\"", b"\"user_message\"", b"\"response_item\""];
    KINDS.iter().any(|k| memchr::memmem::find(line, k).is_some())
}

fn timestamp(line: &[u8]) -> Option<u64> {
    const KEY: &[u8] = b"\"timestamp\":\"";
    let at = memchr::memmem::find(line, KEY)? + KEY.len();
    let iso = std::str::from_utf8(line.get(at..at + 19)?).ok()?;
    super::stamp::iso_secs(iso)
}

#[cfg(test)]
mod tests {
    use super::{first_after, len};

    #[test]
    fn skips_hook_lines_and_entries_before_the_wait_and_starts_at_the_offset() {
        let p = std::env::temp_dir().join(format!("factory-resume-{}.jsonl", std::process::id()));
        let lines = [
            r#"{"type":"assistant","timestamp":"2026-11-27T07:42:00.100Z"}"#,
            r#"{"type":"system","subtype":"stop_hook_summary","timestamp":"2026-11-27T07:42:09.000Z"}"#,
            r#"{"type":"user","message":{"content":"yes"},"timestamp":"2026-11-27T07:51:33.500Z"}"#,
            r#"{"timestamp":"2026-11-27T07:52:00.000Z","type":"event_msg","payload":{"type":"user_message"}}"#,
        ];
        std::fs::write(&p, lines.join("\n")).unwrap();
        let iso = super::super::stamp::iso_secs;
        let wait = iso("2026-11-27T07:42:08Z").unwrap();
        let path = crate::paths::text(&p);
        assert_eq!(first_after(&path, wait, 0), iso("2026-11-27T07:51:33Z"));
        // From the offset of the Codex line on, the Claude reply before it is never read.
        let off = (lines[..3].join("\n").len() + 1) as u64;
        assert_eq!(first_after(&path, wait, off), iso("2026-11-27T07:52:00Z"));
        assert_eq!(first_after(&path, wait, len(&path) + 99), iso("2026-11-27T07:51:33Z"));
        assert_eq!(first_after(&path, wait + 3600, 0), None);
        assert_eq!((first_after("", wait, 0), len("")), (None, 0));
        let _ = std::fs::remove_file(p);
    }
}
