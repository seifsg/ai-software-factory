//! `doctor`: finds what old factory versions and copies left behind (hooks naming removed scripts, old
//! launchers and state, a second Stop guard, an old plugin id, stale copied files), one line each.
//! `--fix` moves each safe item into a dated backup (never deletes) and refreshes stale copies; a config
//! file holding anything else is only reported. Exit 1 while anything is left to do.

use crate::git::{Repo, index};
use crate::paths;
use std::path::{Path, PathBuf};

const OLD: [&str; 5] = ["fast_gate", "run-gate.sh", "skills/safe-engine/", "resolve_bundle", "hooks/windows.cmd"];

struct Doctor {
    fix: bool,
    out: Vec<String>,
    left: bool,
    stamp: String,
    n: u32,
    /// The backup path of the last move (a failed refresh names it).
    last: String,
}

/// Runs the doctor; returns its lines and whether anything is left to do.
pub fn run(root: &Path, fix: bool) -> (Vec<String>, bool) {
    let h = paths::home();
    let p = std::env::var_os("CLAUDE_PROJECT_DIR")
        .filter(|v| !v.is_empty())
        .map(|v| PathBuf::from(paths::norm(&v.to_string_lossy())))
        .unwrap_or_else(crate::guard::cwd);
    let p = if paths::text(&p) == paths::text(&h) { PathBuf::from("/nonexistent") } else { p };
    let x = std::env::var_os("CODEX_HOME")
        .filter(|v| !v.is_empty())
        .map(|v| PathBuf::from(paths::norm(&v.to_string_lossy())))
        .unwrap_or_else(|| h.join(".codex"));
    let mut d = Doctor { fix, out: Vec::new(), left: false, stamp: if fix { stamp() } else { String::new() }, n: 0, last: String::new() };
    for base in [&h, &p] {
        if base.join(".agents/.claude-plugin/plugin.json").is_file() {
            continue;
        }
        let s = base.join(".agents/skills");
        if s.join("safe-engine").is_dir() {
            d.old_dir(&s.join("safe-engine"), "old launcher, now safe-factory");
        }
        if s.join("improve-factory/scripts/resolve_bundle.py").is_file() {
            d.old_dir(&s.join("improve-factory"), "1.x launcher");
        }
    }
    if h.join(".safe-engine").is_dir() {
        d.mv(&h.join(".safe-engine"), "1.x run state and self-updater");
    }
    let on = read(&h.join(".claude/settings.json")).contains("safe-factory@") || cursor_plugin(&h);
    let files = [
        x.join("hooks.json"),
        h.join(".cursor/hooks.json"),
        h.join(".claude/settings.json"),
        p.join(".claude/settings.json"),
        p.join(".claude/settings.local.json"),
        p.join(".codex/hooks.json"),
        p.join(".cursor/hooks.json"),
    ];
    for f in files.iter().filter(|f| hit(&read(f))) {
        let text = read(f);
        if text.contains("safe-engine@ai-software-factory") {
            d.todo(f, "old plugin id enabled: /plugin install safe-factory@ai-software-factory, then delete the safe-engine@ line");
        }
        if OLD.iter().any(|o| text.contains(o)) {
            if only_old_hooks(&text) {
                d.mv(f, "hooks of an old factory version; the plugin brings its own (copied skills: add hooks again, install.md)");
            } else {
                d.todo(f, "hooks of an old factory version; delete entries naming fast_gate, run-gate.sh, skills/safe-engine/ or hooks/windows.cmd");
            }
        } else if on
            && paths::text(f).contains("/.claude/")
            && text.lines().any(|l| l.find("\"command\"").is_some_and(|i| l[i..].contains("run-guard.sh")))
        {
            d.todo(f, "second Stop guard: the plugin already runs it; delete that entry");
        }
    }
    let night = root.join("../tools/night");
    if night.join("codex.rules").is_file() && x.join("rules/factory.rules").is_file() {
        d.stale(&x.join("rules/factory.rules"), &night.join("codex.rules"));
    }
    let hook = pre_push(&p);
    if night.join("pre-push").is_file() && read(&hook).contains("Factory pre-push hook") {
        d.stale(&hook, &night.join("pre-push"));
    }
    (d.out, d.left)
}

impl Doctor {
    fn say(&mut self, f: &Path, msg: &str) {
        self.out.push(format!("{}: {msg}", paths::text(f)));
    }

    fn todo(&mut self, f: &Path, msg: &str) {
        self.left = true;
        self.say(f, msg);
    }

    /// Moves `f` into the backup with --fix, else reports it. False when the move failed.
    fn mv(&mut self, f: &Path, why: &str) -> bool {
        if !self.fix {
            self.todo(f, &format!("{why}; --fix moves it to a backup"));
            return true;
        }
        let b = paths::cache_dir().join("removed").join(&self.stamp);
        let name = f.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
        let t = loop {
            self.n += 1;
            let t = b.join(format!("{}-{name}", self.n));
            if !t.exists() {
                break t;
            }
        };
        self.last = paths::text(&t);
        let ok = std::fs::create_dir_all(&b).is_ok() && move_path(f, &t).is_ok();
        if ok {
            use std::io::Write;
            let line = format!("{}\t{}\n", paths::text(&t), paths::text(f));
            let _ =
                std::fs::OpenOptions::new().create(true).append(true).open(b.join("index")).and_then(|mut i| i.write_all(line.as_bytes()));
            let msg = format!("{why}; moved to {}", paths::text(&t));
            self.say(f, &msg);
        } else {
            self.todo(f, &format!("{why}; move failed"));
        }
        ok
    }

    /// A copy that differs from the plugin's file: --fix backs it up and copies the current one.
    fn stale(&mut self, copy: &Path, src: &Path) {
        if std::fs::read(copy).ok() == std::fs::read(src).ok() {
            return;
        }
        if !self.fix {
            self.todo(copy, &format!("stale copy of {}; --fix refreshes it", paths::text(src)));
            return;
        }
        if self.mv(copy, "stale copy") {
            if std::fs::copy(src, copy).is_ok() {
                self.say(copy, &format!("refreshed from {}", paths::text(src)));
            } else {
                let msg = format!("refresh failed; restore it from {}", self.last);
                self.todo(copy, &msg);
            }
        }
    }

    /// An old folder moves unless Git tracks it; an old factory checkout gets its update command instead.
    fn old_dir(&mut self, dir: &Path, what: &str) {
        let Some(repo) = Repo::discover(dir).filter(|r| tracked(r, dir)) else {
            self.mv(dir, what);
            return;
        };
        if !repo.config.get("remote.origin.url").is_some_and(|u| u.contains("ai-software-factory")) {
            return;
        }
        let text = paths::text(dir);
        let ck = text.rfind("/.agents/").map_or(text.as_str(), |i| &text[..i]).to_string();
        let db = std::fs::read_to_string(repo.common.join("refs/remotes/origin/HEAD"))
            .ok()
            .and_then(|t| t.trim().strip_prefix("ref: refs/remotes/origin/").map(String::from))
            .unwrap_or_else(|| "main".into());
        self.todo(
            Path::new(&ck),
            &format!("old factory checkout (tracks {what}); --fix leaves it: git -C \"{ck}\" switch {db} && git -C \"{ck}\" pull"),
        );
    }
}

/// Git tracks something under `dir` (`git ls-files --error-unmatch .`).
fn tracked(repo: &Repo, dir: &Path) -> bool {
    let rel = paths::text(dir).strip_prefix(&format!("{}/", paths::text(&repo.work))).map(|s| format!("{s}/"));
    let Some(rel) = rel else { return false };
    let data = std::fs::read(repo.gitdir.join("index")).unwrap_or_default();
    // An index this reader refuses (split, sparse) counts as tracked: never move what Git may track.
    !data.is_empty() && index::parse(&data).map_or(true, |e| e.iter().any(|e| e.path.starts_with(rel.as_bytes())))
}

fn read(p: &Path) -> String {
    std::fs::read_to_string(p).unwrap_or_default()
}

/// Any old factory name, a guard script or the old plugin id in a hook file.
fn hit(text: &str) -> bool {
    OLD.iter().any(|o| text.contains(o)) || text.contains("run-guard.sh") || text.contains("safe-engine@")
}

/// A Cursor install of the plugin (it runs the guard too).
fn cursor_plugin(h: &Path) -> bool {
    let root = h.join(".cursor/plugins");
    let level = |d: &Path| {
        std::fs::read_dir(d).map(|rd| rd.flatten().map(|e| e.path()).filter(|p| p.is_dir()).collect::<Vec<_>>()).unwrap_or_default()
    };
    level(&root).iter().any(|a| a.join("safe-factory").is_dir() || level(a).iter().any(|b| b.join("safe-factory").is_dir()))
}

/// A file moves whole only when pretty-printed (2 spaces) and holding nothing but old factory command hooks.
fn only_old_hooks(text: &str) -> bool {
    let (mut n, mut k, mut o, mut nr) = (0, 0, 0, 0);
    for (i, l) in text.lines().enumerate() {
        nr += 1;
        let parts: Vec<&str> = l.split("\"command\":").collect();
        for a in &parts[1..] {
            n += 1;
            if OLD.iter().any(|x| a.contains(x)) {
                k += 1;
            }
        }
        let typed = l.match_indices("\"type\":").any(|(t, _)| {
            let v = l[t + 7..].trim_start_matches(' ');
            v.starts_with('"') && v[1..].chars().next().is_some_and(|c| c != 'c')
        });
        o += i32::from(typed);
        if i == 1 && !l.starts_with("  \"") {
            o += 1;
        }
        if l.starts_with("  \"") && !l.starts_with("  \"hooks\"") && !l.starts_with("  \"version\"") {
            o += 1;
        }
    }
    nr > 2 && n > 0 && n == k && o == 0
}

/// The project's pre-push hook: main checkout or worktree (hooks live in the common folder).
fn pre_push(p: &Path) -> PathBuf {
    let g = p.join(".git");
    let g = if g.is_file() {
        let first = read(&g).lines().next().unwrap_or("").to_string();
        let t = first.strip_prefix("gitdir: ").unwrap_or(&first).to_string();
        let base = PathBuf::from(format!("{t}/../.."));
        if paths::is_abs(&t) { base } else { p.join(base) }
    } else {
        g
    };
    g.join("hooks/pre-push")
}

/// `YYYYMMDD-HHMMSS` in local time is what the sh doctor used; UTC here (no time zone database).
fn stamp() -> String {
    crate::receipt::utc_iso(paths::now()).replace(['-', ':'], "").replace('T', "-").trim_end_matches('Z').to_string()
}

/// `factory doctor [<plugin root>] [--fix]`
pub fn cli(args: &[&str]) -> u8 {
    let fix = args.contains(&"--fix");
    let root = args.iter().rev().find(|a| **a != "--fix").map(|r| PathBuf::from(paths::norm(r))).unwrap_or_else(plugin_root);
    let (lines, left) = run(&root, fix);
    for l in lines {
        println!("{l}");
    }
    u8::from(left)
}

/// The plugin root: the folder above this binary's `scripts/`.
pub fn plugin_root() -> PathBuf {
    std::env::current_exe().ok().and_then(|p| Some(p.parent()?.parent()?.to_path_buf())).unwrap_or_else(|| PathBuf::from("."))
}

/// Moves a file or folder like `mv`: a rename, else (another volume) a copy, then removal of the source.
fn move_path(from: &Path, to: &Path) -> std::io::Result<()> {
    if std::fs::rename(from, to).is_ok() {
        return Ok(());
    }
    copy_all(from, to)?;
    if from.is_dir() { std::fs::remove_dir_all(from) } else { std::fs::remove_file(from) }
}

fn copy_all(from: &Path, to: &Path) -> std::io::Result<()> {
    if !from.is_dir() {
        return std::fs::copy(from, to).map(|_| ());
    }
    std::fs::create_dir_all(to)?;
    for e in std::fs::read_dir(from)? {
        let e = e?;
        copy_all(&e.path(), &to.join(e.file_name()))?;
    }
    Ok(())
}
