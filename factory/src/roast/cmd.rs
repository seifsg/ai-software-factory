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
/// Codex features turned off: its shell (it could read any file and the browser could send it out) and the
/// desktop app's own browser and computer use.
const NO_FEATURES: [&str; 5] = ["shell_tool", "unified_exec", "browser_use", "computer_use", "in_app_browser"];
/// Host variables a nested CLI keeps: where its login lives, or the login itself.
const LOGIN_VARS: [&str; 6] = ["CODEX_HOME", "CODEX_API_KEY", "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX"];
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

/// Builds the outside agent's command for `url`, working in the folder `out`; the browser may load only `origin`.
pub fn build(agent: &Agent, npx: &Path, out: &Path, url: &str, origin: &str) -> Result<Job, String> {
    let npx = super::work::clean(npx)?;
    let o = text(out);
    let pw = mcp_args(&o, origin);
    let mut c = quiet_command(&agent.path);
    match agent.vendor {
        Vendor::Codex => codex(&mut c, &npx, &o, &pw),
        Vendor::Claude => claude(&mut c, &npx, out, &pw)?,
    }
    scrub(&mut c);
    c.current_dir(out);
    let brief = include_str!("brief.md").replace("{URL}", url);
    Ok(Job { command: c, brief })
}

/// Playwright MCP's own arguments: shots and snapshots stay in the work folder, requests stay on the app's origin
/// (a guard against a steered agent sending data elsewhere; Playwright itself calls it no security boundary).
fn mcp_args<'a>(o: &'a str, origin: &'a str) -> [&'a str; 9] {
    ["-y", MCP, "--headless", "--isolated", "--output-dir", o, "--viewport-size=1440x900", "--allowed-origins", origin]
}

/// `codex exec`, read-only sandbox, no shell (a live probe answered "NO SHELL"), no desktop browser or computer use:
/// the browser tools above are all it has. Brief on stdin, last message to `agent.md`.
fn codex(c: &mut Command, npx: &str, o: &str, pw: &[&str]) {
    let toml = |items: &[&str]| format!("[{}]", items.iter().map(|s| format!("'{s}'")).collect::<Vec<_>>().join(","));
    let set = |k: &str, v: String| ["-c".to_string(), format!("mcp_servers.pw.{k}={v}")];
    c.args(["exec", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config", "-s", "read-only", "-C", o]);
    for feature in NO_FEATURES {
        c.args(["--disable", feature]);
    }
    c.args(["-c", "model_reasoning_effort=medium"]);
    c.args(set("command", format!("'{npx}'")));
    c.args(set("args", toml(pw)));
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
fn claude(c: &mut Command, npx: &str, out: &Path, pw: &[&str]) -> Result<(), String> {
    let write = |name: &str, json: serde_json::Value| {
        let file = out.join(name);
        std::fs::write(&file, json.to_string()).map(|()| text(&file)).map_err(|e| format!("cannot write {}: {e}", text(&file)))
    };
    let mcp = write("mcp.json", serde_json::json!({ "mcpServers": { "pw": { "command": npx, "args": pw} } }))?;
    let settings = write("settings.json", serde_json::json!({ "disableAllHooks": true }))?;
    let allowed = TOOLS.iter().map(|t| format!("mcp__pw__{t}")).collect::<Vec<_>>().join(",");
    c.args(["-p", "--model", "sonnet", "--restricted", "--settings", &settings, "--strict-mcp-config", "--mcp-config", &mcp]);
    c.args(["--tools", "", "--allowedTools", &allowed, "--permission-mode", "dontAsk"]);
    c.args(["--max-turns", MAX_TURNS, "--max-budget-usd", MAX_USD, "--no-session-persistence", "--output-format", "json"]);
    c.env("MCP_TIMEOUT", (MCP_START_SECS * 1000).to_string());
    Ok(())
}

/// Drops the host agent's session variables: a nested CLI would bind to the host's session or rename MCP tools.
/// Keeps the ones that say where or how the login lives. The login check runs with the same env as the roast.
pub(super) fn scrub(c: &mut Command) {
    for (k, _) in std::env::vars_os() {
        let key = k.to_string_lossy();
        let host = key.starts_with("CLAUDE") || key.starts_with("CODEX_");
        if host && !LOGIN_VARS.contains(&key.as_ref()) {
            c.env_remove(&k);
        }
    }
}
