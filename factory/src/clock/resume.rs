//! When a waiting session came back: the first transcript entry after the wait that the session or its owner
//! wrote (Claude Code `user`/`assistant` lines, Codex `user_message`/`response_item`). Hook and system lines do not count.

use std::io::{Read, Seek, SeekFrom};

/// How much of a transcript's end is read: a resume sits in the last turns, and transcripts grow to many MB.
const TAIL: u64 = 4 << 20;

/// Unix seconds of the first counted entry strictly after `after`, if the transcript holds one.
pub fn first_after(transcript: &str, after: u64) -> Option<u64> {
    if transcript.is_empty() {
        return None;
    }
    let mut f = std::fs::File::open(crate::paths::norm(transcript)).ok()?;
    let len = f.metadata().ok()?.len();
    f.seek(SeekFrom::Start(len.saturating_sub(TAIL))).ok()?;
    let mut buf = Vec::new();
    f.read_to_end(&mut buf).ok()?;
    buf.split(|&b| b == b'\n').filter(|l| counted(l)).filter_map(timestamp).find(|t| *t > after)
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
    use super::first_after;

    #[test]
    fn skips_hook_lines_and_entries_before_the_wait() {
        let p = std::env::temp_dir().join(format!("factory-resume-{}.jsonl", std::process::id()));
        let lines = [
            r#"{"type":"assistant","timestamp":"2026-11-27T07:42:00.100Z"}"#,
            r#"{"type":"system","subtype":"stop_hook_summary","timestamp":"2026-11-27T07:42:09.000Z"}"#,
            r#"{"type":"user","message":{"content":"yes"},"timestamp":"2026-11-27T07:51:33.500Z"}"#,
            r#"{"timestamp":"2026-11-27T07:52:00.000Z","type":"event_msg","payload":{"type":"user_message"}}"#,
        ];
        std::fs::write(&p, lines.join("\n")).unwrap();
        let wait = super::super::stamp::iso_secs("2026-11-27T07:42:08Z").unwrap();
        let path = crate::paths::text(&p);
        assert_eq!(first_after(&path, wait), super::super::stamp::iso_secs("2026-11-27T07:51:33Z"));
        assert_eq!(first_after(&path, wait + 3600), None);
        assert_eq!(first_after("", wait), None);
        let _ = std::fs::remove_file(p);
    }
}
