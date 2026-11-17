//! Assemble the exact committed diff, common run inputs and explicitly selected proof once.

use crate::git::{Repo, command};
use std::fmt::Write as _;
use std::path::{Component, Path};

#[derive(Default)]
struct Options<'a> {
    base: Option<&'a str>,
    head: Option<&'a str>,
    proof: Vec<&'a str>,
    context: Vec<&'a str>,
}

impl<'a> Options<'a> {
    fn parse(args: &[&'a str]) -> Result<Self, String> {
        let mut options = Self::default();
        let mut pairs = args.chunks_exact(2);
        for pair in &mut pairs {
            let [flag, value] = [pair[0], pair[1]];
            match flag {
                "--base" if options.base.is_none() => options.base = Some(value),
                "--head" if options.head.is_none() => options.head = Some(value),
                "--proof" => options.proof.push(value),
                "--context" => options.context.push(value),
                _ => return Err(format!("unknown or repeated packet option {flag}")),
            }
        }
        if let Some(flag) = pairs.remainder().first() {
            return Err(format!("missing value for {flag}"));
        }
        Ok(options)
    }
}

/// Inputs that can be shared by independent reviewers; no earlier handbacks are read implicitly.
pub(super) fn assemble(args: &[&str]) -> Result<String, String> {
    let options = Options::parse(args)?;
    let repo = Repo::discover(&crate::guard::cwd()).ok_or("not in a Git work tree")?;
    let base = commit(&repo, options.base, "--base")?;
    let head = commit(&repo, options.head, "--head")?;
    let mut out = format!("# Review evidence\n\nBase: {base}\nCandidate: {head}\n\n");
    let ticket = ".factory/ticket.md";
    if repo.work.join(ticket).try_exists().map_err(|e| format!("{ticket}: {e}"))? {
        section(&mut out, ticket, &proof(&repo, ticket)?);
    }
    let run = proof(&repo, ".factory/run.md")?;
    section(&mut out, ".factory/run.md through Build", build_record(&run));
    for file in options.context {
        let path = relative(file)?;
        if path.starts_with(".factory") {
            return Err(format!("{file}: committed context must be outside .factory"));
        }
        let oid_path = format!("{head}:{}", crate::paths::text(&path));
        section(&mut out, file, &git(&repo, &["cat-file", "blob", &oid_path])?);
    }
    let diff = git(
        &repo,
        &[
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--no-color",
            "--no-renames",
            "--ignore-submodules=none",
            "-U2147483647",
            base,
            head,
            "--",
        ],
    )?;
    section(&mut out, "Committed diff with full text context", &diff);
    for file in options.proof {
        section(&mut out, file, &proof(&repo, file)?);
    }
    Ok(out)
}

fn commit<'a>(repo: &Repo, value: Option<&'a str>, flag: &str) -> Result<&'a str, String> {
    let sha = value.ok_or_else(|| format!("{flag} is required"))?;
    if sha.len() != 40 || !sha.bytes().all(|b| b.is_ascii_hexdigit()) || repo.commit_tree(sha).is_none() {
        return Err(format!("{flag} requires a full local commit SHA: {sha}"));
    }
    Ok(sha)
}

fn git(repo: &Repo, args: &[&str]) -> Result<String, String> {
    let out = command(repo).env("GIT_NO_REPLACE_OBJECTS", "1").args(args).output().map_err(|e| format!("could not run git: {e}"))?;
    if !out.status.success() || !out.stderr.is_empty() {
        return Err(format!("git {} failed: {}", args[0], String::from_utf8_lossy(&out.stderr).trim()));
    }
    String::from_utf8(out.stdout).map_err(|_| format!("git {} returned non-UTF-8 data", args[0]))
}

pub(super) fn relative(file: &str) -> Result<std::path::PathBuf, String> {
    let normalized = crate::paths::norm(file);
    let path = Path::new(&normalized);
    if path.as_os_str().is_empty() || path.components().any(|p| !matches!(p, Component::Normal(_))) {
        return Err(format!("{file}: expected a checkout-relative path"));
    }
    Ok(path.to_path_buf())
}

pub(super) fn proof(repo: &Repo, file: &str) -> Result<String, String> {
    let path = relative(file)?;
    let invalid = || format!("{file}: proof must be a file inside the checkout's .factory directory");
    if !path.starts_with(".factory") {
        return Err(invalid());
    }
    let resolved = repo.work.join(path).canonicalize().map_err(|e| format!("{file}: {e}"))?;
    let work = repo.work.canonicalize().map_err(|e| format!("checkout: {e}"))?;
    if !resolved.starts_with(work.join(".factory")) || !resolved.is_file() {
        return Err(invalid());
    }
    std::fs::read_to_string(resolved).map_err(|e| format!("{file}: {e}"))
}

fn build_record(run: &str) -> &str {
    through(run, &["## 6 Verify", "## 7 PR", "## 8 Review"])
}

/// Keep a prefix of the run through a phase, ignoring headings inside fences.
pub(super) fn through<'a>(run: &'a str, stop_at: &[&str]) -> &'a str {
    // Exact step heading outside fences, so examples in the run cannot cut off the record.
    let mut fence = None;
    let mut offset = 0;
    for line in run.split_inclusive('\n') {
        let text = line.trim();
        let marker = text.as_bytes().first().copied();
        let width = text.bytes().take_while(|&b| Some(b) == marker).count();
        match fence {
            Some((open, min)) if marker == Some(open) && width >= min && width == text.len() => fence = None,
            None if width >= 3 && matches!(marker, Some(b'`' | b'~')) => fence = marker.map(|m| (m, width)),
            _ => {}
        }
        if fence.is_none() && stop_at.iter().any(|heading| line.starts_with(heading)) {
            return &run[..offset];
        }
        offset += line.len();
    }
    run
}

pub(super) fn section(out: &mut String, name: &str, contents: &str) {
    // Pick a delimiter longer than any backtick run in the content.
    let length = contents.split(|c| c != '`').map(str::len).max().unwrap_or(0) + 1;
    let fence = "`".repeat(length.max(3));
    let name = name.replace(['\r', '\n'], " ");
    let newline = if contents.ends_with('\n') { "" } else { "\n" };
    writeln!(out, "## {name}\n\n{fence}text\n{contents}{newline}{fence}\n").unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn share_only_the_build_record_and_keep_examples() {
        let input =
            "## 5 Build\n````text\n```\n## 6 Verify example\n````\n~~~md\n## 8 Review example\n~~~\n## 6 Verify ✔\nprevious verdict\n";
        let cut = build_record(input);
        assert!(cut.contains("## 6 Verify example"));
        assert!(!cut.contains("previous verdict"));
        let mut out = String::new();
        section(&mut out, "run", cut);
        assert!(out.contains("`````text"));
    }

    #[test]
    fn reject_escaping_and_partial_options() {
        assert!(relative("../elsewhere").is_err());
        assert!(relative("/elsewhere").is_err());
        assert!(Options::parse(&["--head", "one", "--head", "two"]).is_err());
        assert!(Options::parse(&["--proof"]).is_err());
    }
}
