//! The ticket half of a close-out: is the run's ticket closed and does it record the merge?
//! Verify only: `ticketing` owns tracker writes; the agent fixes what this names, then reruns.

use super::facts::{Issue, Pr};

/// The GitHub issue URL a run header names, else None (another tracker, or `local: ...`).
pub fn github_issue(link: &str) -> Option<&str> {
    let rest = link.strip_prefix("https://github.com/")?;
    let mut p = rest.split('/');
    let ok = matches!((p.next(), p.next(), p.next(), p.next(), p.next()), (Some(o), Some(r), Some("issues"), Some(n), None)
        if !o.is_empty() && !r.is_empty() && !n.is_empty() && n.bytes().all(|b| b.is_ascii_digit()));
    ok.then_some(link)
}

/// What the ticket still lacks: `closed`, `PR link`, `merge commit`; empty when it records the merge.
/// A PR that closes the issue by keyword (or that GitHub lists as closing it) links both natively.
pub fn missing(pr: &Pr, issue: &Issue) -> Vec<&'static str> {
    let native = pr.closes.iter().any(|u| u == &issue.url) || issue.closed_by.iter().any(|u| u == &pr.url);
    let same_repo = issue.url.rsplit_once("/issues/").map(|(r, _)| r) == pr.url.rsplit_once("/pull/").map(|(r, _)| r);
    let pr_link = native || issue.text.contains(&pr.url) || (same_repo && cites(&issue.text, pr.number));
    let short = &pr.merge_oid[..pr.merge_oid.len().min(7)];
    let commit = native || (!short.is_empty() && issue.text.contains(short));
    [(!(issue.closed || issue.reopened), "closed"), (!pr_link, "PR link"), (!commit, "merge commit")]
        .into_iter()
        .filter(|(m, _)| *m)
        .map(|(_, w)| w)
        .collect()
}

/// True when `text` cites `#<n>` as a whole number (`#34` is not `#340`).
fn cites(text: &str, n: u64) -> bool {
    let tag = format!("#{n}");
    text.match_indices(&tag).any(|(i, _)| !text[i + tag.len()..].starts_with(|c: char| c.is_ascii_digit()))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pr() -> Pr {
        Pr {
            merged: true,
            url: "https://github.com/o/r/pull/34".into(),
            number: 34,
            head_ref: "fix/x".into(),
            head_oid: "a".repeat(40),
            merge_oid: "1234567890".into(),
            closes: vec![],
            base_ref: "main".into(),
            cross_repo: false,
        }
    }
    fn issue(closed: bool, text: &str) -> Issue {
        Issue { url: "https://github.com/o/r/issues/7".into(), closed, reopened: false, text: text.into(), closed_by: vec![] }
    }

    #[test]
    fn closing_keyword_links_both() {
        let mut p = pr();
        p.closes.push("https://github.com/o/r/issues/7".into());
        assert!(missing(&p, &issue(true, "")).is_empty());
        assert_eq!(missing(&p, &issue(false, "")), ["closed"]);
    }

    #[test]
    fn by_hand_record_needs_link_and_commit() {
        assert!(missing(&pr(), &issue(true, "Done: #34 merged as 1234567")).is_empty());
        assert_eq!(missing(&pr(), &issue(true, "see #340, commit 1234567")), ["PR link"]);
        assert_eq!(missing(&pr(), &issue(true, "https://github.com/o/r/pull/34")), ["merge commit"]);
        assert_eq!(missing(&pr(), &issue(false, "")), ["closed", "PR link", "merge commit"]);
        let reopened = Issue { reopened: true, ..issue(false, "#34 merged as 1234567") };
        assert!(missing(&pr(), &reopened).is_empty(), "a person reopened it after merge: it keeps that status");
    }

    #[test]
    fn github_issue_links_only() {
        assert!(github_issue("https://github.com/o/r/issues/7").is_some());
        for l in [
            "local: .factory/ticket.md",
            "https://github.com/o/r/pull/7",
            "https://linear.app/x/issue/A-1",
            "https://github.com/o/r/issues/7x",
        ] {
            assert!(github_issue(l).is_none(), "{l}");
        }
    }
}
