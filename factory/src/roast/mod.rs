//! `factory roast`: another vendor's agent CLI plays the worst user on a running web app and roasts it.
//! Why: a second model in a real browser finds what the builder's own checks miss. Default on at step 6;
//! `FACTORY_ROAST=0` turns it off. One receipt line on stdout; the report and shots land in `<out>`.

mod cmd;
mod pick;
mod report;
mod run;
mod url;
mod work;

pub use pick::{Vendor, order};
pub use report::{Verdict, parse};
pub use url::{host, is_local};

use crate::paths::text;
use std::path::PathBuf;
use std::time::Duration;

const USAGE: &str = "usage: factory roast <url> <out folder> [--cli codex|claude]";
/// Hard cap on the outside agent, seconds; `FACTORY_ROAST_SECS` overrides.
const SECS: u64 = 600;

/// The parsed command line.
struct Opts<'a> {
    url: &'a str,
    out: PathBuf,
    cli: Option<Vendor>,
}

/// Entry point for `factory roast`. Exit 0 with a verdict or a SKIP line, 1 when the run is INCOMPLETE, 2 on usage.
pub fn cli(args: &[&str]) -> u8 {
    let Some(o) = parse_args(args) else {
        eprintln!("{USAGE}");
        return 2;
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

fn parse_args<'a>(args: &[&'a str]) -> Option<Opts<'a>> {
    let (url, out, cli) = match args {
        [url, out] => (url, out, None),
        [url, out, "--cli", name] => (url, out, Some(Vendor::named(name)?)),
        _ => return None,
    };
    (!url.is_empty() && !out.is_empty()).then(|| Opts { url, out: PathBuf::from(out), cli })
}

/// Runs one roast. `Err` is a skip reason: nothing ran, the caller goes on.
/// Other hosts than this machine need `FACTORY_ROAST_ANY_HOST=1`: an env prefix, so the plain command an allow rule
/// lets through can never reach a shared or live site.
fn roast(o: &Opts) -> Result<String, String> {
    let env = |k: &str, v: &str| std::env::var(k).is_ok_and(|x| x == v);
    if env("FACTORY_ROAST", "0") {
        return Err("off (FACTORY_ROAST=0)".into());
    }
    host(o.url).ok_or_else(|| format!("{} is not a plain http(s) URL", o.url))?;
    if !env("FACTORY_ROAST_ANY_HOST", "1") && !is_local(o.url) {
        return Err(format!("{} is not a local URL (localhost, 127.x, ::1, .localhost, .test); FACTORY_ROAST_ANY_HOST=1 allows it", o.url));
    }
    let npx = pick::find("npx").ok_or("npx not found: the browser needs Node.js")?;
    let agent = pick::choose(o.cli)?;
    std::fs::create_dir_all(&o.out).map_err(|e| format!("cannot create {}: {e}", text(&o.out)))?;
    let out = PathBuf::from(work::clean(&o.out)?);
    let secs = std::env::var("FACTORY_ROAST_SECS").ok().and_then(|s| s.parse().ok()).filter(|&s| s > 0).unwrap_or(SECS);
    let work = work::Work::new()?;
    let job = cmd::build(&agent, &npx, work.path(), o.url)?;
    let done = run::run(job, Duration::from_secs(secs), work.path())?;
    // The agent ran: from here a failure is INCOMPLETE (exit 1), never a SKIP.
    let name = agent.vendor.name();
    Ok(match report::finish(agent.vendor, work.path(), &done).and_then(|r| work.collect(&out).map(|()| r)) {
        Ok((verdict, n)) => format!("roast {name} {} {n} findings {}s {}", verdict.token(), done.secs, text(&out.join("roast.md"))),
        Err(e) => format!("roast {name} {} 0 findings {}s ({e})", report::Verdict::Incomplete.token(), done.secs),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn args() {
        assert!(parse_args(&["http://localhost:3000", "o"]).is_some());
        assert!(parse_args(&["http://localhost:3000", "o", "--cli", "codex"]).is_some_and(|o| o.cli == Some(Vendor::Codex)));
        assert!(parse_args(&["http://localhost:3000"]).is_none());
        assert!(parse_args(&["u", "o", "--cli"]).is_none());
        assert!(parse_args(&["u", "o", "--cli", "cursor"]).is_none());
        assert!(parse_args(&["u", "o", "--any-host"]).is_none());
        assert!(parse_args(&["", "o"]).is_none());
    }
}
