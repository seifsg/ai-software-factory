//! The outside agent's command line: read-only, a pinned headless browser, an allowlist without code-running tools.

use super::pick::{Agent, Vendor};
use crate::paths::{quiet_command, text};
use std::path::Path;
use std::process::Command;

/// Pinned: `@latest` re-resolves on every cold start and can miss the MCP startup timeout.
const MCP: &str = "@playwright/mcp@0.0.86";
/// The only browser tools the agent gets. Left out on purpose: `browser_run_code_unsafe` (runs Node, wrote files
/// outside the Codex sandbox in a live test), `browser_file_upload`, `browser_install`.
const TOOLS: [&str; 18] = [
    "browser_navigate",
    "browser_navigate_back",
    "browser_click",
    "browser_type",
    "browser_fill_form",
    "browser_select_option",
    "browser_press_key",
    "browser_hover",
    "browser_drag",
    "browser_snapshot",
    "browser_take_screenshot",
    "browser_evaluate",
    "browser_console_messages",
    "browser_network_requests",
    "browser_wait_for",
    "browser_resize",
    "browser_handle_dialog",
    "browser_tabs",
];
/// Startup wait for the browser server: a first `npx` download is slow.
const MCP_START_SECS: u32 = 120;
/// Claude only: turn and spend caps (Codex has neither flag; the timeout bounds it).
const MAX_TURNS: &str = "80";
const MAX_USD: &str = "3";

/// One ready-to-spawn job: the command and the brief for its stdin.
pub struct Job {
    pub command: Command,
    pub brief: String,
}

/// Builds the outside agent's command for `url`, running inside the absolute report folder `out`.
pub fn build(agent: &Agent, npx: &Path, out: &Path, url: &str) -> Result<Job, String> {
    let npx = text(npx);
    let o = text(out);
    let mut c = quiet_command(&agent.path);
    match agent.vendor {
        Vendor::Codex => codex(&mut c, &npx, &o),
        Vendor::Claude => claude(&mut c, &npx, out)?,
    }
    scrub(&mut c);
    c.current_dir(out);
    let brief = include_str!("brief.md").replace("{URL}", url);
    Ok(Job { command: c, brief })
}

/// Playwright MCP's own arguments; shots and snapshots stay in the report folder.
fn mcp_args(o: &str) -> [&str; 7] {
    ["-y", MCP, "--headless", "--isolated", "--output-dir", o, "--viewport-size=1440x900"]
}

/// `codex exec`, read-only sandbox, the brief on stdin, the last message to `agent.md`.
fn codex(c: &mut Command, npx: &str, o: &str) {
    let toml = |items: &[&str]| format!("[{}]", items.iter().map(|s| format!("'{s}'")).collect::<Vec<_>>().join(","));
    let set = |k: &str, v: String| ["-c".to_string(), format!("mcp_servers.pw.{k}={v}")];
    c.args(["exec", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config", "-s", "read-only", "-C", o]);
    c.args(["-c", "model_reasoning_effort=medium"]);
    c.args(set("command", format!("'{npx}'")));
    c.args(set("args", toml(&mcp_args(o))));
    c.args(set("required", "true".into()));
    c.args(set("startup_timeout_sec", MCP_START_SECS.to_string()));
    c.args(set("tool_timeout_sec", "60".into()));
    c.args(set("default_tools_approval_mode", "approve".into()));
    c.args(set("enabled_tools", toml(&TOOLS)));
    c.args(["-o", &format!("{o}/agent.md"), "-"]);
}

/// `claude -p`, no built-in tools, only the allowlisted browser tools, JSON result on stdout.
/// `--restricted` skips the owner's settings files (so their plugins and hooks), and the settings file turns off
/// any hook left: a live run otherwise answered the factory's own Stop hook instead of reporting.
fn claude(c: &mut Command, npx: &str, out: &Path) -> Result<(), String> {
    let o = text(out);
    let write = |name: &str, json: serde_json::Value| {
        let file = out.join(name);
        std::fs::write(&file, json.to_string()).map(|()| text(&file)).map_err(|e| format!("cannot write {}: {e}", text(&file)))
    };
    let mcp = write("mcp.json", serde_json::json!({ "mcpServers": { "pw": { "command": npx, "args": mcp_args(&o) } } }))?;
    let settings = write("settings.json", serde_json::json!({ "disableAllHooks": true }))?;
    let allowed = TOOLS.iter().map(|t| format!("mcp__pw__{t}")).collect::<Vec<_>>().join(",");
    c.args(["-p", "--model", "sonnet", "--restricted", "--settings", &settings, "--strict-mcp-config", "--mcp-config", &mcp]);
    c.args(["--tools", "", "--allowedTools", &allowed, "--permission-mode", "dontAsk"]);
    c.args(["--max-turns", MAX_TURNS, "--max-budget-usd", MAX_USD, "--no-session-persistence", "--output-format", "json"]);
    c.env("MCP_TIMEOUT", (MCP_START_SECS * 1000).to_string());
    Ok(())
}

/// Drops the host agent's session variables: a nested CLI would bind to the host's session or rename MCP tools.
/// Keeps `CODEX_HOME` and `CLAUDE_CONFIG_DIR`: they say where the login lives.
fn scrub(c: &mut Command) {
    for (k, _) in std::env::vars_os() {
        let key = k.to_string_lossy();
        let host = key.starts_with("CLAUDE") || key.starts_with("CODEX_");
        if host && key != "CODEX_HOME" && key != "CLAUDE_CONFIG_DIR" {
            c.env_remove(&k);
        }
    }
}
