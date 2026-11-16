//! `update-check`: at session start, says when a newer factory release exists (from a cached version, no
//! network on this path) and what `doctor` finds; refreshes the cache in a detached background process.
//! `FACTORY_NO_UPDATE_CHECK` turns both off.

use crate::paths;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

const SLUG: &str = "seifsg/ai-software-factory";

/// The session-start text: leftovers first, then the release notice. Empty when there is nothing to say.
/// `refresh` starts the background fetch of the latest release (off in tests that must stay offline).
pub fn check(root: &Path, refresh: bool) -> String {
    if std::env::var_os("FACTORY_NO_UPDATE_CHECK").is_some_and(|v| !v.is_empty()) {
        return String::new();
    }
    let mut out = String::new();
    let (lines, left) = crate::doctor::run(root, false);
    if left && !lines.is_empty() {
        out.push_str(&format!(
            "Factory leftovers on this machine:\n{}\nTell the owner in one line and offer what each line says, owner's OK first (`{} doctor --fix` moves leftovers to a backup). Never stop or wait for it.\n",
            lines.join("\n"),
            crate::guard::exe()
        ));
    }
    let manifest = root.join(".claude-plugin/plugin.json");
    let Ok(text) = std::fs::read_to_string(&manifest) else { return out };
    let Some(have) = manifest_version(&text) else { return out };
    let cache = paths::cache_dir();
    if refresh {
        spawn_refresh();
    }
    let new = std::fs::read_to_string(cache.join("latest")).ok().and_then(|t| t.lines().next().map(String::from)).unwrap_or_default();
    if let (Some(h), Some(n)) = (plain(&have), plain(&new)) {
        if new != have && n > h {
            out.push_str(&notice(&new, &have));
        }
    }
    out
}

/// The first `"version": "<v>"` value of a manifest, as the sh reader took it (first line holding it).
fn manifest_version(text: &str) -> Option<String> {
    let l = text.lines().find(|l| l.contains("\"version\""))?;
    let after = &l[l.find("\"version\"")? + 9..];
    let v = after.split('"').nth(1)?;
    (!v.is_empty()).then(|| v.to_string())
}

/// `x.y.z` as numbers; None for anything else (pre-releases and odd tags stay quiet).
fn plain(v: &str) -> Option<(u64, u64, u64)> {
    if v.is_empty() || !v.bytes().all(|b| b.is_ascii_digit() || b == b'.') || !v.as_bytes()[0].is_ascii_digit() {
        return None;
    }
    let mut it = v.split('.');
    let (a, b, c) = (it.next()?, it.next()?, it.next()?);
    Some((a.parse().ok()?, b.parse().ok()?, c.parse().unwrap_or(0)))
}

fn notice(new: &str, have: &str) -> String {
    format!(
        "AI Software Factory {new} is out (installed {have}). Before any factory run, tell the owner and ask: update now or continue? What is new: https://github.com/{SLUG}/releases/tag/v{new}. Update: Claude Code `claude plugin update safe-factory@ai-software-factory`, Codex `codex plugin marketplace upgrade ai-software-factory` (clone timed out: `codex plugin marketplace remove ai-software-factory`, `codex plugin marketplace add https://github.com/{SLUG}.git --sparse .claude-plugin --sparse .agents`, `codex plugin add safe-factory@ai-software-factory`, then trust the hooks in `/hooks`), Cursor: Marketplace installs update by themselves; team imports once an admin enables Auto Refresh; a GitHub install has no proven update path, see docs/install.md. Then start a new session.\n"
    )
}

/// Starts `factory update-check --refresh` detached, so the hook returns at once.
fn spawn_refresh() {
    let Ok(exe) = std::env::current_exe() else { return };
    let mut c = Command::new(exe);
    c.args(["update-check", "--refresh"]).stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null());
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        c.creation_flags(0x0000_0008 | 0x0800_0000); // DETACHED_PROCESS | CREATE_NO_WINDOW
        keep_std_handles();
    }
    let _ = c.spawn();
}

/// Marks this process's stdin, stdout and stderr not inheritable. Why: Windows hands every inheritable
/// handle to a child, so the background fetch would hold the host's hook pipe open and the host would wait
/// on it (up to the fetch's 20 s) before it reads this hook's reply.
#[cfg(windows)]
fn keep_std_handles() {
    use std::ffi::c_void;
    unsafe extern "system" {
        fn GetStdHandle(n: u32) -> *mut c_void;
        fn SetHandleInformation(h: *mut c_void, mask: u32, flags: u32) -> i32;
    }
    const HANDLE_FLAG_INHERIT: u32 = 1;
    for n in [-10i32, -11, -12] {
        // SAFETY: GetStdHandle takes any STD_* id; SetHandleInformation only changes the flag of a handle
        // this process owns, and a null or invalid handle makes it fail without effect.
        unsafe {
            let h = GetStdHandle(n as u32);
            if !h.is_null() && h as isize != -1 {
                SetHandleInformation(h, HANDLE_FLAG_INHERIT, 0);
            }
        }
    }
}

/// The background fetch: the release marked Latest through `gh`, else `curl`, each cut at 20 s; written only
/// on success through its own temp file and a rename. Temp files a killed fetch left are swept after a minute.
fn refresh() {
    let cache = paths::cache_dir();
    if std::fs::create_dir_all(&cache).is_err() {
        return;
    }
    sweep(&cache);
    let tag = run_for(Command::new("gh").args(["api", &format!("repos/{SLUG}/releases/latest"), "--jq", ".tag_name"]))
        .filter(|t| !t.trim().is_empty())
        .or_else(|| {
            run_for(Command::new("curl").args(["-fsm", "20", &format!("https://api.github.com/repos/{SLUG}/releases/latest")]))
                .and_then(|body| tag_name(&body))
        })
        .unwrap_or_default();
    let v = tag.trim().strip_prefix('v').unwrap_or("").to_string();
    if v.is_empty() {
        return;
    }
    let tmp = cache.join(format!("latest.{}", std::process::id()));
    if std::fs::write(&tmp, format!("{v}\n")).is_ok() && std::fs::rename(&tmp, cache.join("latest")).is_err() {
        let _ = std::fs::remove_file(&tmp);
    }
}

/// `"tag_name": "<v>"` from the API's JSON (any spacing).
fn tag_name(body: &str) -> Option<String> {
    serde_json::from_str::<serde_json::Value>(body).ok()?.get("tag_name")?.as_str().map(String::from)
}

/// Runs a command for at most 20 s; its stdout on success.
fn run_for(c: &mut Command) -> Option<String> {
    let mut child = c.stdin(Stdio::null()).stdout(Stdio::piped()).stderr(Stdio::null()).spawn().ok()?;
    let start = Instant::now();
    loop {
        match child.try_wait() {
            Ok(Some(s)) => {
                let mut out = String::new();
                use std::io::Read;
                child.stdout.take()?.read_to_string(&mut out).ok()?;
                return s.success().then_some(out);
            }
            Ok(None) if start.elapsed() < Duration::from_secs(20) => std::thread::sleep(Duration::from_millis(50)),
            _ => {
                let _ = child.kill();
                return None;
            }
        }
    }
}

fn sweep(cache: &Path) {
    let Ok(rd) = std::fs::read_dir(cache) else { return };
    for e in rd.flatten() {
        let name = e.file_name().to_string_lossy().into_owned();
        if name.starts_with("latest.") && name.len() > 7 && paths::age_secs(&e.path()).is_some_and(|a| a > 60) {
            let _ = std::fs::remove_file(e.path());
        }
    }
}

/// `factory update-check [<plugin root>]`; `--refresh` is the background fetch it starts.
pub fn cli(args: &[&str]) -> u8 {
    if args == ["--refresh"] {
        refresh();
        return 0;
    }
    let root = args.first().map(|r| PathBuf::from(paths::norm(r))).unwrap_or_else(crate::doctor::plugin_root);
    print!("{}", check(&root, true));
    0
}
