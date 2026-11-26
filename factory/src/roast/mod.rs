//! `factory roast`: another vendor's agent CLI plays the worst user on a running web app and roasts it.
//! Why: a second model in a real browser finds what the builder's own checks miss. Default on at step 6;
//! `FACTORY_ROAST=0` turns it off. One receipt line on stdout; the report and shots land in `<out>`.

mod cmd;
mod pick;
mod report;
mod reuse;
mod run;
mod tree;
mod url;
mod work;

pub use pick::{Vendor, order};
pub use report::{Verdict, parse};
pub use url::{host, is_local};

use crate::paths::text;
use std::path::PathBuf;
use std::time::Duration;

const USAGE: &str = "usage: factory roast <url> <out folder> [--cli codex|claude] [--inert <glob>]...";
/// Hard cap on the outside agent, seconds; `FACTORY_ROAST_SECS` overrides.
const SECS: u64 = 600;
/// Roasts running at once on this machine, across sessions; `FACTORY_ROAST_SLOTS` overrides.
const SLOTS: u64 = 2;

/// The parsed command line.
struct Opts<'a> {
    url: &'a str,
    out: PathBuf,
    cli: Option<Vendor>,
    /// Paths the app never serves (`docs/**`): a later tree changing only these keeps this roast.
    inert: Vec<&'a str>,
}

/// Entry point for `factory roast`. Exit 0 with a verdict or a SKIP line, 1 when the run is INCOMPLETE, 2 on usage.
pub fn cli(args: &[&str]) -> u8 {
    let o = match parse_args(args) {
        Ok(o) => o,
        Err(why) => {
            eprintln!("{why}{USAGE}");
            return 2;
        }
    };
    match roast(&o) {
        Ok(line) => {
            println!("{line}");
            u8::from(line.contains(" INCOMPLETE "))
        }
        Err(skip) => {
            println!("SKIP {skip}");
            0
        }
    }
}

/// `<url> <out>`, then `--cli <name>` at most once and `--inert <glob>` any number of times.
fn parse_args<'a>(args: &[&'a str]) -> Result<Opts<'a>, String> {
    let [url, out, rest @ ..] = args else { return Err(String::new()) };
    let (mut rest, mut cli, mut inert) = (rest, None, Vec::new());
    while !rest.is_empty() {
        match rest {
            ["--cli", name, tail @ ..] if cli.is_none() => (cli, rest) = (Some(Vendor::named(name).ok_or("")?), tail),
            ["--inert", glob, tail @ ..] => {
                crate::receipt::carry::check_glob(glob).map_err(|e| format!("{e}\n"))?;
                inert.push(*glob);
                rest = tail;
            }
            _ => return Err(String::new()),
        }
    }
    (!url.is_empty() && !out.is_empty()).then(|| Opts { url, out: PathBuf::from(out), cli, inert }).ok_or_else(String::new)
}

/// Runs one roast, or reuses the last one when the app has not changed since. `Err` is a skip reason: nothing
/// ran, the caller goes on.
fn roast(o: &Opts) -> Result<String, String> {
    gate(o.url)?;
    let here = std::env::current_dir().map_err(|e| format!("cannot read the current folder: {e}"))?;
    let stand = reuse::stand(&here);
    if let Some((repo, tree)) = stand.as_ref().filter(|_| !env_is("FACTORY_ROAST_FRESH", "1"))
        && let Some(line) = reuse::find(&o.out, o.url, o.cli.map(Vendor::name), &o.inert, repo, tree)
    {
        return Ok(line);
    }
    let npx = pick::find("npx").ok_or("npx not found: the browser needs Node.js")?;
    let agent = pick::choose(o.cli)?;
    let secs = env_number("FACTORY_ROAST_SECS", SECS, 1, 86_400)?;
    let slots = env_number("FACTORY_ROAST_SLOTS", SLOTS, 1, 16)?;
    std::fs::create_dir_all(&o.out).map_err(|e| format!("cannot create {}: {e}", text(&o.out)))?;
    let out = PathBuf::from(work::clean(&o.out)?);
    reuse::forget(&out)?;
    // Waits inside this call while other sessions' roasts fill every slot: no polling turns, no tokens.
    let _place = crate::queue::hold("roast", slots as usize, &["factory", "roast", o.url])?;
    let work = work::Work::new()?;
    let job = cmd::build(&agent, &npx, work.path(), o.url)?;
    let done = run::run(job, Duration::from_secs(secs), work.path())?;
    // The agent ran: from here a failure is INCOMPLETE (exit 1), never a SKIP.
    let name = agent.vendor.name();
    // `forget` again after the copy: a `roast.txt` the agent wrote itself must never stand as the record.
    let finished = report::finish(agent.vendor, work.path(), &done).and_then(|r| work.collect(&out).and_then(|()| reuse::forget(&out)).map(|()| r));
    Ok(match finished {
        Ok((verdict, n)) => {
            let line = format!("roast {name} {} {n} findings {}s {}", verdict.token(), done.secs, text(&out.join("roast.md")));
            if let (Some((_, tree)), false) = (&stand, verdict == Verdict::Incomplete)
                && let Err(e) = reuse::save(&out, o.url, tree, &o.inert, &line)
            {
                eprintln!("factory roast: {e}; the next roast runs again");
            }
            line
        }
        Err(e) => format!("roast {name} {} 0 findings {}s ({e})", Verdict::Incomplete.token(), done.secs),
    })
}

/// `Err` (a skip reason) when roasting is off or the URL is not one to roast.
/// Other hosts than this machine need `FACTORY_ROAST_ANY_HOST=1`: an env prefix, so the plain command an allow rule
/// lets through can never reach a shared or live site.
fn gate(url: &str) -> Result<(), String> {
    if env_is("FACTORY_ROAST", "0") {
        return Err("off (FACTORY_ROAST=0)".into());
    }
    host(url).ok_or_else(|| format!("{url} is not a plain http(s) URL"))?;
    if !env_is("FACTORY_ROAST_ANY_HOST", "1") && !is_local(url) {
        return Err(format!("{url} is not a local URL (localhost, 127.x, ::1, .localhost, .test); FACTORY_ROAST_ANY_HOST=1 allows it"));
    }
    Ok(())
}

fn env_is(key: &str, value: &str) -> bool {
    std::env::var(key).is_ok_and(|v| v == value)
}

/// An env number in `lo..=hi`, `default` when unset; a bad value is named, never replaced silently.
fn env_number(key: &str, default: u64, lo: u64, hi: u64) -> Result<u64, String> {
    let value = std::env::var(key).ok();
    crate::machine::number(value.as_deref(), default, lo, hi).ok_or_else(|| format!("{key} must be a number from {lo} to {hi}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn args() {
        let ok = |a: &[&str]| parse_args(a).is_ok();
        assert!(ok(&["http://localhost:3000", "o"]));
        assert!(parse_args(&["http://localhost:3000", "o", "--cli", "codex"]).is_ok_and(|o| o.cli == Some(Vendor::Codex)));
        assert!(parse_args(&["u", "o", "--inert", "docs/**", "--cli", "claude", "--inert", "*.md"]).is_ok_and(|o| o.inert == ["docs/**", "*.md"]));
        for bad in [&["http://localhost:3000"][..], &["u", "o", "--cli"], &["u", "o", "--cli", "cursor"], &["u", "o", "--any-host"], &["", "o"]] {
            assert!(!ok(bad), "{bad:?}");
        }
        assert!(!ok(&["u", "o", "--cli", "codex", "--cli", "claude"]));
        assert!(parse_args(&["u", "o", "--inert", "**"]).is_err_and(|e| e.contains("matches every path")));
        assert!(parse_args(&["u", "o", "--inert", "src/**"]).is_err_and(|e| e.contains("source paths")));
    }
}
