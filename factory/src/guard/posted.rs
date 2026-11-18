//! The block a coordinator just posted in chat, read back from its session transcript, so `guard step` needs no
//! second copy on stdin: the newest assistant text that holds the step's heading (or a todo's `T<k> pre:` line).
//! Reads Claude Code (`message.content[].text`) and Codex (`payload.content[].output_text`) transcript lines.
//! Only a post newer than `since` counts, so a stale transcript or a block not posted again never gets written.

use serde_json::Value;
use std::path::Path;

/// The posted block for `label` (`3`, `2b`, `T1`): from its heading line up to the next step heading in the same
/// text item, or the todo line alone. None when the transcript is unreadable or holds no such post at or after
/// `since` (`YYYY-MM-DDTHH:MM:SS`, UTC; lines carry ISO `timestamp`s, compared as text).
pub fn block(transcript: &Path, label: &str, heading: &str, since: &str) -> Option<String> {
    let bytes = std::fs::read(transcript).ok()?;
    let text = String::from_utf8_lossy(&bytes);
    for l in text.lines().rev().filter(|l| l.contains("assistant")) {
        let Ok(v) = serde_json::from_str::<Value>(l) else { continue };
        // Only dated lines count: hosts also write undated request records quoting assistant messages, which
        // are never taken (a stale copy) and never end the scan; the first dated line older than `since` does.
        let Some(t) = v["timestamp"].as_str().and_then(|ts| ts.get(..19)) else { continue };
        if t < since {
            return None;
        }
        if let Some(b) = texts(&v).into_iter().rev().find_map(|t| cut(&t, label, heading)) {
            return Some(b);
        }
    }
    None
}

/// The current Claude Code session's transcript (`CLAUDE_CODE_SESSION_ID` under the projects folder), if any.
pub fn own_transcript() -> Option<std::path::PathBuf> {
    let id = std::env::var("CLAUDE_CODE_SESSION_ID").ok().filter(|s| !s.is_empty() && !s.contains(['/', '\\', '.']))?;
    let base = std::env::var_os("CLAUDE_CONFIG_DIR").map_or_else(|| crate::paths::home().join(".claude"), std::path::PathBuf::from);
    std::fs::read_dir(base.join("projects")).ok()?.flatten().map(|d| d.path().join(format!("{id}.jsonl"))).find(|p| p.is_file())
}

/// Assistant text items of one transcript line, in order; empty for any other line.
fn texts(v: &Value) -> Vec<String> {
    let msg = if v["message"]["role"] == "assistant" { &v["message"] } else if v["payload"]["role"] == "assistant" { &v["payload"] } else { return Vec::new() };
    let Some(items) = msg["content"].as_array() else { return Vec::new() };
    items
        .iter()
        .filter(|c| c["type"] == "text" || c["type"] == "output_text")
        .filter_map(|c| c["text"].as_str().map(String::from))
        .collect()
}

/// The block for `label` inside one text item.
fn cut(t: &str, label: &str, heading: &str) -> Option<String> {
    let lines: Vec<&str> = t.lines().collect();
    if label.starts_with('T') {
        let pre = format!("{label} pre:");
        return lines.iter().rev().find(|l| l.starts_with(&pre)).map(|l| l.to_string());
    }
    let start = lines.iter().rposition(|l| l.starts_with(heading))?;
    let end = lines[start + 1..].iter().position(|l| is_step_heading(l)).map_or(lines.len(), |e| start + 1 + e);
    let block = lines[start..end].join("\n");
    Some(block.trim_end().to_string())
}

/// `## <0-8>[b] ` opens a step block.
fn is_step_heading(l: &str) -> bool {
    let Some(r) = l.strip_prefix("## ") else { return false };
    let b = r.as_bytes();
    matches!(b.first(), Some(b'0'..=b'8')) && (b.get(1) == Some(&b' ') || (b.get(1) == Some(&b'b') && b.get(2) == Some(&b' ')))
}

#[cfg(test)]
mod tests {
    use super::*;

    const S: &str = "2026-11-18T05:59:59";

    fn write(name: &str, lines: &[&str]) -> std::path::PathBuf {
        let p = std::env::temp_dir().join(format!("posted-{}-{name}.jsonl", std::process::id()));
        std::fs::write(&p, lines.join("\n") + "\n").unwrap();
        p
    }

    #[test]
    fn takes_the_newest_post_up_to_the_next_step_heading() {
        let p = write("newest", &[
            r###"{"timestamp":"2026-11-18T06:00:00.000Z","type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"## 3 Plan\nold"}]}}"###,
            r###"{"type":"user","message":{"role":"user","content":"## 3 Plan\nnot mine"}}"###,
            r###"{"timestamp":"2026-11-18T06:00:00.000Z","type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"## 3 Plan\n**Files:** a\n\n## 4 Before\nb"},{"type":"tool_use","input":{"command":"## 3 Plan\nstdin copy"}}]}}"###,
        ]);
        assert_eq!(block(&p, "3", "## 3 Plan", S).as_deref(), Some("## 3 Plan\n**Files:** a"));
        assert_eq!(block(&p, "4", "## 4 Before", S).as_deref(), Some("## 4 Before\nb"));
        assert_eq!(block(&p, "5", "## 5 Build", S), None);
        let _ = std::fs::remove_file(p);
    }

    #[test]
    fn an_older_post_never_counts() {
        let p = write("old", &[r###"{"timestamp":"2026-11-18T06:00:00.000Z","message":{"role":"assistant","content":[{"type":"text","text":"## 3 Plan\nold"}]}}"###]);
        assert_eq!(block(&p, "3", "## 3 Plan", "2026-11-18T06:00:01"), None);
        assert!(block(&p, "3", "## 3 Plan", "2026-11-18T06:00:00").is_some());
        let _ = std::fs::remove_file(p);
    }

    #[test]
    fn undated_request_records_after_the_post_do_not_stop_the_scan() {
        let p = write("blob", &[
            r###"{"timestamp":"2026-11-18T06:00:00.000Z","message":{"role":"assistant","content":[{"type":"text","text":"## 3 Plan\nnew"}]}}"###,
            r###"{"timestamp":"2026-11-18T06:00:01.000Z","type":"user","message":{"role":"user","content":[{"type":"tool_result","content":"ok"}]}}"###,
            r###"{"type":"api-request-blob","sessionId":"s","hash":"h","message":{"role":"assistant","content":[{"type":"text","text":"## 3 Plan\nold"}]}}"###,
        ]);
        assert_eq!(block(&p, "3", "## 3 Plan", S).as_deref(), Some("## 3 Plan\nnew"));
        // An undated copy alone is never taken.
        let q = write("blob-only", &[r###"{"type":"api-request-blob","message":{"role":"assistant","content":[{"type":"text","text":"## 3 Plan\nold"}]}}"###]);
        assert_eq!(block(&q, "3", "## 3 Plan", S), None);
        let _ = std::fs::remove_file(q);
        let _ = std::fs::remove_file(p);
    }

    #[test]
    fn reads_codex_lines_and_todo_lines() {
        let p = write("codex", &[r###"{"timestamp":"2026-11-18T06:00:00.000Z","type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"done\nT2 pre: a do: b post: c"}]}}"###]);
        assert_eq!(block(&p, "T2", "", S).as_deref(), Some("T2 pre: a do: b post: c"));
        assert_eq!(block(&p, "T1", "", S), None);
        let _ = std::fs::remove_file(p);
    }

    #[test]
    fn a_2b_heading_is_not_step_2() {
        let p = write("2b", &[r###"{"timestamp":"2026-11-18T06:00:00.000Z","message":{"role":"assistant","content":[{"type":"text","text":"## 2 Recommend\nx\n## 2b Challenge\ny"}]}}"###]);
        assert_eq!(block(&p, "2", "## 2 Recommend", S).as_deref(), Some("## 2 Recommend\nx"));
        assert_eq!(block(&p, "2b", "## 2b Challenge", S).as_deref(), Some("## 2b Challenge\ny"));
        let _ = std::fs::remove_file(p);
    }
}
