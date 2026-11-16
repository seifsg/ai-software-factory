//! Hook IO: the host's JSON on stdin in, one reply out. Claude Code, Codex and Cursor share the shape.

use serde_json::Value;
use std::io::{Read, Write};

/// One hook event. Fields absent from the JSON read as empty; invalid JSON reads as an empty event.
#[derive(Debug, Default, Clone)]
pub struct Input {
    pub session_id: String,
    pub transcript_path: String,
    pub cwd: String,
    pub last_assistant_message: String,
    pub stop_hook_active: bool,
    pub source: String,
    /// The host reports a running subagent among its background tasks (its result wakes the session).
    pub subagent_running: bool,
    pub hook_event_name: String,
}

impl Input {
    /// Parses the host's JSON. Why lenient: a hook must never fail the host's turn on odd input.
    pub fn parse(bytes: &[u8]) -> Input {
        let v: Value = serde_json::from_slice(bytes).unwrap_or(Value::Null);
        let s = |k: &str| v.get(k).and_then(Value::as_str).unwrap_or_default().to_string();
        let subagent_running = v
            .get("background_tasks")
            .and_then(Value::as_array)
            .is_some_and(|a| a.iter().any(|t| t.get("type").and_then(Value::as_str) == Some("subagent")));
        Input {
            session_id: s("session_id"),
            transcript_path: s("transcript_path"),
            cwd: s("cwd"),
            last_assistant_message: s("last_assistant_message"),
            stop_hook_active: v.get("stop_hook_active").and_then(Value::as_bool).unwrap_or(false),
            source: s("source"),
            subagent_running,
            hook_event_name: s("hook_event_name"),
        }
    }

    /// Reads and parses all of stdin.
    pub fn from_stdin() -> Input {
        let mut buf = Vec::new();
        let _ = std::io::stdin().read_to_end(&mut buf);
        Input::parse(&buf)
    }
}

/// What a hook prints: a block decision, a notice for the owner, or plain context text.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Reply {
    Block(String),
    System(String),
    Text(String),
}

impl Reply {
    /// The exact bytes the host reads, newline included.
    pub fn bytes(&self) -> Vec<u8> {
        match self {
            Reply::Block(r) => format!("{{\"decision\":\"block\",\"reason\":{}}}\n", json_str(r)).into_bytes(),
            Reply::System(m) => format!("{{\"systemMessage\":{}}}\n", json_str(m)).into_bytes(),
            Reply::Text(t) => t.clone().into_bytes(),
        }
    }

    /// The reply text without its JSON wrapper (the plain check line reads it).
    pub fn inner(&self) -> &str {
        match self {
            Reply::Block(s) | Reply::System(s) | Reply::Text(s) => s,
        }
    }

    /// Writes the reply to stdout.
    pub fn print(&self) {
        let mut out = std::io::stdout().lock();
        let _ = out.write_all(&self.bytes());
        let _ = out.flush();
    }
}

/// A JSON string literal; serde escapes only quotes, backslashes and control characters, as hosts expect.
pub fn json_str(s: &str) -> String {
    serde_json::to_string(s).unwrap_or_else(|_| "\"\"".into())
}
