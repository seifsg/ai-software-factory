//! The merge facts a close-out acts on, read once from `gh` JSON: the PR and the run's ticket.
//! Why: the binary proves the merge itself instead of trusting a claim; parsing is split from fetching so
//! tests feed recorded JSON with no network.

use serde_json::Value;
use std::path::Path;

/// `gh pr view` fields the close-out needs.
pub const PR_FIELDS: &str = "state,url,number,headRefName,headRefOid,baseRefName,isCrossRepository,mergeCommit,closingIssuesReferences";
/// `gh issue view` fields the ticket check needs.
pub const ISSUE_FIELDS: &str = "url,state,stateReason,body,comments,closedByPullRequestsReferences";

/// A pull request as the close-out sees it.
#[derive(Debug, Clone, Default)]
pub struct Pr {
    pub merged: bool,
    pub url: String,
    pub number: u64,
    /// Branch name of the PR head, as pushed.
    pub head_ref: String,
    /// Full sha of the PR head at merge.
    pub head_oid: String,
    /// Full sha of the merge (or squash) commit; empty while unmerged.
    pub merge_oid: String,
    /// Issue URLs the PR closes with a closing keyword.
    pub closes: Vec<String>,
    /// Branch the PR merged into.
    pub base_ref: String,
    /// The head branch lives in a fork, not in this repository.
    pub cross_repo: bool,
}

/// A GitHub issue as the ticket check sees it.
#[derive(Debug, Clone, Default)]
pub struct Issue {
    pub url: String,
    pub closed: bool,
    /// Open again after a close (`stateReason` REOPENED): a person moved it, so it keeps that status.
    pub reopened: bool,
    /// Body and every comment, joined: where a PR link and merge commit can be recorded by hand.
    pub text: String,
    /// URLs of merged PRs GitHub records as closing it (its close event links the PR and the merge commit).
    pub closed_by: Vec<String>,
}

fn s(v: &Value, k: &str) -> String {
    v.get(k).and_then(Value::as_str).unwrap_or_default().to_string()
}

fn urls(v: &Value, k: &str) -> Vec<String> {
    v.get(k).and_then(Value::as_array).map(|a| a.iter().map(|x| s(x, "url")).filter(|u| !u.is_empty()).collect()).unwrap_or_default()
}

impl Pr {
    /// Err unless merged: the close-out never acts on an open or closed-unmerged PR.
    pub fn require_merged(&self) -> Result<(), String> {
        if self.merged { Ok(()) } else { Err(format!("{} is not merged", self.url)) }
    }

    /// Parses `gh pr view --json <PR_FIELDS>` output; a missing url or head means the JSON is not a PR.
    pub fn parse(json: &str) -> Result<Pr, String> {
        let v: Value = serde_json::from_str(json).map_err(|e| format!("PR JSON: {e}"))?;
        let pr = Pr {
            merged: s(&v, "state") == "MERGED",
            url: s(&v, "url"),
            number: v.get("number").and_then(Value::as_u64).unwrap_or(0),
            head_ref: s(&v, "headRefName"),
            head_oid: s(&v, "headRefOid"),
            merge_oid: v.get("mergeCommit").map(|m| s(m, "oid")).unwrap_or_default(),
            closes: urls(&v, "closingIssuesReferences"),
            base_ref: s(&v, "baseRefName"),
            cross_repo: v.get("isCrossRepository").and_then(Value::as_bool).unwrap_or(false),
        };
        if pr.url.is_empty() || pr.head_oid.is_empty() || pr.number == 0 {
            return Err("PR JSON lacks url, number or headRefOid".into());
        }
        if pr.merged && pr.merge_oid.is_empty() {
            return Err("merged PR JSON lacks mergeCommit".into());
        }
        Ok(pr)
    }
}

impl Issue {
    /// Parses `gh issue view --json <ISSUE_FIELDS>` output.
    pub fn parse(json: &str) -> Result<Issue, String> {
        let v: Value = serde_json::from_str(json).map_err(|e| format!("issue JSON: {e}"))?;
        let mut text = s(&v, "body");
        for c in v.get("comments").and_then(Value::as_array).into_iter().flatten() {
            text.push('\n');
            text.push_str(&s(c, "body"));
        }
        let issue = Issue {
            url: s(&v, "url"),
            closed: s(&v, "state") == "CLOSED",
            reopened: s(&v, "state") == "OPEN" && s(&v, "stateReason") == "REOPENED",
            text,
            closed_by: urls(&v, "closedByPullRequestsReferences"),
        };
        if issue.url.is_empty() {
            return Err("issue JSON lacks url".into());
        }
        Ok(issue)
    }
}

/// Runs `gh <args> --json <fields>` in `dir`; its stdout, or the first error line.
pub fn gh(dir: &Path, args: &[&str], fields: &str) -> Result<String, String> {
    let out = crate::paths::quiet_command("gh")
        .args(args)
        .args(["--json", fields])
        .current_dir(dir)
        .stdin(std::process::Stdio::null())
        .output()
        .map_err(|e| format!("gh: {e}"))?;
    if !out.status.success() {
        let err = String::from_utf8_lossy(&out.stderr);
        return Err(format!("gh {}: {}", args.join(" "), err.lines().find(|l| !l.trim().is_empty()).unwrap_or("failed")));
    }
    Ok(String::from_utf8_lossy(&out.stdout).into_owned())
}
